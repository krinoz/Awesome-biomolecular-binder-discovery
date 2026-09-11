#!/usr/bin/env python3
"""Bounded PPIformer mutation ddG inference with external checkpoints."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import torch


MUTATION = re.compile(r"^[ACDEFGHIKLMNPQRSTVWY][A-Za-z0-9][+-]?\d+[A-Za-z]?[ACDEFGHIKLMNPQRSTVWY]$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ppi-path", required=True)
    parser.add_argument("--mutations", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--impute", action="store_true")
    args = parser.parse_args()

    ppi_path = Path(args.ppi_path).resolve(strict=True)
    if not ppi_path.is_file() or ppi_path.suffix.lower() not in {".pdb", ".ent"}:
        raise ValueError("ppi-path must be an existing PDB file")
    if ppi_path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError("PPI structure exceeds the 20 MiB limit")
    if not 1 <= len(args.mutations) <= 128:
        raise ValueError("one to 128 mutations are required")
    for mutation_set in args.mutations:
        mutations = mutation_set.split(",")
        if not 1 <= len(mutations) <= 32 or any(not MUTATION.fullmatch(item) for item in mutations):
            raise ValueError(f"invalid SKEMPI mutation string: {mutation_set}")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    cache_dir = Path(os.environ.get("PPIFORMER_CACHE_DIR", "/work/cache/pyg")).resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)

    # PPIformer inference does not use experiment logging.  The inherited
    # ODesign image exposes a newer wandb build that requires Pydantic 2,
    # whereas Graphein/PPIformer require Pydantic 1.  Make Lightning take its
    # documented no-wandb import path instead of importing that unrelated
    # logger during model deserialization.
    sys.modules["wandb"] = None

    import ppiformer.definitions as definitions

    definitions.PPIFORMER_PYG_DATA_CACHE_DIR = cache_dir
    from ppiformer.tasks.node import DDGPPIformer
    from ppiformer.utils.api import predict_ddg

    weights_dir = Path(os.environ.get("PPIFORMER_WEIGHTS_DIR", "/models/ddg_regression"))
    checkpoints = [weights_dir / f"{index}.ckpt" for index in range(3)]
    missing = [str(path) for path in checkpoints if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing PPIformer checkpoints: {missing}")

    # The published checkpoints contain initialized LazyLinear modules whose
    # class was converted to Linear while retaining the lazy state-dict hook.
    # Newer Torch versions no longer expose that hook on Linear, so Python's
    # checkpoint unpickler cannot restore the bound method without this
    # compatibility alias.
    if not hasattr(torch.nn.Linear, "_lazy_load_hook"):
        torch.nn.Linear._lazy_load_hook = torch.nn.LazyLinear._lazy_load_hook
    from torch_geometric.nn.dense.linear import Linear as GeometricLinear

    if not hasattr(GeometricLinear, "_lazy_load_hook"):
        GeometricLinear._lazy_load_hook = torch.nn.LazyLinear._lazy_load_hook

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    models = [
        DDGPPIformer.load_from_checkpoint(path, map_location=torch.device("cpu")).eval().to(device)
        for path in checkpoints
    ]
    values = predict_ddg(models, ppi_path, args.mutations, impute=args.impute)
    ddg = values.detach().float().cpu().numpy()
    if ddg.shape != (len(args.mutations),) or not np.isfinite(ddg).all():
        raise RuntimeError("PPIformer returned invalid ddG values")

    payload = {
        "status": "success",
        "model": "PPIformer-ddg-regression-ensemble",
        "ppi_path": str(ppi_path),
        "device": str(device),
        "impute": args.impute,
        "predictions": [
            {"mutation": mutation, "ddg_kcal_mol": float(value)}
            for mutation, value in zip(args.mutations, ddg, strict=True)
        ],
        "interpretation": "Negative predicted ddG favors stronger binding; positive predicted ddG favors weaker binding.",
        "output_directory": str(output_dir),
    }
    result_path = output_dir / "result.json"
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    payload["result_path"] = str(result_path)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

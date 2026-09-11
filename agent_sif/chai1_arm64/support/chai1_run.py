#!/usr/bin/env python3
"""Bounded launcher for official Chai-1 inference."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np


def _finite_score_file(path: Path) -> dict[str, object]:
    with np.load(path) as values:
        summary: dict[str, object] = {"path": str(path), "arrays": {}}
        for key in values.files:
            array = values[key]
            summary["arrays"][key] = {
                "shape": list(array.shape),
                "finite": bool(np.isfinite(array).all()),
            }
        return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-fasta", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--num-trunk-recycles", type=int, default=1)
    parser.add_argument("--num-diffn-timesteps", type=int, default=200)
    parser.add_argument("--num-diffn-samples", type=int, default=1)
    parser.add_argument("--num-trunk-samples", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--use-esm-embeddings", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--use-msa-server", action="store_true")
    parser.add_argument("--use-templates-server", action="store_true")
    parser.add_argument("--low-memory", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--fasta-names-as-cif-chains", action="store_true")
    args = parser.parse_args()

    if not 0 <= args.num_trunk_recycles <= 3:
        raise ValueError("num-trunk-recycles must be between 0 and 3")
    if not 1 <= args.num_diffn_timesteps <= 200:
        raise ValueError("num-diffn-timesteps must be between 1 and 200")
    if not 1 <= args.num_diffn_samples <= 5:
        raise ValueError("num-diffn-samples must be between 1 and 5")
    if not 1 <= args.num_trunk_samples <= 2:
        raise ValueError("num-trunk-samples must be one or two")
    if args.use_templates_server and not args.use_msa_server:
        raise ValueError("template-server mode requires MSA-server mode")

    fasta_path = Path(args.input_fasta)
    if not fasta_path.is_absolute() or not fasta_path.is_file():
        raise ValueError("input-fasta must be an existing absolute container path")
    if fasta_path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("input FASTA exceeds 2 MiB")

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        raise ValueError("output-dir must be absolute")
    output_dir.mkdir(parents=True, exist_ok=False)

    os.environ.setdefault("MPLCONFIGDIR", "/work/cache/matplotlib")
    os.environ.setdefault("XDG_CACHE_HOME", "/work/cache")
    from chai_lab.chai1 import run_inference

    candidates = run_inference(
        fasta_file=fasta_path,
        output_dir=output_dir,
        use_esm_embeddings=args.use_esm_embeddings,
        use_msa_server=args.use_msa_server,
        use_templates_server=args.use_templates_server,
        num_trunk_recycles=args.num_trunk_recycles,
        num_diffn_timesteps=args.num_diffn_timesteps,
        num_diffn_samples=args.num_diffn_samples,
        num_trunk_samples=args.num_trunk_samples,
        seed=args.seed,
        device="cuda:0",
        low_memory=args.low_memory,
        fasta_names_as_cif_chains=args.fasta_names_as_cif_chains,
    )

    cif_paths = [Path(path) for path in candidates.cif_paths]
    if not cif_paths or any(not path.is_file() or path.stat().st_size == 0 for path in cif_paths):
        raise RuntimeError("Chai-1 returned no non-empty CIF")
    aggregate_scores = [float(item.aggregate_score.item()) for item in candidates.ranking_data]
    if not all(np.isfinite(score) for score in aggregate_scores):
        raise RuntimeError("Chai-1 returned a non-finite aggregate score")
    score_summaries = [_finite_score_file(path) for path in sorted(output_dir.glob("scores.*.npz"))]
    if any(not array["finite"] for item in score_summaries for array in item["arrays"].values()):
        raise RuntimeError("Chai-1 score file contains non-finite values")

    payload = {
        "status": "success",
        "model": "Chai-1",
        "input_fasta": str(fasta_path),
        "output_directory": str(output_dir),
        "cif_paths": [str(path) for path in cif_paths],
        "aggregate_scores": aggregate_scores,
        "score_files": score_summaries,
        "settings": {
            "num_trunk_recycles": args.num_trunk_recycles,
            "num_diffn_timesteps": args.num_diffn_timesteps,
            "num_diffn_samples": args.num_diffn_samples,
            "num_trunk_samples": args.num_trunk_samples,
            "seed": args.seed,
            "use_esm_embeddings": args.use_esm_embeddings,
            "use_msa_server": args.use_msa_server,
            "use_templates_server": args.use_templates_server,
            "low_memory": args.low_memory,
        },
    }
    result_path = output_dir / "result.json"
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

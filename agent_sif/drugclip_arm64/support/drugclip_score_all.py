#!/usr/bin/env python3
"""Score every pocket/ligand pair with DrugCLIP.

This is the containerized form of the latest retrieval workflow in
debug.ipynb: encode each ligand once, encode every pocket, calculate the
normalized embedding inner-product matrix, and save the long-form table as
Pocket,Ligand,Score with index=False.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from tqdm import tqdm

DRUGCLIP_ROOT = Path("/opt/DrugCLIP")
sys.path.insert(0, str(DRUGCLIP_ROOT))

import unicore  # noqa: E402
from unicore import checkpoint_utils, options, tasks  # noqa: E402
import unimol  # noqa: F401,E402  Registers DrugCLIP task/model.


def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run all-pairs DrugCLIP pocket/ligand retrieval."
    )
    parser.add_argument("--mol-lmdb", required=True)
    parser.add_argument("--pocket-lmdb", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--emb-dir", required=True)
    parser.add_argument("--data-dir", default=str(DRUGCLIP_ROOT / "data"))
    parser.add_argument("--max-pocket-atoms", type=int, default=256)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument(
        "--top-k-per-pocket",
        type=int,
        default=0,
        help="0 writes the full all-pairs table; positive values retain K ligands per pocket.",
    )
    return parser.parse_args()


def build_drugclip(cli: argparse.Namespace):
    if cli.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available inside the container")

    parser = options.get_validation_parser()
    options.add_model_args(parser)
    model_args = options.parse_args_and_arch(
        parser,
        input_args=[
            cli.data_dir,
            "--task",
            "drugclip",
            "--arch",
            "drugclip",
            "--valid-subset",
            "test",
            "--num-workers",
            "0",
            "--batch-size",
            "128",
            "--max-pocket-atoms",
            str(cli.max_pocket_atoms),
            "--seed",
            str(cli.seed),
            "--path",
            cli.checkpoint,
        ],
    )

    task = tasks.setup_task(model_args)
    model = task.build_model(model_args)
    state = checkpoint_utils.load_checkpoint_to_cpu(cli.checkpoint)
    missing = model.load_state_dict(state["model"], strict=False)
    if missing.missing_keys or missing.unexpected_keys:
        print(
            f"checkpoint load: missing={len(missing.missing_keys)} "
            f"unexpected={len(missing.unexpected_keys)}",
            file=sys.stderr,
        )
    model = model.to(cli.device)
    model.eval()
    return task, model


def encode_pockets(task, model, pocket_lmdb: str):
    dataset = task.load_pockets_dataset(pocket_lmdb)
    loader = torch.utils.data.DataLoader(
        dataset, batch_size=16, collate_fn=dataset.collater
    )
    representations: list[np.ndarray] = []
    names: list[str] = []

    for sample in tqdm(loader, desc="Encoding pockets"):
        sample = unicore.utils.move_to_cuda(sample)
        distance = sample["net_input"]["pocket_src_distance"]
        edge_type = sample["net_input"]["pocket_src_edge_type"]
        tokens = sample["net_input"]["pocket_src_tokens"]
        padding_mask = tokens.eq(model.pocket_model.padding_idx)
        embedded = model.pocket_model.embed_tokens(tokens)
        n_node = distance.size(-1)
        bias = model.pocket_model.gbf_proj(model.pocket_model.gbf(distance, edge_type))
        bias = bias.permute(0, 3, 1, 2).contiguous().view(-1, n_node, n_node)
        outputs = model.pocket_model.encoder(
            embedded, padding_mask=padding_mask, attn_mask=bias
        )
        projected = model.pocket_project(outputs[0][:, 0, :])
        projected = projected / projected.norm(dim=-1, keepdim=True)
        representations.append(projected.detach().cpu().numpy())
        names.extend(sample["pocket_name"])

    if not representations:
        raise ValueError("Pocket LMDB contained no records")
    return np.concatenate(representations, axis=0), names


def write_scores(
    pocket_reps: np.ndarray,
    pocket_names: list[str],
    mol_reps: np.ndarray,
    mol_names: list[str],
    output_csv: Path,
    top_k_per_pocket: int,
) -> int:
    scores = pocket_reps @ mol_reps.T
    matrix = pd.DataFrame(scores, index=pocket_names, columns=mol_names)
    pairs = matrix.stack().rename("Score").reset_index()
    pairs.columns = ["Pocket", "Ligand", "Score"]

    if top_k_per_pocket > 0:
        pairs = (
            pairs.sort_values(["Pocket", "Score"], ascending=[True, False])
            .groupby("Pocket", sort=False, as_index=False)
            .head(top_k_per_pocket)
        )
    pairs = pairs.sort_values("Score", ascending=False).reset_index(drop=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(output_csv, index=False)
    return len(pairs)


def main() -> None:
    cli = parse_cli()
    for name in ("mol_lmdb", "pocket_lmdb", "checkpoint"):
        path = Path(getattr(cli, name)).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"{name} not found: {path}")
        setattr(cli, name, str(path))
    if cli.top_k_per_pocket < 0:
        raise ValueError("--top-k-per-pocket must be zero or positive")

    output_csv = Path(cli.output_csv).resolve()
    emb_dir = Path(cli.emb_dir).resolve()
    emb_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")

    task, model = build_drugclip(cli)
    with torch.inference_mode():
        mol_reps, mol_names = task.encode_mols_once(
            model, cli.mol_lmdb, str(emb_dir), "atoms", "coordinates"
        )
        pocket_reps, pocket_names = encode_pockets(task, model, cli.pocket_lmdb)
        rows = write_scores(
            pocket_reps,
            pocket_names,
            mol_reps,
            mol_names,
            output_csv,
            cli.top_k_per_pocket,
        )

    print(
        f"wrote {rows} rows for {len(pocket_names)} pockets x "
        f"{len(mol_names)} ligands to {output_csv}"
    )


if __name__ == "__main__":
    main()

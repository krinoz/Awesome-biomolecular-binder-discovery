#!/usr/bin/env python3
"""Offline, bounded InterPLM feature extraction over shared ESM-2 weights."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import torch


MODELS = {
    "esm2-8m": {
        "path": "/models/esm2/esm2-8m",
        "layers": {1, 2, 3, 4, 5, 6},
        "sae": "/models/interplm/sae/esm2-8m",
    },
    "esm2-650m": {
        "path": "/models/esm2/esm2-650m",
        "layers": {1, 9, 18, 24, 30, 33},
        "sae": "/models/interplm/sae/esm2-650m",
    },
}
AA = re.compile(r"^[ACDEFGHIKLMNPQRSTVWYBXZJUO]+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract local ESM-2 embeddings and pretrained InterPLM SAE features."
    )
    parser.add_argument("--sequence", required=True, help="One amino-acid sequence, length 1-1022.")
    parser.add_argument("--model", choices=sorted(MODELS), default="esm2-8m")
    parser.add_argument("--layer", type=int, required=True)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--top-k", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sequence = re.sub(r"\s+", "", args.sequence).upper()
    if not 1 <= len(sequence) <= 1022 or not AA.fullmatch(sequence):
        raise ValueError("sequence must contain 1-1022 valid amino-acid symbols")
    spec = MODELS[args.model]
    if args.layer not in spec["layers"]:
        raise ValueError(f"unsupported pretrained SAE layer for {args.model}: {args.layer}")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    if not 1 <= args.top_k <= 100:
        raise ValueError("top-k must be between 1 and 100")

    model_path = Path(spec["path"])
    sae_dir = Path(spec["sae"]) / f"layer_{args.layer}"
    for required in (
        model_path / "config.json",
        model_path / "model.safetensors",
        model_path / "tokenizer_config.json",
        model_path / "vocab.txt",
        sae_dir / "ae_normalized.pt",
        sae_dir / "config.yaml",
    ):
        if not required.is_file():
            raise FileNotFoundError(required)

    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)

    from interplm.embedders.esm import ESM
    from interplm.sae.inference import load_sae

    embedder = ESM(model_name=str(model_path), device=args.device, max_length=1024)
    embeddings = embedder.embed_single_sequence(sequence, args.layer).astype(np.float32, copy=False)
    sae = load_sae(sae_dir, model_name="ae_normalized.pt", device=args.device)
    with torch.inference_mode():
        feature_tensor = sae.encode(torch.from_numpy(embeddings).to(args.device))
    features = feature_tensor.detach().float().cpu().numpy()

    if not np.isfinite(embeddings).all() or not np.isfinite(features).all():
        raise RuntimeError("non-finite embedding or SAE feature values")
    mean_activation = features.mean(axis=0)
    top = np.argsort(mean_activation)[-args.top_k :][::-1]

    np.save(output / "esm_embeddings.npy", embeddings)
    np.savez_compressed(output / "sae_features.npz", features=features)
    summary = {
        "status": "success",
        "model": args.model,
        "model_path": str(model_path),
        "layer": args.layer,
        "device": args.device,
        "sequence_length": len(sequence),
        "embedding_shape": list(embeddings.shape),
        "feature_shape": list(features.shape),
        "finite": True,
        "nonzero_features": int(np.count_nonzero(np.max(features, axis=0) > 0)),
        "top_mean_features": [
            {"feature": int(index), "mean_activation": float(mean_activation[index])}
            for index in top
        ],
        "embedding_path": str(output / "esm_embeddings.npy"),
        "features_path": str(output / "sae_features.npz"),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

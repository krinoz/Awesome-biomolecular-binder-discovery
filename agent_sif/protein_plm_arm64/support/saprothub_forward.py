#!/usr/bin/env python3
"""Offline, reproducible inference for the five retained SaProtHub models.

The model snapshots are mounted read-only below /models.  No network access is
required at inference time and no Hugging Face cache is populated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
from pathlib import Path

import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer


MODELS = {
    "colabsaprot_35m": {
        "hf_id": "westlake-repl/SaProt_35M_AF2",
        "revision": "316cd4017d29f4657b959365f24b57f1ee278912",
        "subdir": "colabsaprot_35m",
        "kind": "saprot",
    },
    "colabsaprot_650m": {
        "hf_id": "westlake-repl/SaProt_650M_AF2",
        "revision": "d9b9ad00ef61c0990e611b2b43f2231c7de24b38",
        "subdir": "colabsaprot_650m",
        "kind": "saprot",
    },
    "colabesm2_35m": {
        "hf_id": "facebook/esm2_t12_35M_UR50D",
        "revision": "6fbf070e65b0b7291e7bbcd451118c216cff79d8",
        "subdir": "colabesm2_35m",
        "kind": "sequence",
    },
    "colabesm2_150m": {
        "hf_id": "facebook/esm2_t30_150M_UR50D",
        "revision": "a695f6045e2e32885fa60af20c13cb35398ce30c",
        "subdir": "colabesm2_150m",
        "kind": "sequence",
    },
    "colabesm2_650m": {
        "hf_id": "facebook/esm2_t33_650M_UR50D",
        "revision": "08e4846e537177426273712802403f7ba8261b6c",
        "subdir": "colabesm2_650m",
        "kind": "sequence",
    },
}

AA_ALPHABET = set("ACDEFGHIKLMNPQRSTVWY")
THREEDI_ALPHABET = set("pynwrqhgdlvtmfsaeikc#")


def _clean_aa(value: str) -> str:
    seq = "".join(value.split()).upper()
    if not seq:
        raise ValueError("sequence is empty")
    invalid = sorted(set(seq) - AA_ALPHABET)
    if invalid:
        raise ValueError(f"unsupported amino-acid symbols: {''.join(invalid)}")
    return seq


def _token_input(alias: str, aa_sequence: str, structure_sequence: str | None) -> tuple[str, int]:
    aa = _clean_aa(aa_sequence)
    if len(aa) > 1022:
        raise ValueError("sequence exceeds the validated 1022-residue limit")
    if MODELS[alias]["kind"] != "saprot":
        if structure_sequence:
            raise ValueError("structure_sequence is only valid for ColabSaProt")
        return aa, len(aa)

    if structure_sequence is None:
        three_di = "#" * len(aa)
    else:
        three_di = "".join(structure_sequence.split()).lower()
        if len(three_di) != len(aa):
            raise ValueError("structure_sequence length must match the amino-acid sequence")
        invalid = sorted(set(three_di) - THREEDI_ALPHABET)
        if invalid:
            raise ValueError(f"unsupported Foldseek 3Di symbols: {''.join(invalid)}")
    # The official SaProt vocabulary consists of AA+3Di pairs.  Whitespace
    # keeps each two-character pair explicit for EsmTokenizer.
    return " ".join(a + s for a, s in zip(aa, three_di)), len(aa)


def _resolve_device(value: str) -> torch.device:
    if value == "auto":
        value = "cuda:0" if torch.cuda.is_available() else "cpu"
    device = torch.device(value)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable in the container")
    return device


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=sorted(MODELS))
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--structure-sequence")
    parser.add_argument("--models-root", default="/models")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--precision", choices=["bf16", "fp32"], default="bf16")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    started = time.perf_counter()
    spec = MODELS[args.model]
    model_dir = Path(args.models_root, spec["subdir"]).resolve(strict=True)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    model_input, residue_count = _token_input(args.model, args.sequence, args.structure_sequence)
    device = _resolve_device(args.device)
    dtype = torch.bfloat16 if args.precision == "bf16" and device.type == "cuda" else torch.float32
    if device.type == "cuda":
        torch.cuda.set_device(device)
        torch.cuda.reset_peak_memory_stats(device.index or 0)

    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    encoded = tokenizer(
        model_input,
        return_tensors="pt",
        return_special_tokens_mask=True,
        add_special_tokens=True,
    )
    special = encoded.pop("special_tokens_mask").bool()
    encoded = {key: value.to(device) for key, value in encoded.items()}
    model = AutoModelForMaskedLM.from_pretrained(
        model_dir,
        local_files_only=True,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
    ).to(device)
    model.eval()

    with torch.inference_mode():
        outputs = model(**encoded, output_hidden_states=True, return_dict=True)
        hidden = outputs.hidden_states[-1]
        valid = encoded["attention_mask"].bool() & ~special.to(device)
        residue_hidden = hidden[valid]
        if residue_hidden.shape[0] != residue_count:
            raise RuntimeError(
                f"token/residue mismatch: {residue_hidden.shape[0]} tokens for {residue_count} residues"
            )
        pooled = residue_hidden.float().mean(dim=0).cpu().contiguous()
        logits = outputs.logits

    pooled_bytes = pooled.numpy().tobytes()
    payload = {
        "status": "success",
        "model": args.model,
        "hf_id": spec["hf_id"],
        "revision": spec["revision"],
        "model_directory": str(model_dir),
        "sequence_length": residue_count,
        "input_token_count": int(encoded["input_ids"].shape[1]),
        "device": str(device),
        "dtype": str(next(model.parameters()).dtype),
        "hidden_shape": list(hidden.shape),
        "logits_shape": list(logits.shape),
        "pooled_embedding_shape": list(pooled.shape),
        "pooled_embedding_l2": float(torch.linalg.vector_norm(pooled)),
        "pooled_embedding_first8": [float(x) for x in pooled[:8]],
        "pooled_embedding_sha256": hashlib.sha256(pooled_bytes).hexdigest(),
        "finite": bool(torch.isfinite(pooled).all()),
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "torch_version": torch.__version__,
    }
    if device.type == "cuda":
        payload["gpu_peak_allocated_bytes"] = int(torch.cuda.max_memory_allocated(device.index or 0))
        payload["gpu_peak_reserved_bytes"] = int(torch.cuda.max_memory_reserved(device.index or 0))
    if not payload["finite"] or not math.isfinite(payload["pooled_embedding_l2"]):
        raise RuntimeError("model produced a non-finite embedding")
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

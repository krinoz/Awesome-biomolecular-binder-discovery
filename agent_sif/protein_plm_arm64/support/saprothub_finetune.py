#!/usr/bin/env python3
"""Bounded SaProtHub LoRA fine-tuning and fresh-process adapter validation."""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import torch


SAPROT_ROOT = Path("/opt/SaProtHub/saprot")
MODEL_ROOT = Path("/models")
WORK_ROOT = Path("/work")
INPUT_ROOT = WORK_ROOT / "finetune_inputs"
OUTPUT_ROOT = WORK_ROOT / "finetune"
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

MODELS = {
    "colabsaprot_35m": MODEL_ROOT / "colabsaprot_35m",
    "colabsaprot_650m": MODEL_ROOT / "colabsaprot_650m",
}
TASKS = {
    "classification": ("saprot/saprot_classification_model", "saprot/saprot_classification_dataset"),
    "regression": ("saprot/saprot_regression_model", "saprot/saprot_regression_dataset"),
    "token_classification": ("saprot/saprot_token_classification_model", "saprot/saprot_token_classification_dataset"),
    "pair_classification": ("saprot/saprot_pair_classification_model", "saprot/saprot_pair_classification_dataset"),
    "pair_regression": ("saprot/saprot_pair_regression_model", "saprot/saprot_pair_regression_dataset"),
}
MAX_CSV_BYTES = 2 * 1024 * 1024
MAX_ROWS = 2048
MAX_STEPS = 100
MAX_BATCH = 8


def canonical_under(path: str | Path, root: Path) -> Path:
    value = Path(path).resolve(strict=True)
    root = root.resolve(strict=True)
    if value != root and root not in value.parents:
        raise ValueError(f"path must be under {root}: {value}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def adapter_inventory(adapter_dir: Path) -> list[dict]:
    result = []
    for path in sorted(p for p in adapter_dir.rglob("*") if p.is_file()):
        result.append({
            "path": str(path.relative_to(adapter_dir)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    return result


def normalize_sequence(sequence: str) -> str:
    sequence = sequence.strip().replace(" ", "")
    if not sequence or len(sequence) > 2044:
        raise ValueError("sequence must contain 1..2044 characters before SaProt tokenization")
    if all(ch in "ACDEFGHIKLMNPQRSTVWYBXZJUO" for ch in sequence.upper()):
        return "".join(f"{aa.upper()}#" for aa in sequence)
    if len(sequence) % 2:
        raise ValueError("SaProt AA+3Di sequence must have an even number of characters")
    return sequence


def validate_and_copy_csv(source: Path, destination: Path, task: str) -> dict:
    if source.stat().st_size > MAX_CSV_BYTES:
        raise ValueError(f"CSV exceeds {MAX_CSV_BYTES} bytes")
    required = {
        "classification": {"sequence", "label", "stage"},
        "regression": {"sequence", "label", "stage"},
        "token_classification": {"sequence", "label", "stage"},
        "pair_classification": {"sequence_1", "sequence_2", "label", "stage", "name_1", "name_2", "chain_1", "chain_2"},
        "pair_regression": {"sequence_1", "sequence_2", "label", "stage", "name_1", "name_2", "chain_1", "chain_2"},
    }[task]
    with source.open(newline="", encoding="utf-8") as src:
        reader = csv.DictReader(src)
        fields = [str(f).lower() for f in (reader.fieldnames or [])]
        if not required.issubset(fields):
            raise ValueError(f"CSV needs columns {sorted(required)}; got {fields}")
        rows = []
        stage_counts = {"train": 0, "valid": 0, "test": 0}
        for idx, raw in enumerate(reader):
            if idx >= MAX_ROWS:
                raise ValueError(f"CSV exceeds {MAX_ROWS} data rows")
            row = {str(k).lower(): v for k, v in raw.items()}
            stage = str(row["stage"]).strip().lower()
            if stage not in stage_counts:
                raise ValueError(f"row {idx + 2}: stage must be train, valid, or test")
            row["stage"] = stage
            stage_counts[stage] += 1
            if task.startswith("pair_"):
                row["sequence_1"] = normalize_sequence(str(row["sequence_1"]))
                row["sequence_2"] = normalize_sequence(str(row["sequence_2"]))
            else:
                row["sequence"] = normalize_sequence(str(row["sequence"]))
            if "classification" in task and task != "token_classification":
                row["label"] = str(int(row["label"]))
            elif "regression" in task:
                value = float(row["label"])
                if not math.isfinite(value):
                    raise ValueError(f"row {idx + 2}: non-finite label")
                row["label"] = repr(value)
            rows.append(row)
    if not rows or not stage_counts["train"] or not stage_counts["valid"]:
        raise ValueError("CSV must have at least one train row and one valid row")
    destination.parent.mkdir(parents=True, exist_ok=False)
    with destination.open("w", newline="", encoding="utf-8") as dst:
        writer = csv.DictWriter(dst, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return {"rows": len(rows), "stage_counts": stage_counts, "input_sha256": sha256(source)}


def import_official():
    sys.path.insert(0, str(SAPROT_ROOT))
    from easydict import EasyDict
    from utils import lr_scheduler as official_lr
    from utils.construct_lmdb import construct_lmdb
    from utils.module_loader import my_load_dataset, my_load_model
    # torch>=2.6 removed the positional ``verbose`` argument used by the pinned
    # official scheduler. Preserve the official constant-LR semantics on NGC torch 2.8.
    def constant_lr_init(self, optimizer, last_epoch=-1, verbose=False, init_lr=0.0):
        del verbose
        self.init_lr = init_lr
        torch.optim.lr_scheduler.LRScheduler.__init__(self, optimizer, last_epoch=last_epoch)
    official_lr.ConstantLRScheduler.__init__ = constant_lr_init
    return EasyDict, construct_lmdb, my_load_dataset, my_load_model


def model_config(EasyDict, model_path: Path, task: str, num_labels: int, learning_rate: float,
                 rank: int, alpha: int, dropout: float, adapter_dir: Path | None = None):
    model_py, _ = TASKS[task]
    config_list = [] if adapter_dir is None else [{"lora_config_path": str(adapter_dir)}]
    return EasyDict({
        "model_py_path": model_py,
        "num_labels": num_labels,
        "kwargs": {
            "config_path": str(model_path),
            "load_pretrained": True,
            "freeze_backbone": False,
            "gradient_checkpointing": False,
            "save_path": None,
            "save_weights_only": True,
            "lr_scheduler_kwargs": {"class": "ConstantLRScheduler", "init_lr": learning_rate},
            "optimizer_kwargs": {"class": "AdamW", "betas": [0.9, 0.98], "weight_decay": 0.01},
            "lora_kwargs": {
                "num_lora": 1,
                "r": rank,
                "lora_alpha": alpha,
                "lora_dropout": dropout,
                "is_trainable": adapter_dir is None,
                "config_list": config_list,
            },
        },
    })


def dataset_config(EasyDict, model_path: Path, task: str, lmdb_root: Path, batch_size: int):
    _, dataset_py = TASKS[task]
    return EasyDict({
        "dataset_py_path": dataset_py,
        "tokenizer": str(model_path),
        "train_lmdb": str(lmdb_root / "train"),
        "valid_lmdb": str(lmdb_root / "valid"),
        "test_lmdb": str(lmdb_root / "test"),
        "dataloader_kwargs": {"batch_size": batch_size, "num_workers": 0, "pin_memory": False},
        "kwargs": {},
    })


def read_first_sequence(csv_path: Path, task: str) -> str:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    return row["sequence_1" if task.startswith("pair_") else "sequence"]


def train(args: argparse.Namespace) -> dict:
    if args.model not in MODELS or args.task not in TASKS:
        raise ValueError("unsupported model or task")
    if not SAFE_NAME.fullmatch(args.run_name):
        raise ValueError("run_name must match [A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
    if not 1 <= args.max_steps <= MAX_STEPS or not 1 <= args.batch_size <= MAX_BATCH:
        raise ValueError(f"max_steps must be 1..{MAX_STEPS}; batch_size 1..{MAX_BATCH}")
    if not 2 <= args.num_labels <= 128:
        raise ValueError("num_labels must be 2..128")
    if not 1e-7 <= args.learning_rate <= 1e-2:
        raise ValueError("learning_rate must be within 1e-7..1e-2")
    if args.rank not in (2, 4, 8, 16, 32) or not 1 <= args.alpha <= 128 or not 0 <= args.dropout <= 0.5:
        raise ValueError("invalid bounded LoRA hyperparameters")

    source = canonical_under(args.csv, INPUT_ROOT)
    model_path = MODELS[args.model].resolve(strict=True)
    output_root = OUTPUT_ROOT.resolve(strict=True)
    output_dir = output_root / args.run_name
    if output_dir.exists():
        raise FileExistsError(f"output already exists: {output_dir}")
    csv_copy = output_dir / "input.csv"
    input_info = validate_and_copy_csv(source, csv_copy, args.task)
    lmdb_root = output_dir / "lmdb" / "dataset"
    adapter_dir = output_dir / "adapter"
    result_path = output_dir / "result.json"

    EasyDict, construct_lmdb, my_load_dataset, my_load_model = import_official()
    construct_lmdb(str(csv_copy), str(output_dir / "lmdb"), "dataset", args.task)
    model_cfg = model_config(EasyDict, model_path, args.task, args.num_labels, args.learning_rate,
                             args.rank, args.alpha, args.dropout)
    data_cfg = dataset_config(EasyDict, model_path, args.task, lmdb_root, args.batch_size)

    import pytorch_lightning as pl
    pl.seed_everything(args.seed, workers=True)
    use_cuda = args.device == "cuda:0"
    if use_cuda:
        torch.cuda.reset_peak_memory_stats()
    model = my_load_model(model_cfg)
    # Official notebook plotting assumes google.colab; the cluster MCP is deliberately headless.
    model.plot_valid_metrics_curve = lambda _metrics: None
    data_module = my_load_dataset(data_cfg)
    trainer = pl.Trainer(
        accelerator="gpu" if use_cuda else "cpu", devices=1,
        precision="bf16-mixed" if use_cuda else "32-true", logger=False,
        enable_checkpointing=False, enable_model_summary=False, max_epochs=1,
        max_steps=args.max_steps, limit_train_batches=args.max_steps,
        limit_val_batches=1, num_sanity_val_steps=0, use_distributed_sampler=False,
    )
    started = time.time()
    trainer.fit(model=model, datamodule=data_module)
    elapsed = time.time() - started
    model.model.save_pretrained(adapter_dir, safe_serialization=True)
    peak_alloc = int(torch.cuda.max_memory_allocated()) if use_cuda else 0
    peak_reserved = int(torch.cuda.max_memory_reserved()) if use_cuda else 0
    inventory = adapter_inventory(adapter_dir)
    first_sequence = read_first_sequence(csv_copy, args.task)
    del trainer, data_module, model
    gc.collect()
    torch.cuda.empty_cache()

    reload_path = output_dir / "reload.json"
    command = [
        sys.executable, str(Path(__file__).resolve()), "reload",
        "--model", args.model, "--task", args.task, "--adapter", str(adapter_dir),
        "--sequence", first_sequence, "--num-labels", str(args.num_labels),
        "--rank", str(args.rank), "--alpha", str(args.alpha), "--dropout", str(args.dropout),
        "--output", str(reload_path), "--device", args.device,
    ]
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=900)
    if completed.returncode or not reload_path.is_file():
        raise RuntimeError("fresh-process adapter reload failed:\n" + (completed.stderr + completed.stdout)[-12000:])
    reload_result = json.loads(reload_path.read_text())
    payload = {
        "status": "ok", "model": args.model, "task": args.task, "run_name": args.run_name,
        "official_revision": "2f39673a37e0b35f83788dcf8ef5ad326a42871c",
        "max_steps": args.max_steps, "trainer_global_step": args.max_steps,
        "limit_val_batches": 1, "precision": "bf16-mixed" if use_cuda else "fp32", "device": args.device,
        "elapsed_seconds": elapsed,
        "peak_memory_allocated_bytes": peak_alloc, "peak_memory_reserved_bytes": peak_reserved,
        "adapter_dir": str(adapter_dir), "adapter_files": inventory,
        "fresh_process_reload": reload_result, **input_info,
    }
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(output_dir / "lmdb")
    return payload


def reload_adapter(args: argparse.Namespace) -> dict:
    adapter = canonical_under(args.adapter, OUTPUT_ROOT)
    output = Path(args.output).resolve()
    if OUTPUT_ROOT.resolve() not in output.parents:
        raise ValueError("reload output must be under external finetune runtime")
    EasyDict, _, _, my_load_model = import_official()
    model_path = MODELS[args.model].resolve(strict=True)
    cfg = model_config(EasyDict, model_path, args.task, args.num_labels, 1e-4,
                       args.rank, args.alpha, args.dropout, adapter)
    use_cuda = args.device == "cuda:0"
    if use_cuda:
        torch.cuda.reset_peak_memory_stats()
    model = my_load_model(cfg).to(args.device).eval()
    tokenizer = model.tokenizer
    sequence = normalize_sequence(args.sequence)
    tokens = tokenizer.tokenize(sequence)[:1022]
    encoded = tokenizer.batch_encode_plus([" ".join(tokens)], return_tensors="pt", padding=True)
    encoded = {k: v.to(args.device) for k, v in encoded.items()}
    autocast = torch.autocast("cuda", dtype=torch.bfloat16) if use_cuda else torch.autocast("cpu", enabled=False)
    with torch.inference_mode(), autocast:
        if args.task.startswith("pair_"):
            raise ValueError("fresh reload validation currently requires a non-pair task")
        logits = model(inputs=encoded)
    tensor = logits.detach().float().cpu()
    finite = bool(torch.isfinite(tensor).all().item())
    payload = {
        "status": "ok" if finite else "nonfinite", "finite": finite,
        "shape": list(tensor.shape), "mean": float(tensor.mean()), "std": float(tensor.std(unbiased=False)),
        "tensor_sha256": hashlib.sha256(tensor.numpy().tobytes()).hexdigest(),
        "peak_memory_allocated_bytes": int(torch.cuda.max_memory_allocated()) if use_cuda else 0,
        "peak_memory_reserved_bytes": int(torch.cuda.max_memory_reserved()) if use_cuda else 0,
        "pid": os.getpid(),
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if not finite:
        raise RuntimeError("adapter prediction produced non-finite values")
    return payload


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)
    p = sub.add_parser("train")
    p.add_argument("--model", choices=sorted(MODELS), required=True)
    p.add_argument("--task", choices=sorted(TASKS), required=True)
    p.add_argument("--csv", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--max-steps", type=int, default=1)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--num-labels", type=int, default=2)
    p.add_argument("--learning-rate", type=float, default=1e-4)
    p.add_argument("--rank", type=int, default=8)
    p.add_argument("--alpha", type=int, default=16)
    p.add_argument("--dropout", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=20000812)
    p.add_argument("--device", choices=["cuda:0", "cpu"], default="cuda:0")
    p = sub.add_parser("reload")
    p.add_argument("--model", choices=sorted(MODELS), required=True)
    p.add_argument("--task", choices=sorted(TASKS), required=True)
    p.add_argument("--adapter", required=True)
    p.add_argument("--sequence", required=True)
    p.add_argument("--num-labels", type=int, required=True)
    p.add_argument("--rank", type=int, required=True)
    p.add_argument("--alpha", type=int, required=True)
    p.add_argument("--dropout", type=float, required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--device", choices=["cuda:0", "cpu"], default="cuda:0")
    return root


def main() -> int:
    args = parser().parse_args()
    payload = train(args) if args.command == "train" else reload_adapter(args)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

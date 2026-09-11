#!/usr/bin/env python3
"""Bounded launcher for official DISCO inference with external weights."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--experiment", choices=["designable", "diverse"], default="designable")
    parser.add_argument("--effort", choices=["fast", "max"], default="fast")
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--disable-deepspeed-attention", action="store_true")
    args = parser.parse_args()

    input_json = Path(args.input_json).resolve(strict=True)
    if input_json.suffix.lower() != ".json" or not input_json.is_file():
        raise ValueError("input-json must be an existing JSON file")
    if input_json.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("input JSON exceeds the 2 MiB MCP limit")
    jobs = json.loads(input_json.read_text())
    if not isinstance(jobs, list) or not 1 <= len(jobs) <= 32:
        raise ValueError("DISCO input must contain one to 32 jobs")
    if not 1 <= len(args.seeds) <= 8 or any(seed < 0 or seed > 2147483647 for seed in args.seeds):
        raise ValueError("one to eight non-negative seeds are required")
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)

    seeds = "[" + ",".join(str(seed) for seed in args.seeds) + "]"
    command = [
        "/opt/envs/disco/bin/python", "/opt/DISCO/runner/inference.py",
        f"experiment={args.experiment}", f"effort={args.effort}",
        f"input_json_path={input_json}", f"seeds={seeds}",
        f"dump_dir={output_dir}", "load_checkpoint_path=/models/DISCO.pt",
    ]
    if args.disable_deepspeed_attention:
        command.append("model.use_deepspeed_evo_attention=false")
    environment = os.environ.copy()
    environment.update({
        "PYTHONPATH": "/opt/DISCO",
        "DISCO_DPLM_PATH": "/models/dplm_650m",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "WANDB_MODE": "offline",
    })
    completed = subprocess.run(
        command,
        # Hydra creates its own timestamped log directory relative to cwd.
        # Keep that write under the MCP result directory rather than the
        # immutable SIF filesystem.
        cwd=output_dir,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=7200,
    )
    log_path = output_dir / "disco.log"
    log_path.write_text(completed.stdout)
    errors = [path for path in (output_dir / "ERR").glob("*") if path.is_file() and path.stat().st_size]
    structures = sorted([*output_dir.rglob("*.pdb"), *output_dir.rglob("*.cif")])
    sequences = sorted(path for path in output_dir.rglob("*.txt") if "ERR" not in path.parts)
    if completed.returncode or errors or not structures or not sequences:
        detail = completed.stdout[-16000:]
        raise RuntimeError(
            f"DISCO failed or lacked structure/sequence outputs (rc={completed.returncode}, errors={len(errors)}):\n{detail}"
        )
    payload = {
        "status": "success",
        "model": "DISCO",
        "input_json_path": str(input_json),
        "experiment": args.experiment,
        "effort": args.effort,
        "seeds": args.seeds,
        "output_directory": str(output_dir),
        "structure_paths": [str(path) for path in structures],
        "sequence_paths": [str(path) for path in sequences],
        "log_path": str(log_path),
    }
    result_path = output_dir / "result.json"
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

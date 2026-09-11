#!/usr/bin/env python3
"""Bounded launcher for the official ODesign rigid-protein checkpoint."""

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
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--num-samples", type=int, default=1)
    parser.add_argument("--num-steps", type=int, default=200)
    parser.add_argument("--num-cycles", type=int, default=10)
    parser.add_argument("--invfold-topk", type=int, default=1)
    parser.add_argument("--invfold-temperature", type=float, default=1.0)
    parser.add_argument("--use-msa", action="store_true")
    parser.add_argument("--enable-partial-diffusion", action="store_true")
    parser.add_argument("--partial-diffusion-snr", type=float, default=0.1)
    args = parser.parse_args()

    input_json = Path(args.input_json).resolve(strict=True)
    if input_json.suffix.lower() != ".json" or not input_json.is_file():
        raise ValueError("input-json must be an existing JSON file")
    payload = json.loads(input_json.read_text())
    if not isinstance(payload, list) or not payload:
        raise ValueError("input-json must contain a non-empty list of design records")
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    for record in payload:
        if not isinstance(record, dict):
            raise ValueError("each design record must be a JSON object")
        ref_file = record.get("ref_file")
        if not ref_file:
            continue
        ref_path = Path(ref_file)
        candidates = [ref_path] if ref_path.is_absolute() else [
            input_json.parent / ref_path,
            Path("/opt/ODesign") / ref_path,
        ]
        resolved_ref = next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)
        if resolved_ref is None:
            raise FileNotFoundError(f"referenced structure does not exist: {ref_file}")
        record["ref_file"] = str(resolved_ref)
    resolved_input_json = output_dir / "input.resolved.json"
    resolved_input_json.write_text(json.dumps(payload, indent=2) + "\n")
    if not 1 <= len(args.seeds) <= 8 or any(seed < 0 or seed > 2147483647 for seed in args.seeds):
        raise ValueError("one to eight non-negative seeds are required")
    if not 1 <= args.num_samples <= 16 or not 1 <= args.num_steps <= 200 or not 0 <= args.num_cycles <= 10:
        raise ValueError("num-samples/num-steps/num-cycles exceed the bounded MCP range")
    if not 1 <= args.invfold_topk <= 16 or not 0.01 <= args.invfold_temperature <= 5.0:
        raise ValueError("invalid inverse-folding settings")

    seeds = "[" + ",".join(str(seed) for seed in args.seeds) + "]"
    command = [
        "/opt/envs/odesign/bin/python", "/opt/ODesign/scripts/inference.py",
        "exp=train_odesign_base_prot_rigid",
        "data_root_dir=/data",
        "ckpt_root_dir=/ckpt",
        "exp.infer_model_name=odesign_base_prot_rigid",
        "exp.design_modality=protein",
        f"exp.input_json_path={resolved_input_json}",
        "exp.exp_name=odesign_prot_rigid",
        f"exp.seeds={seeds}",
        f"exp.model.sample_diffusion.N_sample={args.num_samples}",
        f"exp.model.sample_diffusion.N_step={args.num_steps}",
        f"exp.model.N_cycle={args.num_cycles}",
        f"exp.invfold_topk={args.invfold_topk}",
        f"exp.invfold_temp={args.invfold_temperature}",
        f"exp.use_msa={'true' if args.use_msa else 'false'}",
        "exp.num_workers=0",
        f"exp.model.inference_noise_schedulers.coordinate.partial_diffusion.enable={'true' if args.enable_partial_diffusion else 'false'}",
        f"exp.model.inference_noise_schedulers.coordinate.partial_diffusion.snr={args.partial_diffusion_snr}",
        "hydra/job_logging=default",
        "hydra/hydra_logging=default",
        f"hydra.run.dir={output_dir}",
    ]
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": "/opt/ODesign",
            "WANDB_MODE": "offline",
            "TRITON_CACHE_DIR": "/work/cache/triton",
        }
    )
    completed = subprocess.run(
        command,
        cwd="/opt/ODesign",
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=7200,
    )
    (output_dir / "odesign.log").write_text(completed.stdout)
    errors = [path for path in (output_dir / "errors").glob("*") if path.is_file() and path.stat().st_size]
    structures = sorted(output_dir.rglob("*.cif"))
    if completed.returncode or errors or not structures:
        detail = completed.stdout[-16000:]
        raise RuntimeError(f"ODesign failed or produced no CIF (rc={completed.returncode}, errors={len(errors)}):\n{detail}")
    payload = {
        "status": "success",
        "model": "odesign_base_prot_rigid",
        "input_json_path": str(input_json),
        "output_directory": str(output_dir),
        "seeds": args.seeds,
        "num_samples": args.num_samples,
        "num_steps": args.num_steps,
        "num_cycles": args.num_cycles,
        "structure_paths": [str(path) for path in structures],
        "log_path": str(output_dir / "odesign.log"),
    }
    result_path = output_dir / "result.json"
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

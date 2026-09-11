#!/usr/bin/env python3
"""Extract per-chain amino-acid and Foldseek 3Di sequences safely."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from Bio.PDB import MMCIFParser, PDBParser
from Bio.PDB.Polypeptide import is_aa


def _chain_from_descriptor(descriptor: str) -> str:
    token = descriptor.split()[0]
    if "_" not in token:
        raise ValueError(f"Foldseek descriptor has no chain suffix: {descriptor!r}")
    chain = token.rsplit("_", 1)[-1]
    if not chain:
        raise ValueError(f"Foldseek descriptor has an empty chain: {descriptor!r}")
    return chain


def _plddt_for_chain(path: Path, chain_id: str) -> np.ndarray:
    suffix = path.suffix.lower()
    parser = MMCIFParser(QUIET=True) if suffix in {".cif", ".mmcif"} else PDBParser(QUIET=True)
    model = parser.get_structure("input", str(path))[0]
    if chain_id not in model:
        raise ValueError(f"chain {chain_id!r} is absent from the parsed structure")
    values: list[float] = []
    for residue in model[chain_id]:
        if not is_aa(residue, standard=False) or "CA" not in residue:
            continue
        atoms = list(residue.get_atoms())
        values.append(float(np.mean([atom.get_bfactor() for atom in atoms])))
    return np.asarray(values, dtype=float)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--structure", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--chain")
    parser.add_argument("--foldseek", default="/opt/foldseek/bin/foldseek")
    parser.add_argument("--plddt-mask", action="store_true")
    parser.add_argument("--plddt-threshold", type=float, default=70.0)
    args = parser.parse_args()

    structure = Path(args.structure).resolve(strict=True)
    if not structure.is_file() or structure.suffix.lower() not in {".pdb", ".cif", ".mmcif"}:
        raise ValueError("structure must be an existing PDB or mmCIF file")
    foldseek = Path(args.foldseek).resolve(strict=True)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="foldseek-3di-", dir=output.parent) as temporary:
        descriptor_path = Path(temporary, "descriptor.tsv")
        completed = subprocess.run(
            [
                str(foldseek), "structureto3didescriptor", "-v", "0", "--threads", "1",
                "--chain-name-mode", "1", str(structure), str(descriptor_path),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
        )
        if completed.returncode or not descriptor_path.is_file():
            raise RuntimeError((completed.stderr + "\n" + completed.stdout)[-12000:])

        for raw_line in descriptor_path.read_text().splitlines():
            fields = raw_line.split("\t")
            if len(fields) < 3:
                raise ValueError(f"malformed Foldseek descriptor row: {raw_line[:200]!r}")
            chain = _chain_from_descriptor(fields[0])
            if args.chain is not None and chain != args.chain:
                continue
            sequence = fields[1].strip().upper()
            structure_sequence = fields[2].strip().lower()
            if len(sequence) != len(structure_sequence):
                raise ValueError(f"Foldseek AA/3Di length mismatch for chain {chain}")
            masked = 0
            if args.plddt_mask:
                scores = _plddt_for_chain(structure, chain)
                if len(scores) != len(structure_sequence):
                    raise ValueError(
                        f"pLDDT/3Di length mismatch for chain {chain}: {len(scores)} != {len(structure_sequence)}"
                    )
                chars = np.asarray(list(structure_sequence), dtype="<U1")
                low = scores < args.plddt_threshold
                chars[low] = "#"
                masked = int(low.sum())
                structure_sequence = "".join(chars.tolist())
            records.append({
                "chain": chain,
                "sequence": sequence,
                "structure_sequence": structure_sequence,
                "combined_sequence": "".join(a + b for a, b in zip(sequence, structure_sequence)),
                "length": len(sequence),
                "masked_3di_positions": masked,
            })

    if not records:
        requested = f" chain {args.chain!r}" if args.chain is not None else ""
        raise ValueError(f"Foldseek produced no protein records for{requested}")
    if len(records) > 64 or sum(item["length"] for item in records) > 8192:
        raise ValueError("structure exceeds the bounded 64-chain/8192-residue MCP limit")
    payload = {
        "status": "success",
        "structure_path": str(structure),
        "plddt_mask": bool(args.plddt_mask),
        "plddt_threshold": args.plddt_threshold,
        "records": records,
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create two ligands and one pocket for a real DrugCLIP container test."""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import lmdb
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem


def write_lmdb(path: Path, records: list[dict]) -> None:
    env = lmdb.open(
        str(path), subdir=False, map_size=64 * 1024 * 1024, lock=True
    )
    with env.begin(write=True) as txn:
        for index, record in enumerate(records):
            txn.put(str(index).encode("ascii"), pickle.dumps(record))
    env.sync()
    env.close()


def ligand(smiles: str) -> dict:
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    params = AllChem.ETKDGv3()
    params.randomSeed = 20260828
    if AllChem.EmbedMolecule(mol, params) != 0:
        raise RuntimeError(f"Could not embed {smiles}")
    AllChem.UFFOptimizeMolecule(mol, maxIters=50)
    mol = Chem.RemoveHs(mol)
    return {
        "atoms": [atom.GetSymbol() for atom in mol.GetAtoms()],
        "coordinates": [np.asarray(mol.GetConformer().GetPositions(), dtype=np.float32)],
        "smi": Chem.MolToSmiles(mol),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir")
    args = parser.parse_args()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    write_lmdb(output / "mols.lmdb", [ligand("CCO"), ligand("CCN")])
    write_lmdb(
        output / "pockets.lmdb",
        [
            {
                "pocket": "tiny_pocket",
                "pocket_atoms": ["CA", "N", "C", "O", "CB", "S"],
                "pocket_coordinates": np.asarray(
                    [
                        [0.0, 0.0, 0.0],
                        [1.4, 0.1, 0.0],
                        [2.5, 0.8, 0.1],
                        [3.6, 0.5, 0.0],
                        [1.2, 1.5, 0.7],
                        [2.1, 2.4, 1.0],
                    ],
                    dtype=np.float32,
                ),
            }
        ],
    )
    print(output / "mols.lmdb")
    print(output / "pockets.lmdb")


if __name__ == "__main__":
    main()

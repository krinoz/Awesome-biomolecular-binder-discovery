# DrugCLIP ARM64 container

This image contains the official DrugCLIP source and its required Uni-Mol
encoder implementation. The full DrugCLIP checkpoint is mounted externally;
the standalone Uni-Mol pretraining checkpoint is intentionally not used.

The production entry follows the latest `debug.ipynb` workflow: ligand
embeddings are cached, pocket embeddings are computed, every pocket/ligand
inner product is calculated, and a long-form `Pocket,Ligand,Score` CSV is
written with `index=False`.

```bash
/path/to/mcp-suite/patches/run_drugclip.sh \
  ligands.lmdb pockets.lmdb scores.csv embeddings 0
```

The final argument is top-K per pocket. Zero retains the complete all-pairs
table. Application commands are not added to `PATH`; the launcher calls the
absolute Python and script paths.

Expected ligand LMDB keys are `atoms`, `coordinates`, and `smi`. Expected
pocket LMDB keys are `pocket_atoms`, `pocket_coordinates`, and optionally
`pocket` for the displayed pocket name.

The original upstream README is `/opt/DrugCLIP/README.md`. The private
development notebook is not redistributed in this publication; use the
included scoring script.

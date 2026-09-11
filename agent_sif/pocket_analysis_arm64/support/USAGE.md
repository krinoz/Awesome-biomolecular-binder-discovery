# Pocket analysis ARM64

This image contains two independent, real analysis programs. Application
commands are intentionally not added to `PATH`; invoke the absolute paths.

## PeSTo i_v4_1

Purpose: predict per-residue probabilities for protein, nucleic-acid, ion,
small-molecule and lipid interfaces. The five output PDB files store the
probability in the B-factor field.

The checkpoint is external and read-only. Example:

```bash
apptainer exec --nv \
  --bind /work:/work \
  pocket_analysis_arm64.sif \
  /usr/bin/python /opt/pesto/apply_model.py \
  --config_model_name pesto \
  --device cuda \
  --input_folder /work/input_pdbs \
  --output_folder /work/pesto_outputs \
  --checkpoint /path/to/mcp-suite/models/pesto/i_v4_1/model_ckpt.pt
```

Use `--device cpu` for CPU inference. PeSTo accepts PDB files in the input
folder. Upstream documentation is retained at `/opt/pesto/README.md`.

## P2Rank 2.5.1

Purpose: predict and rank ligand-binding pockets from PDB or mmCIF structures.
It produces pocket and residue CSV tables plus visualization files.

```bash
apptainer exec \
  --bind /work:/work \
  pocket_analysis_arm64.sif \
  /opt/p2rank/prank predict \
  -f /work/input/1fbl.pdb \
  -o /work/p2rank_outputs
```

The upstream guide and examples are retained under `/opt/p2rank/`.

### P2Rank dataset mode

For a batch, put the `.ds` file beside the structures and list one relative
PDB/mmCIF path per line. Blank lines and lines beginning with `#` are ignored.

```text
# protein_list.ds
tau_proteins/structure_1.pdb
tau_proteins/structure_2.cif
```

The external launcher binds the dataset directory read-only, so all relative
paths below that directory are visible in the container:

```bash
/path/to/mcp-suite/patches/run_p2rank_dataset.sh \
  /work/input/protein_list.ds \
  /work/p2rank_outputs \
  64
```

Usage is `run_p2rank_dataset.sh DATASET.ds OUTPUT_DIR [THREADS]`; the default
thread count is 64. For absolute input paths outside the dataset directory,
invoke `apptainer exec` directly and add the required `--bind` paths.

## fpocket status

fpocket is not included unless its VMD molfile dependency is rebuilt as a
native Linux ARM64 library. The upstream repository ships an x86-64
`LINUXAMD64` static library, so embedding it would create a partially working
or non-native tool. P2Rank prediction does not depend on fpocket.

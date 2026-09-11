# colabfold_arm64_cuda12

Retained image: `colabfold_arm64_cuda12.sif`

## Purpose

AlphaFold2 protein prediction, AlphaFold2 multimer for protein-protein complexes, and OpenMM relaxation.

## Inputs and outputs

FASTA/complex sequence input; predicted PDB/mmCIF, confidence files and optional relaxed structures.

## Upstream

- https://github.com/sokrypton/ColabFold

## Build record and limitations

Pinned source 0c788a0e8dca909f2c669784f9dd38e8c9682ff0. Use the remote MMseqs2 server for MSA. No local MSA database setup or database download is part of this guide. Keep OpenMM here rather than deploying a duplicate OpenMM SIF. JAX CUDA12 dependencies are ranges, not a frozen environment.

Recovered recipe sequence (read in this order):

1. [01-colabfold_arm64_cuda12.def](01-colabfold_arm64_cuda12.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-colabfold_arm64_cuda12.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/colabfold` | `/opt/colabfold` |

## External assets

Shared AlphaFold2 parameters/cache mounted at /work/cache. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/opt/colabfold-venv/bin/colabfold_batch --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work colabfold_arm64_cuda12.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

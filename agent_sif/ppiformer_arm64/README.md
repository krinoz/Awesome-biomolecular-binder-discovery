# ppiformer_arm64

Retained image: `ppiformer_arm64.sif`

## Purpose

Mutation-effect/ddG estimation for affinity-oriented analysis; not absolute small-molecule affinity prediction.

## Inputs and outputs

Complex PDB and mutation specification files; mutation scores.

## Upstream

- https://github.com/anton-bushuiev/PPIformer

## Build record and limitations

Source pin e324f5f30dd0dae55d194ac6b4d18c772219c3ee. Historical build inherits the ODesign runtime for CUDA/PyG, not its model weights. Equiformer, mutils and PPIRef source archives are required. Exact final pruning/repack is not included.

Recovered recipe sequence (read in this order):

1. [01-ppiformer_arm64.def](01-ppiformer_arm64.def)
2. [02-ppiformer_arm64_fix.def](02-ppiformer_arm64_fix.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-ppiformer_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/parent.sif` | `parent runtime (see recipe order)` |
| `build-context/PPIformer-e324f5f3.tar.gz` | `/opt/src/PPIformer.tar.gz` |
| `build-context/equiformer-pytorch-2a81808b.tar.gz` | `/opt/src/equiformer-pytorch.tar.gz` |
| `build-context/mutils-c3b99888.tar.gz` | `/opt/src/mutils.tar.gz` |
| `build-context/PPIRef-a2a5b6d0.tar.gz` | `/opt/src/PPIRef.tar.gz` |
| `build-context/ppiformer_run.py` | `/opt/ppiformer/ppiformer_run.py` |

## External assets

Official ddG checkpoints at /models/ddg_regression. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/opt/envs/ppiformer/bin/python /opt/ppiformer/ppiformer_run.py --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work ppiformer_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

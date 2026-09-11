# iggm_arm64

Retained image: `iggm_arm64.sif`

## Purpose

Antibody design using IgGM.

## Inputs and outputs

Upstream sequence/structure inputs; designed structures and sequence outputs.

## Upstream

- https://github.com/TencentAI4S/IgGM

## Build record and limitations

Pinned source 06abc563b3fc8c7ea020543add16b69b6f8a1c8d. Source tar must have repository contents at its root (no extra enclosing directory). The base is NVIDIA DGL 23.07, not the newer PyTorch base.

Recovered recipe sequence (read in this order):

1. [01-iggm_arm64.def](01-iggm_arm64.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-iggm_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/IgGM-src.tar` | `/IgGM-src.tar` |

## External assets

Official IgGM checkpoints mounted at /opt/IgGM/checkpoints. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
python /opt/IgGM/design.py --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work iggm_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

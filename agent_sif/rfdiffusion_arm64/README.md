# rfdiffusion_arm64

Retained image: `rfdiffusion_arm64.sif`

## Purpose

RFdiffusion v1 backbone generation and the condition modes supported by its checkpoint/configuration.

## Inputs and outputs

PDB and Hydra configuration in; PDB and accompanying metadata out.

## Upstream

- https://github.com/RosettaCommons/RFdiffusion

## Build record and limitations

Pinned source 86507b6538f51fce57b5a72477165f03999ed7ae; NVIDIA DGL 23.07 ARM64 base. One successful mode must not be generalized to every checkpoint. A generic unpinned dllogger dependency remains.

Recovered recipe sequence (read in this order):

1. [01-rfdiffusion_arm64.def](01-rfdiffusion_arm64.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-rfdiffusion_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/RFdiffusion` | `/app/RFdiffusion` |

## External assets

Official RFdiffusion checkpoints mounted at /app/RFdiffusion/models. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
python /app/RFdiffusion/scripts/run_inference.py --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work rfdiffusion_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

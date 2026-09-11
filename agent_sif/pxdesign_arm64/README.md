# pxdesign_arm64

Retained image: `pxdesign_arm64.sif`

## Purpose

PXDesign backbone/pipeline workflows and Protenix structure prediction, including supported mini/template variants.

## Inputs and outputs

Upstream JSON/configuration and optional structures/templates in; structures and scores out.

## Upstream

- https://github.com/bytedance/PXDesign
- https://github.com/bytedance/Protenix

## Build record and limitations

Four source revisions are recorded in recipe labels (PXDesign, Protenix, PXDesignBench, ColabDesign). ARM64 compatibility includes the FlashAttention varlen alias and retained CUTLASS source. Source checkout alone is not evidence all model variants passed.

Recovered recipe sequence (read in this order):

1. [01-pxdesign_arm64.def](01-pxdesign_arm64.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-pxdesign_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/PXDesign` | `/opt/pxdesign` |
| `build-context/Protenix` | `/opt/protenix` |
| `build-context/PXDesignBench` | `/opt/pxdbench` |
| `build-context/ColabDesign` | `/opt/colabdesign` |

## External assets

Separate PXDesign and Protenix assets mounted under /work/weights and /work/cache. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/opt/envs/pxdesign/bin/pxdesign --help
/opt/envs/pxdesign/bin/protenix --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work pxdesign_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

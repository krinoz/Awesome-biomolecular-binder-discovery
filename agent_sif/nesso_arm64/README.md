# nesso_arm64

Retained image: `nesso_arm64.sif`

## Purpose

Nesso prediction runtime.

## Inputs and outputs

Upstream YAML/configuration inputs; predicted structures and associated results.

## Upstream

- https://github.com/recursionpharma/nesso

## Build record and limitations

Source pin 6c72f66720d9d3447fd73c515cda963e39128b1f. Apply base, NumPy 1.26.4 compatibility, then user-site isolation in order. Broad dependency ranges remain. Embedded final test checks imports/NumPy ABI, not prediction accuracy.

Recovered recipe sequence (read in this order):

1. [01-nesso_arm64.def](01-nesso_arm64.def)
2. [02-nesso_arm64_numpy_compat.def](02-nesso_arm64_numpy_compat.def)
3. [03-nesso_arm64_final.def](03-nesso_arm64_final.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-nesso_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/parent.sif` | `parent runtime (see recipe order)` |

## External assets

Nesso model/CCD assets and ESM2 snapshot external; NESSO_ESM2_MODEL=/models/esm2_t33_650M_UR50D. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/usr/bin/python3 -m nesso.main --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work nesso_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

# disco_arm64

Retained image: `disco_arm64.sif`

## Purpose

DISCO multimodal sequence/structure co-design.

## Inputs and outputs

Upstream design configuration and conditioning files; generated sequence/structure outputs.

## Upstream

- https://github.com/DISCO-design/DISCO

## Build record and limitations

Source pin 82b594f838eb61dd8c78ae3a403ccb8f00cf7abf. The second recipe repairs libXrender/TRITON paths. Additional runtime patches and final repack may not be represented; do not claim an exact reconstruction.

Recovered recipe sequence (read in this order):

1. [01-disco_arm64.def](01-disco_arm64.def)
2. [02-disco_arm64_fix.def](02-disco_arm64_fix.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-disco_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/DISCO-82b594f8.tar.gz` | `/opt/DISCO.tar.gz` |
| `build-context/disco_plm.py` | `/opt/disco/plm.py` |
| `build-context/disco_run.py` | `/opt/disco/disco_run.py` |
| `build-context/parent.sif` | `parent runtime (see recipe order)` |

## External assets

DISCO checkpoint and DPLM-650M snapshot under /models; DISCO_DPLM_PATH=/models/dplm_650m. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/opt/envs/disco/bin/python /opt/disco/disco_run.py --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work disco_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

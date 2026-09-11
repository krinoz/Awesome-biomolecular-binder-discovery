# pocket_analysis_arm64

Retained image: `pocket_analysis_arm64.sif`

## Purpose

PeSTo interface/pocket analysis and P2Rank pocket prediction.

## Inputs and outputs

PDB directory for PeSTo; PDB or .ds file listing structures for P2Rank; per-atom/interface outputs or pocket/residue CSV outputs.

## Upstream

- https://github.com/LBM-EPFL/PeSTo_Inference
- https://github.com/rdk/p2rank

## Build record and limitations

PeSTo 5f8ebe0597f256b8b76b3a4c8027bfb855d9d24b; P2Rank 2.5.1; Java 17 ARM64. fpocket was not embedded and is not advertised. Final repack added documentation; keep .ds paths consistent with the container mount.

Recovered recipe sequence (read in this order):

1. [01-pocket_analysis_arm64.def](01-pocket_analysis_arm64.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-pocket_analysis_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/pesto-src` | `/opt/pesto` |
| `build-context/p2rank` | `/opt/p2rank` |
| `build-context/apply_model.py` | `/opt/pesto/apply_model.py` |
| `build-context/USAGE.md` | `/opt/pocket-analysis/README.md` |
| `build-context/SOURCE_PINS.txt` | `/opt/pocket-analysis/SOURCE_PINS.txt` |

## External assets

PeSTo i_v4_1/model_ckpt.pt is external. P2Rank distribution contains its own small prediction assets. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/usr/bin/python /opt/pesto/apply_model.py --help
bash /opt/p2rank/prank help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work pocket_analysis_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

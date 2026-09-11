# drugclip_arm64

Retained image: `drugclip_arm64.sif`

## Purpose

DrugCLIP pocket-ligand embedding and all-pairs scoring, following the retained scoring script.

## Inputs and outputs

Ligand LMDB and pocket LMDB in; embedding cache and Pocket,Ligand,Score CSV out (index=False).

## Upstream

- https://github.com/bowen-gao/DrugCLIP

## Build record and limitations

DrugCLIP 7a3a3fa33673f8668c811790f2e4681c98af44ef. Uni-Core source archive is needed; its exact pin was not recovered. The private development notebook is intentionally omitted from this publication and its COPY line removed; the scoring program is included.

Recovered recipe sequence (read in this order):

1. [01-drugclip_arm64.def](01-drugclip_arm64.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-drugclip_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/unicore_source.tar.gz` | `/opt/sources/unicore_source.tar.gz` |
| `build-context/drugclip_source.tar.gz` | `/opt/sources/drugclip_source.tar.gz` |
| `build-context/drugclip_score_all.py` | `/opt/drugclip_tools/drugclip_score_all.py` |
| `build-context/make_tiny_inputs.py` | `/opt/drugclip_tools/make_tiny_inputs.py` |
| `build-context/README_CONTAINER.md` | `/opt/drugclip_tools/README.md` |

## External assets

Full DrugCLIP checkpoint_best.pt mounted explicitly. No standalone Uni-Mol pretraining checkpoint is required. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/usr/bin/python /opt/drugclip_tools/drugclip_score_all.py --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work drugclip_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

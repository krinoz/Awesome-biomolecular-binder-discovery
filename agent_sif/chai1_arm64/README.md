# chai1_arm64

Retained image: `chai1_arm64.sif`

## Purpose

Chai-1 all-atom complex prediction.

## Inputs and outputs

FASTA and optional upstream auxiliary inputs; CIF and score files.

## Upstream

- https://github.com/chaidiscovery/chai-lab

## Build record and limitations

Source pin 66c38d1fe5c6756a89ff8596b1dea87d305ec06f. The traced Chai ESM component is not interchangeable with a raw fair-esm checkpoint merely because both are ESM-2.

Recovered recipe sequence (read in this order):

1. [01-chai1_arm64.def](01-chai1_arm64.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-chai1_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/chai-lab-66c38d1.tar.gz` | `/opt/chai-lab.tar.gz` |
| `build-context/chai1_run.py` | `/opt/chai1/chai1_run.py` |

## External assets

Official Chai assets at /models, including conformers and the traced ESM-2 3B component. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/opt/envs/chai1/bin/python /opt/chai1/chai1_run.py --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work chai1_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

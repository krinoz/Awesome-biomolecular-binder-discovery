# foundry_arm64

Retained image: `foundry_arm64.sif`

## Purpose

RFD3 atom-conditioned backbone generation; ProteinMPNN and LigandMPNN sequence design; RF3 is included by the all-extras installation, not claimed validated here.

## Inputs and outputs

Structural/configuration files in; designed structures, sequences and model-specific metadata out.

## Upstream

- https://github.com/RosettaCommons/foundry

## Build record and limitations

Source pin faf42996a3cfc5f2caa726777c5745dd74c9b040. RFD3 generation and ProteinMPNN were used in completed benchmark runs. This does not validate every checkpoint or RF3. LigandMPNN is retained inside Foundry, not a duplicate image. Final PATH/documentation repack is not fully captured by this recipe.

Recovered recipe sequence (read in this order):

1. [01-foundry_arm64.def](01-foundry_arm64.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-foundry_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/foundry` | `/opt/foundry` |

## External assets

Foundry checkpoints mounted at /weights; FOUNDRY_CHECKPOINT_DIRS=/weights. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/opt/foundry-venv/bin/rfd3 --help
/opt/foundry-venv/bin/mpnn --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work foundry_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

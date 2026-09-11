# protein_plm_arm64

Retained image: `protein_plm_arm64.sif`

## Purpose

SaProt/ESM2 embeddings, selected LoRA workflows, Foldseek 3Di encoding and InterPLM sparse-autoencoder analysis.

## Inputs and outputs

FASTA or PDB/mmCIF and chain selection; embeddings, 3Di/sequence strings, model-analysis outputs or trained adapters.

## Upstream

- https://github.com/westlake-repl/SaProtHub
- https://github.com/ElanaPearl/interPLM

## Build record and limitations

SaProtHub 2f39673a37e0b35f83788dcf8ef5ad326a42871c; InterPLM 5f4cbf90a0b3c1c031951ffd0b3b8e11b6f2ed61. SaProtHub is an intermediate build dependency, not a separate retained SIF. ColabProTrek is excluded. The selected-source archive layout must be reconstructed; a full upstream tarball is not automatically equivalent.

Recovered recipe sequence (read in this order):

1. [01-saprothub_arm64.def](01-saprothub_arm64.def)
2. [02-protein_plm_interplm_arm64.def](02-protein_plm_interplm_arm64.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-saprothub_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/SaProtHub-selected-2f39673a.tar.gz` | `/opt/SaProtHub-selected.tar.gz` |
| `build-context/saprothub_forward.py` | `/opt/saprothub/saprothub_forward.py` |
| `build-context/saprothub_extract_3di.py` | `/opt/saprothub/saprothub_extract_3di.py` |
| `build-context/saprothub_finetune.py` | `/opt/saprothub/saprothub_finetune.py` |
| `build-context/parent.sif` | `parent runtime (see recipe order)` |
| `build-context/InterPLM-5f4cbf90.tar.gz` | `/opt/InterPLM.tar.gz` |
| `build-context/interplm_run.py` | `/opt/interplm/interplm_run.py` |
| `build-context/INTERPLM_CONTAINER_USAGE.md` | `/opt/interplm/USAGE.md` |

## External assets

Selected SaProt/ESM2 snapshots and InterPLM SAE checkpoints mounted under /models. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/opt/envs/saprothub/bin/python /opt/saprothub/saprothub_forward.py --help
/opt/envs/interplm/bin/python /opt/interplm/interplm_run.py --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work protein_plm_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

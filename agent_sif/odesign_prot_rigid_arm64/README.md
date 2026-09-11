# odesign_prot_rigid_arm64

Retained image: `odesign_prot_rigid_arm64.sif`

## Purpose

ODesign rigid-protein backbone design and its multi-stage sequence-design workflow.

## Inputs and outputs

Upstream design specification and structural inputs; generated structures/sequences.

## Upstream

- https://github.com/OTeam-AI4S/ODesign

## Build record and limitations

Source pin 87b67dec1a26c0915286bf47c3dc7102635ea0cc. Use the rigid model, not an uninstalled flex variant. Sequence-design stages use ProteinMPNN/LigandMPNN rather than a separately claimed ODesign inverse-folding model. Repair recipes are ordered; the abandoned biotite 1.2 trial is excluded.

Recovered recipe sequence (read in this order):

1. [01-odesign_prot_rigid_arm64.def](01-odesign_prot_rigid_arm64.def)
2. [02-odesign_repair_arm64.def](02-odesign_repair_arm64.def)
3. [03-odesign_biotite14_repair.def](03-odesign_biotite14_repair.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-odesign_prot_rigid_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/ODesign-87b67dec.tar.gz` | `/opt/ODesign.tar.gz` |
| `build-context/odesign_run.py` | `/opt/odesign/odesign_run.py` |
| `build-context/parent.sif` | `parent runtime (see recipe order)` |
| `build-context/odesign_torch_geometric_pt24.patch` | `/opt/odesign/odesign_torch_geometric_pt24.patch` |
| `build-context/odesign_flash_attn_compat.patch` | `/opt/odesign/odesign_flash_attn_compat.patch` |

## External assets

odesign_base_prot_rigid plus ProteinMPNN/LigandMPNN checkpoints at /ckpt; CCD assets at /data. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/opt/envs/odesign/bin/python /opt/odesign/odesign_run.py --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work odesign_prot_rigid_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

# boltz_family_arm64

Retained image: `boltz_family_arm64.sif`

## Purpose

BoltzGen joint design and backbone generation; BoltzGen inverse folding; Boltz-2 complex structure prediction; a separate Boltz-2 affinity workflow.

## Inputs and outputs

Design/complex YAML and optional PDB/mmCIF inputs; generated PDB/mmCIF, sequence and confidence/affinity outputs.

## Upstream

- https://github.com/HannesStark/boltzgen
- https://github.com/jwohlwend/boltz

## Build record and limitations

One shared environment, BoltzGen 0.3.2 and native Boltz 2.2.1. Do not add a second standalone Boltz image. The CCD mols archive is embedded, unlike model weights. Recorded recipe includes both upstream README trees. Final image was repacked; dependency resolution is not a complete lockfile.

Recovered recipe sequence (read in this order):

1. [01-boltz_family_arm64.def](01-boltz_family_arm64.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-boltz_family_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

## External assets

BoltzGen checkpoint directory at /opt/model-cache/boltzgen; Boltz-2 boltz2_conf.ckpt and boltz2_aff.ckpt mounted individually at /opt/model-cache/boltz2. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/opt/envs/boltzgen/bin/boltzgen --help
/opt/envs/boltzgen/bin/boltz --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work boltz_family_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

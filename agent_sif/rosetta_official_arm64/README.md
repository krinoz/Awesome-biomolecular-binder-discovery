# rosetta_official_arm64

Retained image: `rosetta_official_arm64.sif`

## Purpose

Official Rosetta/PyRosetta runtime, distinct from the removed rosetta_mcp image.

## Inputs and outputs

Structures and Rosetta/PyRosetta scripts; structures, energies and analysis outputs.

## Upstream

- https://github.com/RosettaCommons/rosetta

## Build record and limitations

Embedded provenance is docker://rosettacommons/rosetta:latest. No immutable image digest was recovered. A later latest tag is not guaranteed equivalent. Python ABI must match any integration; do not copy its Python module into another environment.

Recorded pull route (mutable tag, not an exact rebuild):

```bash
apptainer pull rosetta_official_arm64.sif docker://rosettacommons/rosetta:latest
```

Check the ARM64 manifest and official license before pulling.

## External assets

Use only officially licensed assets; do not redistribute the image or PyRosetta package through this repository. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
python -c "import pyrosetta; print(pyrosetta.__file__)"
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work rosetta_official_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

# bindcraft_mcp

Retained image: `bindcraft_mcp.sif`

## Purpose

BindCraft binder design runtime, with external AF2 assets and a separate PyRosetta integration dependency.

## Inputs and outputs

Target PDB and BindCraft settings; binder structures, sequences and metrics.

## Upstream

- https://github.com/MacromNex/bindcraft_mcp
- https://github.com/martinpacesa/BindCraft

## Build record and limitations

MCP source checkout acedaa2b8369bacf4db3b63954e154229725df94. This recovered Dockerfile omits PyRosetta; it alone cannot reproduce the repaired sidecar workflow. It also retains historical PATH/entrypoint settings removed in the deployed repack. Explicitly incomplete final-image reconstruction.

Recovered recipe sequence (read in this order):

1. [01-bindcraft_mcp.arm64.Dockerfile](01-bindcraft_mcp.arm64.Dockerfile)

Use the upstream repository as Docker build context, not this recipe-only directory:

```bash
docker build --platform linux/arm64 -f 01-bindcraft_mcp.arm64.Dockerfile -t bindcraft_mcp:local /path/to/prepared-context
docker save bindcraft_mcp:local -o /path/to/node-runtime/bindcraft_mcp.tar
apptainer build bindcraft_mcp.sif docker-archive:///path/to/node-runtime/bindcraft_mcp.tar
```

## External assets

Shared AlphaFold2 parameters at /app/repo/scripts/params. Official Rosetta/PyRosetta image is separate. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/env/bin/python /app/repo/scripts/run_bindcraft.py --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work bindcraft_mcp.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

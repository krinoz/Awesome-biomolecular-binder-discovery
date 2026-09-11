# public_python_mcp

Retained image: `public_python_mcp.sif`

## Purpose

Shared Python service image for retained public/sequence adapters.

## Inputs and outputs

MCP queries or service-specific files; structured results and reports.

## Upstream

- https://github.com/charlesxu90/ProteinMCP

## Build record and limitations

Historical recipe includes InterPro, MSA, protein-sol, PyMOL and PubMed code. PyMOL was withdrawn from the active tool set; its presence in the build history is not an endorsement or re-registration. Per-adapter revisions and post-build API repairs are incomplete.

Recovered recipe sequence (read in this order):

1. [01-public_python_mcp.arm64.Dockerfile](01-public_python_mcp.arm64.Dockerfile)

Use the upstream repository as Docker build context, not this recipe-only directory:

```bash
docker build --platform linux/arm64 -f 01-public_python_mcp.arm64.Dockerfile -t public_python_mcp:local /path/to/prepared-context
docker save public_python_mcp:local -o /path/to/node-runtime/public_python_mcp.tar
apptainer build public_python_mcp.sif docker-archive:///path/to/node-runtime/public_python_mcp.tar
```

## External assets

No bundled model weights asserted. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/usr/local/bin/run-public-python-mcp interpro_mcp
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work public_python_mcp.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

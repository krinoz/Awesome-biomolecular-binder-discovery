# bio-mcp

Retained image: `bio-mcp.sif`

## Purpose

Biology API MCP service bundle.

## Inputs and outputs

MCP requests; structured service responses.

## Upstream

- https://github.com/acashmoney/bio-mcp

## Build record and limitations

Source checkout eb153e774fb63efedede77ecca43ccd5021aed5a. Embedded SIF provenance points to a former Docker archive. Node lts-alpine is mutable; protocol startup is not equivalent to successful calls to every API.

Recovered recipe sequence (read in this order):

1. [01-Dockerfile](01-Dockerfile)

Use the upstream repository as Docker build context, not this recipe-only directory:

```bash
docker build --platform linux/arm64 -f 01-Dockerfile -t bio-mcp:local /path/to/prepared-context
docker save bio-mcp:local -o /path/to/node-runtime/bio-mcp.tar
apptainer build bio-mcp.sif docker-archive:///path/to/node-runtime/bio-mcp.tar
```

## External assets

No model weights. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
node /app/build/index.js
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work bio-mcp.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

# arxiv

Retained image: `arxiv.sif`

## Purpose

arXiv search/document retrieval service.

## Inputs and outputs

Search/document requests; records and downloaded documents.

## Upstream

- https://github.com/blazickjp/arxiv-mcp-server

## Build record and limitations

Source checkout 164dfa61a0eea3299518da3b8d9d081ae7276532. Historical Docker PATH differs from the final pathless repack; use the absolute interpreter.

Recovered recipe sequence (read in this order):

1. [01-Dockerfile](01-Dockerfile)

Use the upstream repository as Docker build context, not this recipe-only directory:

```bash
docker build --platform linux/arm64 -f 01-Dockerfile -t arxiv:local /path/to/prepared-context
docker save arxiv:local -o /path/to/node-runtime/arxiv.tar
apptainer build arxiv.sif docker-archive:///path/to/node-runtime/arxiv.tar
```

## External assets

No model weights. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/app/.venv/bin/python -m arxiv_mcp_server --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work arxiv.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

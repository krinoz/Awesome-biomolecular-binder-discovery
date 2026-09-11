# pubmed

Retained image: `pubmed.sif`

## Purpose

PubMed retrieval service.

## Inputs and outputs

Search/identifier requests; bibliographic records.

## Upstream

- https://github.com/JackKuo666/PubMed-MCP-Server

## Build record and limitations

Source checkout 2a254f418f431e7ee5c161e38c8144890d52c20b. Upstream requirements are not fully locked; API functionality needs separate runtime checks.

Recovered recipe sequence (read in this order):

1. [01-Dockerfile](01-Dockerfile)

Use the upstream repository as Docker build context, not this recipe-only directory:

```bash
docker build --platform linux/arm64 -f 01-Dockerfile -t pubmed:local /path/to/prepared-context
docker save pubmed:local -o /path/to/node-runtime/pubmed.tar
apptainer build pubmed.sif docker-archive:///path/to/node-runtime/pubmed.tar
```

## External assets

No model weights. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
python /app/pubmed_server.py
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work pubmed.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

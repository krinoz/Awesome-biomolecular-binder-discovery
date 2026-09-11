# public_node_mcp

Retained image: `public_node_mcp.sif`

## Purpose

Shared Node service image for AlphaFold DB, KEGG, NCBI Datasets, Open Targets, PDB, Protein Atlas, STRING and UniProt adapters.

## Inputs and outputs

MCP query requests; structured remote API results.

## Upstream

- https://github.com/charlesxu90/ProteinMCP

## Build record and limitations

Needs the eight source directories named in COPY. Their exact per-adapter source pins were not recovered. Node18-alpine and npm resolution are not a frozen build; retained services must not all be assumed operational.

Recovered recipe sequence (read in this order):

1. [01-public_node_mcp.arm64.Dockerfile](01-public_node_mcp.arm64.Dockerfile)

Use the upstream repository as Docker build context, not this recipe-only directory:

```bash
docker build --platform linux/arm64 -f 01-public_node_mcp.arm64.Dockerfile -t public_node_mcp:local /path/to/prepared-context
docker save public_node_mcp:local -o /path/to/node-runtime/public_node_mcp.tar
apptainer build public_node_mcp.sif docker-archive:///path/to/node-runtime/public_node_mcp.tar
```

## External assets

No model weights. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/usr/local/bin/run-public-mcp pdb
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work public_node_mcp.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

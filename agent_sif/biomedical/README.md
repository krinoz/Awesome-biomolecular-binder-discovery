# biomedical

Retained image: `biomedical.sif`

## Purpose

Rust BioMCP biomedical retrieval CLI/service, not a modeling environment.

## Inputs and outputs

Search identifiers/queries; structured retrieval results.

## Upstream

- https://github.com/genomoncology/biomcp

## Build record and limitations

Source checkout 92a2f92d2a24474fde7e8f76ee84c69d6d55fed3. Rust 1.88/bookworm build, Debian runtime. Endpoint availability is not guaranteed by an image build.

Recovered recipe sequence (read in this order):

1. [01-biomedical.arm64.Dockerfile](01-biomedical.arm64.Dockerfile)

Use the upstream repository as Docker build context, not this recipe-only directory:

```bash
docker build --platform linux/arm64 -f 01-biomedical.arm64.Dockerfile -t biomedical:local /path/to/prepared-context
docker save biomedical:local -o /path/to/node-runtime/biomedical.tar
apptainer build biomedical.sif docker-archive:///path/to/node-runtime/biomedical.tar
```

## External assets

No model weights; credentials, if required by a service, supplied at runtime only. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/usr/local/bin/biomcp --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work biomedical.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

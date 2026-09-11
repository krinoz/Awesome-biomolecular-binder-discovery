# mmseqs_foldseek_arm64

Retained image: `mmseqs_foldseek_arm64.sif`

## Purpose

Sequence/search utilities: MMseqs2, Foldseek, FoldMason, Folddisco and Riboseek.

## Inputs and outputs

FASTA, PDB/mmCIF and motif/query inputs; alignments, search hits, clusters and JSON/TSV reports.

## Upstream

- https://github.com/soedinglab/MMseqs2
- https://github.com/steineggerlab/foldseek

## Build record and limitations

Foldseek 10-941cd33, FoldMason 4-dd3c235, Folddisco 2-9375a2d, Riboseek v1.0.1. MMseqs2 uses an unpinned distribution package. Foldseek clustering was used in the completed benchmark. Search APIs and their databases are not frozen by the SIF.

Recovered recipe sequence (read in this order):

1. [01-mmseqs_foldseek_arm64.def](01-mmseqs_foldseek_arm64.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-mmseqs_foldseek_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/sequence_structure_search_server.py` | `/opt/search_mcp/server.py` |
| `build-context/SEARCH_GUIDE.md` | `/opt/docs/SEARCH_GUIDE.md` |

## External assets

No model weights. Online search endpoints are remote services; no large search database download is provided. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/opt/foldseek/bin/foldseek version
/opt/folddisco/bin/folddisco --help
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work mmseqs_foldseek_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

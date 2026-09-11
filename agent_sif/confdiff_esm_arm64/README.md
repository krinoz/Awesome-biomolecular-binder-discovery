# confdiff_esm_arm64

Retained image: `confdiff_esm_arm64.sif`

## Purpose

ConFDiff conformational sampling environment and ESMFold protein refolding.

## Inputs and outputs

Sequence/configuration files in; sampled or predicted structures out.

## Upstream

- https://github.com/bytedance/ConfDiff
- https://github.com/facebookresearch/esm

## Build record and limitations

ConfDiff checkout observed at 9cfae1c14121e423d8d455d03506c7e8ee580e48. ESMFold completed large refolding runs. That evidence does not establish ConFDiff sampling parity. Recipe includes legacy OpenFold implementation primitives needed by ESMFold, not an OpenFold model or checkpoint. Later repair/repack history is incomplete.

Recovered recipe sequence (read in this order):

1. [01-confdiff_esm_arm64.def](01-confdiff_esm_arm64.def)

From this directory, after preparing all context inputs:

```bash
apptainer build --fakeroot output-stage-1.sif 01-confdiff_esm_arm64.def
```

For each localimage stage, provide the preceding stage (or the named cross-image dependency) as `build-context/parent.sif` and write to a **different** output filename. See [BUILDING.md](../BUILDING.md).

### Required build context

Host paths were normalized; nothing is downloaded automatically by this documentation. Copy matching files from `support/` where supplied. Obtain source trees/archives from the upstream revisions above and in recipe labels. Required tar layouts are defined by each recipe's extraction command. Missing items are real reconstruction prerequisites, not bundled assets.

| Host input | Container destination/use |
|---|---|
| `build-context/ConfDiff` | `/opt/confdiff` |

## External assets

ESMFold/ESM checkpoints in a shared Torch cache; set TORCH_HOME to the mounted cache. ConFDiff checkpoints are separate. See [WEIGHTS.md](../WEIGHTS.md).

## Runtime entry points

The following are in-container entry points for source/CLI discovery, not completed scientific examples. Use `apptainer exec`, explicit paths, and read the upstream README/source for full arguments. No MCP registration is required to execute code directly.

```bash
/opt/envs/confdiff/bin/python -c "import esm; print(esm.__file__)"
```

Example wrapper:

```bash
apptainer exec --nv --bind /absolute/work:/work confdiff_esm_arm64.sif /bin/bash
```

Omit `--nv` for CPU-only services. Bind model files read-only at the locations above and use a writable node-local directory for caches/results. Some historical recipes have opinionated runscripts; `exec` bypasses those.

## Evidence boundary

The retained SIF and recipe were inspected; no rebuild or fresh model validation was performed for this branch. `%test` sections generally establish imports/CLI availability only. Completed RFD3, ProteinMPNN, ESMFold and Foldseek benchmark computations are historical execution evidence, not a guarantee that a newly resolved dependency stack behaves identically.

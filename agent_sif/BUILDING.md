# Build and runtime conventions

## Hardware and build location

Build on Linux ARM64/aarch64. The historical GPU target was NVIDIA GH200. A Docker `--platform linux/arm64` flag does not make x86 CUDA libraries usable on ARM64. NGC PyTorch 25.06 and DGL 23.07 bases supply different Python/Torch/CUDA stacks; do not combine their site-packages blindly.

Use an allocated compute node for builds, not a shared login node. Put extraction, Apptainer cache, temporary root filesystems and Python caches on node-local storage, for example a job-specific directory below `/run/user/$(id -u)`. This may be memory-backed and counts against job memory. It is not persistent after the allocation ends. Merely naming a project directory `runtime` does **not** avoid filesystem inode quotas.

```bash
build_tmp=$(mktemp -d /run/user/$(id -u)/sif-build.XXXXXX)
export APPTAINER_TMPDIR="$build_tmp/tmp"
export APPTAINER_CACHEDIR="$build_tmp/cache"
mkdir -p "$APPTAINER_TMPDIR" "$APPTAINER_CACHEDIR"
```

`--fakeroot` requires site support. On a Docker-capable ARM64 builder, use Docker, save an archive, then convert to SIF. Registry access and licenses must be obtained through normal authorized channels; no credentials are shipped here.

## Preparing context

Each definition's `%files` entries use `build-context/` paths. They are **not** generated automatically. Fetch the listed source revision, preserve the upstream license, and exclude model weights, datasets, `.git`, caches and credentials from source archives. Copy the included support files to their named context location. For DrugCLIP the private notebook reference was deliberately removed; this is a documented publication change, not an exact original definition.

For localimage stages, `build-context/parent.sif` is an input from the previous stage. Never overwrite the input image while building its child. Cross-image dependencies: Protein PLM starts with the included SaProtHub intermediate recipe; PPIformer inherits an ODesign runtime; BindCraft's repaired PyRosetta integration needs additional sidecar material not fully recovered here.

The recovered Dockerfiles expect the directories listed in `COPY` and may include historical PATH settings. They are build-history records, not proof of the later pathless repack. Do not publish a newly built image as equivalent to the retained one without recovering those changes and validating it.

## Direct code execution

Use `apptainer exec image.sif /absolute/interpreter /absolute/script ...`. Application CLI directories are intentionally not added to the host PATH. PATH does not limit a model's API capabilities; explicit interpreter selection avoids accidental environment selection. Installed Python modules and upstream source remain available for custom code.

Mount shared checkpoints read-only. Mount a job-local writable workspace for caches and results. For Boltz-2, bind checkpoints individually so that the embedded `mols/` directory is not hidden by a directory mount. For ColabFold use the remote MMseqs2 service; do not set up local MSA databases.

## Verification and persistence

Imports and `--help` are not model validation. A new build needs an actual small workload, output checks, and model-specific acceptance criteria before being advertised as tested. This publication did not run those workloads.

Persist results and their referenced structural files together before the job ends. Keep an inventory inside a compressed archive and verify it before deleting source files. A score JSON pointing into a vanished shared cache is not a backup of the structures.

# Provenance and scope

This branch records the 24 SIF filenames present in the deployment's container directory on 2026-09-11. Recipes were recovered from its patches, staging, audit and source directories. Application source trees and large binary build contexts are not vendored. Original site/user-specific absolute paths were normalized, and private development notebooks were excluded.

An inspected SIF may retain only `Bootstrap: localimage` with a temporary rootfs as its embedded definition. This establishes that it was repacked, not how every layer was created. Most final images in this inventory have that limitation. Retained base and repair recipes are published as evidence; missing repack scripts and unpinned package resolution prevent a claim of complete or bit-identical reproduction.

Examples of recorded changes: externalized AF2/ESM weights, explicit application interpreters instead of application PATH injection, Python 3.12 dataclass repairs for fair-esm, legacy ESMFold attention compatibility, Protenix FlashAttention import aliasing, ODesign PyG/Biotite repairs, and Nesso NumPy ABI/user-site fixes. Some are inline in recipes; others are only known to have happened during a later repack. Do not silently assume an unrecorded patch is present in a fresh build.

Upstream commit labels are retained where available. A current checkout revision is identified as such and is not proof of the exact contents originally copied into a build. NGC tags, apt repositories and some pip/npm constraints remain mutable. No new environment lockfile is fabricated.

Excluded as standalone retired tools: old gpu_mcp, old SaProtHub, separate Boltz/OpenMM/LigandMPNN images, PLMC, BioEmu and the removed protein-design MCP. SaProtHub recipes are included only as a prerequisite of the retained Protein PLM image. Historical public Python code may still contain an adapter that was subsequently deregistered; image contents are not the active agent tool registry.

## Licensing

Upstream code, Dockerfiles and patches retain the licenses of their respective projects. Source links are provided per image. This documentation does not relicense third-party software or grant rights to distribute NGC, Rosetta/PyRosetta, checkpoints or datasets. Fetch upstream sources with their original license/notice files; do not copy credentials or licensed binaries into this Git branch.

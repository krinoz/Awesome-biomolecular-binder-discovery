# External model assets

No checkpoint, SIF, dataset, cache or private download link is included. Obtain assets from the official upstream projects linked in each image README, subject to their licenses. Do not treat permission to run a model as permission to redistribute its weights.

Use a persistent shared model store and bind it read-only into containers. Store formats matter: fair-esm Torch checkpoints, Hugging Face snapshots and Chai traced ESM components are not interchangeable just because their model names match. Share a physical asset only after confirming the expected architecture, serialization and version.

| Family | External assets |
|---|---|
| Boltz family | BoltzGen design/inverse-folding checkpoints; Boltz-2 confidence and affinity checkpoints. CCD chemical data is embedded by the recipe. |
| Foundry | Official RFD3/MPNN checkpoints; RF3 assets only for workflows separately validated. |
| RFdiffusion | Official checkpoint appropriate to the selected generation mode. |
| IgGM | Official IgGM checkpoints. |
| ColabFold / BindCraft | Shared compatible AlphaFold2 parameter files; separate writable compilation caches. |
| ConFDiff / ESMFold | ESMFold v1 and ESM2 3B/contact-regression assets in a Torch cache; separate ConFDiff weights for sampling. |
| PXDesign / Protenix | Variant-specific model checkpoints and auxiliary structural assets. |
| Chai-1 | Official model components, conformers and traced ESM feature model. |
| DISCO | DISCO checkpoint and DPLM-650M snapshot. |
| ODesign | odesign_base_prot_rigid, pipeline MPNN weights and CCD assets. |
| PPIformer | Official ddG regression checkpoint collection. |
| Protein PLM | Selected SaProt/ESM2 snapshots plus compatible InterPLM SAE weights. No ColabProTrek. |
| Pocket analysis | PeSTo i_v4_1 checkpoint; P2Rank small bundled prediction assets accompany its distribution. |
| DrugCLIP | Full DrugCLIP checkpoint; **not** mol_pre_no_h_220816.pt. |
| Nesso | Nesso checkpoint, CCD and ESM2 assets. |
| Rosetta | Official licensed distribution; do not vendor PyRosetta binaries here. |

Typical explicit mount (replace paths with actual files):

```bash
apptainer exec --nv \
  --bind /absolute/models:/models:ro \
  --bind /absolute/job-work:/work \
  image.sif /absolute/interpreter /absolute/script --help
```

This is a mount pattern, not a claim that every image uses `/models`; consult its README and environment section for the actual expected destination. Model acquisition/version-lock scripts remain a documented gap where not recovered.

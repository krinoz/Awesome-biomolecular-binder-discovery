# Retained ARM64 SIF build records

English-only build/provenance inventory, recorded 2026-09-11. This is a **source-only reconstruction package**, not a release of binary images and not a claim of bit-for-bit reproducibility. No container builds or model runs were performed for this publication.

This directory is independent of the repository's existing generic `containers/` recipes. It documents 24 images retained in the inspected deployment, including retrieval-service containers. Retention, import tests and successful scientific calculations are different evidence levels.

See [build and runtime conventions](BUILDING.md), [external weights](WEIGHTS.md), and [provenance limitations](PROVENANCE.md).

| Retained image | Purpose | Build record |
|---|---|---|
| `boltz_family_arm64.sif` | BoltzGen joint design and backbone generation; BoltzGen inverse folding; Boltz-2 complex structure prediction; a separate Boltz-2 affinity workflow. | [Details](boltz_family_arm64/README.md) |
| `foundry_arm64.sif` | RFD3 atom-conditioned backbone generation; ProteinMPNN and LigandMPNN sequence design; RF3 is included by the all-extras installation, not claimed validated here. | [Details](foundry_arm64/README.md) |
| `rfdiffusion_arm64.sif` | RFdiffusion v1 backbone generation and the condition modes supported by its checkpoint/configuration. | [Details](rfdiffusion_arm64/README.md) |
| `iggm_arm64.sif` | Antibody design using IgGM. | [Details](iggm_arm64/README.md) |
| `colabfold_arm64_cuda12.sif` | AlphaFold2 protein prediction, AlphaFold2 multimer for protein-protein complexes, and OpenMM relaxation. | [Details](colabfold_arm64_cuda12/README.md) |
| `confdiff_esm_arm64.sif` | ConFDiff conformational sampling environment and ESMFold protein refolding. | [Details](confdiff_esm_arm64/README.md) |
| `pxdesign_arm64.sif` | PXDesign backbone/pipeline workflows and Protenix structure prediction, including supported mini/template variants. | [Details](pxdesign_arm64/README.md) |
| `chai1_arm64.sif` | Chai-1 all-atom complex prediction. | [Details](chai1_arm64/README.md) |
| `disco_arm64.sif` | DISCO multimodal sequence/structure co-design. | [Details](disco_arm64/README.md) |
| `odesign_prot_rigid_arm64.sif` | ODesign rigid-protein backbone design and its multi-stage sequence-design workflow. | [Details](odesign_prot_rigid_arm64/README.md) |
| `ppiformer_arm64.sif` | Mutation-effect/ddG estimation for affinity-oriented analysis; not absolute small-molecule affinity prediction. | [Details](ppiformer_arm64/README.md) |
| `protein_plm_arm64.sif` | SaProt/ESM2 embeddings, selected LoRA workflows, Foldseek 3Di encoding and InterPLM sparse-autoencoder analysis. | [Details](protein_plm_arm64/README.md) |
| `pocket_analysis_arm64.sif` | PeSTo interface/pocket analysis and P2Rank pocket prediction. | [Details](pocket_analysis_arm64/README.md) |
| `drugclip_arm64.sif` | DrugCLIP pocket-ligand embedding and all-pairs scoring, following the retained scoring script. | [Details](drugclip_arm64/README.md) |
| `nesso_arm64.sif` | Nesso prediction runtime. | [Details](nesso_arm64/README.md) |
| `bindcraft_mcp.sif` | BindCraft binder design runtime, with external AF2 assets and a separate PyRosetta integration dependency. | [Details](bindcraft_mcp/README.md) |
| `mmseqs_foldseek_arm64.sif` | Sequence/search utilities: MMseqs2, Foldseek, FoldMason, Folddisco and Riboseek. | [Details](mmseqs_foldseek_arm64/README.md) |
| `rosetta_official_arm64.sif` | Official Rosetta/PyRosetta runtime, distinct from the removed rosetta_mcp image. | [Details](rosetta_official_arm64/README.md) |
| `biomedical.sif` | Rust BioMCP biomedical retrieval CLI/service, not a modeling environment. | [Details](biomedical/README.md) |
| `bio-mcp.sif` | Biology API MCP service bundle. | [Details](bio-mcp/README.md) |
| `arxiv.sif` | arXiv search/document retrieval service. | [Details](arxiv/README.md) |
| `pubmed.sif` | PubMed retrieval service. | [Details](pubmed/README.md) |
| `public_node_mcp.sif` | Shared Node service image for AlphaFold DB, KEGG, NCBI Datasets, Open Targets, PDB, Protein Atlas, STRING and UniProt adapters. | [Details](public_node_mcp/README.md) |
| `public_python_mcp.sif` | Shared Python service image for retained public/sequence adapters. | [Details](public_python_mcp/README.md) |

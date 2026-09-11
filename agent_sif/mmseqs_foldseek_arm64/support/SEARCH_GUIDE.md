# MMseqs2 + Foldseek family on Isambard

This image combines sequence-MSA and structure-search utilities. Public structure
databases are queried through `https://search.foldseek.com/api`; they are not
bundled in the image and are not downloaded to project storage.

## Fixed executable paths

The image does not add application directories to `PATH`. Call binaries by their
fixed absolute paths:

- MMseqs2: `/usr/bin/mmseqs`
- Foldseek: `/opt/foldseek/bin/foldseek`
- FoldMason: `/opt/foldmason/bin/foldmason`
- Folddisco: `/opt/folddisco/bin/folddisco`
- Riboseek: `/opt/riboseek/bin/riboseek`

Official documentation is under `/opt/docs/{mmseqs2,foldseek,foldmason,folddisco,riboseek}`.

## MCP tools

- `list_search_databases`: live public database names and paths.
- `generate_msa`, `generate_msa_from_file`: local MMseqs2 database to A3M.
- `foldseek_structure_search`: chain/monomer structure search.
- `foldseek_complex_search`: Foldseek-Multimer whole-complex search.
- `foldseek_interface_search`: protein-interface search.
- `foldmason_structure_msa`: multiple structure alignment for 2..4999 structures.
- `folddisco_motif_search`: discontinuous protein-residue geometry search.
- `riboseek_rna_search`: RNA search against the public AF3 RNA collection.

Foldseek alignment modes are `3diaa` (fast local 3Di+AA), `tmalign` (global),
and `lolalign` (probabilistic multi-domain local alignment). They are parameters,
not separate tools.

### Foldseek structure search example

```json
{
  "query_path": "/work/inputs/query.pdb",
  "output_dir": "/work/results/foldseek_query",
  "databases": ["pdb100", "afdb-swissprot"],
  "alignment_mode": "3diaa",
  "max_wait_seconds": 1200
}
```

### Folddisco motif example

```json
{
  "query_path": "/work/inputs/enzyme.pdb",
  "motif_residues": "A64,A86,A90,A114,A137,A145",
  "output_dir": "/work/results/folddisco_enzyme",
  "databases": ["pdb_folddisco"],
  "max_wait_seconds": 1200
}
```

Folddisco searches the geometry of selected protein residues. It does not encode
the identity or coordinates of benchmark ligand atoms, so ligand-conditioned
design benchmarks still require their native ligand/motif evaluator.

## Direct local examples

Small local structure-to-structure search:

```bash
apptainer exec mmseqs_foldseek_arm64.sif \
  /opt/foldseek/bin/foldseek easy-search query.pdb target.pdb result.m8 tmp
```

Local discontinuous-motif search requires a prebuilt Folddisco index:

```bash
apptainer exec mmseqs_foldseek_arm64.sif \
  /opt/folddisco/bin/folddisco query -i INDEX -p query.pdb -q A64,A86,A90
```

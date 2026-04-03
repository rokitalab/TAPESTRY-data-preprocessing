# release notes

## current release (v2)
-   Release date: 2026-04-03
-   OpenPedCan data release date: 2024-03-01 (v15)
-   Status: available

### Data sources:
[Tumor enriched splicing](https://github.com/rokitalab/tumor-enriched-splicing):
- `cohort-histologies.tsv`
- `control-cohort-histologies.tsv`
- `recurrent-primary-tumor-enriched-oncofetal-splice-junctions-annotated.tsv.gz`
- `tumor-enriched-oncofetal-splice-junction-log2-cpm-combat-corrected.qs2`
- `tumor-enriched-oncofetal-splice-junction-ctrl-log2-cpm-combat-corrected.qs2`

OpenPedCan (v15):
- `cptac-protein-imputed-prot-expression-abundance.tsv.gz`
- `gene-expression-rsem-tpm-collapsed.rds`
- `rna-isoform-expression-rsem-tpm.rds`
- `hope-protein-imputed-prot-expression-abundance.tsv.gz`
- `histologies.tsv`

```         
v2/
├── cohort-histologies.tsv
├── control-cohort-histologies.tsv
├── cptac-protein-imputed-prot-expression-abundance.tsv.gz
├── gene-expression-rsem-tpm-collapsed.rds
├── histologies.tsv
├── hope-protein-imputed-prot-expression-abundance.tsv.gz
├── md5sum.txt
├── recurrent-primary-tumor-enriched-oncofetal-splice-junctions-annotated.tsv.gz
├── release-notes.md
├── rna-isoform-expression-rsem-tpm.rds
├── tumor-enriched-oncofetal-splice-junction-log2-cpm-combat-corrected.qs2
└── tumor-enriched-oncofetal-splice-junction-ctrl-log2-cpm-combat-corrected.qs2
```


## archived release (v1)
-   Release date: 2026-01-13
-   OpenPedCan data release date: 2024-03-01 (v15)
-   Status: available

### Data sources:
OpenPedCan (v15):
- `cptac-protein-imputed-prot-expression-abundance.tsv.gz`
- `gene-expression-rsem-tpm-collapsed.rds`
- `rna-isoform-expression-rsem-tpm.rds`
- `hope-protein-imputed-prot-expression-abundance.tsv.gz`
- `histologies.tsv`

Rokita lab data merges (v3), created using rMATS v4.3:
- `pbta-rmats_merged_raw_*.qs2`

[Germline preprocessing](https://github.com/rokitalab/germline-preprocessing)
- `somalier-ancestry-prediction-superpopulation.tsv`

```         
v1/
├── cptac-protein-imputed-prot-expression-abundance.tsv.gz
├── gene-expression-rsem-tpm-collapsed.rds
├── histologies.tsv
├── hope-protein-imputed-prot-expression-abundance.tsv.gz
├── md5sum.txt
├── pbta-rmats_merged_raw_A3SS.qs2
├── pbta-rmats_merged_raw_A5SS.qs2
├── pbta-rmats_merged_raw_RI.qs2
├── pbta-rmats_merged_raw_SE.qs2
├── release-notes.md
├── rna-isoform-expression-rsem-tpm.rds
└── somalier-ancestry-prediction-superpopulation.tsv
```

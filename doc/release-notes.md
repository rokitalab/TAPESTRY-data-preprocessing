# release notes

## current release (v2)
-   Release date: 2026-04-10
-   OpenPedCan data release date: 2024-03-01 (v15)
-   Status: available

### Data sources:
Tumor enriched splicing repo – [commit 5c9b5acd00857f5cf2d145a5ecca5fd54fa4beb9](https://github.com/rokitalab/tumor-enriched-splicing/tree/5c9b5acd00857f5cf2d145a5ecca5fd54fa4beb9):
- `cohort-histologies.tsv`
- `control-cohort-histologies.tsv`
- `recurrent-primary-tumor-enriched-oncofetal-splice-junctions-annotated.tsv.gz`
- `tumor-enriched-oncofetal-splice-junction-cpm-ctrls.rds`
- `tumor-enriched-oncofetal-splice-junction-cpm.rds`

Tumor enriched splicing (v9 data release):
- `evodevo*`
- `GSE73721*`
- `ped-normal-brain*`

OpenPedCan (v15):
- `cptac-protein-imputed-prot-expression-abundance.tsv.gz`
- `gene-expression-rsem-tpm-collapsed.rds`
- `rna-isoform-expression-rsem-tpm.rds`
- `hope-protein-imputed-prot-expression-abundance.tsv.gz`
- `histologies.tsv`
- `independent-specimens*`

```         
v2/
├── all-tumor-enriched-oncofetal-splice-junctions-annotated.tsv.gz
├── cohort-histologies.tsv
├── control-cohort-histologies.tsv
├── cptac-protein-imputed-prot-expression-abundance.tsv.gz
├── evodevo_gene-expression-rsem-tpm-collapsed.all.rds
├── evodevo_rna-isoform-expression-rsem-tpm.rds
├── evodevo-histologies.tsv
├── gene-expression-rsem-tpm-collapsed.rds
├── GSE73721-normal-histologies.tsv
├── GSE73721-normal-rna-isoform-expression-rsem-tpm.rds
├── histologies.tsv
├── hope-protein-imputed-prot-expression-abundance.tsv.gz
├── independent-specimens.rnaseqpanel.primary.tsv
├── independent-specimens.rnaseqpanel.relapse.tsv
├── independent-specimens.wgswxspanel.primary.prefer.wgs.tsv
├── independent-specimens.wgswxspanel.relapse.prefer.wgs.tsv
├── md5sum.txt
├── ped-normal-brain-gene-expression-rsem-tpm.all.rds
├── ped-normal-brain-histologies.tsv
├── ped-normal-brain-isoform-expression-rsem-tpm.rds
├── recurrent-primary-tumor-enriched-oncofetal-splice-junctions-annotated.tsv.gz
├── release-notes.md
├── rna-isoform-expression-rsem-tpm.rds
├── tumor-enriched-oncofetal-splice-junction-cpm-ctrls.rds
└── tumor-enriched-oncofetal-splice-junction-cpm.rds
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

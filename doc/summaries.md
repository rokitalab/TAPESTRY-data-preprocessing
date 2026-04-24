# Summary Views

Precomputed materialized views for the API summary pages. Defined in `db/migrations/04_summaries.sql`. Refreshed after pipelines run via `pipelines/refresh_views.py`.

To refresh manually:
```sql
REFRESH MATERIALIZED VIEW tesj_gene_summary;
REFRESH MATERIALIZED VIEW tesj_histology_summary;
```

---

## tesj_gene_summary

One row per gene. Aggregates TESJ junction counts across `tesj`, `sample_tesj`, `tesj_recurrence`, and `tesj_domain`.

| Column | Type | Notes |
|---|---|---|
| `gene` | TEXT | `tesj.gene_symbol` |
| `num_samples` | BIGINT | Distinct biospecimen IDs with at least one junction for this gene |
| `num_junctions` | BIGINT | Distinct junctions |
| `num_plot_groups` | BIGINT | Distinct plot groups in `tesj_recurrence` |
| `num_domains_affected` | BIGINT | Distinct domain names in `tesj_domain` |
| `num_oncofetal` | BIGINT | Junctions where `consensus_specificity = 'Oncofetal'` |
| `num_tumor_specific` | BIGINT | Junctions where `consensus_specificity = 'Tumor-specific'` |
| `num_annotated_junction` | BIGINT | Junctions where `status = 'Annotated junction'` |
| `num_novel_junction` | BIGINT | Junctions where `status = 'Novel junction'` |
| `num_novel_splice_site` | BIGINT | Junctions where `status = 'Novel splice site'` |
| `num_pref_a3_short` | BIGINT | Junctions where `preference_code = 'A3-'` |
| `num_pref_a3_long` | BIGINT | Junctions where `preference_code = 'A3+'` |
| `num_pref_a5_short` | BIGINT | Junctions where `preference_code = 'A5-'` |
| `num_pref_a5_long` | BIGINT | Junctions where `preference_code = 'A5+'` |
| `num_pref_ei` | BIGINT | Junctions where `preference_code = 'EI'` |
| `num_pref_es` | BIGINT | Junctions where `preference_code = 'ES'` |
| `num_pref_ri` | BIGINT | Junctions where `preference_code = 'RI'` |

### Relationships

```
tesj        (junction)       → tesj_gene_summary
sample_tesj (biospecimen_id) → tesj_gene_summary.num_samples
tesj_recurrence (plot_group) → tesj_gene_summary.num_plot_groups
tesj_domain (domain_name)    → tesj_gene_summary.num_domains_affected
```

---

## tesj_histology_summary

One row per histology (`plot_group`). Aggregates TESJ junction counts across `sample`, `sample_tesj`, and `tesj`.

| Column | Type | Notes |
|---|---|---|
| `plot_group` | TEXT | `sample.plot_group` |
| `num_samples` | BIGINT | Distinct biospecimen IDs in this plot group |
| `num_junctions` | BIGINT | Distinct junctions observed in this plot group |
| `num_genes` | BIGINT | Distinct genes with at least one junction in this plot group |
| `num_oncofetal` | BIGINT | Junctions where `consensus_specificity = 'Oncofetal'` |
| `num_tumor_specific` | BIGINT | Junctions where `consensus_specificity = 'Tumor-specific'` |
| `num_annotated_junction` | BIGINT | Junctions where `status = 'Annotated junction'` |
| `num_novel_junction` | BIGINT | Junctions where `status = 'Novel junction'` |
| `num_novel_splice_site` | BIGINT | Junctions where `status = 'Novel splice site'` |
| `num_pref_a3_short` | BIGINT | Junctions where `preference_code = 'A3-'` |
| `num_pref_a3_long` | BIGINT | Junctions where `preference_code = 'A3+'` |
| `num_pref_a5_short` | BIGINT | Junctions where `preference_code = 'A5-'` |
| `num_pref_a5_long` | BIGINT | Junctions where `preference_code = 'A5+'` |
| `num_pref_ei` | BIGINT | Junctions where `preference_code = 'EI'` |
| `num_pref_es` | BIGINT | Junctions where `preference_code = 'ES'` |
| `num_pref_ri` | BIGINT | Junctions where `preference_code = 'RI'` |

### Relationships

```
sample      (plot_group)     → tesj_histology_summary
sample_tesj (junction)       → tesj_histology_summary.num_junctions
tesj        (gene_symbol)    → tesj_histology_summary.num_genes
```

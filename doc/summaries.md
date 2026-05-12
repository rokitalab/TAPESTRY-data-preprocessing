# Summary Views

Precomputed materialized views for the API summary pages. Defined in `db/migrations/04_summaries.sql`. Refreshed after pipelines run via `pipelines/refresh_views.py`.

To refresh manually:
```sql
REFRESH MATERIALIZED VIEW tej_gene_summary;
REFRESH MATERIALIZED VIEW tej_histology_summary;
```

---

## tej_gene_summary

One row per gene. Aggregates TEJ junction counts across `tej`, `sample_tej`, `tej_recurrence`, and `tej_domain`.

| Column | Type | Notes |
|---|---|---|
| `gene` | TEXT | `tej.gene_symbol` |
| `num_samples` | BIGINT | Distinct biospecimen IDs with at least one junction for this gene |
| `num_junctions` | BIGINT | Distinct junctions |
| `num_plot_groups` | BIGINT | Distinct plot groups in `tej_recurrence` |
| `num_domains_affected` | BIGINT | Distinct domain names in `tej_domain` |
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
tej        (junction)       → tej_gene_summary
sample_tej (biospecimen_id) → tej_gene_summary.num_samples
tej_recurrence (plot_group) → tej_gene_summary.num_plot_groups
tej_domain (domain_name)    → tej_gene_summary.num_domains_affected
```

---

## tej_histology_summary

One row per histology (`plot_group`). Aggregates TEJ junction counts across `sample`, `sample_tej`, and `tej`.

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
sample      (plot_group)     → tej_histology_summary
sample_tej (junction)       → tej_histology_summary.num_junctions
tej        (gene_symbol)    → tej_histology_summary.num_genes
```

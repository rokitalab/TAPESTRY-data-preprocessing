-- 04_summaries.sql
-- Materialized views summarising TEJ results per gene and per histology.
-- Refresh after pipelines run: REFRESH MATERIALIZED VIEW tej_gene_summary, tej_histology_summary;

DROP MATERIALIZED VIEW IF EXISTS tej_gene_summary;
CREATE MATERIALIZED VIEW tej_gene_summary AS
SELECT
    t.gene_symbol                      AS gene,
    COUNT(DISTINCT st.biospecimen_id)  AS num_samples,
    COUNT(DISTINCT t.junction)         AS num_junctions,
    COUNT(DISTINCT tr.plot_group)      AS num_plot_groups,
    COUNT(DISTINCT td.domain_name)     AS num_domains_affected,
    COUNT(DISTINCT CASE WHEN t.consensus_specificity = 'Oncofetal' THEN t.junction END)      AS num_oncofetal,
    COUNT(DISTINCT CASE WHEN t.consensus_specificity = 'Tumor-specific' THEN t.junction END) AS num_tumor_specific,
    COUNT(DISTINCT CASE WHEN t.status = 'Annotated junction' THEN t.junction END)           AS num_annotated_junction,
    COUNT(DISTINCT CASE WHEN t.status = 'Novel junction' THEN t.junction END)               AS num_novel_junction,
    COUNT(DISTINCT CASE WHEN t.status = 'Novel splice site' THEN t.junction END)            AS num_novel_splice_site,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'A3-' THEN t.junction END)                AS num_pref_a3_short,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'A3+' THEN t.junction END)                AS num_pref_a3_long,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'A5-' THEN t.junction END)                AS num_pref_a5_short,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'A5+' THEN t.junction END)                AS num_pref_a5_long,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'EI' THEN t.junction END)                 AS num_pref_ei,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'ES' THEN t.junction END)                 AS num_pref_es,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'RI' THEN t.junction END)                 AS num_pref_ri
FROM tej t
LEFT JOIN sample_tej st             ON t.junction = st.junction
LEFT JOIN sample s                   ON st.biospecimen_id = s.biospecimen_id
LEFT JOIN tej_recurrence tr         ON t.junction = tr.junction
LEFT JOIN tej_domain td             ON t.junction = td.junction
WHERE s.cancer_group IS NOT NULL
GROUP BY t.gene_symbol;

CREATE INDEX ON tej_gene_summary (gene);

DROP MATERIALIZED VIEW IF EXISTS tej_histology_summary;
CREATE MATERIALIZED VIEW tej_histology_summary AS
SELECT
    s.plot_group,
    COUNT(DISTINCT s.biospecimen_id)                                                         AS num_samples,
    COUNT(DISTINCT st.junction)                                                              AS num_junctions,
    COUNT(DISTINCT t.gene_symbol)                                                            AS num_genes,
    COUNT(DISTINCT CASE WHEN t.consensus_specificity = 'Oncofetal' THEN st.junction END)    AS num_oncofetal,
    COUNT(DISTINCT CASE WHEN t.consensus_specificity = 'Tumor-specific' THEN st.junction END) AS num_tumor_specific,
    COUNT(DISTINCT CASE WHEN t.status = 'Annotated junction' THEN st.junction END)          AS num_annotated_junction,
    COUNT(DISTINCT CASE WHEN t.status = 'Novel junction' THEN st.junction END)              AS num_novel_junction,
    COUNT(DISTINCT CASE WHEN t.status = 'Novel splice site' THEN st.junction END)           AS num_novel_splice_site,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'A3-' THEN st.junction END)               AS num_pref_a3_short,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'A3+' THEN st.junction END)               AS num_pref_a3_long,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'A5-' THEN st.junction END)               AS num_pref_a5_short,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'A5+' THEN st.junction END)               AS num_pref_a5_long,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'EI' THEN st.junction END)                AS num_pref_ei,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'ES' THEN st.junction END)                AS num_pref_es,
    COUNT(DISTINCT CASE WHEN t.preference_code = 'RI' THEN st.junction END)                AS num_pref_ri
FROM sample s
LEFT JOIN sample_tej st ON s.biospecimen_id = st.biospecimen_id
LEFT JOIN tej t         ON st.junction = t.junction
WHERE s.cancer_group IS NOT NULL
GROUP BY s.plot_group;

CREATE INDEX ON tej_histology_summary (plot_group);

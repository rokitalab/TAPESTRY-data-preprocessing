#!/usr/bin/env python3
"""
02_tej.py

ETL for recurrent primary-tumor TEJ annotation file → tej, tej_domain, sample_tej tables.

Run:
  python -m pipelines.02_tej

Environment (read by db package):
  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
"""
from __future__ import annotations

import csv
import gzip
from pathlib import Path

from db.connection import get_connection

_NA = {"NA", "N/A", "", "nan", "NaN", "None", "none", "null"}

RECURRENT_FILE = Path("data/recurrent-primary-tumor-enriched-oncofetal-splice-junctions-annotated.tsv.gz")


def _str(val: str | None) -> str | None:
    if val is None or val.strip() in _NA:
        return None
    return val.strip()


def _int(val: str | None) -> int | None:
    v = _str(val)
    if v is None:
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _float(val: str | None) -> float | None:
    v = _str(val)
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _bool_yes(val: str | None) -> bool | None:
    v = _str(val)
    if v is None:
        return None
    return v.lower() == "yes"


def read_tsv_gz(path: Path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f, delimiter="\t")


def _junction_dict(row: dict) -> dict:
    return {
        "junction":               row["junction"],
        "chr":                    _str(row["chr"]),
        "strand":                 _str(row["strand"]),
        "gene_symbol":            _str(row["gene_symbol"]),
        "boundary":               _str(row["boundary"]),
        "up_jc_start":            _int(row["up_jc_start"]),
        "up_jc_end":              _int(row["up_jc_end"]),
        "down_jc_start":          _int(row["down_jc_start"]),
        "down_jc_end":            _int(row["down_jc_end"]),
        "in_cds":                 _bool_yes(row.get("in_cds")),
        "consequence":            _str(row["consequence"]),
        "consensus_jc_event_type": _str(row["consensus_jc_event_type"]),
        "junction_preference":    _str(row["junction_preference"]),
        "preference_code":        _str(row["preference_code"]),
        "novel_ss":               _bool_yes(row.get("novel_ss")),
        "junction_name":          _str(row["junction_name"]),
        "consensus_specificity":  _str(row.get("consensus_specificity")),
        "status":                 _str(row.get("status")),
        "min_cpm_fc_all":         _float(row["min_cpm_fc_all"]),
        "min_cpm_fc_postnatal":   _float(row["min_cpm_fc_postnatal"]),
        "min_cpm_snr_all":        _float(row["min_cpm_snr_all"]),
        "min_cpm_snr_postnatal":  _float(row["min_cpm_snr_postnatal"]),
        "max_mean_cpm_all":       _float(row["max_mean_cpm_all"]),
        "max_mean_cpm_postnatal": _float(row["max_mean_cpm_postnatal"]),
    }


def _domain_rows(row: dict) -> list[tuple]:
    domains = []

    pfam_id = _str(row["pfam_id"])
    if pfam_id is not None:
        domains.append((
            row["junction"],
            "pfam",
            pfam_id,
            _str(row["pfam_name"]),
            _str(row["pfam_description"]),
            _int(row["pfam_domain_start"]),
            _int(row["pfam_domain_end"]),
            _str(row["pfam_domain_overlap_type"]),
            _bool_yes(row.get("junction_overlaps_pfam_domain")),
        ))

    uniprot_type = _str(row["uniprot_domain_type"])
    if uniprot_type is not None:
        domains.append((
            row["junction"],
            "uniprot",
            uniprot_type,
            None,
            None,
            _int(row["uniprot_domain_start"]),
            _int(row["uniprot_domain_end"]),
            None,
            None,
        ))

    return domains


def load(conn) -> None:
    seen_junctions: dict[str, dict] = {}
    seen_domains: dict[str, list[tuple]] = {}
    sample_rows: list[tuple] = []
    # (junction, plot_group) → set of biospecimen_ids
    recurrence_samples: dict[tuple[str, str], set[str]] = {}

    for row in read_tsv_gz(RECURRENT_FILE):
        junc = row["junction"]
        if junc not in seen_junctions:
            seen_junctions[junc] = _junction_dict(row)
            seen_domains[junc] = _domain_rows(row)

        biospecimen_id = _str(row["Kids_First_Biospecimen_ID"])
        plot_group = _str(row["plot_group"])
        if biospecimen_id and plot_group:
            recurrence_samples.setdefault((junc, plot_group), set()).add(biospecimen_id)

        sample_rows.append((
            biospecimen_id,
            junc,
            _float(row["junction_cpm"]),
            _float(row["gene_tpm"]),
            _int(row["junction_count"]),
            _str(row["event_type_sample"]),
        ))

    print(f"Read {len(seen_junctions)} unique junctions, {len(sample_rows)} sample-junction rows")

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO tej (
                junction, chr, strand, gene_symbol, boundary,
                up_jc_start, up_jc_end, down_jc_start, down_jc_end,
                in_cds, consequence, consensus_jc_event_type,
                junction_preference, preference_code, novel_ss, junction_name,
                consensus_specificity, status,
                min_cpm_fc_all, min_cpm_fc_postnatal,
                min_cpm_snr_all, min_cpm_snr_postnatal,
                max_mean_cpm_all, max_mean_cpm_postnatal
            ) VALUES (
                %(junction)s, %(chr)s, %(strand)s, %(gene_symbol)s, %(boundary)s,
                %(up_jc_start)s, %(up_jc_end)s, %(down_jc_start)s, %(down_jc_end)s,
                %(in_cds)s, %(consequence)s, %(consensus_jc_event_type)s,
                %(junction_preference)s, %(preference_code)s, %(novel_ss)s, %(junction_name)s,
                %(consensus_specificity)s, %(status)s,
                %(min_cpm_fc_all)s, %(min_cpm_fc_postnatal)s,
                %(min_cpm_snr_all)s, %(min_cpm_snr_postnatal)s,
                %(max_mean_cpm_all)s, %(max_mean_cpm_postnatal)s
            )
            ON CONFLICT (junction) DO NOTHING
            """,
            list(seen_junctions.values()),
        )

        domain_rows = [d for domains in seen_domains.values() for d in domains]
        cur.executemany(
            """
            INSERT INTO tej_domain (
                junction, domain_source, domain_type, domain_name, domain_description,
                domain_start, domain_end, overlap_type, overlaps_domain
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            domain_rows,
        )

        cur.executemany(
            """
            INSERT INTO sample_tej (
                biospecimen_id, junction, junction_cpm, gene_tpm,
                junction_count, event_type_sample
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (biospecimen_id, junction) DO NOTHING
            """,
            sample_rows,
        )

        cur.execute("""
            SELECT plot_group, COUNT(*) AS n
            FROM sample
            WHERE rna_library IS NOT NULL
              AND plot_group IS NOT NULL
              AND is_independent_primary = TRUE
            GROUP BY plot_group
        """)
        total_by_plot_group = {pg: n for pg, n in cur.fetchall()}

        recurrence_rows = []
        for (junc, plot_group), biospecimen_ids in recurrence_samples.items():
            total = total_by_plot_group.get(plot_group)
            if total:
                recurrence_rows.append((
                    junc,
                    plot_group,
                    len(biospecimen_ids),
                    total,
                    round(len(biospecimen_ids) / total * 100, 2),
                ))

        cur.executemany(
            """
            INSERT INTO tej_recurrence (
                junction, plot_group, sample_count, total_samples, pct
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (junction, plot_group) DO NOTHING
            """,
            recurrence_rows,
        )

    conn.commit()
    print("02_tej done.")


def main() -> None:
    if not RECURRENT_FILE.exists():
        raise SystemExit(f"Input file not found: {RECURRENT_FILE}")

    with get_connection() as conn:
        load(conn)


if __name__ == "__main__":
    main()

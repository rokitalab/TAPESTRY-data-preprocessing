#!/usr/bin/env python3
"""
01_histologies.py

ETL for histologies files → patient, sample tables.

Run:
  python -m pipelines.01_histologies

Environment (read by db package):
  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
"""
from __future__ import annotations

import csv
from pathlib import Path

from db.connection import get_connection

# Values treated as NULL
_NA = {"NA", "N/A", "", "nan", "NaN", "None", "none", "null"}

TUMOR_FILE    = Path("data/cohort-histologies.tsv")
CONTROLS_FILE = Path("data/control-cohort-histologies.tsv")

# Secondary files used to enrich control sample metadata.
# Each entry: (path, delimiter, key_column) where key_column is the column
# in the secondary file whose value matches sample_id in control-cohort-histologies.
_CONTROL_SOURCES = [
    ("data/histologies.tsv",                  "\t", "Kids_First_Biospecimen_ID"),
    ("data/evodevo-histologies.tsv",          "\t", "Kids_First_Biospecimen_ID"),
    ("data/ped-normal-brain-histologies.tsv", "\t", "Kids_First_Biospecimen_ID"),
    ("data/ped-normal-brain-histologies.tsv", "\t", "sample_id"),
]
# GSE73721 samples have no participant ID → patient_id = NULL; no lookup needed.


_RNA_LIBRARY_MAP = {
    "stranded": "total RNA stranded",
}


def _str(val: str | None) -> str | None:
    if val is None or val.strip() in _NA:
        return None
    return val.strip()


def _rna_library(val: str | None) -> str | None:
    v = _str(val)
    if v is None:
        return None
    return _RNA_LIBRARY_MAP.get(v, v)


def _bool(val: str | None) -> bool | None:
    v = _str(val)
    if v is None:
        return None
    return v.lower() in {"yes", "true", "1"}


def _int(val: str | None) -> int | None:
    v = _str(val)
    if v is None:
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def read_tsv(path: Path, delimiter: str = "\t") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def _build_control_lookup() -> dict[str, dict]:
    """Build a mapping from control sample_id → secondary-file row."""
    lookup: dict[str, dict] = {}
    for path_str, delim, key_col in _CONTROL_SOURCES:
        p = Path(path_str)
        if not p.exists():
            continue
        for row in read_tsv(p, delim):
            k = _str(row.get(key_col))
            if k and k not in lookup:
                lookup[k] = row
    return lookup


def load_tumor(rows: list[dict[str, str]], conn) -> None:
    seen_patient: dict[str, dict] = {}

    for row in rows:
        pid = _str(row["Kids_First_Participant_ID"])
        seen_patient.setdefault(pid, row)

    with conn.cursor() as cur:
        # 1. patient
        cur.executemany(
            """
            INSERT INTO patient (
                patient_id, reported_gender, germline_sex_estimate,
                age_at_diagnosis_days, race, ethnicity, superpopulation,
                os_status, os_days, efs_status, efs_days, cancer_predispositions
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (patient_id) DO NOTHING
            """,
            [
                (
                    pid,
                    _str(r.get("reported_gender")),
                    _str(r.get("germline_sex_estimate")),
                    _int(r.get("age_at_diagnosis_days")),
                    _str(r.get("race")),
                    _str(r.get("ethnicity")),
                    _str(r.get("predicted_ancestry")),
                    _str(r.get("OS_status")),
                    _int(r.get("OS_days")),
                    _str(r.get("EFS_status")),
                    _int(r.get("EFS_days")),
                    _str(r.get("cancer_predispositions")),
                )
                for pid, r in seen_patient.items()
            ],
        )

        # 2. sample
        cur.executemany(
            """
            INSERT INTO sample (
                biospecimen_id, patient_id, cancer_group, molecular_subtype,
                match_id, resection, primary_site, cns_region,
                plot_group, cohort, sub_cohort, rna_library,
                composition, tumor_descriptor, is_independent_primary
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (biospecimen_id) DO NOTHING
            """,
            [
                (
                    _str(row["Kids_First_Biospecimen_ID"]),
                    _str(row["Kids_First_Participant_ID"]),
                    _str(row.get("cancer_group")),
                    _str(row.get("molecular_subtype")),
                    _str(row.get("match_id")),
                    _str(row.get("extent_of_tumor_resection")),
                    _str(row.get("primary_site")),
                    _str(row.get("CNS_region")),
                    _str(row.get("plot_group")),
                    _str(row.get("cohort")),
                    _str(row.get("sub_cohort")),
                    _rna_library(row.get("RNA_library")),
                    _str(row.get("composition")),
                    _str(row.get("tumor_descriptor")),
                    _bool(row.get("is_independent_primary")),
                )
                for row in rows
            ],
        )


def load_controls(
    control_rows: list[dict[str, str]],
    lookup: dict[str, dict],
    conn,
) -> None:
    seen_patient: dict[str, dict] = {}
    for row in control_rows:
        detail = lookup.get(_str(row["sample_id"]), {})
        pid = _str(detail.get("Kids_First_Participant_ID"))
        if pid and pid not in seen_patient:
            seen_patient[pid] = detail

    with conn.cursor() as cur:
        # 1. patient (controls have no cancer, OS, or EFS data)
        if seen_patient:
            cur.executemany(
                """
                INSERT INTO patient (
                    patient_id, reported_gender, germline_sex_estimate,
                    age_at_diagnosis_days, race, ethnicity
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (patient_id) DO NOTHING
                """,
                [
                    (
                        pid,
                        _str(r.get("reported_gender")),
                        _str(r.get("germline_sex_estimate")),
                        _int(r.get("age_at_diagnosis_days")),
                        _str(r.get("race")),
                        _str(r.get("ethnicity")),
                    )
                    for pid, r in seen_patient.items()
                ],
            )

        # 2. sample (controls have no cancer_group or molecular_subtype)
        cur.executemany(
            """
            INSERT INTO sample (
                biospecimen_id, patient_id,
                plot_group, primary_site, composition,
                cohort, sub_cohort, rna_library
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (biospecimen_id) DO NOTHING
            """,
            [
                (
                    _str(row["sample_id"]),
                    _str(lookup.get(_str(row["sample_id"]), {}).get("Kids_First_Participant_ID")),
                    _str(row.get("subgroup")),
                    _str(lookup.get(_str(row["sample_id"]), {}).get("primary_site")),
                    _str(lookup.get(_str(row["sample_id"]), {}).get("composition")),
                    _str(row.get("cohort")),
                    _str(row.get("subgroup")),
                    _rna_library(row.get("RNA_library")),
                )
                for row in control_rows
            ],
        )


def load(rows: list[dict[str, str]], control_rows: list[dict[str, str]]) -> None:
    lookup = _build_control_lookup()

    with get_connection() as conn:
        load_tumor(rows, conn)
        load_controls(control_rows, lookup, conn)
        conn.commit()


def main() -> None:
    if not TUMOR_FILE.exists():
        raise SystemExit(f"Input file not found: {TUMOR_FILE}")
    if not CONTROLS_FILE.exists():
        raise SystemExit(f"Controls file not found: {CONTROLS_FILE}")

    rows = read_tsv(TUMOR_FILE)
    print(f"Read {len(rows)} tumor rows")

    control_rows = read_tsv(CONTROLS_FILE)
    print(f"Read {len(control_rows)} control rows")

    load(rows, control_rows)
    print("01_histologies done.")


if __name__ == "__main__":
    main()

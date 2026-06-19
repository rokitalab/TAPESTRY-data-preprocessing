#!/usr/bin/env python3
"""
gene_junction_summary_compute.py

Computes the genome-wide junction summary (median CPM + total reads per
gene/junction/plot_group) from the raw merged splice-junction file
(data/v3/SJ.merged.tsv.gz) and writes it to a flat intermediate file
(data/v3/gene_junction_summary.tsv). pipelines/05_gene_junction_summary.py
loads that file into the gene_junction_summary table.

Covers both annotated and unannotated junctions (annotated is recorded as
its own field rather than filtered on). median_cpm is taken over every
sample in the plot_group, not just the ones with a row for that junction in
SJ.merged.tsv.gz -- samples with no reads at a junction are treated as 0,
not excluded, since otherwise the denominator would silently shrink to
"samples expressing this junction" and overstate typical expression.

This is split out from the DB-loading step for the same reason as
sj_library_size.py: it's an expensive single pass over a 23GB file
(~45-90 minutes) and has no need to touch the database at all, so it
shouldn't be coupled to DB availability or repeated just to retry a load.
Sample plot_group/cohort/is_independent_primary are read directly from the
same source files 01_histologies.py uses (data/cohort-histologies.tsv,
data/control-cohort-histologies.tsv) rather than the `sample` table, so this
script can run before the DB is even reachable.

Group assignment mirrors ../TAPESTRY/src/components/PlotArea.jsx's
collapseControlGroup(): Evo-devo's per-timepoint plot_group values collapse
to Forebrain/Hindbrain (Prenatal)/(Postnatal), and "Brain - X" / "basal
ganglia" values collapse the same way. Evo-devo samples additionally keep
their raw per-timepoint plot_group as a second group membership, so the
individual-timepoint view has data too. Samples are dropped entirely if
they have no plot_group, or if is_independent_primary is explicitly FALSE
(controls/cell lines, where it's NULL, are unaffected).

Control samples' collapsed group is further suffixed with their cohort's
facet label (PlotArea's COHORT_FACET_NAMES), since the collapsed group
alone collides across cohorts -- e.g. GTEx's "Brain - Cerebellum" and
Pediatric brain's "Cerebellum" both collapse to "Cerebellum", but they're
distinct sample populations and PlotArea itself keys groups by
`${cohort}::${histology}` to keep them apart. The raw per-timepoint
Evo-devo membership is left unsuffixed since it's parsed by the frontend's
region/timepoint splitting logic, not the cohort-keyed grouping.

Run:
  python -m pipelines.gene_junction_summary_compute
"""
from __future__ import annotations

import bisect
import csv
import gzip
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path

SJ_FILE = Path("data/v3/SJ.merged.tsv.gz")
GTF_FILE = Path("data/gencode.v39.primary_assembly.annotation.gtf.gz")
LIBRARY_SIZE_FILE = Path("data/v3/library_sizes.tsv")
OUTPUT_FILE = Path("data/v3/gene_junction_summary.tsv")

TUMOR_FILE = Path("data/cohort-histologies.tsv")
CONTROLS_FILE = Path("data/control-cohort-histologies.tsv")

_PROGRESS_EVERY = 200_000_000
# No annotated human gene exceeds this length; bounds the backward interval
# walk in dense regions once paired with the running max-end prefix check.
_MAX_GENE_SPAN = 3_000_000

_STRAND_CODES = {b"1": "+", b"2": "-"}
_NA = {"NA", "N/A", "", "nan", "NaN", "None", "none", "null"}

# Mirrors PlotArea.jsx's COHORT_FACET_NAMES -- the facet label shown for each
# control cohort, used here to disambiguate collapsed plot_groups that
# collide across cohorts (e.g. "Cerebellum" from both GTEx and Pediatric
# brain).
_COHORT_FACET_LABELS = {
    "Pediatric brain cell type": "Cell of Origin",
    "Evo-devo": "Evo-devo",
    "Pediatric brain": "Pediatric Brain",
    "GTEx": "GTEx <40",
}


def _facet_label(cohort: str | None) -> str:
    return _COHORT_FACET_LABELS.get(cohort, "Other")


def _str(val: str | None) -> str | None:
    if val is None or val.strip() in _NA:
        return None
    return val.strip()


def _open_sj():
    """Stream-decompress via the system gzip binary. Python's gzip module
    is ~4x slower than this for a file this size (measured)."""
    proc = subprocess.Popen(["gzcat", str(SJ_FILE)], stdout=subprocess.PIPE)
    return proc, proc.stdout


GeneIndex = dict[str, tuple[list[int], list[tuple[int, int, str]], list[int]]]


def _load_gene_intervals() -> GeneIndex:
    """chr -> (starts, [(start, end, gene_symbol)] sorted by start, running max-end prefix)."""
    by_chrom: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    with gzip.open(GTF_FILE, "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if fields[2] != "gene":
                continue
            chrom, start, end, attrs = fields[0], int(fields[3]), int(fields[4]), fields[8]
            gene_name = None
            for part in attrs.split(";"):
                part = part.strip()
                if part.startswith("gene_name "):
                    gene_name = part.split('"')[1]
                    break
            if gene_name:
                by_chrom[chrom].append((start, end, gene_name))

    index: GeneIndex = {}
    for chrom, ivs in by_chrom.items():
        ivs.sort()
        starts = [s for s, _, _ in ivs]
        max_end_prefix = []
        running_max = -1
        for _, end, _ in ivs:
            running_max = max(running_max, end)
            max_end_prefix.append(running_max)
        index[chrom] = (starts, ivs, max_end_prefix)
    return index


def _genes_at(index: GeneIndex, chrom: str, pos: int) -> set[str]:
    entry = index.get(chrom)
    if not entry:
        return set()
    starts, ivs, max_end_prefix = entry
    j = bisect.bisect_right(starts, pos) - 1
    genes: set[str] = set()
    while j >= 0:
        if max_end_prefix[j] < pos:
            break
        start, end, name = ivs[j]
        if end >= pos:
            genes.add(name)
        if start < pos - _MAX_GENE_SPAN:
            break
        j -= 1
    return genes


def _genes_for_junction(index: GeneIndex, chrom: str, istart: int, iend: int) -> set[str]:
    return _genes_at(index, chrom, istart) | _genes_at(index, chrom, iend)


def _collapse_control_group(plot_group: str) -> str:
    if plot_group.startswith("Forebrain-"):
        return "Forebrain (Prenatal)" if "Week Post Conception" in plot_group else "Forebrain (Postnatal)"
    if plot_group.startswith("Hindbrain-"):
        return "Hindbrain (Prenatal)" if "Week Post Conception" in plot_group else "Hindbrain (Postnatal)"
    if plot_group.startswith("Brain - "):
        stripped = plot_group[len("Brain - "):]
        return "Basal Ganglia" if "basal ganglia" in stripped else stripped
    if "basal ganglia" in plot_group:
        return "Basal Ganglia"
    return plot_group


def _load_sample_groups() -> dict[str, tuple[str, ...]]:
    """biospecimen_id -> group memberships (collapsed plot_group, cohort-
    suffixed for controls, plus the raw evo-devo timepoint where
    applicable). Omits samples with no plot_group or with
    is_independent_primary explicitly FALSE. Reads directly from the same
    source files 01_histologies.py uses to build the `sample` table, so this
    works without a DB connection."""
    out: dict[str, tuple[str, ...]] = {}

    with TUMOR_FILE.open(newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            plot_group = _str(row.get("plot_group"))
            if plot_group is None:
                continue
            ip = _str(row.get("is_independent_primary"))
            if ip is not None and ip.lower() not in {"yes", "true", "1"}:
                continue
            biospecimen_id = _str(row["Kids_First_Biospecimen_ID"])
            groups = {_collapse_control_group(plot_group)}
            if _str(row.get("cohort")) == "Evo-devo":
                groups.add(plot_group)
            out[biospecimen_id] = tuple(groups)

    with CONTROLS_FILE.open(newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            plot_group = _str(row.get("subgroup"))
            if plot_group is None:
                continue
            biospecimen_id = _str(row["sample_id"])
            cohort = _str(row.get("cohort"))
            collapsed = _collapse_control_group(plot_group)
            groups = {f"{collapsed} ({_facet_label(cohort)})"}
            if cohort == "Evo-devo":
                groups.add(plot_group)
            out[biospecimen_id] = tuple(groups)

    return out


def _load_library_sizes() -> dict[str, int]:
    sizes: dict[str, int] = {}
    with LIBRARY_SIZE_FILE.open() as f:
        next(f)  # header
        for line in f:
            sample_id, total = line.rstrip("\n").split("\t")
            sizes[sample_id] = int(total)
    return sizes


def _group_sizes(sample_groups: dict[str, tuple[str, ...]]) -> dict[str, int]:
    """Total number of samples carrying each group membership -- the
    denominator for zero-padding median_cpm in write_summary, since a
    sample with no reads at a junction never produces a cpm_values row for
    it but still belongs to the group."""
    sizes: dict[str, int] = defaultdict(int)
    for groups in sample_groups.values():
        for g in groups:
            sizes[g] += 1
    return sizes


def compute_summary(
    library_sizes: dict[str, int],
    sample_groups: dict[str, tuple[str, ...]],
    gene_index: GeneIndex,
) -> tuple[dict[tuple, list[float]], dict[tuple, int], dict[tuple, str]]:
    print("Scanning junctions, attributing to genes + groups...")
    cpm_values: dict[tuple, list[float]] = defaultdict(list)
    total_reads: dict[tuple, int] = defaultdict(int)
    annotated: dict[tuple, str] = {}
    proc, stream = _open_sj()
    next(stream)  # header
    n = 0
    for line in stream:
        parts = line.rstrip(b"\n").split(b"\t")
        sample_id = parts[0].decode()
        groups = sample_groups.get(sample_id)
        if not groups:
            continue
        lib_size = library_sizes.get(sample_id, 0)
        if lib_size == 0:
            continue
        chrom = parts[1].decode()
        istart, iend = int(parts[2]), int(parts[3])
        genes = _genes_for_junction(gene_index, chrom, istart, iend)
        if not genes:
            continue
        strand = _STRAND_CODES.get(parts[4])
        is_annotated = parts[6] == b"1"
        reads = int(parts[7])
        cpm = reads / lib_size * 1_000_000
        for gene in genes:
            for group in groups:
                key = (gene, chrom, istart, iend, strand, group)
                cpm_values[key].append(cpm)
                total_reads[key] += reads
                annotated.setdefault(key, is_annotated)
        n += 1
        if n % _PROGRESS_EVERY == 0:
            print(f"  {n:,} rows scanned, {len(cpm_values):,} keys so far...")
    proc.wait()
    print(f"  Done: {n:,} rows scanned, {len(cpm_values):,} distinct (gene, junction, group) keys.")
    return cpm_values, total_reads, annotated


def write_summary(
    cpm_values: dict[tuple, list[float]],
    total_reads: dict[tuple, int],
    annotated: dict[tuple, str],
    group_sizes: dict[str, int],
) -> None:
    """Samples in a group with zero reads at a junction never make it into
    cpm_values, so median/mean are taken over the observed values padded
    with one 0.0 per missing sample (group_sizes[group] - len(values)),
    rather than over only the samples that happened to express the
    junction. mean_cpm is included alongside median_cpm because median
    collapses to 0 for any junction detected in under half the group,
    hiding real signal from lowly-detected but strongly-expressed events
    that mean still captures."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w") as f:
        f.write("gene_symbol\tchr\tintron_start\tintron_end\tstrand\tannotated\tplot_group\tnum_samples_detected\tmedian_cpm\tmean_cpm\ttotal_reads\n")
        for key, values in cpm_values.items():
            gene, chrom, istart, iend, strand, group = key
            zero_count = max(group_sizes[group] - len(values), 0)
            padded = values + [0.0] * zero_count
            f.write(
                f"{gene}\t{chrom}\t{istart}\t{iend}\t{strand or ''}\t{int(annotated[key])}\t{group}\t"
                f"{len(values)}\t{statistics.median(padded)}\t{statistics.mean(padded)}\t{total_reads[key]}\n"
            )
    print(f"Wrote {len(cpm_values):,} rows to {OUTPUT_FILE}")


def main() -> None:
    if not SJ_FILE.exists():
        raise SystemExit(f"Input file not found: {SJ_FILE}")
    if not GTF_FILE.exists():
        raise SystemExit(f"GTF file not found: {GTF_FILE}")
    if not LIBRARY_SIZE_FILE.exists():
        raise SystemExit(
            f"Library size file not found: {LIBRARY_SIZE_FILE}\n"
            "Run `python -m pipelines.sj_library_size` first."
        )
    if not TUMOR_FILE.exists():
        raise SystemExit(f"Tumor histologies file not found: {TUMOR_FILE}")
    if not CONTROLS_FILE.exists():
        raise SystemExit(f"Control histologies file not found: {CONTROLS_FILE}")

    print("Loading gene intervals from GTF...")
    gene_index = _load_gene_intervals()
    n_genes = sum(len(ivs) for _, ivs, _ in gene_index.values())
    print(f"  {n_genes:,} genes across {len(gene_index)} chromosomes.")

    library_sizes = _load_library_sizes()
    print(f"Loaded library sizes for {len(library_sizes):,} samples.")

    sample_groups = _load_sample_groups()
    print(f"{len(sample_groups):,} samples have a usable plot_group.")
    group_sizes = _group_sizes(sample_groups)

    cpm_values, total_reads, annotated = compute_summary(library_sizes, sample_groups, gene_index)
    write_summary(cpm_values, total_reads, annotated, group_sizes)

    print("gene_junction_summary_compute done.")


if __name__ == "__main__":
    main()

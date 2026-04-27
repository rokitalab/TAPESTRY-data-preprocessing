from db.connection import db_cursor


def main():
    with db_cursor() as cur:
        cur.execute("REFRESH MATERIALIZED VIEW tej_gene_summary")
        cur.execute("REFRESH MATERIALIZED VIEW tej_histology_summary")
    print("Refreshed materialized views.")


if __name__ == "__main__":
    main()

# database/migrations

Raw SQL migrations applied sequentially by your migration process or manually via scripts.

Naming convention (2-digit, ordered):
- `01_initial.sql`
- `02_add_users_table.sql`

Each file should be idempotent where possible and safe to re-run.

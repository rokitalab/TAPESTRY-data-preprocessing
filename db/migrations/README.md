# db/migrations

SQL migrations applied sequentially by the seed runner (`db/seed.py`).

Naming convention: 2-digit prefix, ordered:

| File | Description |
|------|-------------|
| `01_histologies.sql` | Creates `patient` and `sample` tables with indexes |

Each file should be idempotent where possible (`CREATE TABLE IF NOT EXISTS`, etc.).

---
id: tech-guide-migration
title: "Guide: change the schema"
kind: tech
status: current
summary: How to add a schema change as a migration file, the rules for it, how it applies at start and with mise run migrate, how to reset the dev database and how to test a migration.
read_when: you add, change or remove a table or a column, or a migration fails
updated: 2026-11-05
verified: 2026-11-05
source_anchors: [app/core/migrate.py, app/migrations/0001_init.sql, app/migrations/0002_sample_data.sql, tests/unit/test_migrate.py, tests/integration/test_sample_data.py, mise.toml]
depends_on: [tech-architecture, tech-practices]
review_cycle: quarterly
---

# Guide: change the schema

Every schema change is a new SQL file in `app/migrations/`. The runner in `app/core/migrate.py`
applies the file once. The model is in [`architecture.md`](./architecture.md).

## 1. Rules

- Name the file `NNNN_slug.sql`. Use the next free four-digit number and a snake case slug, for example `0003_add_expense_note.sql`.
- Never edit a file that the runner applied. The record says the file ran, so an edit makes databases differ.
- Never write a down migration. Migrations are forward only. To undo a change, add a new file.
- Put one concern in one file. A failure then points to one change.
- Write the backfill of data in the same file in SQL. Existing rows must satisfy the new schema.
- Write no `BEGIN` or `COMMIT`. The runner wraps each file in one transaction.
- Store money as `INTEGER` minor units, and give each money column a currency code column.
- Store dates as `TEXT` in ISO form. Name columns `expense_date`, `payment_date` and `created_at`.
- Add `NOT NULL` and `CHECK` constraints in the schema when the rule is simple. Services still validate.

### Dev-only files

A dev-only file holds sample data for local work. It never holds schema.

- Write `-- splitwise: dev-only` as the first line of the file.
- The runner applies the file only when `SPLITWISE_ENV` is `dev`. In `test` and `prod` it skips the file, logs `migration.skipped` and does not record it. A test or prod database never holds the data.
- Use the marker for sample data only. Never use it for a table, a column or an index, because then the schema differs between environments.
- Write the file so it cannot fail on a database that has some rows. Use `INSERT OR IGNORE` and look up each id with a subselect. Never write an id.
- `0002_sample_data.sql` is the example. It creates 4 users and 3 groups.

## 2. Add a change

1. Find the next number: `ls app/migrations`.
2. Create `app/migrations/NNNN_slug.sql`.
3. Write the SQL for the change and its backfill.
4. Run `mise run migrate`. Check the log event `migration.applied`.
5. Update the repository functions that use the changed tables.
6. Write the test of section 5.
7. Run `mise run test`.

If step 4 fails, fix the SQL. The runner rolled the file back, so the file is not recorded. You may
edit it. If the file ran on another database, add a new file instead.

## 3. SQLite limits and the rebuild pattern

SQLite `ALTER TABLE` can rename a table, rename a column, add a column and drop a column that no
index, key or constraint uses. It cannot change a column type, add a constraint to a column or
drop a column in a key.

| Change | Method |
|---|---|
| Add a column | `ALTER TABLE ... ADD COLUMN`. A `NOT NULL` column needs a default |
| Rename | `ALTER TABLE ... RENAME` |
| Add an index | `CREATE INDEX` |
| Change a type or a constraint | Rebuild the table |

The rebuild pattern keeps the data:

```sql
CREATE TABLE expenses_new (
  id INTEGER PRIMARY KEY,
  group_id INTEGER NOT NULL REFERENCES groups(id),
  amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
  currency TEXT NOT NULL
);
INSERT INTO expenses_new (id, group_id, amount_minor, currency)
  SELECT id, group_id, amount_minor, currency FROM expenses;
DROP TABLE expenses;
ALTER TABLE expenses_new RENAME TO expenses;
CREATE INDEX expenses_group_idx ON expenses (group_id, expense_date);
```

After a rebuild, create again every index and trigger of the old table. The drop deletes them.
Other tables that reference the table need no change, because the new table keeps the name.
The runner checks `PRAGMA foreign_key_check` after each file.

## 4. How migrations apply

| Moment | What happens |
|---|---|
| App start | The lifespan runs pending files in ascending order before the first request |
| `mise run migrate` | The same runner runs without the server |
| Each file | One transaction. The runner inserts a row in `schema_migrations` in the same transaction |
| Failure | The file rolls back and the app does not start. The log shows the file name and the error |
| Gap or edit | The runner stops if a recorded name differs from its file |

### Reset the dev database

CAUTION: this deletes every group, expense and payment in `_data/`.

1. Stop the server.
2. Run `mise run db-reset`.
3. Start the server.

Use a reset when you edit a migration that only your database ran, or when the data is broken.

## 5. Test a migration

Write a unit test in `tests/unit/test_migrate.py`.

1. Create an empty temp database.
2. Apply the migrations up to `NNNN-1`.
3. Insert rows in the old shape.
4. Apply `NNNN`.
5. Assert on the new shape and on the backfilled rows.

```python
def test_0002_backfills_note(tmp_db):
    migrate(tmp_db, upto=1)
    tmp_db.execute("INSERT INTO expenses (...) VALUES (...)")
    migrate(tmp_db, upto=2)
    row = tmp_db.execute("SELECT note FROM expenses").fetchone()
    assert row["note"] == ""
```

One more test applies all files to an empty database and checks the list of recorded versions.

## Related docs

- [`architecture.md`](./architecture.md): the migration model and its reasons
- [`practices.md`](./practices.md): the testing and money rules
- [`project-structure.md`](./project-structure.md): where migration files live
- [`../infra/dev-environment.md`](../infra/dev-environment.md): the `migrate` and `db-reset` tasks

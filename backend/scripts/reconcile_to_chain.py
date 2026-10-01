"""reconcile an existing database with the migration chain

Why this exists
---------------
The chain in backend/migrations had no working baseline (see
0001_initial_schema): databases were actually built by
`SQLModel.metadata.create_all()` at app startup, and their `alembic_version`
rows record revisions that never ran. Verified against a production copy:

  * `add_cascade_del_opp_fk` is stamped applied, and its effect IS present;
  * `a1b2c3d4e5f6` (add_api_keys_table) is NOT stamped, yet `api_keys`
    exists - with a shape that revision would never have produced;
  * `add_opportunity_status` never ran, so `opportunities.status` is VARCHAR.

So you cannot `alembic stamp` onto the new chain: stamping asserts the
baseline already ran, and any real divergence would then be skipped silently
and forever, leaving whoever trusts `alembic current` next with the same lie.

What it does
------------
1. Compares the ACTUAL schema with the models - the only consistent source of
   truth - using alembic's autogenerate comparer.
2. Classifies every difference:
     additive      creates a missing object; cannot lose data
     structural    changes a column's type/nullability/default; MAY lose data
     destructive   drops an object that may hold data
3. With --apply: executes ONLY the additive set, stamps 0001, re-compares and
   reports what remains. Structural and destructive differences are never
   applied by this script - it has no safe way to know whether a type change
   is lossy, and it will not find out on your data.

Usage
-----
    python scripts/reconcile_to_chain.py                     # dry run + report
    python scripts/reconcile_to_chain.py --url <dsn>         # point elsewhere
    python scripts/reconcile_to_chain.py --apply --snapshot-backup /tmp/pre.bak
    python scripts/reconcile_to_chain.py --json

Run it against a COPY first. That is not boilerplate: this script exists
precisely because the target's recorded state cannot be trusted.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlalchemy as sa  # noqa: E402
from alembic.autogenerate import compare_metadata  # noqa: E402
from alembic.migration import MigrationContext  # noqa: E402
from alembic.operations import Operations  # noqa: E402
from alembic.operations.ops import (  # noqa: E402,F401
    AddColumnOp,
    CreateForeignKeyOp,
    CreateIndexOp,
    CreateTableOp,
    ModifyTableOps,
)
from alembic import command as alembic_command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

from app.config import settings  # noqa: E402
import app.models  # noqa: F401,E402  (registers every table on SQLModel.metadata)

BASELINE_REV = "0001_initial_schema"
BACKEND_DIR = Path(__file__).resolve().parent.parent

# compare_metadata kinds, bucketed by whether applying them can lose data.
ADDITIVE_KINDS = {"add_table", "add_column", "add_index", "add_fk",
                  "add_unique_constraint", "add_check_constraint",
                  "add_not_null_constraint"}
STRUCTURAL_KINDS = {"modify_type", "modify_nullable", "modify_default",
                    "modify_comment", "add_server_default",
                    "remove_server_default", "change_server_default"}
DESTRUCTIVE_KINDS = {"remove_table", "remove_column", "remove_index",
                     "remove_fk", "remove_unique_constraint",
                     "remove_check_constraint", "remove_not_null_constraint"}


def flatten(diffs):
    """compare_metadata yields (kind, ...) tuples and list-of-tuples groups."""
    out = []
    for item in diffs:
        if isinstance(item, list):
            out.extend(item)
        elif isinstance(item, tuple):
            out.append(item)
    return out


def describe(diff) -> str:
    kind = diff[0]
    try:
        if kind in ("add_table", "remove_table"):
            return f"{kind:24s} {diff[1].name}"
        if kind in ("add_column", "remove_column", "modify_type", "modify_nullable",
                    "modify_default"):
            schema, table, col = diff[1], diff[2], diff[3]
            detail = ""
            if isinstance(diff[-1], dict):
                d = diff[-1]
                detail = " ".join(
                    f"{k}={_short(v)}" for k, v in sorted(d.items())
                    if k.startswith("existing") or k in ("nullable", "type_")
                )
            return f"{kind:24s} {table}.{col} {detail}".rstrip()
        if kind in ("add_index", "remove_index"):
            idx = diff[1]
            return f"{kind:24s} {idx.name}"
        if kind in ("add_fk", "remove_fk"):
            con = diff[1]
            cols = [d.parent.name for d in con.elements]
            return (f"{kind:24s} {con.table.name}{cols} -> "
                    f"{con.referred_table.name} ondelete={con.ondelete!r}")
    except Exception as exc:  # reporting must never crash a reconciliation
        return f"{kind:24s} <describe failed: {exc}>"
    return f"{kind:24s} {diff[1]!r}"


def _short(v) -> str:
    s = type(v).__name__
    if s.endswith("TypeEngine") or s in ("VARCHAR", "String", "DateTime", "Uuid",
                                         "Boolean", "Float", "Integer"):
        s = f"{v!r}"
    return (s[:60] + "...") if len(s) > 60 else s


def apply_additive(engine) -> int:
    """Execute only the ops autogenerate classifies as purely additive.

    Note this walks ModifyTableOps containers: compare_metadata groups
    per-column changes under them, so an inner AddColumnOp is additive while
    its sibling ModifyColumnTypeOp in the same container is not. Filtering has
    to happen at the inner op, never at the group.
    """
    count = 0
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        ops = Operations(ctx)
        diffs = flatten(compare_metadata(ctx, SQLModel.metadata))

        for diff in diffs:
            kind = diff[0]
            if kind not in ADDITIVE_KINDS:
                continue
            if kind == "add_table":
                ops.create_table(diff[1])
            elif kind == "add_column":
                ops.add_column(diff[2], diff[1])
            elif kind == "add_index":
                idx = diff[1]
                cols = [c.name if hasattr(c, "name") else str(c)
                        for c in (idx.expressions if hasattr(idx, "expressions")
                                  else idx.columns)]
                ops.create_index(idx.name, idx.table.name, cols,
                                 unique=idx.unique)
            elif kind == "add_fk":
                con = diff[1]
                # Referenced columns come from the constraint's own
                # ForeignKey.target, NOT referred_table.primary_key: the
                # autogenerate-side table objects are detached proxies whose
                # primary key collection is empty, which yields a
                # mismatched-length constraint and an ArgumentError.
                ops.create_foreign_key(
                    con.name, con.table.name, con.referred_table.name,
                    [d.parent.name for d in con.elements],
                    [fk.column.name for fk in con.elements
                     for f in fk._table_constraint_for_update if False] if False
                    else [fk.target_fullname.split(".")[-1] for fk in con.elements],
                    ondelete=con.ondelete,
                )
            elif kind in ("add_unique_constraint", "add_check_constraint"):
                con = diff[1]
                creator = (ops.create_unique_constraint
                           if kind.endswith("unique_constraint")
                           else ops.create_check_constraint)
                creator(con.name, con.table.name,
                        [d.parent.name for d in con.elements])
            else:  # pragma: no cover - ADDITIVE_KINDS is exhaustive above
                raise NotImplementedError(f"unhandled additive kind {kind!r}")
            count += 1
    return count





def _snapshot(engine, path: str) -> bool:
    """pg_dump -Fc the target. Returns False if it could not be produced."""
    dsn = engine.url.render_as_string(hide_password=False)
    print(f"\npg_dump -Fc -> {path}")
    try:
        with open(path, "wb") as fh:
            subprocess.run(["pg_dump", "-Fc", "-d", dsn], check=True, stdout=fh)
    except FileNotFoundError:
        print("pg_dump not found on PATH; no snapshot taken.", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as exc:
        print(f"pg_dump failed (exit {exc.returncode}).", file=sys.stderr)
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reconcile a database with the migration chain.")
    ap.add_argument("--url", default=None,
                    help="target DSN (default: settings.DATABASE_URL)")
    ap.add_argument("--apply", action="store_true",
                    help="apply additive changes and stamp the baseline")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--snapshot-backup", metavar="PATH",
                    help="pg_dump -Fc the target to PATH before applying; if a "
                         "snapshot cannot be written, --apply aborts. Needs a "
                         "pg_dump on PATH (absent in containerised setups).")
    ap.add_argument("--no-stamp", action="store_true",
                    help="apply changes but leave alembic_version alone")
    args = ap.parse_args()

    engine = sa.create_engine(args.url or settings.DATABASE_URL)

    with engine.connect() as conn:
        diffs = flatten(compare_metadata(MigrationContext.configure(conn),
                                         SQLModel.metadata))

    buckets = {
        "additive": [d for d in diffs if d[0] in ADDITIVE_KINDS],
        "structural": [d for d in diffs if d[0] in STRUCTURAL_KINDS],
        "destructive": [d for d in diffs if d[0] in DESTRUCTIVE_KINDS],
        "other": [d for d in diffs
                  if d[0] not in ADDITIVE_KINDS | STRUCTURAL_KINDS | DESTRUCTIVE_KINDS],
    }

    if args.json:
        print(json.dumps({
            "target": str(engine.url.render_as_string(hide_password=True)),
            "total": len(diffs),
            **{k: [describe(d) for d in v] for k, v in buckets.items()},
        }, indent=2))
    else:
        print(f"target: {engine.url.render_as_string(hide_password=True)}")
        print(f"differences vs models: {len(diffs)}")
        for label, group in (
            ("ADDITIVE      (missing objects; applied by --apply)", buckets["additive"]),
            ("STRUCTURAL    (type/nullability/default; NOT applied)", buckets["structural"]),
            ("DESTRUCTIVE   (would drop objects; NOT applied)", buckets["destructive"]),
            ("OTHER         (unclassified; NOT applied)", buckets["other"]),
        ):
            print(f"\n{label}: {len(group)}")
            for d in group:
                print("   ", describe(d))
        if not diffs:
            print("\nschema already matches the models.")

    if not args.apply:
        if not args.json:
            print("\ndry run; pass --apply to change anything.")
        return 0

    skipped = (buckets["structural"] + buckets["destructive"] + buckets["other"])
    if skipped:
        print(
            f"\nApplying the additive set only. {len(skipped)} structural/"
            "destructive/unclassified difference(s) are deliberately left for "
            "an explicit revision - see list above.",
            file=sys.stderr,
        )

    if args.apply and args.snapshot_backup:
        if not _snapshot(engine, args.snapshot_backup):
            print(
                "aborting: could not write the snapshot. Refusing to change a "
                "database we cannot roll back.", file=sys.stderr)
            return 3

    n = apply_additive(engine)
    print(f"\napplied {n} additive change(s).")

    if not args.no_stamp:
        cfg = Config(str(BACKEND_DIR / "alembic.ini"))
        cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
        # env.py honours ALEMBIC_DATABASE_URL, which is what makes it safe to
        # drive alembic's own command API from here rather than re-implementing
        # stamp against a private constructor.
        import os
        os.environ["ALEMBIC_DATABASE_URL"] = engine.url.render_as_string(hide_password=False)
        # purge=True is required, not cosmetic. These databases carry
        # alembic_version rows naming revisions that the new chain does not
        # contain (they were dropped as never-executed); without purge, alembic
        # tries to resolve the existing rows and aborts with
        # "Can't locate revision identified by 'add_cascade_del_opp_fk'".
        # Purge rewrites the table from scratch, which is exactly the intent:
        # the old stamps are noise, not history.
        alembic_command.stamp(cfg, BASELINE_REV, purge=True)
        print(f"stamped {BASELINE_REV} (purged previous version_num rows)")

    with engine.connect() as conn:
        residual = flatten(compare_metadata(MigrationContext.configure(conn),
                                           SQLModel.metadata))
    print(f"residual differences after reconcile: {len(residual)}")
    for d in residual:
        print("   ", describe(d))
    print(
        "\nResidual structural differences are EXPECTED until you decide how to\n"
        "resolve them; the database is now inside the chain either way."
        if residual else ""
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

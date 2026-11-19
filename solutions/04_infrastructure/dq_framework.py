"""
=============================================================
StackUp Engineering Academy - Data Engineering Assessment
Module: dq_framework.py
Task 4.3 - Reusable, configurable data quality framework
=============================================================

Rules and thresholds come from dq_config.DQ_CONFIG (or a dict you pass in).
The engine contains no dataset-specific rules.

Core checks (6)
---------------
  completeness, uniqueness, validity_numeric, validity_date,
  consistency, referential_integrity

Bonus checks (run only if configured)
-------------------------------------
  distribution, freshness, outliers

Extending
---------
  * New rule values  -> edit dq_config.py
  * New check type   -> decorate a function with @register_check("name")
  * New consistency rule type -> @register_consistency_rule("type")

Usage
-----
    from dq_framework import run_data_quality_checks, run_all_checks

    report = run_data_quality_checks(
        df, "projects", reference_tables={"employees": employees_df}
    )

    reports = run_all_checks(
        {"projects": p, "employees": e, "transactions": t},
        output_dir="outputs",          # also writes dq_report_{dataset}.md
    )
"""

import logging
import os
from datetime import datetime
from typing import Callable, Optional

import numpy as np
import pandas as pd

from dq_config import DQ_CONFIG

logger = logging.getLogger(__name__)

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"

CHECK_REGISTRY: dict = {}
CONSISTENCY_RULES: dict = {}


# ── Registration helpers ───────────────────────────────────────────────────────

def register_check(name: str) -> Callable:
    """Register a dataset-level check: fn(df, cfg, ctx) -> result dict | None.

    Returning None means "not configured for this dataset" (check is not run).
    """
    def decorator(fn):
        CHECK_REGISTRY[name] = fn
        return fn
    return decorator


def register_consistency_rule(rule_type: str) -> Callable:
    """Register a consistency rule: fn(df, rule) -> (label, violations|None, skip_reason|None)."""
    def decorator(fn):
        CONSISTENCY_RULES[rule_type] = fn
        return fn
    return decorator


def _missing(df: pd.DataFrame, cols) -> list:
    return [c for c in cols if c not in df.columns]


# ── Check 1: Completeness ──────────────────────────────────────────────────────

@register_check("completeness")
def check_completeness(df, cfg, ctx):
    threshold = cfg.get("completeness_threshold")
    if threshold is None:
        return None

    fraction = (1 - df.isnull().mean()).round(4)
    failed = [col for col, val in fraction.items() if val < threshold]
    return {
        "status": FAIL if failed else PASS,
        "threshold": threshold,
        "details": {col: float(val) for col, val in fraction.items()},
        "failed_columns": failed,
    }


# ── Check 2: Uniqueness ────────────────────────────────────────────────────────

@register_check("uniqueness")
def check_uniqueness(df, cfg, ctx):
    pk = cfg.get("pk_columns")
    if not pk:
        return None

    miss = _missing(df, pk)
    if miss:
        return {"status": SKIP, "details": f"PK column(s) not found: {miss}"}

    total = len(df)
    unique = len(df.drop_duplicates(subset=pk))
    null_keys = int(df[pk].isna().any(axis=1).sum())
    ok = unique == total and null_keys == 0

    details = f"{', '.join(pk)}: {unique} unique / {total} total"
    if null_keys:
        details += f"; {null_keys} null key value(s)"
    return {"status": PASS if ok else FAIL, "details": details}


# ── Check 3: Validity - numeric ────────────────────────────────────────────────

@register_check("validity_numeric")
def check_validity_numeric(df, cfg, ctx):
    ranges = cfg.get("numeric_ranges")
    if not ranges:
        return None

    messages, skipped, failed = [], [], False
    for col, bounds in ranges.items():
        if col not in df.columns:
            skipped.append(col)
            continue

        raw = df[col]
        values = pd.to_numeric(raw, errors="coerce")
        non_numeric = int((raw.notna() & values.isna()).sum())
        lo, hi = bounds.get("min"), bounds.get("max")
        below = int((values < lo).sum()) if lo is not None else 0
        above = int((values > hi).sum()) if hi is not None else 0

        parts = []
        if below:
            parts.append(f"{below} value(s) below minimum ({lo})")
        if above:
            parts.append(f"{above} value(s) above maximum ({hi})")
        if non_numeric:
            parts.append(f"{non_numeric} non-numeric value(s)")

        if parts:
            failed = True
            messages.append(f"{col}: " + ", ".join(parts))
        else:
            messages.append(f"{col}: all values within [{lo}, {hi}]")

    if skipped:
        messages.append(f"skipped (column not found): {skipped}")
    if len(skipped) == len(ranges):
        return {"status": SKIP, "details": "; ".join(messages)}
    return {"status": FAIL if failed else PASS, "details": "; ".join(messages)}


# ── Check 4: Validity - date ───────────────────────────────────────────────────

def _parse_dates(series: pd.Series) -> pd.Series:
    """Parse to datetime; unparseable / out-of-range values become NaT."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    return pd.to_datetime(series.astype("string"), errors="coerce")


@register_check("validity_date")
def check_validity_date(df, cfg, ctx):
    date_cols = cfg.get("date_columns")
    if not date_cols:
        return None

    non_future = set(cfg.get("non_future_dates", []))
    today = pd.Timestamp.now().normalize()
    messages, skipped, failed = [], [], False

    for col in date_cols:
        if col not in df.columns:
            skipped.append(col)
            continue

        parsed = _parse_dates(df[col])
        invalid = int((df[col].notna() & parsed.isna()).sum())
        future = int((parsed > today).sum()) if col in non_future else 0

        parts = []
        if invalid:
            parts.append(f"{invalid} invalid date(s)")
        if future:
            parts.append(f"{future} future date(s)")

        if parts:
            failed = True
            messages.append(f"{col}: " + ", ".join(parts))
        else:
            messages.append(f"{col}: all dates valid")

    if skipped:
        messages.append(f"skipped (column not found): {skipped}")
    if len(skipped) == len(date_cols):
        return {"status": SKIP, "details": "; ".join(messages)}
    return {"status": FAIL if failed else PASS, "details": "; ".join(messages)}


# ── Check 5: Consistency (rules are pluggable) ─────────────────────────────────

@register_consistency_rule("before")
def _rule_before(df, rule):
    earlier, later = rule["columns"]
    label = f"{earlier} < {later}"
    miss = _missing(df, [earlier, later])
    if miss:
        return label, None, f"column(s) not found: {miss}"

    a, b = _parse_dates(df[earlier]), _parse_dates(df[later])
    violations = int((a.notna() & b.notna() & (a >= b)).sum())
    return label, violations, None


@register_consistency_rule("non_negative")
def _rule_non_negative(df, rule):
    col = rule["column"]
    label = f"{col} >= 0"
    if col not in df.columns:
        return label, None, f"column not found: {col}"

    values = pd.to_numeric(df[col], errors="coerce")
    return label, int((values < 0).sum()), None


@register_consistency_rule("salary_by_level")
def _rule_salary_by_level(df, rule):
    sal_col, lvl_col = rule["salary_column"], rule["level_column"]
    label = f"{sal_col} within band for {lvl_col}"
    miss = _missing(df, [sal_col, lvl_col])
    if miss:
        return label, None, f"column(s) not found: {miss}"

    salary = pd.to_numeric(df[sal_col], errors="coerce")
    violations = 0
    for level, band in rule["bands"].items():
        rows = df[lvl_col] == level
        lo, hi = band.get("min"), band.get("max")
        bad = pd.Series(False, index=df.index)
        if lo is not None:
            bad |= salary < lo
        if hi is not None:
            bad |= salary > hi
        violations += int((rows & bad).sum())
    return label, violations, None


@register_check("consistency")
def check_consistency(df, cfg, ctx):
    rules = cfg.get("consistency_rules")
    if not rules:
        return None

    messages, ran, failed = [], 0, False
    for rule in rules:
        rule_type = rule.get("type")
        fn = CONSISTENCY_RULES.get(rule_type)
        if fn is None:
            messages.append(f"unknown rule type '{rule_type}' (skipped)")
            continue

        label, violations, skip_reason = fn(df, rule)
        if skip_reason:
            messages.append(f"{label}: skipped ({skip_reason})")
            continue

        ran += 1
        if violations:
            failed = True
        messages.append(f"{label}: {violations} violation(s)")

    if ran == 0:
        return {"status": SKIP, "details": "; ".join(messages)}
    return {"status": FAIL if failed else PASS, "details": "; ".join(messages)}


# ── Check 6: Referential integrity ─────────────────────────────────────────────

@register_check("referential_integrity")
def check_referential_integrity(df, cfg, ctx):
    fks = cfg.get("foreign_keys")
    if not fks:
        return None

    refs = ctx.get("reference_tables", {})
    messages, ran, failed = [], 0, False

    for col, (ref_table, ref_col) in fks.items():
        label = f"{col} -> {ref_table}.{ref_col}"
        if col not in df.columns:
            messages.append(f"{label}: skipped (column '{col}' not found)")
            continue
        if ref_table not in refs or ref_col not in refs[ref_table].columns:
            messages.append(f"{label}: skipped (reference table/column not provided)")
            continue

        ran += 1
        values = df[col].dropna()
        valid_keys = set(refs[ref_table][ref_col].dropna())
        orphans = values[~values.isin(valid_keys)]

        if len(orphans):
            failed = True
            sample = orphans.drop_duplicates().head(3).tolist()
            messages.append(
                f"{label}: {len(orphans)} orphan row(s), "
                f"{orphans.nunique()} distinct value(s), e.g. {sample}"
            )
        else:
            messages.append(f"{label}: all {len(values)} non-null values found")

    if ran == 0:
        return {"status": SKIP, "details": "; ".join(messages)}
    return {"status": FAIL if failed else PASS, "details": "; ".join(messages)}


# ── Bonus: Distribution ────────────────────────────────────────────────────────

@register_check("distribution")
def check_distribution(df, cfg, ctx):
    conf = cfg.get("distribution")
    if not conf:
        return None

    limit = conf.get("max_same_value_pct", 0.30)
    messages, ran, failed = [], 0, False
    for col in conf.get("columns", []):
        if col not in df.columns or df[col].dropna().empty:
            messages.append(f"{col}: skipped (missing or empty)")
            continue
        ran += 1
        shares = df[col].value_counts(normalize=True, dropna=True)
        top_value, top_share = shares.index[0], float(shares.iloc[0])
        if top_share > limit:
            failed = True
            messages.append(
                f"{col}: {top_share:.1%} of values are '{top_value}' (limit {limit:.0%})"
            )
        else:
            messages.append(f"{col}: most common value is {top_share:.1%} (limit {limit:.0%})")

    if ran == 0:
        return {"status": SKIP, "details": "; ".join(messages)}
    return {"status": FAIL if failed else PASS, "details": "; ".join(messages)}


# ── Bonus: Freshness ───────────────────────────────────────────────────────────

@register_check("freshness")
def check_freshness(df, cfg, ctx):
    conf = cfg.get("freshness")
    if not conf:
        return None

    col, max_age = conf["column"], conf.get("max_age_days", 30)
    if col not in df.columns:
        return {"status": SKIP, "details": f"column not found: {col}"}

    latest = _parse_dates(df[col]).max()
    if pd.isna(latest):
        return {"status": FAIL, "details": f"{col}: no valid dates found"}

    as_of = pd.Timestamp(conf["as_of"]) if conf.get("as_of") else pd.Timestamp.now()
    age = (as_of - latest).days
    return {
        "status": FAIL if age > max_age else PASS,
        "details": f"latest {col}: {latest.date()} ({age} days old, max allowed {max_age})",
    }


# ── Bonus: Outliers ────────────────────────────────────────────────────────────

@register_check("outliers")
def check_outliers(df, cfg, ctx):
    conf = cfg.get("outliers")
    if not conf:
        return None

    k = conf.get("std_threshold", 3)
    messages, ran, failed = [], 0, False
    for col in conf.get("columns", []):
        if col not in df.columns:
            messages.append(f"{col}: skipped (column not found)")
            continue
        values = pd.to_numeric(df[col], errors="coerce").dropna()
        std = values.std()
        if len(values) < 2 or not std or np.isnan(std):
            messages.append(f"{col}: skipped (no variance)")
            continue
        ran += 1
        count = int(((values - values.mean()).abs() > k * std).sum())
        if count:
            failed = True
        messages.append(f"{col}: {count} value(s) beyond {k} std dev")

    if ran == 0:
        return {"status": SKIP, "details": "; ".join(messages)}
    return {"status": FAIL if failed else PASS, "details": "; ".join(messages)}


# ── Orchestration ──────────────────────────────────────────────────────────────

def run_data_quality_checks(
    df: pd.DataFrame,
    dataset_name: str,
    config: Optional[dict] = None,
    reference_tables: Optional[dict] = None,
) -> dict:
    """
    Run every configured check on a DataFrame and return a structured report:

        {"dataset_name", "checks_run", "checks_passed", "checks_failed", "results": {...}}

    Checks that cannot run (missing columns / reference tables) are marked SKIP
    and are not counted in checks_run. Logs a WARNING for every FAIL.
    """
    logger.info("Running data quality checks on: %s", dataset_name)

    cfg = (config or DQ_CONFIG).get(dataset_name)
    if cfg is None:
        logger.warning("No DQ config found for dataset '%s'", dataset_name)
        return {
            "dataset_name": dataset_name,
            "checks_run": 0,
            "checks_passed": 0,
            "checks_failed": 0,
            "results": {},
        }

    ctx = {"dataset_name": dataset_name, "reference_tables": reference_tables or {}}
    results = {}

    for name, check_fn in CHECK_REGISTRY.items():
        try:
            result = check_fn(df, cfg, ctx)
        except Exception as exc:  # a broken rule must not stop the pipeline
            result = {"status": FAIL, "details": f"check raised {type(exc).__name__}: {exc}"}

        if result is None:
            continue

        results[name] = result
        if result["status"] == FAIL:
            logger.warning("%s | %s FAILED: %s", dataset_name, name, result.get("details"))

    executed = [r for r in results.values() if r["status"] in (PASS, FAIL)]
    passed = sum(1 for r in executed if r["status"] == PASS)

    return {
        "dataset_name": dataset_name,
        "checks_run": len(executed),
        "checks_passed": passed,
        "checks_failed": len(executed) - passed,
        "results": results,
    }


def run_all_checks(
    datasets: dict,
    config: Optional[dict] = None,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Run checks on several datasets at once. Every dataset is also available as a
    reference table to the others, so foreign keys are validated automatically.
    Writes dq_report_{dataset}.md per dataset when output_dir is given.
    """
    reports = {}
    for name, df in datasets.items():
        reports[name] = run_data_quality_checks(
            df, name, config=config, reference_tables=datasets
        )
        if output_dir:
            write_markdown_report(reports[name], output_dir)
    return reports


# ── Markdown report (bonus) ────────────────────────────────────────────────────

_ICONS = {PASS: "✅", FAIL: "❌", SKIP: "⏭️"}


def _format_details(details) -> str:
    if isinstance(details, dict):
        return "\n".join(f"- `{k}`: {v}" for k, v in details.items())
    if isinstance(details, list):
        return "\n".join(f"- {item}" for item in details)
    if isinstance(details, str) and "; " in details:
        return "\n".join(f"- {part}" for part in details.split("; "))
    return str(details)


def write_markdown_report(report: dict, output_dir: str) -> str:
    """Write outputs/dq_report_{dataset}.md and return its path."""
    os.makedirs(output_dir, exist_ok=True)
    name = report["dataset_name"]
    path = os.path.join(output_dir, f"dq_report_{name}.md")

    lines = [
        f"# Data Quality Report - {name}",
        "",
        f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}",
        "",
        "| Checks run | Passed | Failed |",
        "|---|---|---|",
        f"| {report['checks_run']} | {report['checks_passed']} | {report['checks_failed']} |",
        "",
        "## Summary",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for check, res in report["results"].items():
        lines.append(f"| {check} | {_ICONS[res['status']]} {res['status']} |")

    lines += ["", "## Details", ""]
    for check, res in report["results"].items():
        lines.append(f"### {_ICONS[res['status']]} {check} - {res['status']}")
        lines.append("")
        lines.append(_format_details(res.get("details", "")))
        if res.get("failed_columns"):
            lines += ["", f"**Failed columns:** {', '.join(res['failed_columns'])}"]
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("DQ markdown report written: %s", path)
    return path

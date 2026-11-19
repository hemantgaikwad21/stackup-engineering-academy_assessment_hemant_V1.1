"""
=============================================================
StackUp Engineering Academy - Data Engineering Assessment
Module: dq_config.py
Task 4.3 - Data quality rules and thresholds
=============================================================

ALL rules live here. To add a rule, edit this dict - no pipeline code changes.

Supported keys per dataset
--------------------------
completeness_threshold : float (0-1)   min share of non-null values per column
pk_columns             : list[str]     primary key column(s)
numeric_ranges         : {col: {"min": x, "max": y}}   either bound optional
date_columns           : list[str]     columns that must hold valid dates
non_future_dates       : list[str]     date columns that must not be in the future
consistency_rules      : list[dict]    types: "before", "non_negative", "salary_by_level"
foreign_keys           : {col: (ref_table, ref_col)}

Bonus checks (only run when the key is present)
-----------------------------------------------
distribution : {"max_same_value_pct": 0.30, "columns": [...]}
freshness    : {"column": "...", "max_age_days": 30, "as_of": "YYYY-MM-DD" (optional)}
outliers     : {"std_threshold": 3, "columns": [...]}

Any rule that references a column missing from the DataFrame is reported as
skipped (not failed), so adjust column names below to match your data.
"""

DQ_CONFIG = {
    "projects": {
        "completeness_threshold": 0.90,
        "pk_columns": ["project_id"],
        "numeric_ranges": {
            "budget": {"min": 0, "max": 10_000_000},
            "actual_cost": {"min": 0, "max": 10_000_000},
        },
        "date_columns": ["start_date", "end_date"],
        "non_future_dates": [],  # end_date may legitimately be in the future
        "consistency_rules": [
            {"type": "before", "columns": ["start_date", "end_date"]},
            {"type": "non_negative", "column": "actual_cost"},
        ],
        "foreign_keys": {
            "project_manager_id": ("employees", "employee_id"),
        },
        # Bonus
        "distribution": {"max_same_value_pct": 0.30, "columns": ["budget"]},
        "outliers": {"std_threshold": 3, "columns": ["budget", "actual_cost"]},
    },
    "employees": {
        "completeness_threshold": 0.85,
        "pk_columns": ["employee_id"],
        "numeric_ranges": {
            "salary": {"min": 10_000, "max": 100_000},
            "years_experience": {"min": 0, "max": 50},
        },
        "date_columns": ["hire_date"],
        "non_future_dates": ["hire_date"],
        "consistency_rules": [
            {"type": "non_negative", "column": "salary"},
            # TODO: set "level_column" and the level names/bands to match
            # employees.csv. Skipped automatically if the column is absent.
            {
                "type": "salary_by_level",
                "salary_column": "salary",
                "level_column": "job_level",
                "bands": {
                    "Junior": {"min": 10_000, "max": 40_000},
                    "Mid": {"min": 30_000, "max": 70_000},
                    "Senior": {"min": 50_000, "max": 100_000},
                },
            },
        ],
        "foreign_keys": {},
        # Bonus
        "distribution": {"max_same_value_pct": 0.30, "columns": ["salary"]},
        "outliers": {"std_threshold": 3, "columns": ["salary", "years_experience"]},
    },
    "transactions": {
        "completeness_threshold": 0.85,  # approved_by is legitimately null for some rows
        "pk_columns": ["transaction_id"],
        "numeric_ranges": {
            "amount_aed": {"min": 0, "max": 10_000_000},
        },
        "date_columns": ["transaction_date"],
        "non_future_dates": ["transaction_date"],
        "consistency_rules": [
            {"type": "non_negative", "column": "amount_aed"},
        ],
        "foreign_keys": {
            "project_id": ("projects", "project_id"),
            "approved_by": ("employees", "employee_id"),
        },
        # Bonus
        "distribution": {"max_same_value_pct": 0.30, "columns": ["amount_aed"]},
        "freshness": {"column": "transaction_date", "max_age_days": 30},
        "outliers": {"std_threshold": 3, "columns": ["amount_aed"]},
    },
}

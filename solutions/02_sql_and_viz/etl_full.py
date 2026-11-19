"""
=============================================================
StackUp Engineering Academy — Data Engineering Assessment
Starter File: etl_starter.py
Pillars: Foundations (Tasks 1.1, 1.3) | SQL & Viz (Task 2.2) | Infrastructure (Task 4.3)
=============================================================

SCENARIO
--------
You are a Data Engineer at Presight. The project management team has provided
three raw data extracts from their operational systems:
  - datasets/projects.csv        → project records
  - datasets/employees.csv       → employee/HR records
  - datasets/transactions.json   → financial transactions per project

Your job is to clean, transform, and load this data into a structured format
ready for analytics and reporting.

TASKS COVERED BY THIS FILE
---------------------------
  Task 1.1  → Clean and transform projects.csv and employees.csv using Pandas
  Task 1.3  → Identify and fix data quality issues in employees.csv
  Task 2.2  → Build a full ETL pipeline ingesting all three sources
  Task 4.3  → Implement a data quality check framework (min. 3 checks)

HOW TO RUN
----------
  python starter_files/etl_starter.py

OUTPUT
------
  Cleaned CSVs and a summary report written to: outputs/
"""

import pandas as pd
import json
import os
import logging
from datetime import datetime
import numpy as np


os.environ["HADOOP_HOME"] = r"C:\Users\hemant.gaikwad\hadoop"
os.environ["hadoop.home.dir"] = r"C:\Users\hemant.gaikwad\hadoop"
# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = r"C:\Users\hemant.gaikwad\OneDrive - Presight AI\Stackup\Final"

DATA_DIR = os.path.join(BASE_DIR, "datasets")

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==============================================================================
# TASK 1.1 — Load and transform projects.csv
# ==============================================================================
def load_projects(filepath: str) -> pd.DataFrame:
    """
    Load projects.csv into a DataFrame.

    TODO:
      - Load the CSV
      - Parse date columns correctly (start_date, end_date)
      - Add a derived column: budget_variance = actual_cost - budget
      - Add a derived column: is_over_budget (True/False)
      - Add a derived column: duration_days (end_date - start_date, where available)
      - Return the cleaned DataFrame
    """

    logger.info("Loading projects data...")

    df = pd.read_csv(
        filepath,
        parse_dates=["start_date", "end_date"]
    )

    df["budget_variance"] = (
        df["actual_cost"] - df["budget"]
    )

    df["is_over_budget"] = (
        df["actual_cost"] > df["budget"]
    )

    df["duration_days"] = (
        df["end_date"] - df["start_date"]
    ).dt.days

    logger.info(
        "Loaded %s project records",
        len(df)
    )

    return df


def transform_projects(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply business logic transformations to the projects DataFrame.

    TODO:
      - Standardise the 'status' column values (strip whitespace, title case)
      - Replace any missing budget or actual_cost values with 0
      - Add a 'status_category' column: group statuses into
        ['Active', 'Closed', 'Pending'] using the mapping below:
          Active  → In Progress
          Closed  → Completed
          Pending → Not Started, On Hold
      - Return the transformed DataFrame
    """
    logger.info("Transforming projects data...")

    # Status mapping
    status_map = {
        "In Progress": "Active",
        "Completed": "Closed",
        "Not Started": "Pending",
        "On Hold": "Pending"
    }

    # YOUR CODE HERE
# Replace null numeric values
    df["budget"] = df["budget"].fillna(0)
    df["actual_cost"] = df["actual_cost"].fillna(0)

    # Standardize status values
    df["status"] = (
        df["status"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    # Calculate budget utilization percentage
    df["budget_utilisation_pct"] = np.where(
        df["budget"] > 0,
        (df["actual_cost"] / df["budget"]) * 100,
        0
    )

    # Group statuses into business-friendly categories
    df["status_category"] = (
        df["status"]
        .map(status_map)
        .fillna("Pending")
    )

    # Standardize priority values
    df["priority"] = (
        df["priority"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    # Assign project risk level
    # High:
    #   - Critical priority
    #   - Over budget projects
    # Medium:
    #   - High priority projects
    #   - Budget utilization above 90%
    # Low:
    #   - Everything else
    df["risk_level"] = np.where(
        (df["priority"] == "Critical")
        | (df["is_over_budget"]),
        "High",
        np.where(
            (df["priority"] == "High")
            | (df["budget_utilisation_pct"] > 90),
            "Medium",
            "Low"
        )
    )

    logger.info("Project transformations completed")
    return df


# ==============================================================================
# TASK 1.3 — Data quality issues in employees.csv
# ==============================================================================

def load_employees(filepath: str) -> pd.DataFrame:
    """
    Load employees.csv and identify data quality issues.

    TODO:
      - Load the CSV
      - Log a summary: total rows, null counts per column
      - Return the raw DataFrame (do not fix issues here — fix in clean_employees)
    """
    logger.info("Loading employees data...")

    # YOUR CODE HERE
     # Load employee data
    df = pd.read_csv(filepath)
    
        # Log dataset size
    logger.info(
            "Total employee records: %s",
            len(df)
        )
    
        # Log null analysis
    logger.info(
            "Null counts per column:\n%s",
            df.isnull().sum()
        )
    
        # Log datatypes
    logger.info(
            "Column data types:\n%s",
            df.dtypes
        )

    return df


def clean_employees(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix at least THREE data quality issues found in employees.csv.

    Known issues to find and fix (there may be more — find them all):
      1. Missing values in key columns
      2. Invalid date values
      3. Implausible numeric values (salary, years_experience)
      4. Records that should not be active

    TODO:
      - Document each issue you find in a comment before fixing it
      - Apply your fixes
      - Log a summary of changes made (rows affected per issue)
      - Return the cleaned DataFrame

    HINT: Look carefully at every column. Some issues are subtle.
    """
    logger.info("Cleaning employees data...")

    # Issue 1: <describe what you found>
    # YOUR CODE HERE
# ------------------------------------------------------------------
    # Issue 1: Missing email addresses
    # ------------------------------------------------------------------

    missing_email_count = (
        df["email"].isna().sum()
    )

    df["email"] = df["email"].fillna(
        "unknown@presight.ai"
    )

    logger.info(
        "Missing email values fixed: %s",
        missing_email_count
    )

    # Issue 2: <describe what you found>
    # YOUR CODE HERE
      # ------------------------------------------------------------------
        # Issue 2: Invalid hire date values
        # Examples: -999, 99999-01-01
        # ------------------------------------------------------------------
    
    df["hire_date"] = pd.to_datetime(
            df["hire_date"],
            errors="coerce"
        )
    
    invalid_dates_count = (
            df["hire_date"].isna().sum()
        )
    
    logger.info(
            "Invalid hire dates found: %s",
            invalid_dates_count
        )

    # Issue 3: <describe what you found>
    # YOUR CODE HERE
    # ------------------------------------------------------------------
        # Issue 3: Negative years of experience
        # ------------------------------------------------------------------
    
    invalid_exp_count = (
            df["years_experience"] < 0
        ).sum()
    
    df.loc[
            df["years_experience"] < 0,
            "years_experience"
        ] = 0
    
    logger.info(
            "Negative years_experience records fixed: %s",
            invalid_exp_count
        )

    # Add more as needed...
 # ------------------------------------------------------------------
    # Issue 4: Standardize employee status values
    # ------------------------------------------------------------------

    df["status"] = (
        df["status"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    logger.info(
        "Status values standardized"
    )
     # ------------------------------------------------------------------
        # Generate DQ Summary Report
        # ------------------------------------------------------------------
    
    quality_summary = pd.DataFrame(
            {
                "issue": [
                    "missing_email",
                    "invalid_hire_date",
                    "negative_experience"
                ],
                "count": [
                    missing_email_count,
                    invalid_dates_count,
                    invalid_exp_count
                ]
            }
        )
    
    quality_summary.to_csv(
            os.path.join(
                OUTPUT_DIR,
                "quality_summary.csv"
            ),
            index=False
        )
    
    logger.info(
            "Quality summary created"
        )
    
    return df


# ==============================================================================
# TASK 2.2 — Full ETL pipeline
# ==============================================================================

def load_transactions(filepath: str) -> pd.DataFrame:
    """
    Load transactions.json into a DataFrame.

    TODO:
      - Load the JSON file
      - Flatten into a tabular structure
      - Parse transaction_date as a date type
      - Handle null values appropriately (document your decisions)
      - Return the DataFrame
    """
    logger.info("Loading transactions data...")

    # YOUR CODE HERE
    #df = None
     # Load JSON file
    with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    
        # Flatten JSON into DataFrame
    df = pd.json_normalize(data)
    
        # Convert transaction_date to datetime
    df["transaction_date"] = pd.to_datetime(
            df["transaction_date"],
            errors="coerce"
        )

    return df


def enrich_transactions(
    transactions: pd.DataFrame,
    projects: pd.DataFrame,
    employees: pd.DataFrame
) -> pd.DataFrame:
    """
    Enrich transactions with project and employee context.

    TODO:
      - Join project_name and department from projects onto transactions via project_id
      - Join approver full_name from employees onto transactions via approved_by = employee_id
      - Add a column: is_approved (True if approved_by is not null, else False)
      - Add a column: amount_aed — same as amount but cast to float, nulls → 0.0
      - Return the enriched DataFrame
    """
    logger.info("Enriching transactions...")

    # YOUR CODE HERE
     # ------------------------------------------------------------------
        # Join project details from projects dataset
        # ------------------------------------------------------------------
    
    transactions = transactions.merge(
            projects[
                [
                    "project_id",
                    "project_name",
                    "department"
                ]
            ],
            on="project_id",
            how="left"
        )
    
        # ------------------------------------------------------------------
        # Join approver details from employees dataset
        # ------------------------------------------------------------------
    
    transactions = transactions.merge(
            employees[
                [
                    "employee_id",
                    "full_name"
                ]
            ],
            left_on="approved_by",
            right_on="employee_id",
            how="left"
        )
    
    transactions = transactions.rename(
            columns={
                "full_name": "approver_name"
            }
        )
    
        # ------------------------------------------------------------------
        # Approval flag
        # ------------------------------------------------------------------
    
    transactions["is_approved"] = (
            transactions["approved_by"].notna()
        )
    
        # ------------------------------------------------------------------
        # Amount in AED
        # ------------------------------------------------------------------
    
    transactions["amount_aed"] = (
            pd.to_numeric(
                transactions["amount"],
                errors="coerce"
            )
            .fillna(0.0)
            .astype(float)
        )
# ------------------------------------------------------------------
# Transaction Year Month
# ------------------------------------------------------------------
    transactions["transaction_year_month"] = (
    transactions["transaction_date"].dt.strftime("%Y-%m")
)
    
    logger.info(
            "Transactions enriched successfully. Total rows: %s",
            len(transactions)
        )

    return transactions


def write_outputs(projects: pd.DataFrame, employees: pd.DataFrame, transactions: pd.DataFrame):
    """
    Write cleaned and enriched DataFrames to the outputs/ directory.

    TODO:
      - Write each DataFrame to a CSV in outputs/
      - Write a pipeline_summary.txt with:
          - Run timestamp
          - Row counts before and after cleaning per dataset
          - List of data quality issues found and fixed
    """
    logger.info("Writing outputs...")

    # YOUR CODE HERE
    # Write cleaned projects dataset
    projects.to_csv(
            os.path.join(
                OUTPUT_DIR,
                "projects_clean.csv"
            ),
            index=False
        )
    # Write enriched transactions dataset

    transactions.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "transactions_clean.csv"
        ),
        index=False
    )
        # Write cleaned employees dataset
    employees.to_csv(
            os.path.join(
                OUTPUT_DIR,
                "employees_clean.csv"
            ),
            index=False
        )
    
        # Create pipeline execution summary
    with open(
            os.path.join(
                OUTPUT_DIR,
                "pipeline_summary.txt"
            ),
            "w",
            encoding="utf-8"
        ) as f:
    
            f.write(
                f"Pipeline Run Timestamp: "
                f"{datetime.now()}\n\n"
            )
    
            f.write(
                f"Projects Rows: "
                f"{len(projects)}\n"
            )
    
            f.write(
                f"Employees Rows: "
                f"{len(employees)}\n\n"
            )
    
            f.write(
                "Data Quality Issues Fixed:\n"
            )
    
            f.write(
                "- Missing email addresses\n"
            )
    
            f.write(
                "- Invalid hire dates\n"
            )
    
            f.write(
                "- Negative years of experience\n"
            )
    
    logger.info(
            "Output files written successfully"
        )
    pass


# ==============================================================================
# TASK 4.3 — Data quality check framework
# ==============================================================================

def run_data_quality_checks(df: pd.DataFrame, dataset_name: str) -> dict:
    """
    Run a suite of data quality checks on a DataFrame.

    Implement AT LEAST the following checks:
      1. Completeness   — what % of values are non-null per column?
      2. Uniqueness     — are primary key columns unique?
      3. Validity       — do numeric columns fall within expected ranges?
      4. Consistency    — do date columns follow logical ordering (start < end)?
      5. Referential integrity — do foreign keys exist in the referenced table?
                                 (implement this in the pipeline function below)

    TODO:
      - Run each check
      - Return a dict with check name → result (pass/fail + details)
      - Log a warning for any failed check
    """
    logger.info(f"Running data quality checks on: {dataset_name}")

    results = {}

    # Check 1: Completeness
    # YOUR CODE HERE
      # --------------------------------------------------------------
        # Check 1 : Completeness
        # --------------------------------------------------------------
        
    completeness = (
            (1 - df.isnull().mean()) * 100
        ).round(2)
    
    results["completeness"] = completeness.to_dict()

    # Check 2: Uniqueness
    # YOUR CODE HERE
    if "employee_id" in df.columns:
    
            results["uniqueness"] = {
                "employee_id_unique":
                df["employee_id"].is_unique
            }
    
    elif "project_id" in df.columns:
    
            results["uniqueness"] = {
                "project_id_unique":
                df["project_id"].is_unique
            }
    
    elif "transaction_id" in df.columns:
    
            results["uniqueness"] = {
                "transaction_id_unique":
                df["transaction_id"].is_unique
            }
    
    else:
    
            results["uniqueness"] = {
                "status": "Not Applicable"
            }

    # Check 3: Validity
    # YOUR CODE HERE
    numeric_issues = {}

    numeric_columns = df.select_dtypes(
        include=["number"]
    ).columns

    for col in numeric_columns:

        invalid_count = (df[col] < 0).sum()

        numeric_issues[col] = int(invalid_count)

    results["validity"] = numeric_issues


    # Check 4: Consistency
    # YOUR CODE HERE
# --------------------------------------------------------------
# Check 4 : Consistency
# Check if start_date occurs before end_date
# --------------------------------------------------------------

    if (
        "start_date" in df.columns and
        "end_date" in df.columns
    ):

        invalid_date_order = (
            (
                df["start_date"].notna()
            )
            &
            (
                df["end_date"].notna()
            )
            &
            (
                df["start_date"] >
                df["end_date"]
            )
        ).sum()

        results["consistency"] = {
            "invalid_date_order": int(invalid_date_order),
            "pass": invalid_date_order == 0
        }

        if invalid_date_order > 0:
            logger.warning(
                "%s consistency check failed. Invalid date pairs found: %s",
                dataset_name,
                invalid_date_order
            )

    else:
    
        results["consistency"] = {
            "status": "Not Applicable"
        }

    return results


# ==============================================================================
# PIPELINE ENTRY POINT
# ==============================================================================

def run_pipeline():
    """
    Orchestrates the full ETL pipeline end to end.
    Call each function in the correct order.
    """
    logger.info("=" * 60)
    logger.info("Starting ETL pipeline")
    logger.info("=" * 60)

    # Step 1: Load raw data
    raw_projects      = load_projects(os.path.join(DATA_DIR, "projects.csv"))
    raw_employees     = load_employees(os.path.join(DATA_DIR, "employees.csv"))
    raw_transactions  = load_transactions(os.path.join(DATA_DIR, "transactions.json"))

    # Step 2: Clean
    clean_projects    = transform_projects(raw_projects)
    clean_emp         = clean_employees(raw_employees)

    # Step 3: Enrich
    enriched_txn      = enrich_transactions(raw_transactions, clean_projects, clean_emp)

    # Step 4: Data quality checks
    dq_projects       = run_data_quality_checks(clean_projects, "projects")
    dq_employees      = run_data_quality_checks(clean_emp, "employees")
    dq_transactions   = run_data_quality_checks(enriched_txn, "transactions")

    logger.info("DQ Results — Projects:     %s", dq_projects)
    logger.info("DQ Results — Employees:    %s", dq_employees)
    logger.info("DQ Results — Transactions: %s", dq_transactions)

    # Step 5: Write outputs
    write_outputs(clean_projects, clean_emp, enriched_txn)

    logger.info("Pipeline complete. Outputs written to: %s", OUTPUT_DIR)


if __name__ == "__main__":
    run_pipeline()

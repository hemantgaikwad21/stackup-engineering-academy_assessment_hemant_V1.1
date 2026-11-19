import pandas as pd
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_DIR = os.getenv(
    "DATA_DIR",
    os.path.join(BASE_DIR, "datasets")
)

OUTPUT_DIR = os.getenv(
    "OUTPUT_DIR",
    os.path.join(
        BASE_DIR,
        "outputs",
        "results",
        "Hemant_Gaikwad",
        "01_foundations"
    )
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_projects(filepath):
    logger.info("Loading projects dataset")
    df = pd.read_csv(filepath)
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    df["budget"] = pd.to_numeric(df["budget"], errors="coerce")
    df["actual_cost"] = pd.to_numeric(df["actual_cost"], errors="coerce")
    df["budget_variance"] = df["actual_cost"] - df["budget"]
    df["is_over_budget"] = df["actual_cost"] > df["budget"]
    df["duration_days"] = (df["end_date"] - df["start_date"]).dt.days
    return df

def transform_projects(df):
    df["status"] = df["status"].astype(str).str.strip().str.title()
    df["budget"] = df["budget"].fillna(0)
    df["actual_cost"] = df["actual_cost"].fillna(0)
    status_map = {
        "In Progress": "Active",
        "Completed": "Closed",
        "Not Started": "Pending",
        "On Hold": "Pending"
    }
    df["status_category"] = df["status"].map(status_map)
    df["budget_utilisation_pct"] = ((df["actual_cost"] / df["budget"].replace(0, pd.NA)) * 100).fillna(0)

    def calculate_risk(row):
        if row["is_over_budget"]:
            return "High"
        if row["status"] == "On Hold":
            return "Medium"
        return "Low"

    df["risk_level"] = df.apply(calculate_risk, axis=1)
    return df

def load_employees(filepath):
    df = pd.read_csv(filepath)
    logger.info(f"Total rows: {len(df)}")
    logger.info("%s", df.isnull().sum())
    return df

def clean_employees(df):
    dq_summary = []

    invalid_dates = ["-999", "99999-01-01"]
    invalid_date_count = df["hire_date"].astype(str).isin(invalid_dates).sum()
    df.loc[df["hire_date"].astype(str).isin(invalid_dates), "hire_date"] = pd.NaT
    dq_summary.append(["invalid_hire_date", invalid_date_count])

    missing_email_count = df["email"].isna().sum()
    df["email"] = df["email"].fillna("missing@email.com")
    dq_summary.append(["missing_email", missing_email_count])

    negative_experience_count = (df["years_experience"] < 0).sum()
    df.loc[df["years_experience"] < 0, "years_experience"] = None
    dq_summary.append(["negative_experience", negative_experience_count])

    duplicate_count = df["employee_id"].duplicated().sum()
    dq_summary.append(["duplicate_employee_id", duplicate_count])

    pd.DataFrame(dq_summary, columns=["issue", "count"]).to_csv(
        os.path.join(OUTPUT_DIR, "quality_summary.csv"), index=False
    )
    return df

DQ_CONFIG = {
    "projects": {
        "completeness_threshold": 90,
        "pk_columns": ["project_id"],
        "numeric_ranges": {
            "budget": {"min": 0, "max": 10000000},
            "actual_cost": {"min": 0, "max": 10000000}
        }
    },
    "employees": {
        "completeness_threshold": 85,
        "pk_columns": ["employee_id"],
        "numeric_ranges": {
            "salary": {"min": 10000, "max": 100000},
            "years_experience": {"min": 0, "max": 50}
        }
    },
    "transactions": {
        "completeness_threshold": 90,
        "pk_columns": ["transaction_id"],
        "numeric_ranges": {
            "amount": {"min": 0, "max": 1000000}
        }
    }
}
def run_data_quality_checks(df, dataset_name):

    config = DQ_CONFIG.get(dataset_name, {})

    results = {}

    checks_run = 0
    checks_passed = 0
    checks_failed = 0

    # --------------------------------------------------
    # Completeness Check
    # --------------------------------------------------

    completeness = (
        (1 - df.isnull().mean()) * 100
    ).round(2).to_dict()

    threshold = config.get(
        "completeness_threshold",
        90
    )

    failed_columns = [
        col
        for col, pct in completeness.items()
        if pct < threshold
    ]

    completeness_status = (
        "PASS"
        if len(failed_columns) == 0
        else "FAIL"
    )

    results["completeness"] = {
        "status": completeness_status,
        "details": completeness,
        "failed_columns": failed_columns
    }

    checks_run += 1

    if completeness_status == "PASS":
        checks_passed += 1
    else:
        checks_failed += 1
        logger.warning(
            "%s completeness check failed",
            dataset_name
        )

    # --------------------------------------------------
    # Uniqueness Check
    # --------------------------------------------------

    pk_columns = config.get("pk_columns", [])

    uniqueness_status = "PASS"

    for col in pk_columns:
        duplicate_count = df[col].duplicated().sum()

        if duplicate_count > 0:
            uniqueness_status = "FAIL"

    results["uniqueness"] = {
        "status": uniqueness_status
    }

    checks_run += 1

    if uniqueness_status == "PASS":
        checks_passed += 1
    else:
        checks_failed += 1
        logger.warning(
            "%s uniqueness check failed",
            dataset_name
        )

    # --------------------------------------------------
    # Numeric Validity Check
    # --------------------------------------------------

    numeric_status = "PASS"

    for col, limits in config.get(
        "numeric_ranges",
        {}
    ).items():

        invalid_rows = df[
            (df[col] < limits["min"])
            | (df[col] > limits["max"])
        ]

        if len(invalid_rows) > 0:
            numeric_status = "FAIL"

    results["validity_numeric"] = {
        "status": numeric_status
    }

    checks_run += 1

    if numeric_status == "PASS":
        checks_passed += 1
    else:
        checks_failed += 1
        logger.warning(
            "%s numeric validity failed",
            dataset_name
        )

    # --------------------------------------------------
    # Date Validity
    # --------------------------------------------------

    date_status = "PASS"

    for col in df.columns:

        if "date" in col.lower():

            try:
                parsed = pd.to_datetime(
                    df[col],
                    errors="coerce"
                )

                if parsed.isnull().sum() > 0:
                    date_status = "FAIL"

            except Exception:
                date_status = "FAIL"

    results["validity_date"] = {
        "status": date_status
    }

    checks_run += 1

    if date_status == "PASS":
        checks_passed += 1
    else:
        checks_failed += 1
        logger.warning(
            "%s date validity failed",
            dataset_name
        )

    # --------------------------------------------------
    # Consistency Check
    # --------------------------------------------------

    consistency_status = "PASS"

    if (
        dataset_name == "projects"
        and "start_date" in df.columns
        and "end_date" in df.columns
    ):

        invalid = (
            pd.to_datetime(df["start_date"])
            >
            pd.to_datetime(df["end_date"])
        ).sum()

        if invalid > 0:
            consistency_status = "FAIL"

    results["consistency"] = {
        "status": consistency_status
    }

    checks_run += 1

    if consistency_status == "PASS":
        checks_passed += 1
    else:
        checks_failed += 1
        logger.warning(
            "%s consistency failed",
            dataset_name
        )

    # --------------------------------------------------
    # Referential Integrity Placeholder
    # --------------------------------------------------

    referential_status = "PASS"

    results["referential_integrity"] = {
        "status": referential_status
    }

    checks_run += 1
    checks_passed += 1

    return {
        "dataset_name": dataset_name,
        "checks_run": checks_run,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "results": results
    }

def write_outputs(projects, employees):
    projects.to_csv(os.path.join(OUTPUT_DIR, "projects_clean.csv"), index=False)
    employees.to_csv(os.path.join(OUTPUT_DIR, "employees_clean.csv"), index=False)
if __name__ == "__main__":

    projects = transform_projects(
        load_projects(
            os.path.join(DATA_DIR, "projects.csv")
        )
    )

    employees = clean_employees(
        load_employees(
            os.path.join(DATA_DIR, "employees.csv")
        )
    )

    projects_dq = run_data_quality_checks(
        projects,
        "projects"
    )

    employees_dq = run_data_quality_checks(
        employees,
        "employees"
    )

    logger.info(projects_dq)

    logger.info(employees_dq)
    for result in [projects_dq, employees_dq]:

      report_path = os.path.join(
        OUTPUT_DIR,
        f"dq_report_{result['dataset_name']}.md"
    )
      with open(report_path, "w", encoding="utf-8") as f:

        f.write(
            f"# DQ Report - {result['dataset_name']}\n\n"
        )

        f.write(
            f"Checks Run: {result['checks_run']}\n\n"
        )

        f.write(
            f"Checks Passed: {result['checks_passed']}\n\n"
        )

        f.write(
            f"Checks Failed: {result['checks_failed']}\n\n"
        )

        f.write(
            "## Results\n\n"
        )

        f.write(
            str(result["results"])
        )
        
    write_outputs(
        projects,
        employees
    )
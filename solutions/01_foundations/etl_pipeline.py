import pandas as pd
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(BASE_DIR, "datasets")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "results", "Hemant_Gaikwad", "01_foundations")
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

def run_data_quality_checks(df, dataset_name):
    results = {}
    results["completeness"] = (((1 - df.isnull().mean()) * 100).round(2)).to_dict()
    return results

def write_outputs(projects, employees):
    projects.to_csv(os.path.join(OUTPUT_DIR, "projects_clean.csv"), index=False)
    employees.to_csv(os.path.join(OUTPUT_DIR, "employees_clean.csv"), index=False)

if __name__ == "__main__":
    projects = transform_projects(load_projects(os.path.join(DATA_DIR, "projects.csv")))
    employees = clean_employees(load_employees(os.path.join(DATA_DIR, "employees.csv")))
    write_outputs(projects, employees)

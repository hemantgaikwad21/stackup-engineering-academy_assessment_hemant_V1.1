"""
=============================================================
StackUp Engineering Academy — Data Engineering Assessment
Starter File: airflow_dag_starter.py
Pillar: Big Data Processing — Task 3.3
=============================================================

SCENARIO
--------
The ETL pipeline you built in Task 2.2 currently runs manually.
The data team needs it scheduled to run automatically every day at 6:00 AM UAE time,
with proper dependency management, retries, and alerting.

You will build an Airflow DAG that orchestrates the full pipeline
including data quality gate — if DQ checks fail, downstream tasks must not run.

DAG STRUCTURE REQUIRED
-----------------------
  start
    │
    ├── extract_projects
    ├── extract_employees
    └── extract_transactions
          │
          ▼
      validate_data_quality  ← DQ gate: fails DAG if checks don't pass
          │
          ▼
      transform_and_enrich
          │
          ▼
      load_to_output
          │
          ▼
      generate_pipeline_report
          │
          ▼
        end

TASKS
-----
  Task 3.3a → Define the DAG with correct schedule and timezone
  Task 3.3b → Implement each task as a PythonOperator
  Task 3.3c → Wire up task dependencies correctly
  Task 3.3d → Add retry logic and failure alerting (email or log)
  Task 3.3e → Use XCom to pass row counts between tasks for the final report

HOW TO RUN
----------
  Ensure Airflow is running (docker-compose up -d)
  Copy this file to your Airflow dags/ folder, or mount via docker-compose.
  The DAG will appear in the Airflow UI as: presight_etl_pipeline

  Trigger manually for testing:
    airflow dags trigger presight_etl_pipeline
"""

from datetime import datetime, timedelta
import os
import logging

# TODO: ensure apache-airflow is installed
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago

# Import your ETL functions from the etl_starter
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from starter_files.etl_starter import (
    load_projects, load_employees, load_transactions,
    transform_projects, clean_employees, enrich_transactions,
    run_data_quality_checks, write_outputs
)

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "datasets")

# ==============================================================================
# TASK 3.3a — DAG default arguments
# ==============================================================================

# TODO: Fill in the default_args dict
# Requirements:
#   - owner: your name
#   - start_date: January 1 2025
#   - retries: 2
#   - retry_delay: 5 minutes
#   - email_on_failure: False (set True and add your email for bonus marks)
#   - depends_on_past: False

default_args = {
    "owner": "Hemant Gaikwad",
    "start_date": datetime(2025, 1, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "depends_on_past": False
}


# ==============================================================================
# TASK 3.3b — Task functions
# ==============================================================================

def task_extract_projects(**context):
    """
    Extract projects data and push row count to XCom.

    TODO:
      - Call load_projects()
      - Push the row count to XCom with key 'projects_raw_count'
      - Return a status message
    """
    ti = context["ti"]

    projects_df = load_projects()

    ti.xcom_push(
    key="projects_raw_count",
    value=len(projects_df)
)

    return f"Loaded {len(projects_df)} project records"


def task_extract_employees(**context):
    """
    Extract employees data and push row count to XCom.

    TODO:
      - Call load_employees()
      - Push the row count to XCom with key 'employees_raw_count'
    """
    ti = context["ti"]

    employees_df = load_employees()

    ti.xcom_push(
    key="employees_raw_count",
    value=len(employees_df)
)

    return f"Loaded {len(employees_df)} employee records"


def task_extract_transactions(**context):
    """
    Extract transactions data and push row count to XCom.

    TODO:
      - Call load_transactions()
      - Push the row count to XCom with key 'transactions_raw_count'
    """
    ti = context["ti"]

    transactions_df = load_transactions()

    ti.xcom_push(
    key="transactions_raw_count",
    value=len(transactions_df)
)

    return f"Loaded {len(transactions_df)} transaction records"


def task_validate_data_quality(**context):
    """
    Run data quality checks across all three datasets.
    This is the DQ GATE — raise an exception if any critical check fails.

    TODO:
      - Reload all three datasets
      - Run run_data_quality_checks() on each
      - Define what counts as a critical failure (e.g., completeness < 80%)
      - Raise ValueError with a descriptive message if critical checks fail
      - Push the DQ results dict to XCom with key 'dq_results'
      - If all checks pass, log a summary
    """
    ti = context["ti"]

    projects_df = load_projects()
    employees_df = load_employees()
    transactions_df = load_transactions()

    projects_dq = run_data_quality_checks(projects_df)
    employees_dq = run_data_quality_checks(employees_df)
    transactions_dq = run_data_quality_checks(transactions_df)

    dq_results = {
        "projects": projects_dq,
        "employees": employees_dq,
        "transactions": transactions_dq
    }

    for dataset, result in dq_results.items():

        completeness = result.get("completeness", 100)

        if completeness < 80:
            raise ValueError(
                f"Critical DQ failure in {dataset}: completeness={completeness}%"
            )

    ti.xcom_push(
        key="dq_results",
        value=dq_results
    )

    logger.info("All DQ checks passed")

    return dq_results


def task_transform_and_enrich(**context):
    """
    Apply transformations and enrichment.

    TODO:
      - Call transform_projects(), clean_employees(), enrich_transactions()
      - Push cleaned row counts to XCom:
          'projects_clean_count', 'employees_clean_count', 'transactions_clean_count'
    """
    ti = context["ti"]

    projects_df = load_projects()
    employees_df = load_employees()
    transactions_df = load_transactions()

    projects_clean = transform_projects(projects_df)
    employees_clean = clean_employees(employees_df)
    transactions_clean = enrich_transactions(transactions_df)

    ti.xcom_push(
        key="projects_clean_count",
        value=len(projects_clean)
    )

    ti.xcom_push(
        key="employees_clean_count",
        value=len(employees_clean)
    )

    ti.xcom_push(
        key="transactions_clean_count",
        value=len(transactions_clean)
    )

    return "Transformations completed"


def task_load_to_output(**context):
    """
    Write final cleaned data to outputs/.

    TODO:
      - Call write_outputs() with the cleaned DataFrames
      - Log file paths written
    """
    projects_df = transform_projects(load_projects())
    employees_df = clean_employees(load_employees())
    transactions_df = enrich_transactions(load_transactions())

    write_outputs(
        projects_df,
        employees_df,
        transactions_df
    )

    logger.info("Output files written successfully")

    return "Outputs written"


def task_generate_pipeline_report(**context):
    """
    Generate a pipeline run report using XCom values from upstream tasks.

    TODO:
      - Pull all XCom values pushed by upstream tasks
      - Write a report to outputs/pipeline_report_{execution_date}.txt containing:
          - DAG run date and execution time
          - Raw vs clean row counts per dataset
          - DQ check results summary
          - Files written
    """
    ti = context["ti"]
    execution_date = context["execution_date"]

    projects_raw = ti.xcom_pull(
    task_ids="extract_projects",
    key="projects_raw_count"
)

    employees_raw = ti.xcom_pull(
        task_ids="extract_employees",
        key="employees_raw_count"
    )

    transactions_raw = ti.xcom_pull(
        task_ids="extract_transactions",
        key="transactions_raw_count"
    )

    projects_clean = ti.xcom_pull(
        task_ids="transform_and_enrich",
        key="projects_clean_count"
    )

    employees_clean = ti.xcom_pull(
        task_ids="transform_and_enrich",
        key="employees_clean_count"
    )

    transactions_clean = ti.xcom_pull(
        task_ids="transform_and_enrich",
        key="transactions_clean_count"
    )

    dq_results = ti.xcom_pull(
        task_ids="validate_data_quality",
        key="dq_results"
    )

    report_path = os.path.join(BASE_DIR, "outputs", f"pipeline_report_{execution_date.date()}.txt")
    # YOUR CODE HERE — write the report
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:

        f.write(
            f"Pipeline Report\n"
            f"===============\n\n"
            f"Execution Date: {execution_date}\n\n"
            f"Projects: {projects_raw} -> {projects_clean}\n"
            f"Employees: {employees_raw} -> {employees_clean}\n"
            f"Transactions: {transactions_raw} -> {transactions_clean}\n\n"
            f"DQ Results:\n"
            f"{dq_results}\n"
        )

    logger.info("Pipeline report written: %s", report_path)

    return report_path


# ==============================================================================
# TASK 3.3a — DAG definition
# ==============================================================================

# TODO: Define the DAG
# Requirements:
#   - dag_id: 'presight_etl_pipeline'
#   - schedule: daily at 06:00 UAE time (Asia/Dubai = UTC+4, so 02:00 UTC)
#   - catchup: False
#   - tags: ['presight', 'etl', 'assessment']
#   - max_active_runs: 1

with DAG(
    dag_id="presight_etl_pipeline",
    default_args=default_args,
    description="Daily ETL pipeline for Presight project management data",
    schedule_interval="0 2 * * *",      # TODO: replace with correct cron expression
    catchup=False,
    tags=["presight", "etl", "assessment"],
    max_active_runs=1,
) as dag:

    # ── Boundary tasks ─────────────────────────────────────────────────────────
    start = EmptyOperator(task_id="start")
    end   = EmptyOperator(task_id="end")

    # ── Extraction tasks ───────────────────────────────────────────────────────
    # TODO: Define PythonOperator for each extract task
    extract_projects = PythonOperator(
    task_id="extract_projects",
    python_callable=task_extract_projects
    )

    extract_employees = PythonOperator(
    task_id="extract_employees",
    python_callable=task_extract_employees
)
    extract_transactions = PythonOperator(
    task_id="extract_transactions",
    python_callable=task_extract_transactions
)

    # ── DQ gate ────────────────────────────────────────────────────────────────
    validate_dq = PythonOperator(
    task_id="validate_data_quality",
    python_callable=task_validate_data_quality
)

    # ── Transform & load ───────────────────────────────────────────────────────
    transform_enrich = PythonOperator(
    task_id="transform_and_enrich",
    python_callable=task_transform_and_enrich
)
    load_output = PythonOperator(
    task_id="load_to_output",
    python_callable=task_load_to_output
)
    pipeline_report = PythonOperator(
    task_id="generate_pipeline_report",
    python_callable=task_generate_pipeline_report
)

    # ===========================================================================
    # TASK 3.3c — Wire up dependencies
    # ===========================================================================
    # TODO: Set the dependency chain as per the architecture diagram at the top.
    # Extraction tasks run in parallel, then DQ gate, then transform → load → report.
    #
    # YOUR CODE HERE
    start >> [
    extract_projects,
    extract_employees,
    extract_transactions
    ]
    
    [
        extract_projects,
        extract_employees,
        extract_transactions
    ] >> validate_dq
    
    validate_dq >> transform_enrich
    transform_enrich >> load_output
    load_output >> pipeline_report
    pipeline_report >> end

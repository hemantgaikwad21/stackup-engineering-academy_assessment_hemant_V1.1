-- =============================================================
-- StackUp Engineering Academy — Data Engineering Assessment
-- Starter File: data_model_starter.sql
-- Pillars: Foundations (Task 1.2) | SQL & Viz (Tasks 2.1, 2.3)
-- =============================================================
--
-- SCENARIO
-- --------
-- Presight runs a project management platform. You are designing
-- the data warehouse layer that will power analytics dashboards
-- for Finance, Operations, and Executive leadership.
--
-- The source data comes from three operational tables:
--   projects      → datasets/projects.csv
--   employees     → datasets/employees.csv
--   transactions  → datasets/transactions.json
--
-- HOW TO USE
-- ----------
-- This file is divided into four sections.
-- Work through each section in order.
-- Run against your local database (SQLite, PostgreSQL, or DuckDB all work).
-- =============================================================


-- ===========================================================================
-- SECTION 1 — TASK 1.2: Design the data model (Star Schema)
-- ===========================================================================
--
-- Design a star schema for the Presight project analytics warehouse.
--
-- REQUIREMENTS:
--   - One central fact table: fact_transactions
--   - At minimum four dimension tables:
--       dim_project, dim_employee, dim_vendor, dim_date
--   - fact_transactions must include foreign keys to all four dimensions
--   - dim_date must be a proper date dimension (not just a date column)
--     with columns for year, quarter, month, month_name, week, day, is_weekend
--   - Use surrogate keys (integer PKs) on all dimension tables
--   - Preserve the original source system IDs as natural keys
--   - Add a dim_employee_project bridge table to handle the many-to-many
--     relationship between employees and projects (one employee can manage
--     multiple projects; one project can have multiple team members)
--
-- BONUS:
--   - Add a slowly-changing dimension (SCD Type 2) design to dim_employee
--     to track salary changes over time
--
-- DOCUMENT YOUR DECISIONS:
--   Write a comment before each table explaining why you designed it that way.

-- ============================================================================
-- SECTION 1 — TASK 1.2: Design the data model (Star Schema)
-- ============================================================================

-- ============================================================================
-- DIM_DATE
-- ============================================================================
-- Date dimension supports time-series reporting and avoids repeatedly
-- extracting date parts from transaction dates.

CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    week INTEGER,
    day INTEGER,
    day_of_week VARCHAR(20),
    is_weekend BOOLEAN
);

-- ============================================================================
-- DIM_PROJECT
-- ============================================================================
-- Project dimension stores project descriptive attributes.
-- project_id is retained as the source system natural key.

CREATE TABLE dim_project (

    project_key INTEGER PRIMARY KEY,

    project_id VARCHAR(20) UNIQUE,

    project_name VARCHAR(255),

    department VARCHAR(100),

    status VARCHAR(50),

    priority VARCHAR(50),

    region VARCHAR(50),

    budget DECIMAL(18,2),

    actual_cost DECIMAL(18,2)

);

-- ============================================================================
-- DIM_EMPLOYEE (SCD TYPE 2)
-- ============================================================================
-- Employee dimension tracks salary, role and level changes over time.
-- Each version of an employee record receives a new surrogate key.

CREATE TABLE dim_employee (

    employee_key INTEGER PRIMARY KEY,

    employee_id VARCHAR(20),

    full_name VARCHAR(255),

    email VARCHAR(255),

    department VARCHAR(100),

    role_name VARCHAR(100),

    employee_level VARCHAR(50),

    salary DECIMAL(18,2),

    valid_from DATE,

    valid_to DATE,

    is_current BOOLEAN,

    change_reason VARCHAR(255)

);

-- ============================================================================
-- DIM_VENDOR
-- ============================================================================
-- Vendor dimension stores supplier information sourced from transactions.

CREATE TABLE dim_vendor (

    vendor_key INTEGER PRIMARY KEY,

    vendor_id VARCHAR(20),

    vendor_name VARCHAR(255)

);

-- ============================================================================
-- BRIDGE_EMPLOYEE_PROJECT
-- ============================================================================
-- Resolves the many-to-many relationship between employees and projects.

CREATE TABLE bridge_employee_project (

    employee_key INTEGER,

    project_key INTEGER,

    PRIMARY KEY (
        employee_key,
        project_key
    ),

    FOREIGN KEY (employee_key)
        REFERENCES dim_employee(employee_key),

    FOREIGN KEY (project_key)
        REFERENCES dim_project(project_key)

);


-- ============================================================================
-- FACT_TRANSACTIONS
-- ============================================================================
-- Central fact table containing financial transactions.
-- Stores measurable business events and links to all analytical dimensions.
-- Grain: One row per transaction.

CREATE TABLE fact_transactions (

    transaction_key INTEGER PRIMARY KEY,

    -- Natural key from source system
    transaction_id VARCHAR(50),

    -- Foreign Keys
    project_key INTEGER,
    employee_key INTEGER,
    vendor_key INTEGER,
    date_key INTEGER,

    -- Measures
    amount DECIMAL(18,2),

    -- Transaction attributes
    category VARCHAR(100),
    payment_status VARCHAR(50),

    FOREIGN KEY (project_key) REFERENCES dim_project(project_key),

    FOREIGN KEY (employee_key) REFERENCES dim_employee(employee_key),

    FOREIGN KEY (vendor_key) REFERENCES dim_vendor(vendor_key),

    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)

);


-- ===========================================================================
-- SECTION 2 — Load staging data
-- ===========================================================================
--
-- Before answering the business questions, load your cleaned data
-- (output of etl_starter.py) into the tables above.
--
-- If using SQLite: use .import or INSERT statements
-- If using DuckDB: use read_csv_auto() or read_json_auto()
-- If using PostgreSQL: use COPY or \copy

-- Example (DuckDB):
-- INSERT INTO dim_project SELECT * FROM read_csv_auto('outputs/projects_clean.csv');

-- TODO: Load your data here
-- YOUR CODE HERE
-- ============================================================
-- 1. Load Project Dimension
-- ============================================================

INSERT INTO dim_project
SELECT
    ROW_NUMBER() OVER() AS project_key,
    project_id,
    project_name,
    department,
    status,
    priority,
    region,
    budget,
    actual_cost
FROM read_csv_auto(
'C:/Users/hemant.gaikwad/OneDrive - Presight AI/Stackup/Final/outputs/projects_clean.csv'
);

-- ============================================================
-- 2. Load Vendor Dimension
-- ============================================================
INSERT INTO dim_vendor
SELECT
    ROW_NUMBER() OVER (
        ORDER BY vendor_id
    ) AS vendor_key,
    vendor_id,
    vendor_name
FROM (

    SELECT DISTINCT
        vendor_id,
        vendor_name
    FROM read_csv_auto(
        'C:/Users/hemant.gaikwad/OneDrive - Presight AI/Stackup/Final/outputs/transactions_clean.csv'
    )

) v;

-- ============================================================
-- 3. Load Date Dimension
-- ============================================================

INSERT INTO dim_date
SELECT
    ROW_NUMBER() OVER() AS date_key,
    full_date,
    YEAR(full_date)      AS year,
    QUARTER(full_date)   AS quarter,
    MONTH(full_date)     AS month,
    MONTHNAME(full_date) AS month_name,
    WEEK(full_date)      AS week,
    DAY(full_date)       AS day,
    DAYNAME(full_date)   AS day_of_week,
    CASE
        WHEN DAYOFWEEK(full_date) IN (0,6)
        THEN TRUE
        ELSE FALSE
    END AS is_weekend
FROM (
    SELECT
        CAST(generate_series AS DATE) AS full_date
    FROM generate_series(
        DATE '1900-01-01',
        DATE '2200-12-31',
        INTERVAL 1 DAY
    )
);

-- ============================================================
-- 4. Load Employee History (SCD Type 2)
-- ============================================================

INSERT INTO dim_employee
SELECT
    ROW_NUMBER() OVER(
        ORDER BY h.employee_id, h.effective_date
    ) AS employee_key,

    h.employee_id,

    e.full_name,
    e.email,
    e.department,

    h.new_role      AS role_name,
    h.new_level     AS employee_level,
    h.new_salary    AS salary,

    h.effective_date AS valid_from,

    COALESCE(
        LEAD(h.effective_date)
        OVER (
            PARTITION BY h.employee_id
            ORDER BY h.effective_date
        ) - INTERVAL 1 DAY,
        DATE '9999-12-31'
    ) AS valid_to,

    FALSE AS is_current,

    h.change_reason

FROM read_csv_auto(
'C:/Users/hemant.gaikwad/OneDrive - Presight AI/Stackup/Final/datasets/employees_salary_history.csv'
) h

LEFT JOIN read_csv_auto(
'C:/Users/hemant.gaikwad/OneDrive - Presight AI/Stackup/Final/outputs/employees_clean.csv'
) e
ON h.employee_id = e.employee_id;

-- ============================================================
-- 5. Mark Latest Employee Version as Current
-- ============================================================

UPDATE dim_employee
SET
    is_current = TRUE,
    valid_to = DATE '9999-12-31'
WHERE employee_key IN (

    SELECT employee_key
    FROM (
        SELECT
            employee_key,
            ROW_NUMBER() OVER(
                PARTITION BY employee_id
                ORDER BY valid_from DESC
            ) rn
        FROM dim_employee
    ) x
    WHERE rn = 1
);

-- ============================================================
-- 6. Load Employees Without History
-- ============================================================

INSERT INTO dim_employee
SELECT
    (
        SELECT COALESCE(MAX(employee_key),0)
        FROM dim_employee
    )
    + ROW_NUMBER() OVER() AS employee_key,

    e.employee_id,
    e.full_name,
    e.email,
    e.department,

    e.role  AS role_name,
    e.level AS employee_level,

    e.salary,

    e.hire_date AS valid_from,

    DATE '9999-12-31' AS valid_to,

    TRUE AS is_current,

    'No Historical Changes' AS change_reason

FROM read_csv_auto(
'C:/Users/hemant.gaikwad/OneDrive - Presight AI/Stackup/Final/outputs/employees_clean.csv'
) e

WHERE NOT EXISTS (
    SELECT 1
    FROM dim_employee d
    WHERE d.employee_id = e.employee_id
);

-- ============================================================
-- 7. Load Bridge Table
-- ============================================================

INSERT INTO bridge_employee_project
SELECT
    e.employee_key,
    p.project_key
FROM dim_project p
JOIN dim_employee e
    ON p.project_manager_id = e.employee_id
WHERE e.is_current = TRUE;

-- ============================================================
-- 8. Load Fact Transactions
-- ============================================================

INSERT INTO fact_transactions
SELECT
    ROW_NUMBER() OVER() AS transaction_key,

    t.transaction_id,

    p.project_key,
    e.employee_key,
    v.vendor_key,
    d.date_key,

    t.amount,
    t.category,
    t.payment_status

FROM read_csv_auto(
'C:/Users/hemant.gaikwad/OneDrive - Presight AI/Stackup/Final/outputs/transactions_clean.csv'
) t

LEFT JOIN dim_project p
    ON t.project_id = p.project_id

LEFT JOIN dim_employee e
    ON t.approved_by = e.employee_id
   AND e.is_current = TRUE

LEFT JOIN dim_vendor v
    ON t.vendor_id = v.vendor_id

LEFT JOIN dim_date d
    ON CAST(t.transaction_date AS DATE) = d.full_date;

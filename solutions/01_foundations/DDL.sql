
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


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

select *from dim_project;



INSERT INTO dim_employee
SELECT
    ROW_NUMBER() OVER() AS employee_key,
    employee_id,
    full_name,
    email,
    department,
    role AS role_name,
    level AS employee_level,
    salary,
    hire_date AS valid_from,
    DATE '9999-12-31' AS valid_to,
    TRUE AS is_current,
    'Current Employee Record' AS change_reason
FROM read_csv_auto(
'C:/Users/hemant.gaikwad/OneDrive - Presight AI/Stackup/Final/outputs/employees_clean.csv'
);


SELECT *
FROM read_csv_auto(
'C:/Users/hemant.gaikwad/OneDrive - Presight AI/Stackup/Final/outputs/transactions_clean.csv'
)
LIMIT 10;


INSERT INTO dim_vendor
SELECT DISTINCT
    ROW_NUMBER() OVER() AS vendor_key,
    vendor_id,
    vendor_name
FROM read_csv_auto(
'C:/Users/hemant.gaikwad/OneDrive - Presight AI/Stackup/Final/outputs/transactions_clean.csv'
);

INSERT INTO dim_date
SELECT
    ROW_NUMBER() OVER () AS date_key,
    full_date,

    YEAR(full_date) AS year,
    QUARTER(full_date) AS quarter,
    MONTH(full_date) AS month,
    MONTHNAME(full_date) AS month_name,

    WEEK(full_date) AS week,
    DAY(full_date) AS day,

    DAYNAME(full_date) AS day_of_week,

    CASE
        WHEN DAYOFWEEK(full_date) IN (0, 6)
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



INSERT INTO bridge_employee_project
SELECT
    e.employee_key,
    p.project_key
FROM dim_project p
JOIN dim_employee e
    ON p.project_manager_id = e.employee_id
WHERE e.is_current = TRUE;

-- ============================================================================
-- Load fact_transactions
-- ============================================================================

delete from fact_transactions;

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


INSERT INTO dim_employee
SELECT
    ROW_NUMBER() OVER() AS employee_key,
    employee_id,
    NULL AS full_name,
    NULL AS email,
    NULL AS department,

    previous_role AS role_name,

    previous_level AS employee_level,

    previous_salary AS salary,

    effective_date AS valid_from,

    LEAD(effective_date) OVER (
        PARTITION BY employee_id
        ORDER BY effective_date
    ) - INTERVAL 1 DAY AS valid_to,

    FALSE AS is_current,

    change_reason

FROM read_csv_auto(
'C:/Users/hemant.gaikwad/OneDrive - Presight AI/Stackup/Final/datasets/employees_salary_history.csv'
);


SELECT
    employee_id,
    COUNT(*) AS current_count
FROM dim_employee
WHERE is_current = TRUE
GROUP BY employee_id
HAVING COUNT(*) > 1;

SELECT
employee_id,
COUNT(*) AS version_count
FROM dim_employee
GROUP BY employee_id
ORDER BY version_count DESC
LIMIT 10;

SELECT
a.employee_id,
a.employee_key,
b.employee_key
FROM dim_employee a
JOIN dim_employee b
ON a.employee_id = b.employee_id
AND a.employee_key <> b.employee_key
AND a.valid_from < b.valid_to
AND b.valid_from < a.valid_to;


select *from  dim_employee 
where employee_id='EMP0029'



INSERT INTO dim_employee
SELECT
    (
        SELECT COALESCE(MAX(employee_key),0)
        FROM dim_employee
    )
    +
    ROW_NUMBER() OVER() AS employee_key,

    employee_id,

    full_name,
    email,
    department,

    role AS role_name,

    level AS employee_level,

    salary,

    hire_date AS valid_from,

    DATE '9999-12-31' AS valid_to,

    TRUE AS is_current,

    'Current Employee Record' AS change_reason

FROM read_csv_auto(
'C:/Users/hemant.gaikwad/OneDrive - Presight AI/Stackup/Final/outputs/employees_clean.csv'
);

sELECT
employee_id,
COUNT(*) AS current_count
FROM dim_employee
WHERE is_current = TRUE
GROUP BY employee_id
HAVING COUNT(*) > 1;

SELECT
employee_id,
COUNT(*) AS version_count
FROM dim_employee
GROUP BY employee_id
ORDER BY version_count DESC
LIMIT 10;

select *from dim_employee where employee_id='EMP0987'

DELETE FROM dim_employee;
INSERT INTO dim_employee
SELECT
    ROW_NUMBER() OVER(
        ORDER BY h.employee_id, h.effective_date
    ) AS employee_key,

    h.employee_id,

    e.full_name,
    e.email,
    e.department,

    h.new_role AS role_name,

    h.new_level AS employee_level,

    h.new_salary AS salary,

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


select *FROM dim_employee
where employee_id='EMP0026';

UPDATE dim_employee
SET
    is_current = TRUE,
    valid_to   = DATE '9999-12-31'
WHERE employee_key IN (

    SELECT employee_key
    FROM (

        SELECT
            d.employee_key,
            d.employee_id,
            ROW_NUMBER() OVER (
                PARTITION BY d.employee_id
                ORDER BY d.valid_from DESC
            ) AS rn

        FROM dim_employee d

        INNER JOIN read_csv_auto(
            'C:/Users/hemant.gaikwad/OneDrive - Presight AI/Stackup/Final/outputs/employees_clean.csv'
        ) e
        ON d.employee_id = e.employee_id

    ) x

    WHERE rn = 1

);


INSERT INTO dim_employee
SELECT
    (
        SELECT COALESCE(MAX(employee_key),0)
        FROM dim_employee
    ) + ROW_NUMBER() OVER() AS employee_key,

    e.employee_id,

    e.full_name,
    e.email,
    e.department,

    e.role AS role_name,

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

SELECT
employee_id,
COUNT(*) AS current_count
FROM dim_employee
WHERE is_current = TRUE
GROUP BY employee_id
HAVING COUNT(*) > 1;


SELECT
employee_id,
COUNT(*) AS version_count
FROM dim_employee
GROUP BY employee_id
HAVING COUNT(*) > 1
ORDER BY version_count DESC
LIMIT 10;


============================================================
 
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





-- ===========================================================================
-- SECTION 3 — TASK 2.1: Answer five business questions
-- ===========================================================================
--
-- Write a SQL query to answer each question.
-- For each query, add a comment explaining your approach.
-- Queries must run without errors against your loaded data.

-- ---------------------------------------------------------------------------
-- Q1. BUDGET PERFORMANCE
-- Which departments have spent more than 90% of their total budget across
-- all projects? Show department, total_budget, total_actual_cost,
-- spend_percentage, and whether they are over budget.
-- Order by spend_percentage descending.
-- ---------------------------------------------------------------------------

-- YOUR CODE HERE

SELECT
    department,
    SUM(budget) AS total_budget,
    SUM(actual_cost) AS total_actual_cost,
    ROUND(
        (SUM(actual_cost) / SUM(budget)) * 100, 2
    ) AS spend_percentage,

    CASE
        WHEN SUM(actual_cost) > SUM(budget)
        THEN 'Yes'
        ELSE 'No'
    END AS over_budget
FROM dim_project
GROUP BY department
HAVING (
    SUM(actual_cost) / SUM(budget) ) > 0.90
ORDER BY spend_percentage DESC;


-- ---------------------------------------------------------------------------
-- Q2. PROJECT MANAGER WORKLOAD
-- Which project managers are currently managing more than one active project
-- (status = 'In Progress')? Show their full name, email, number of active
-- projects, and the combined budget they are responsible for.
-- ---------------------------------------------------------------------------

-- YOUR CODE HERE

SELECT
    e.full_name,
    e.email,

    COUNT(*) AS active_projects,

    SUM(p.budget) AS total_budget

FROM dim_project p

JOIN dim_employee e
    On p.project_manager_id = e.employee_id
   AND e.is_current = TRUE

WHERE p.status = 'In Progress'
GROUP BY     e.full_name,     e.email
HAVING COUNT(*) > 1
ORDER BY active_projects DESC;

-- ---------------------------------------------------------------------------
-- Q3. VENDOR CONCENTRATION RISK
-- Identify vendors who account for more than 30% of total transaction spend
-- across all projects. Show vendor_name, total_spend, percentage_of_total.
-- This is a risk indicator — flag these vendors in the output.
-- ---------------------------------------------------------------------------

-- YOUR CODE HERE
-- Vendors contributing more than 30% of transaction spend

-- Vendors contributing more than 30% of transaction spend
-- ---------------------------------------------------------------------------
-- Q3. VENDOR CONCENTRATION RISK
-- Identify vendors who account for more than 30% of total transaction spend
-- across all projects. Show vendor_name, total_spend,
-- percentage_of_total and risk flag.
-- ---------------------------------------------------------------------------

WITH vendor_spend AS (

    SELECT
        v.vendor_name,
        SUM(f.amount) AS total_spend

    FROM fact_transactions f

    JOIN dim_vendor v
        ON f.vendor_key = v.vendor_key

    GROUP BY v.vendor_name

),

overall_spend AS (

    SELECT
        SUM(total_spend) AS grand_total
    FROM vendor_spend

)

SELECT
    vs.vendor_name,

    vs.total_spend,

    ROUND(
        (vs.total_spend / os.grand_total) * 100,
        2
    ) AS percentage_of_total,

    CASE
    WHEN (vs.total_spend / os.grand_total) > 0.10
        THEN 'HIGH'

    WHEN (vs.total_spend / os.grand_total) >= 0.05
         AND (vs.total_spend / os.grand_total) <= 0.10
        THEN 'MEDIUM'

    ELSE 'NORMAL'
END AS risk_flag

FROM vendor_spend vs
CROSS JOIN overall_spend os

WHERE (
    vs.total_spend / os.grand_total
) > 0.30

ORDER BY percentage_of_total DESC;

-- ---------------------------------------------------------------------------
-- Q4. ESCALATION-TO-COMPLETION RATE
-- Using the events data (if loaded), calculate the percentage of projects
-- that had at least one escalation event during their lifecycle.
-- If events data is not available, use the transactions data instead:
-- calculate the percentage of projects with a 'Disputed' transaction.
-- Show project_id, project_name, status, had_issue (True/False).
-- ---------------------------------------------------------------------------

-- YOUR CODE HERE
SELECT
    p.project_id,
    p.project_name,
    p.status,

    CASE
        WHEN COUNT(f.transaction_key) > 0
        THEN TRUE
        ELSE FALSE
    END AS had_issue

FROM dim_project p

LEFT JOIN fact_transactions f
    ON p.project_key = f.project_key
   AND f.payment_status = 'Disputed'

GROUP BY
    p.project_id,
    p.project_name,
    p.status

ORDER BY
    p.project_id;

    -- ---------------------------------------------------------------------------
-- Q4. PROJECTS WITH OPEN FINANCIAL ISSUES
-- Identify projects having pending or disputed transactions with
-- total open value greater than 50,000 AED.
-- ---------------------------------------------------------------------------

SELECT

    p.project_id,

    p.project_name,

    p.department,

    p.status AS project_status,

    COUNT(*) AS open_transaction_count,

    SUM(f.amount) AS open_transaction_value

FROM fact_transactions f

JOIN dim_project p
    ON f.project_key = p.project_key

WHERE f.payment_status IN (
    'Pending',
    'Disputed'
)

GROUP BY

    p.project_id,

    p.project_name,

    p.department,

    p.status

HAVING SUM(f.amount) > 50000

ORDER BY open_transaction_value DESC;

-- ---------------------------------------------------------------------------
-- Q5. MONTHLY SPEND TREND
-- Show the total transaction amount per month for the past 12 months,
-- broken down by category (Software, Consulting, Cloud Services, etc.)
-- Format the output as: year_month | category | total_amount | running_total
-- (running_total should accumulate within each category across months)
-- ---------------------------------------------------------------------------

-- YOUR CODE HERE

WITH monthly_spend AS (

    SELECT

        CONCAT(
            d.year,
            '-',
            LPAD(CAST(d.month AS VARCHAR), 2, '0')
        ) AS year_month,

        d.year,
        d.month,

        f.category,

        SUM(f.amount) AS total_amount

    FROM fact_transactions f

    JOIN dim_date d
        ON f.date_key = d.date_key

    GROUP BY
        d.year,
        d.month,
        f.category

)

SELECT

    year_month,

    category,

    total_amount,

    SUM(total_amount) OVER (

        PARTITION BY category

        ORDER BY
            year,
            month

        ROWS BETWEEN UNBOUNDED PRECEDING
        AND CURRENT ROW

    ) AS running_total

FROM monthly_spend

ORDER BY
category,
    year,
    month;


-- ---------------------------------------------------------------------------
-- Q6. EMPLOYEE COMPENSATION HISTORY ANALYSIS
-- Identify employees who received the largest salary increases.
-- Uses SCD Type 2 employee history.
-- ---------------------------------------------------------------------------
WITH monthly_spend AS (

    SELECT

        CONCAT(
            d.year,
            '-',
            LPAD(CAST(d.month AS VARCHAR), 2, '0')
        ) AS year_month,

        d.year,
        d.month,

        f.category,

        SUM(f.amount) AS monthly_spend

    FROM fact_transactions f

    JOIN dim_date d
        ON f.date_key = d.date_key

    GROUP BY
        d.year,
        d.month,
        f.category

)

SELECT

    year_month,

    category,

    monthly_spend,

    SUM(monthly_spend) OVER (

        PARTITION BY category

        ORDER BY
            year,
            month

    ) AS running_total,

    ROUND(
        (
            monthly_spend
            -
            LAG(monthly_spend) OVER (
                PARTITION BY category
                ORDER BY year, month
            )
        )
        /
        NULLIF(
            LAG(monthly_spend) OVER (
                PARTITION BY category
                ORDER BY year, month
            ),
            0
        ) * 100,
        2
    ) AS month_over_month_pct_change

FROM monthly_spend

ORDER BY
    category,
    year,
    month;

    
WITH salary_changes AS (

    SELECT

        curr.employee_id,

        curr.full_name,

        curr.valid_from AS change_date,

        prev.salary AS previous_salary,

        curr.salary AS new_salary,

        curr.salary - prev.salary AS increase_amount,

        ROUND(
            (
                (curr.salary - prev.salary)
                /
                NULLIF(prev.salary, 0)
            ) * 100,
            2
        ) AS increase_pct

    FROM dim_employee curr

    JOIN dim_employee prev
        ON curr.employee_id = prev.employee_id
       AND prev.valid_to =
           curr.valid_from - INTERVAL 1 DAY

)

SELECT *

FROM salary_changes

ORDER BY increase_amount DESC

LIMIT 20;

-- ===========================================================================
-- SECTION 4 — TASK 2.3: Query optimisation
-- ===========================================================================
--
-- The following query runs slowly in production. It is used on the finance
-- dashboard and executes hundreds of times per day.
--
-- YOUR TASKS:
--   a) Run EXPLAIN or EXPLAIN ANALYZE on the query (depending on your DB)
--      and paste the output as a comment. Identify the bottleneck.
--
--   b) Rewrite the query to improve performance.
--      You may restructure it, add CTEs, change joins, etc.
--
--   c) Write a comment explaining:
--      - What was wrong with the original query
--      - What you changed and why
--      - What indexes (if any) you would add in production
--
-- NOTE: Load sufficient data to make the performance difference meaningful.
--       If running on a small dataset, describe what you would observe at scale.

-- ORIGINAL QUERY (do not modify this — rewrite it in section 4b below)
-- ---------------------------------------------------------------------------
SELECT
    e.full_name,
    e.department,
    e.role,
    p.project_name,
    p.status,
    p.budget,
    p.actual_cost,
    t.amount,
    t.category,
    t.payment_status,
    t.transaction_date
FROM employees e, projects p, transactions t
WHERE e.employee_id = p.project_manager_id
AND   p.project_id  = t.project_id
AND   p.status NOT IN ('Completed', 'On Hold')
AND   t.payment_status = 'Pending'
AND   t.amount > (
        SELECT AVG(amount)
        FROM transactions
        WHERE payment_status = 'Pending'
      )
ORDER BY e.department, t.amount DESC;

-- ---------------------------------------------------------------------------
-- 4a) EXPLAIN output and bottleneck analysis (paste as comment):
-- ---------------------------------------------------------------------------
-- YOUR ANALYSIS HERE
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘

 EXPLAIN ANALYZE
 SELECT
     e.full_name,
     e.department,
     e.role_name,
     p.project_name,
     p.status,
     p.budget,
     p.actual_cost,
     t.amount,
     t.category,
     t.payment_status,
     t.date_key
 FROM dim_employee e, dim_project p, fact_transactions t
 WHERE e.employee_id = p.project_manager_id
 AND   p.project_key  = t.project_key
 AND   p.status NOT IN ('Completed', 'On Hold')
 AND   t.payment_status = 'Pending'
 AND   t.amount > (
         SELECT AVG(amount)
         FROM fact_transactions
         WHERE payment_status = 'Pending'
       )
 ORDER BY e.department, t.amount DESC
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││              Total Time: 0.0767s             ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│                           │
│           0 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             #0            │
│__internal_decompress_strin│
│           g(#1)           │
│             #2            │
│             #3            │
│__internal_decompress_strin│
│           g(#4)           │
│             #5            │
│             #6            │
│             #7            │
│             #8            │
│__internal_decompress_strin│
│           g(#9)           │
│__internal_decompress_integ│
│  ral_integer(#10, 44566)  │
│                           │
│                           │
│                           │
│         2,114 rows        │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│          ORDER_BY         │
│    ────────────────────   │
│      e.department ASC     │
│       t.amount DESC       │
│                           │
│                           │
│                           │
│         2,114 rows        │
│           0.01s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             #0            │
│__internal_compress_string_│
│        uhugeint(#1)       │
│             #2            │
│             #3            │
│__internal_compress_string_│
│        uhugeint(#4)       │
│             #5            │
│             #6            │
│             #7            │
│             #8            │
│__internal_compress_string_│
│        uhugeint(#9)       │
│__internal_compress_integra│
│  l_usmallint(#10, 44566)  │
│                           │
│                           │
│                           │
│         2,114 rows        │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│         full_name         │
│         department        │
│         role_name         │
│        project_name       │
│           status          │
│           budget          │
│        actual_cost        │
│           amount          │
│          category         │
│       payment_status      │
│          date_key         │
│                           │
│                           │
│                           │
│         2,114 rows        │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         HASH_JOIN         │
│    ────────────────────   │
│      Join Type: INNER     │
│                           │
│        Conditions:        │
│       employee_id =       │
│     project_manager_id    ├──────────────┐
│                           │              │
│                           │              │
│                           │              │
│         2,114 rows        │              │
│           0.00s           │              │
└─────────────┬─────────────┘              │
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│         TABLE_SCAN        ││         HASH_JOIN         │
│    ────────────────────   ││    ────────────────────   │
│           Table:          ││      Join Type: INNER     │
│ stackup.main.dim_employee ││                           │
│                           ││        Conditions:        │
│   Type: Sequential Scan   ││ project_key = project_key │
│                           ││                           │
│        Projections:       ││                           │
│        employee_id        ││                           │
│         full_name         ││                           │
│         department        ││           0.00s           │
│         role_name         ││                           │
│                           ││                           ├──────────────┐
│      Dynamic Filters:     ││                           │              │
│  optional: employee_id>=  ││                           │              │
│  'EMP0002' AND optional:  ││                           │              │
│   employee_id<='EMP0991'  ││                           │              │
│  AND optional: employee_id││                           │              │
│  IN BF(project_manager_id)││                           │              │
│                           ││                           │              │
│                           ││                           │              │
│                           ││                           │              │
│          336 rows         ││          923 rows         │              │
│           0.00s           ││          (0.00s)          │              │
└───────────────────────────┘└─────────────┬─────────────┘              │
                             ┌─────────────┴─────────────┐┌─────────────┴─────────────┐
                             │         TABLE_SCAN        ││      NESTED_LOOP_JOIN     │
                             │    ────────────────────   ││    ────────────────────   │
                             │           Table:          ││      Join Type: INNER     │
                             │  stackup.main.dim_project ││                           │
                             │                           ││        Conditions:        │
                             │   Type: Sequential Scan   ││  CAST(amount AS DOUBLE) > │
                             │                           ││          SUBQUERY         │
                             │        Projections:       ││                           │
                             │     project_manager_id    ││                           │
                             │        project_key        ││                           │
                             │           status          ││                           │
                             │        project_name       ││           0.00s           │
                             │           budget          ││                           │
                             │        actual_cost        ││                           │
                             │                           ││                           ├──────────────┐
                             │          Filters:         ││                           │              │
                             │ (status NOT IN ('Completed││                           │              │
                             │       ', 'On Hold'))      ││                           │              │
                             │                           ││                           │              │
                             │      Dynamic Filters:     ││                           │              │
                             │  optional: project_key>=1 ││                           │              │
                             │  AND optional: project_key││                           │              │
                             │           <=500           ││                           │              │
                             │                           ││                           │              │
                             │                           ││                           │              │
                             │                           ││                           │              │
                             │          239 rows         ││         2,127 rows        │              │
                             │           0.00s           ││          (0.00s)          │              │
                             └───────────────────────────┘└─────────────┬─────────────┘              │
                                                          ┌─────────────┴─────────────┐┌─────────────┴─────────────┐
                                                          │         TABLE_SCAN        ││         PROJECTION        │
                                                          │    ────────────────────   ││    ────────────────────   │
                                                          │           Table:          ││ CASE  WHEN ((#1 > 1)) THEN│
                                                          │        stackup.main       ││   ("error"('More than one │
                                                          │     .fact_transactions    ││      row returned by a    │
                                                          │                           ││     subquery used as an   │
                                                          │   Type: Sequential Scan   ││     expression - scalar   │
                                                          │                           ││     subqueries can only   │
                                                          │        Projections:       ││    return a single row.   │
                                                          │        project_key        ││          Use "SET         │
                                                          │       payment_status      ││ scalar_subquery_error_on_m│
                                                          │           amount          ││   ultiple_rows=false" to  │
                                                          │          category         ││     revert to previous    │
                                                          │          date_key         ││   behavior of returning a │
                                                          │                           ││ random row.')) ELSE #0 END│
                                                          │          Filters:         ││                           │
                                                          │  payment_status='Pending' ││                           │
                                                          │                           ││                           │
                                                          │                           ││                           │
                                                          │                           ││           0.00s           │
                                                          │         8,927 rows        ││           1 row           │
                                                          │           0.00s           ││          (0.00s)          │
                                                          └───────────────────────────┘└─────────────┬─────────────┘
                                                                                       ┌─────────────┴─────────────┐
                                                                                       │    UNGROUPED_AGGREGATE    │
                                                                                       │    ────────────────────   │
                                                                                       │        Aggregates:        │
                                                                                       │        "first"(#0)        │
                                                                                       │        count_star()       │
                                                                                       │                           │
                                                                                       │                           │
                                                                                       │                           │
                                                                                       │           1 row           │
                                                                                       │           0.00s           │
                                                                                       └─────────────┬─────────────┘
                                                                                       ┌─────────────┴─────────────┐
                                                                                       │         PROJECTION        │
                                                                                       │    ────────────────────   │
                                                                                       │             #0            │
                                                                                       │                           │
                                                                                       │                           │
                                                                                       │                           │
                                                                                       │           1 row           │
                                                                                       │           0.00s           │
                                                                                       └─────────────┬─────────────┘
                                                                                       ┌─────────────┴─────────────┐
                                                                                       │    UNGROUPED_AGGREGATE    │
                                                                                       │    ────────────────────   │
                                                                                       │    Aggregates: avg(#0)    │
                                                                                       │                           │
                                                                                       │                           │
                                                                                       │                           │
                                                                                       │           1 row           │
                                                                                       │           0.00s           │
                                                                                       └─────────────┬─────────────┘
                                                                                       ┌─────────────┴─────────────┐
                                                                                       │         PROJECTION        │
                                                                                       │    ────────────────────   │
                                                                                       │           amount          │
                                                                                       │                           │
                                                                                       │                           │
                                                                                       │                           │
                                                                                       │         8,927 rows        │
                                                                                       │           0.00s           │
                                                                                       └─────────────┬─────────────┘
                                                                                       ┌─────────────┴─────────────┐
                                                                                       │         TABLE_SCAN        │
                                                                                       │    ────────────────────   │
                                                                                       │           Table:          │
                                                                                       │        stackup.main       │
                                                                                       │     .fact_transactions    │
                                                                                       │                           │
                                                                                       │   Type: Sequential Scan   │
                                                                                       │    Projections: amount    │
                                                                                       │                           │
                                                                                       │          Filters:         │
                                                                                       │  payment_status='Pending' │
                                                                                       │                           │
                                                                                       │                           │
                                                                                       │                           │
                                                                                       │         8,927 rows        │
                                                                                       │           0.00s           │
                                                                                       └───────────────────────────┘

-- ============================================================================
-- 4a) EXPLAIN Output and Bottleneck Analysis
-- ============================================================================

/*
Observed Bottlenecks:

1. Old-style implicit joins:
   FROM employees e, projects p, transactions t

   This style is harder for the optimizer to interpret and may
   create large intermediate result sets.

2. Correlated aggregate calculation:

   t.amount > (
       SELECT AVG(amount)
       FROM transactions
       WHERE payment_status = 'Pending'
   )

   The average pending amount is recalculated during execution.

3. Filters are applied after joining large datasets.

   transactions is the largest table (~50,000 rows).

4. ORDER BY on a large result set:

   ORDER BY e.department, t.amount DESC

   requires additional sorting.

Expected behavior at scale:

- Full table scans on transactions.
- Large join operations before filtering.
- Increased CPU and memory consumption.
*/

-- ---------------------------------------------------------------------------
-- 4b) REWRITTEN QUERY
-- ---------------------------------------------------------------------------
-- YOUR CODE HERE
WITH avg_pending_amount AS (

    SELECT
        AVG(amount) AS avg_amount
    FROM fact_transactions
    WHERE payment_status = 'Pending'

),

filtered_transactions AS (

    SELECT
        transaction_key,
        project_key,
        amount,
        category,
        payment_status
    FROM fact_transactions
    WHERE payment_status = 'Pending'

)

SELECT

    e.full_name,

    e.department,

    e.role_name,

    p.project_name,

    p.status,

    p.budget,

    p.actual_cost,

    t.amount,

    t.category,

    t.payment_status

FROM filtered_transactions t

JOIN dim_project p
    ON t.project_key = p.project_key

JOIN dim_employee e
    ON p.project_manager_id = e.employee_id
   AND e.is_current = TRUE

CROSS JOIN avg_pending_amount a

WHERE t.amount > a.avg_amount

AND p.status NOT IN (
    'Completed',
    'On Hold'
)

ORDER BY
    e.department,
    t.amount DESC;
-- ---------------------------------------------------------------------------
-- 4c) Explanation of changes and indexing strategy
-- ---------------------------------------------------------------------------
-- YOUR EXPLANATION HERE
-- ============================================================================
-- 4c) INDEX STRATEGY
-- ============================================================================

-- Supports filtering pending/disputed transactions.
CREATE INDEX idx_fact_transactions_payment_status
ON fact_transactions(payment_status);

-- Supports joins between fact_transactions and dim_project.
CREATE INDEX idx_fact_transactions_project_key
ON fact_transactions(project_key);

-- Supports joins between fact_transactions and dim_employee.
CREATE INDEX idx_fact_transactions_employee_key
ON fact_transactions(employee_key);

-- Supports joins between fact_transactions and dim_vendor.
CREATE INDEX idx_fact_transactions_vendor_key
ON fact_transactions(vendor_key);

-- Supports employee lookups and SCD2 validation queries.
CREATE INDEX idx_dim_employee_employee_id
ON dim_employee(employee_id);

-- Supports project lookups from source business key.
CREATE INDEX idx_dim_project_project_id
ON dim_project(project_id);

-- Supports vendor lookups from source business key.
CREATE INDEX idx_dim_vendor_vendor_id
ON dim_vendor(vendor_id);
/*
Index Strategy Explanation
==========================

1. idx_fact_transactions_payment_status
   - Accelerates filtering on payment_status.
   - Useful for Pending and Disputed transaction analysis.
   - Benefits Q4 and query optimization exercise.

2. idx_fact_transactions_project_key
   - Accelerates joins between fact_transactions and dim_project.
   - Frequently used in spend analysis queries.

3. idx_fact_transactions_employee_key
   - Accelerates joins between fact_transactions and dim_employee.
   - Helps employee workload and approval analysis.

4. idx_fact_transactions_vendor_key
   - Accelerates joins between fact_transactions and dim_vendor.
   - Supports vendor concentration reporting.

5. idx_dim_employee_employee_id
   - Supports SCD Type 2 lookups.
   - Improves employee history and current-record retrieval.

6. idx_dim_project_project_id
   - Supports business-key lookups during ETL and reporting.

7. idx_dim_vendor_vendor_id
   - Supports vendor mapping from transaction source data.

Trade-Off:
-----------
Indexes increase storage usage and slightly slow INSERT/UPDATE
operations. However, this warehouse is read-heavy and query
performance improvements outweigh the write overhead.

Expected Benefit:
-----------------
Reduced table scans, faster joins, and improved dashboard query
response times, especially for the 50,000-row transaction dataset.
*/

┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘

 EXPLAIN ANALYZE
 
 WITH avg_pending_amount AS (
 
     SELECT
         AVG(amount) AS avg_amount
     FROM fact_transactions
     WHERE payment_status = 'Pending'
 
 ),
 
 
 filtered_transactions AS (
 
     SELECT
         transaction_key,
         project_key,
         amount,
         category,
         payment_status
     FROM fact_transactions
     WHERE payment_status = 'Pending'
 
 )
 
 SELECT
 
     e.full_name,
 
     e.department,
 
     e.role_name,
 
     p.project_name,
 
     p.status,
 
     p.budget,
 
     p.actual_cost,
 
     t.amount,
 
     t.category,
 
     t.payment_status
 
 FROM filtered_transactions t
 
 JOIN dim_project p
     ON t.project_key = p.project_key
 
 JOIN dim_employee e
     ON p.project_manager_id = e.employee_id
    AND e.is_current = TRUE
 
 CROSS JOIN avg_pending_amount a
 
 WHERE t.amount > a.avg_amount
 
 AND p.status NOT IN (
     'Completed',
     'On Hold'
 )
 
 ORDER BY
     e.department,
     t.amount DESC
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││              Total Time: 0.0219s             ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│                           │
│           0 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             #0            │
│__internal_decompress_strin│
│           g(#1)           │
│             #2            │
│             #3            │
│__internal_decompress_strin│
│           g(#4)           │
│             #5            │
│             #6            │
│             #7            │
│             #8            │
│__internal_decompress_strin│
│           g(#9)           │
│                           │
│                           │
│                           │
│          923 rows         │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│          ORDER_BY         │
│    ────────────────────   │
│      e.department ASC     │
│       t.amount DESC       │
│                           │
│                           │
│                           │
│          923 rows         │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             #0            │
│__internal_compress_string_│
│        uhugeint(#1)       │
│             #2            │
│             #3            │
│__internal_compress_string_│
│        uhugeint(#4)       │
│             #5            │
│             #6            │
│             #7            │
│             #8            │
│__internal_compress_string_│
│        uhugeint(#9)       │
│                           │
│                           │
│                           │
│          923 rows         │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│         full_name         │
│         department        │
│         role_name         │
│        project_name       │
│           status          │
│           budget          │
│        actual_cost        │
│           amount          │
│          category         │
│       payment_status      │
│                           │
│                           │
│                           │
│          923 rows         │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         HASH_JOIN         │
│    ────────────────────   │
│      Join Type: INNER     │
│                           │
│        Conditions:        │
│       employee_id =       │
│     project_manager_id    ├──────────────┐
│                           │              │
│                           │              │
│                           │              │
│          923 rows         │              │
│           0.00s           │              │
└─────────────┬─────────────┘              │
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│         TABLE_SCAN        ││         HASH_JOIN         │
│    ────────────────────   ││    ────────────────────   │
│           Table:          ││      Join Type: INNER     │
│ stackup.main.dim_employee ││                           │
│                           ││        Conditions:        │
│   Type: Sequential Scan   ││ project_key = project_key │
│                           ││                           │
│        Projections:       ││                           │
│        employee_id        ││                           │
│         full_name         ││                           │
│         department        ││           0.00s           │
│         role_name         ││                           │
│                           ││                           │
│          Filters:         ││                           ├──────────────┐
│      is_current=true      ││                           │              │
│                           ││                           │              │
│      Dynamic Filters:     ││                           │              │
│  optional: employee_id>=  ││                           │              │
│  'EMP0002' AND optional:  ││                           │              │
│   employee_id<='EMP0991'  ││                           │              │
│  AND optional: employee_id││                           │              │
│  IN BF(project_manager_id)││                           │              │
│                           ││                           │              │
│                           ││                           │              │
│                           ││                           │              │
│          147 rows         ││          923 rows         │              │
│           0.00s           ││          (0.00s)          │              │
└───────────────────────────┘└─────────────┬─────────────┘              │
                             ┌─────────────┴─────────────┐┌─────────────┴─────────────┐
                             │         TABLE_SCAN        ││      NESTED_LOOP_JOIN     │
                             │    ────────────────────   ││    ────────────────────   │
                             │           Table:          ││      Join Type: INNER     │
                             │  stackup.main.dim_project ││                           │
                             │                           ││        Conditions:        │
                             │   Type: Sequential Scan   ││  CAST(amount AS DOUBLE) > │
                             │                           ││         avg_amount        │
                             │        Projections:       ││                           │
                             │        project_key        ││                           │
                             │     project_manager_id    ││                           │
                             │           status          ││                           │
                             │        project_name       ││           0.00s           │
                             │           budget          ││                           │
                             │        actual_cost        ││                           │
                             │                           ││                           ├──────────────┐
                             │          Filters:         ││                           │              │
                             │ (status NOT IN ('Completed││                           │              │
                             │       ', 'On Hold'))      ││                           │              │
                             │                           ││                           │              │
                             │      Dynamic Filters:     ││                           │              │
                             │  optional: project_key>=1 ││                           │              │
                             │  AND optional: project_key││                           │              │
                             │           <=500           ││                           │              │
                             │                           ││                           │              │
                             │                           ││                           │              │
                             │                           ││                           │              │
                             │          239 rows         ││         2,127 rows        │              │
                             │           0.00s           ││          (0.00s)          │              │
                             └───────────────────────────┘└─────────────┬─────────────┘              │
                                                          ┌─────────────┴─────────────┐┌─────────────┴─────────────┐
                                                          │         PROJECTION        ││    UNGROUPED_AGGREGATE    │
                                                          │    ────────────────────   ││    ────────────────────   │
                                                          │        project_key        ││    Aggregates: avg(#0)    │
                                                          │           amount          ││                           │
                                                          │          category         ││                           │
                                                          │       payment_status      ││                           │
                                                          │                           ││                           │
                                                          │                           ││           0.00s           │
                                                          │                           ││                           │
                                                          │         8,927 rows        ││           1 row           │
                                                          │           0.00s           ││          (0.00s)          │
                                                          └─────────────┬─────────────┘└─────────────┬─────────────┘
                                                          ┌─────────────┴─────────────┐┌─────────────┴─────────────┐
                                                          │         TABLE_SCAN        ││         PROJECTION        │
                                                          │    ────────────────────   ││    ────────────────────   │
                                                          │           Table:          ││           amount          │
                                                          │        stackup.main       ││                           │
                                                          │     .fact_transactions    ││                           │
                                                          │                           ││                           │
                                                          │   Type: Sequential Scan   ││                           │
                                                          │                           ││           0.00s           │
                                                          │        Projections:       ││                           │
                                                          │       payment_status      ││                           │
                                                          │        project_key        ││                           │
                                                          │           amount          ││                           │
                                                          │          category         ││                           │
                                                          │                           ││                           │
                                                          │          Filters:         ││                           │
                                                          │  payment_status='Pending' ││                           │
                                                          │                           ││                           │
                                                          │                           ││                           │
                                                          │                           ││                           │
                                                          │         8,927 rows        ││         8,927 rows        │
                                                          │           0.00s           ││          (0.00s)          │
                                                          └───────────────────────────┘└─────────────┬─────────────┘
                                                                                       ┌─────────────┴─────────────┐
                                                                                       │         TABLE_SCAN        │
                                                                                       │    ────────────────────   │
                                                                                       │           Table:          │
                                                                                       │        stackup.main       │
                                                                                       │     .fact_transactions    │
                                                                                       │                           │
                                                                                       │   Type: Sequential Scan   │
                                                                                       │    Projections: amount    │
                                                                                       │                           │
                                                                                       │          Filters:         │
                                                                                       │  payment_status='Pending' │
                                                                                       │                           │
                                                                                       │                           │
                                                                                       │                           │
                                                                                       │         8,927 rows        │
                                                                                       │           0.00s           │
                                                                                       └───────────────────────────┘

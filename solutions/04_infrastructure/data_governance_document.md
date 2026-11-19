# Data Governance Document

StackUp Engineering Academy – Data Engineering Assessment

Prepared By: Hemant Gaikwad

Date: October 2026

## Section 1 – Data Inventory

| Dataset | Source System | Format | Update Frequency | Volume Estimate | Daily Growth |
|----------|----------|----------|----------|----------|----------|
| projects | Project Management System | CSV | Daily | 500 records | Low |
| employees | HR Management System | CSV | Daily | 1,000 records | Low |
| transactions | Financial Transaction System | CSV | Daily | 50,000 records | Medium |
| employees_salary_history | HR Compensation System | CSV | As changes occur | 5,000+ records | Low |

## Section 2 – Data Classification

### Classification Definitions

| Classification | Definition |
|--------------|------------|
| Public | Non-sensitive information that may be shared externally |
| Internal | Internal business information with no regulatory restrictions |
| Confidential | Sensitive business information requiring restricted access |
| Personal (PII) | Personally Identifiable Information subject to privacy regulations |

### Projects Dataset

| Column | Classification |
|----------|----------|
| project_id | Internal |
| project_name | Internal |
| department | Internal |
| status | Internal |
| start_date | Internal |
| end_date | Internal |
| budget | Confidential |
| actual_cost | Confidential |
| project_manager_id | Personal (PII) |
| priority | Internal |
| region | Internal |

#### PII Regulations

| Column | Regulation |
|----------|----------|
| project_manager_id | GDPR + UAE PDPL |

### Employees Dataset

| Column | Classification |
|----------|----------|
| employee_id | Personal (PII) |
| full_name | Personal (PII) |
| email | Personal (PII) |
| department | Internal |
| role | Internal |
| level | Internal |
| hire_date | Confidential |
| salary | Confidential |
| manager_id | Personal (PII) |
| region | Internal |
| status | Internal |
| years_experience | Internal |

#### PII Regulations

| Column | Regulation |
|----------|----------|
| employee_id | GDPR + UAE PDPL |
| full_name | GDPR + UAE PDPL |
| email | GDPR + UAE PDPL |
| manager_id | GDPR + UAE PDPL |

### Employee Salary History Dataset

| Column | Classification |
|----------|----------|
| employee_id | Personal (PII) |
| previous_salary | Confidential |
| new_salary | Confidential |
| previous_role | Internal |
| new_role | Internal |
| previous_level | Internal |
| new_level | Internal |
| effective_date | Confidential |
| change_type | Confidential |
| change_reason | Confidential |

#### PII Regulations

| Column | Regulation |
|----------|----------|
| employee_id | GDPR + UAE PDPL |

### Transactions Dataset

| Column | Classification |
|----------|----------|
| transaction_id | Internal |
| project_id | Internal |
| vendor_id | Internal |
| vendor_name | Internal |
| category | Internal |
| amount | Confidential |
| currency | Internal |
| transaction_date | Internal |
| approved_by | Personal (PII) |
| payment_status | Internal |
| invoice_ref | Confidential |
| notes | Internal |

#### PII Regulations

| Column | Regulation |
|----------|----------|
| approved_by | GDPR + UAE PDPL |

## Section 3 – Data Ownership

| Dataset | Data Owner (Role) | Data Steward (Role) | Access Approver |
|----------|----------|----------|----------|
| projects | PMO Manager | Data Steward | PMO Manager |
| employees | HR Director | HR Data Steward | HR Director |
| transactions | Finance Manager | Finance Data Steward | Finance Manager |
| employees_salary_history | Head of HR | HR Data Steward | Head of HR |

### Data Owner vs Data Steward

A Data Owner is accountable for the dataset, defines business rules, approves access requests, and ensures the data supports business objectives.

A Data Steward is responsible for day-to-day management of data quality, metadata, classification, standards compliance, and governance processes.

## Section 4 – Retention Policy

| Dataset | Retention Period | Justification | Disposal Method | Enforced By |
|----------|----------|----------|----------|----------|
| projects | 7 years | Historical project analysis, audits and reporting | Archive then delete | PMO Manager |
| employees | 7 years after employment ends | HR compliance and employment history requirements | Archive then anonymise | HR Director |
| transactions | 7 years | Financial audits, compliance and reporting | Archive then delete | Finance Manager |
| employees_salary_history | 10 years | Historical compensation evidence, labour disputes, regulatory compliance and workforce planning | Archive then anonymise | Head of HR |

### Salary History Special Consideration

Employee salary history contains highly sensitive compensation information. Due to employment, audit and potential legal requirements, salary history should be retained longer than standard employee profile data.

## Section 5 – Access Control

| Persona | Projects | Employees | Transactions | Salary History |
|----------|----------|----------|----------|----------|
| Data Engineer | Read + Write | Read | Read + Write | None |
| BI Analyst | Read | Read | Read | None |
| Finance Team | Read | None | Read + Write | Read |
| HR Team | Read | Read + Write | None | Read + Write |
| Executive | Read | Read | Read | Read |

### Access Justification

Salary history contains highly sensitive compensation data and follows the principle of least privilege.

## Section 6 – Data Lineage

```text
Source Systems
     |
     +--> projects.csv ---------+
     |                          |
     +--> employees.csv ------- ETL Validation & Data Quality Checks
     |                          |
     +--> transactions.csv -----+
     |                          |
     +--> employees_salary_history.csv
                                |
                                v
                        Cleaned Datasets
                                |
                                v
                         Data Warehouse
                                |
                                v
                     Reports / Dashboards
```

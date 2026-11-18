# Chennai Frozen Foods Operations Management System (CFF-OMS)

## 1. Project Summary & Objective
Staff at Chennai Frozen Foods (Ambattur Industrial Estate) previously managed batch production, 3 frozen food lines, raw material suppliers, and quality inspections through ad-hoc spreadsheets and phone calls, resulting in missing records every week. **CFF-OMS** replaces these manual workflows with an auditable, role-based FastAPI + MES web application.

## 2. User Stories (Objective 3)
- **US-01 (RBAC & Login):** As a System Admin, I want role-based permissions (`OPERATOR`, `QC_INSPECTOR`, `SUPERVISOR`, `ADMIN`) so each staff member only performs authorized operations.
- **US-02 (Master Data):** As a Supervisor, I want to manage Suppliers, Raw Materials, Machines, and Production Lines (`LINE_1`, `LINE_2`, `LINE_3`).
- **US-03 (Batch Production Logging):** As a Line Operator, I want to log raw material input (kg), gross frozen output (kg), scrap wastage (kg), shift (`DAY`/`NIGHT`), and freezer telemetry.
- **US-04 (Quality Control Inspection):** As a QC Inspector, I want to log moisture %, core temperature (°C), microbial pass/fail, and rejected output (kg).
- **US-05 (Supervisor Approval Workflow):** As a Plant Supervisor, I want to approve or reject batches after QC inspection and lock approved batches against further edits.
- **US-06 (Fault-Tolerant Historical Import):** As a Supervisor, I want to import dirty historical CSV spreadsheets and receive a structured validation report for missing night-shift moisture, late QC results, and reused batch numbers.
- **US-07 (Yield, Wastage & Rejection Reports):** As a Supervisor, I want accurate KPI reports exported to CSV and PDF.
- **US-08 (Immutable Audit Trail & Alerts):** As an Admin, I want an append-only audit trail of who changed what and automated Email/SMS notifications.

## 3. Object-Oriented Design Patterns (Objective 6)
1. **Repository Pattern (`AbstractRepository` -> `BatchRepository`, `AuditRepository`):** Decouples SQLAlchemy database queries from domain business rules.
2. **Strategy Pattern (`ReportExportStrategy` -> `CSVExportStrategy`, `SimplePDFExportStrategy`):** Allows runtime switching of report rendering algorithms without modifying the service or API controller.

## 4. Quickstart & Running Tests (Objectives 8 & 10)
```bash
pip install fastapi uvicorn sqlalchemy pydantic pytest pytest-cov
uvicorn app.main:app --reload
pytest --cov=app/services tests/test_business_rules.py
```

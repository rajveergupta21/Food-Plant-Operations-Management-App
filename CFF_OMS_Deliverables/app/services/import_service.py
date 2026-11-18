import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict
from pydantic import BaseModel
from app.domain.models import Batch, QualityTest, BatchStatus
from app.repositories.batch_repo import BatchRepository, AuditRepository

class RowValidationIssue(BaseModel):
    row_number: int
    legacy_batch_no: str
    severity: str  # "REJECTED" or "WARNING"
    code: str
    reason: str

class ImportValidationReport(BaseModel):
    total_rows: int
    imported_count: int
    rejected_count: int
    warning_count: int
    issues: List[RowValidationIssue]

class HistoricalImportService:
    VALID_LINES = {"LINE_1": 1, "LINE_2": 2, "LINE_3": 3}

    def __init__(self, batch_repo: BatchRepository, audit_repo: AuditRepository):
        self.batch_repo = batch_repo
        self.audit_repo = audit_repo

    def import_csv(self, csv_content: str, user_id: int) -> ImportValidationReport:
        reader = csv.DictReader(io.StringIO(csv_content.strip()))
        issues: List[RowValidationIssue] = []
        imported_count = rejected_count = warning_count = total_rows = 0
        seen_legacy: Dict[str, str] = {}

        for idx, row in enumerate(reader, start=2):
            total_rows += 1
            legacy_no = (row.get("batch_no") or "").strip()
            line_code = (row.get("line_code") or "").strip()
            shift = (row.get("shift") or "").strip().upper()

            if line_code not in self.VALID_LINES:
                issues.append(RowValidationIssue(
                    row_number=idx, legacy_batch_no=legacy_no or "N/A",
                    severity="REJECTED", code="ERR_INVALID_LINE",
                    reason=f"Unknown production line '{line_code}'."
                ))
                rejected_count += 1
                continue

            # Rule 1: Missing moisture reading on NIGHT shift
            raw_moisture = (row.get("moisture_pct") or "").strip()
            if raw_moisture == "":
                code = "ERR_MISSING_NIGHT_MOISTURE" if shift == "NIGHT" else "ERR_MISSING_MOISTURE"
                issues.append(RowValidationIssue(
                    row_number=idx, legacy_batch_no=legacy_no,
                    severity="REJECTED", code=code,
                    reason=f"Moisture reading missing on {shift} shift; mandatory for cold-chain QC."
                ))
                rejected_count += 1
                continue

            prod_start = datetime.fromisoformat(row["production_start"].strip())
            prod_end = datetime.fromisoformat(row["production_end"].strip())
            tested_at = datetime.fromisoformat(row["qc_tested_at"].strip())

            # Rule 2: Batch numbers reused after system reset
            prod_date_str = prod_start.strftime("%Y%m%d")
            canonical_key = f"{line_code}-{prod_date_str}-{legacy_no}"
            if self.batch_repo.find_by_legacy_no(legacy_no) or (legacy_no in seen_legacy and seen_legacy[legacy_no] != prod_date_str):
                issues.append(RowValidationIssue(
                    row_number=idx, legacy_batch_no=legacy_no,
                    severity="WARNING", code="WARN_REUSED_BATCH_NO_AFTER_RESET",
                    reason=f"Reused legacy batch '{legacy_no}' disambiguated as '{canonical_key}'."
                ))
                warning_count += 1
            seen_legacy[legacy_no] = prod_date_str

            # Rule 3: Quality results recorded a day late
            delay = tested_at - prod_end
            is_late = False
            if delay < timedelta(0):
                issues.append(RowValidationIssue(
                    row_number=idx, legacy_batch_no=legacy_no,
                    severity="REJECTED", code="ERR_QC_BEFORE_PRODUCTION",
                    reason="QC timestamp occurs prior to production completion."
                ))
                rejected_count += 1
                continue
            elif delay >= timedelta(hours=18):
                is_late = True
                issues.append(RowValidationIssue(
                    row_number=idx, legacy_batch_no=legacy_no,
                    severity="WARNING", code="WARN_LATE_QUALITY_RESULT",
                    reason=f"QC recorded {delay.total_seconds()/3600:.1f}h after production end (flagged is_late_entry=True)."
                ))
                warning_count += 1

            batch = Batch(
                canonical_batch_key=canonical_key, legacy_batch_no=legacy_no,
                line_id=self.VALID_LINES[line_code], shift=shift,
                production_start=prod_start, production_end=prod_end,
                total_input_kg=float(row["total_input_kg"]),
                gross_output_kg=float(row["gross_output_kg"]),
                scrap_wastage_kg=float(row.get("scrap_wastage_kg") or 0),
                status=BatchStatus.APPROVED.value, created_by=user_id, approved_by=user_id
            )
            self.batch_repo.add(batch)
            self.batch_repo.db.add(QualityTest(
                batch_id=batch.id, tested_at=tested_at,
                moisture_pct=float(raw_moisture),
                core_temp_c=float(row.get("core_temp_c") or -18.0),
                rejected_output_kg=float(row.get("rejected_output_kg") or 0.0),
                is_late_entry=is_late, result="PASS"
            ))
            imported_count += 1

        self.batch_repo.db.commit()
        return ImportValidationReport(
            total_rows=total_rows, imported_count=imported_count,
            rejected_count=rejected_count, warning_count=warning_count, issues=issues
        )
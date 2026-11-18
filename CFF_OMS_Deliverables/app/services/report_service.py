import csv, io
from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel
from app.domain.models import Batch

class BatchKPIRow(BaseModel):
    canonical_batch_key: str
    input_kg: float
    gross_output_kg: float
    scrap_wastage_kg: float
    qc_rejected_kg: float
    net_good_output_kg: float
    process_yield_pct: float
    wastage_pct: float
    quality_rejection_rate_pct: float

class PlantKPISummary(BaseModel):
    total_input_kg: float
    total_gross_output_kg: float
    total_scrap_wastage_kg: float
    total_qc_rejected_kg: float
    total_net_good_output_kg: float
    overall_process_yield_pct: float
    overall_wastage_pct: float
    overall_quality_rejection_rate_pct: float
    rows: List[BatchKPIRow]

class KPICalculator:
    @staticmethod
    def compute_batch_kpi(batch: Batch) -> BatchKPIRow:
        qc_rej = batch.quality_test.rejected_output_kg if batch.quality_test else 0.0
        net_good = batch.gross_output_kg - qc_rej
        return BatchKPIRow(
            canonical_batch_key=batch.canonical_batch_key,
            input_kg=batch.total_input_kg,
            gross_output_kg=batch.gross_output_kg,
            scrap_wastage_kg=batch.scrap_wastage_kg,
            qc_rejected_kg=qc_rej,
            net_good_output_kg=round(net_good, 2),
            process_yield_pct=round((net_good / batch.total_input_kg) * 100.0, 2),
            wastage_pct=round((batch.scrap_wastage_kg / batch.total_input_kg) * 100.0, 2),
            quality_rejection_rate_pct=round((qc_rej / batch.gross_output_kg) * 100.0, 2)
        )

class ReportExportStrategy(ABC):
    """Design Pattern 2: Strategy Pattern for interchangeable report formats (CSV vs PDF)."""
    @abstractmethod
    def export(self, summary: PlantKPISummary) -> bytes:
        pass
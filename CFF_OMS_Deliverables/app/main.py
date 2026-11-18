from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.domain.models import BatchStatus, User
from app.repositories.batch_repo import BatchRepository, AuditRepository
from app.services.import_service import HistoricalImportService
from app.services.report_service import KPICalculator, CSVExportStrategy, SimplePDFExportStrategy
from app.services.batch_service import BatchWorkflowService, NotificationGateway

app = FastAPI(title="Chennai Frozen Foods Operations Management System (CFF-OMS)", version="2.4.0")

@app.post("/api/v1/imports/historical-csv")
async def import_historical_csv(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_supervisor)):
    content = (await file.read()).decode("utf-8")
    service = HistoricalImportService(BatchRepository(db), AuditRepository(db))
    return service.import_csv(content, user_id=user.id)

@app.post("/api/v1/batches/{batch_id}/workflow")
def transition_batch(batch_id: int, target_status: BatchStatus, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = BatchWorkflowService(BatchRepository(db), AuditRepository(db), NotificationGateway())
    try:
        return service.transition_status(batch_id, target_status, user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

@app.get("/api/v1/reports/kpi")
def export_kpi_report(format: str = Query("json", enum=["json", "csv", "pdf"]), db: Session = Depends(get_db)):
    batches = BatchRepository(db).list_approved_batches()
    summary = KPICalculator.compute_summary(batches)
    if format == "json":
        return summary
    strategy = CSVExportStrategy() if format == "csv" else SimplePDFExportStrategy()
    return Response(content=strategy.export(summary), media_type=strategy.media_type)
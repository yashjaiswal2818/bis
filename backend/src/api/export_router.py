from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any
from src.procurement.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Export"])

class ExportRequest(BaseModel):
    audit_result: Dict[str, Any]
    filename: str = "Tender_Audit.pdf"

@router.post("/export/pdf")
async def export_pdf(request: ExportRequest):
    try:
        pdf_buffer = ReportService.generate_audit_pdf(request.audit_result, request.filename)
        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{request.filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.practice import Practice
from app.models.contract import Contract
from app.services.comparison import compare_contract_rates
from app.services.report import generate_report_html, generate_report_pdf

router = APIRouter()


@router.post("/{contract_id}/compare")
def run_comparison(contract_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contract = (
        db.query(Contract).join(Practice)
        .filter(Contract.id == contract_id, Practice.owner_id == user.id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    results = compare_contract_rates(contract_id, db)
    return results


@router.get("/{contract_id}/html", response_class=HTMLResponse)
def get_report_html(contract_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contract = (
        db.query(Contract).join(Practice)
        .filter(Contract.id == contract_id, Practice.owner_id == user.id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return generate_report_html(contract_id, db)


@router.get("/{contract_id}/pdf")
def get_report_pdf(contract_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contract = (
        db.query(Contract).join(Practice)
        .filter(Contract.id == contract_id, Practice.owner_id == user.id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    pdf_bytes = generate_report_pdf(contract_id, db)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=payeriq-report-{contract_id}.pdf"},
    )

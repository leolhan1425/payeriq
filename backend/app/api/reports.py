from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, ALGORITHM
from app.core.config import settings
from app.models.user import User
from app.models.practice import Practice
from app.models.contract import Contract
from app.services.comparison import compare_contract_rates
from app.services.report import generate_report_html, generate_report_pdf

router = APIRouter()


def _auth_user(token: str, db: Session) -> User:
    """Authenticate user from a query-string JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


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
def get_report_pdf(contract_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    """PDF download — auth via query-string token (window.open can't set headers)."""
    user = _auth_user(token, db)
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

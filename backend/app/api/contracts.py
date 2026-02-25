import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.practice import Practice
from app.models.contract import Contract, ContractStatus
from app.schemas.contract import ContractResponse
from app.services.extraction import extract_rates_from_pdf

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


@router.post("", response_model=ContractResponse)
async def upload_contract(
    background_tasks: BackgroundTasks,
    practice_id: int = Form(...),
    payer_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    practice = db.query(Practice).filter(Practice.id == practice_id, Practice.owner_id == user.id).first()
    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")

    # Save file
    ext = Path(file.filename or "contract.pdf").suffix
    filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / filename
    UPLOAD_DIR.mkdir(exist_ok=True)
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    contract = Contract(
        payer_name=payer_name,
        file_path=str(filepath),
        status=ContractStatus.extracting,
        practice_id=practice_id,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    background_tasks.add_task(extract_rates_from_pdf, contract.id)
    return ContractResponse.model_validate(contract)


@router.get("", response_model=list[ContractResponse])
def list_contracts(
    practice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    practice = db.query(Practice).filter(Practice.id == practice_id, Practice.owner_id == user.id).first()
    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")
    return [ContractResponse.model_validate(c) for c in practice.contracts]


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contract = (
        db.query(Contract)
        .join(Practice)
        .filter(Contract.id == contract_id, Practice.owner_id == user.id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return ContractResponse.model_validate(contract)

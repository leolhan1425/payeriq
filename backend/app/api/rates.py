from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.practice import Practice
from app.models.contract import Contract
from app.models.contract_rate import ContractRate
from app.schemas.contract import ContractRateResponse, ContractRateUpdate

router = APIRouter()


@router.get("/contract/{contract_id}", response_model=list[ContractRateResponse])
def list_rates(contract_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contract = (
        db.query(Contract).join(Practice)
        .filter(Contract.id == contract_id, Practice.owner_id == user.id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return [ContractRateResponse.model_validate(r) for r in contract.rates]


@router.put("/{rate_id}", response_model=ContractRateResponse)
def update_rate(
    rate_id: int,
    body: ContractRateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rate = (
        db.query(ContractRate)
        .join(Contract).join(Practice)
        .filter(ContractRate.id == rate_id, Practice.owner_id == user.id)
        .first()
    )
    if not rate:
        raise HTTPException(status_code=404, detail="Rate not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(rate, field, value)
    db.commit()
    db.refresh(rate)
    return ContractRateResponse.model_validate(rate)


@router.delete("/{rate_id}")
def delete_rate(rate_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rate = (
        db.query(ContractRate)
        .join(Contract).join(Practice)
        .filter(ContractRate.id == rate_id, Practice.owner_id == user.id)
        .first()
    )
    if not rate:
        raise HTTPException(status_code=404, detail="Rate not found")
    db.delete(rate)
    db.commit()
    return {"ok": True}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.practice import Practice
from app.models.contract import Contract
from app.services.negotiation import generate_negotiation_letter

router = APIRouter()


@router.post("/{contract_id}/letter")
def create_negotiation_letter(
    contract_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contract = (
        db.query(Contract).join(Practice)
        .filter(Contract.id == contract_id, Practice.owner_id == user.id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return generate_negotiation_letter(contract_id, db)

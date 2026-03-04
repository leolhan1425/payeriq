from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.practice import Practice
from app.models.medicare import ZipLocality
from app.schemas.practice import PracticeCreate, PracticeResponse

router = APIRouter()


@router.post("", response_model=PracticeResponse)
def create_practice(body: PracticeCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Resolve GPCI locality + carrier from ZIP
    zl = db.query(ZipLocality).filter(ZipLocality.zip_code == body.zip_code).first()
    locality = zl.locality if zl else None
    carrier = zl.carrier if zl else None

    practice = Practice(name=body.name, zip_code=body.zip_code, gpci_locality=locality, gpci_carrier=carrier, specialty=body.specialty, owner_id=user.id)
    db.add(practice)
    db.commit()
    db.refresh(practice)
    return PracticeResponse.model_validate(practice)


@router.get("", response_model=list[PracticeResponse])
def list_practices(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [PracticeResponse.model_validate(p) for p in db.query(Practice).filter(Practice.owner_id == user.id).all()]


@router.get("/{practice_id}", response_model=PracticeResponse)
def get_practice(practice_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    practice = db.query(Practice).filter(Practice.id == practice_id, Practice.owner_id == user.id).first()
    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")
    return PracticeResponse.model_validate(practice)

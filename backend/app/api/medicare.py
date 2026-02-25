"""Admin endpoints for Medicare data loading."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.medicare import MedicareRate, GPCILocality, ZipLocality
from app.services.medicare_loader import load_rvu_from_csv, load_gpci_from_csv, load_zip_crosswalk

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@router.post("/load-rvu")
async def upload_rvu(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    DATA_DIR.mkdir(exist_ok=True)
    filepath = DATA_DIR / "rvu.csv"
    with open(filepath, "wb") as f:
        f.write(await file.read())
    db.query(MedicareRate).delete()
    count = load_rvu_from_csv(filepath, db)
    return {"loaded": count}


@router.post("/load-gpci")
async def upload_gpci(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    DATA_DIR.mkdir(exist_ok=True)
    filepath = DATA_DIR / "gpci.csv"
    with open(filepath, "wb") as f:
        f.write(await file.read())
    db.query(GPCILocality).delete()
    count = load_gpci_from_csv(filepath, db)
    return {"loaded": count}


@router.post("/load-zip")
async def upload_zip_crosswalk(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    DATA_DIR.mkdir(exist_ok=True)
    filepath = DATA_DIR / "zip_crosswalk.csv"
    with open(filepath, "wb") as f:
        f.write(await file.read())
    db.query(ZipLocality).delete()
    count = load_zip_crosswalk(filepath, db)
    return {"loaded": count}


@router.get("/stats")
def medicare_stats(db: Session = Depends(get_db)):
    return {
        "rvu_count": db.query(MedicareRate).count(),
        "gpci_count": db.query(GPCILocality).count(),
        "zip_count": db.query(ZipLocality).count(),
    }

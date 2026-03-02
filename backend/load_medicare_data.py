"""One-time script to load CMS Medicare data from local files."""
import sys
sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.medicare import MedicareRate, GPCILocality, ZipLocality
from app.services.medicare_loader import load_rvu_from_csv, load_gpci_from_csv, load_zip_crosswalk

db = SessionLocal()

print("Clearing existing data...")
db.query(MedicareRate).delete()
db.query(GPCILocality).delete()
db.query(ZipLocality).delete()
db.commit()

print("Loading RVU data...")
rvu_count = load_rvu_from_csv("data/PPRRVU25_JAN.csv", db)
print(f"  Loaded {rvu_count} RVU records")

print("Loading GPCI data...")
gpci_count = load_gpci_from_csv("data/GPCI2025.csv", db)
print(f"  Loaded {gpci_count} GPCI locality records")

print("Loading ZIP crosswalk...")
zip_count = load_zip_crosswalk("data/ZIP5_DEC2025_FINAL.txt", db)
print(f"  Loaded {zip_count} ZIP-locality records")

db.close()
print("Done!")

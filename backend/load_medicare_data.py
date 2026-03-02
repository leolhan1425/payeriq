"""One-time script to load CMS Medicare data from local files."""
import sys
sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.medicare import MedicareRate, GPCILocality, ZipLocality, LabFeeSchedule, Utilization, CommercialBenchmark
from app.services.medicare_loader import (
    load_rvu_from_csv, load_gpci_from_csv, load_zip_crosswalk,
    load_clfs_from_csv, load_utilization_from_csv, load_commercial_from_json,
)

db = SessionLocal()

# Check what to load based on CLI args
load_all = len(sys.argv) == 1
targets = set(sys.argv[1:]) if len(sys.argv) > 1 else set()

if load_all or "rvu" in targets:
    print("Clearing + loading RVU data...")
    db.query(MedicareRate).delete()
    db.commit()
    count = load_rvu_from_csv("data/PPRRVU25_JAN.csv", db)
    print(f"  Loaded {count} RVU records")

if load_all or "gpci" in targets:
    print("Clearing + loading GPCI data...")
    db.query(GPCILocality).delete()
    db.commit()
    count = load_gpci_from_csv("data/GPCI2025.csv", db)
    print(f"  Loaded {count} GPCI locality records")

if load_all or "zip" in targets:
    print("Clearing + loading ZIP crosswalk...")
    db.query(ZipLocality).delete()
    db.commit()
    count = load_zip_crosswalk("data/ZIP5_DEC2025_FINAL.txt", db)
    print(f"  Loaded {count} ZIP-locality records")

if load_all or "clfs" in targets:
    print("Clearing + loading Clinical Lab Fee Schedule...")
    db.query(LabFeeSchedule).delete()
    db.commit()
    count = load_clfs_from_csv("data/CLFS 2025 Q4V1.csv", db)
    print(f"  Loaded {count} CLFS records")

if load_all or "util" in targets:
    print("Clearing + loading utilization data (this takes ~60s)...")
    db.query(Utilization).delete()
    db.commit()
    count = load_utilization_from_csv("data/utilization_2024.csv", db)
    print(f"  Loaded {count} utilization records")

if load_all or "commercial" in targets:
    print("Clearing + loading commercial benchmark data...")
    db.query(CommercialBenchmark).delete()
    db.commit()
    count = load_commercial_from_json("data/tic_commercial_rates.json", db)
    print(f"  Loaded {count} commercial benchmark records")

db.close()
print("Done!")

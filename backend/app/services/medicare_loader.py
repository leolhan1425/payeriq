"""Download and parse CMS Medicare data files."""
import csv
import io
import logging
import zipfile
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.medicare import MedicareRate, GPCILocality, ZipLocality

logger = logging.getLogger(__name__)

# CMS data URLs (2025)
RVU_URL = "https://www.cms.gov/medicaremedicare-fee-service-paymentphyslookuprvu2025/pprrvu25-jan"
GPCI_URL = "https://www.cms.gov/medicaremedicare-fee-service-paymentphyslookuprvu2025/gpci2025"

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def load_rvu_from_csv(filepath: str | Path, db: Session) -> int:
    """Parse PFS RVU CSV file and load into database.

    The file has a 10-row preamble before the header row.
    """
    with open(filepath, "r", encoding="utf-8-sig") as f:
        # Skip preamble rows
        for _ in range(10):
            next(f)
        reader = csv.DictReader(f)
        count = 0
        batch = []
        for row in reader:
            cpt = row.get("HCPCS", "").strip() or row.get("CPT/HCPCS", "").strip()
            if not cpt:
                continue
            rate = MedicareRate(
                cpt_code=cpt,
                modifier=row.get("MOD", "").strip() or None,
                description=row.get("DESCRIPTION", "").strip() or None,
                work_rvu=_float(row.get("WORK RVU", 0)),
                pe_rvu_facility=_float(row.get("FACILITY PE RVU", 0)),
                pe_rvu_nonfacility=_float(row.get("NON-FACILITY PE RVU", 0)),
                mp_rvu=_float(row.get("MP RVU", 0)),
                status_code=row.get("STATUS CODE", "").strip() or None,
            )
            batch.append(rate)
            count += 1
            if len(batch) >= 1000:
                db.bulk_save_objects(batch)
                batch = []
        if batch:
            db.bulk_save_objects(batch)
        db.commit()
        logger.info("Loaded %d RVU records", count)
        return count


def load_gpci_from_csv(filepath: str | Path, db: Session) -> int:
    """Parse GPCI CSV file and load into database."""
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            locality_num = row.get("LOCALITY", "").strip() or row.get("LOCALITY NUMBER", "").strip()
            if not locality_num:
                continue
            gpci = GPCILocality(
                mac=row.get("MAC", "").strip() or None,
                locality_number=locality_num,
                locality_name=row.get("LOCALITY NAME", "").strip() or "",
                state=row.get("STATE", "").strip() or None,
                work_gpci=_float(row.get("WORK GPCI", 1.0)),
                pe_gpci=_float(row.get("PE GPCI", 1.0)),
                mp_gpci=_float(row.get("MP GPCI", 1.0)),
            )
            db.add(gpci)
            count += 1
        db.commit()
        logger.info("Loaded %d GPCI locality records", count)
        return count


def load_zip_crosswalk(filepath: str | Path, db: Session) -> int:
    """Parse ZIP-to-locality crosswalk (fixed-width or CSV)."""
    with open(filepath, "r", encoding="utf-8-sig") as f:
        first_line = f.readline()
        f.seek(0)

        if "," in first_line or "\t" in first_line:
            # CSV format
            reader = csv.DictReader(f)
            count = 0
            batch = []
            for row in reader:
                zc = row.get("ZIP CODE", "").strip() or row.get("ZIP", "").strip()
                if not zc:
                    continue
                zl = ZipLocality(
                    zip_code=zc,
                    carrier=row.get("CARRIER", "").strip() or None,
                    locality=row.get("LOCALITY", "").strip() or "",
                    state=row.get("STATE", "").strip() or None,
                )
                batch.append(zl)
                count += 1
                if len(batch) >= 1000:
                    db.bulk_save_objects(batch)
                    batch = []
            if batch:
                db.bulk_save_objects(batch)
            db.commit()
        else:
            # Fixed-width format: ZIP(5) CARRIER(5) LOCALITY(2) STATE(2)
            count = 0
            batch = []
            for line in f:
                line = line.rstrip("\n")
                if len(line) < 12:
                    continue
                zl = ZipLocality(
                    zip_code=line[0:5].strip(),
                    carrier=line[5:10].strip() or None,
                    locality=line[10:12].strip(),
                    state=line[12:14].strip() if len(line) >= 14 else None,
                )
                batch.append(zl)
                count += 1
                if len(batch) >= 1000:
                    db.bulk_save_objects(batch)
                    batch = []
            if batch:
                db.bulk_save_objects(batch)
            db.commit()

        logger.info("Loaded %d ZIP-locality records", count)
        return count


def _float(val) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0

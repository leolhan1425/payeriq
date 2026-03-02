"""Download and parse CMS Medicare data files."""
import csv
import io
import logging
import zipfile
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from collections import defaultdict

from app.core.database import SessionLocal
from app.models.medicare import MedicareRate, GPCILocality, ZipLocality, LabFeeSchedule, Utilization, CommercialBenchmark

logger = logging.getLogger(__name__)

# CMS data URLs (2025)
RVU_URL = "https://www.cms.gov/medicaremedicare-fee-service-paymentphyslookuprvu2025/pprrvu25-jan"
GPCI_URL = "https://www.cms.gov/medicaremedicare-fee-service-paymentphyslookuprvu2025/gpci2025"

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def load_rvu_from_csv(filepath: str | Path, db: Session) -> int:
    """Parse PFS RVU CSV file and load into database.

    The file has a 9-row preamble, header on row 10, data from row 11.
    Columns have duplicate names so we parse by position:
      0:HCPCS, 1:MOD, 2:DESCRIPTION, 3:STATUS CODE, 4:(unused),
      5:WORK RVU, 6:NON-FAC PE RVU, 7:(NA ind), 8:FAC PE RVU, 9:(NA ind),
      10:MP RVU, ...
    """
    with open(filepath, "r", encoding="utf-8-sig") as f:
        # Skip 10 rows (9 preamble + 1 header)
        for _ in range(10):
            next(f)
        reader = csv.reader(f)
        count = 0
        batch = []
        for cols in reader:
            if len(cols) < 11:
                continue
            cpt = cols[0].strip()
            if not cpt:
                continue
            rate = MedicareRate(
                cpt_code=cpt,
                modifier=cols[1].strip() or None,
                description=cols[2].strip() or None,
                status_code=cols[3].strip() or None,
                work_rvu=_float(cols[5]),
                pe_rvu_nonfacility=_float(cols[6]),
                pe_rvu_facility=_float(cols[8]),
                mp_rvu=_float(cols[10]),
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
    """Parse GPCI CSV file and load into database.

    File has a 2-row preamble (title + blank), then header row with columns:
    Medicare Administrative Contractor (MAC), State, Locality Number,
    Locality Name, 2025 PW GPCI (with 1.0 Floor), 2025 PE GPCI, 2025 MP GPCI
    """
    with open(filepath, "r", encoding="utf-8-sig") as f:
        # Skip 2 preamble rows
        for _ in range(2):
            next(f)
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            locality_num = row.get("Locality Number", "").strip()
            if not locality_num:
                continue
            gpci = GPCILocality(
                mac=row.get("Medicare Administrative Contractor (MAC)", "").strip() or None,
                locality_number=locality_num,
                locality_name=row.get("Locality Name", "").strip() or "",
                state=row.get("State", "").strip() or None,
                work_gpci=_float(row.get("2025 PW GPCI (with 1.0 Floor)", 1.0)),
                pe_gpci=_float(row.get("2025 PE GPCI", 1.0)),
                mp_gpci=_float(row.get("2025 MP GPCI", 1.0)),
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
            # Fixed-width format per ZIP5lyout.txt:
            # State(1-2), ZIP(3-7), Carrier(8-12), Locality(13-14)
            count = 0
            batch = []
            for line in f:
                line = line.rstrip("\n")
                if len(line) < 14:
                    continue
                zl = ZipLocality(
                    state=line[0:2].strip() or None,
                    zip_code=line[2:7].strip(),
                    carrier=line[7:12].strip() or None,
                    locality=line[12:14].strip(),
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


def load_clfs_from_csv(filepath: str | Path, db: Session) -> int:
    """Parse Clinical Lab Fee Schedule CSV.

    File has a 4-row preamble, then header:
    YEAR,HCPCS,MOD,EFF_DATE,INDICATOR,RATE,SHORTDESC,LONGDESC,EXTENDED LONGDESC
    """
    with open(filepath, "r", encoding="cp1252") as f:
        for _ in range(4):
            next(f)
        reader = csv.DictReader(f)
        count = 0
        batch = []
        for row in reader:
            code = row.get("HCPCS", "").strip()
            rate_val = _float(row.get("RATE", 0))
            if not code or rate_val <= 0:
                continue
            rec = LabFeeSchedule(
                cpt_code=code,
                modifier=row.get("MOD", "").strip() or None,
                rate=rate_val,
                description=row.get("SHORTDESC", "").strip() or row.get("LONGDESC", "").strip() or None,
            )
            batch.append(rec)
            count += 1
            if len(batch) >= 1000:
                db.bulk_save_objects(batch)
                batch = []
        if batch:
            db.bulk_save_objects(batch)
        db.commit()
        logger.info("Loaded %d CLFS records", count)
        return count


def load_utilization_from_csv(filepath: str | Path, db: Session) -> int:
    """Parse Medicare PSPS utilization CSV and aggregate to national totals per HCPCS.

    The raw file has ~14M rows at carrier/locality/specialty level.
    We aggregate to one row per HCPCS code with total services, allowed, payment.
    """
    logger.info("Aggregating utilization data (this may take a minute)...")
    agg = defaultdict(lambda: {"services": 0, "allowed": 0.0, "payment": 0.0})

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("HCPCS_CD", "").strip()
            if not code:
                continue
            services = _int(row.get("PSPS_SUBMITTED_SERVICE_CNT", 0))
            allowed = _float(row.get("PSPS_ALLOWED_CHARGE_AMT", 0))
            payment = _float(row.get("PSPS_NCH_PAYMENT_AMT", 0))
            agg[code]["services"] += services
            agg[code]["allowed"] += allowed
            agg[code]["payment"] += payment

    count = 0
    batch = []
    for code, vals in agg.items():
        total_svc = vals["services"]
        rec = Utilization(
            cpt_code=code,
            total_services=total_svc,
            total_allowed=round(vals["allowed"], 2),
            total_payment=round(vals["payment"], 2),
            avg_allowed=round(vals["allowed"] / total_svc, 2) if total_svc > 0 else 0.0,
        )
        batch.append(rec)
        count += 1
        if len(batch) >= 1000:
            db.bulk_save_objects(batch)
            batch = []
    if batch:
        db.bulk_save_objects(batch)
    db.commit()
    logger.info("Loaded %d utilization records (aggregated from PSPS)", count)
    return count


def load_commercial_from_json(filepath: str | Path, db: Session) -> int:
    """Load commercial benchmark rates from DoltHub TiC JSON export."""
    import json
    with open(filepath, "r") as f:
        rows = json.load(f)
    count = 0
    for row in rows:
        code = row.get("billing_code", "").strip()
        avg = _float(row.get("avg_rate", 0))
        if not code or avg <= 0:
            continue
        rec = CommercialBenchmark(
            cpt_code=code,
            avg_rate=avg,
            std_rate=_float(row.get("std_rate")) if row.get("std_rate") else None,
            min_rate=_float(row.get("min_rate")) if row.get("min_rate") else None,
            max_rate=_float(row.get("max_rate")) if row.get("max_rate") else None,
            sample_size=_int(row.get("n", 0)),
            source="UHC-TiC",
        )
        db.add(rec)
        count += 1
    db.commit()
    logger.info("Loaded %d commercial benchmark records", count)
    return count


def _int(val) -> int:
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return 0


def _float(val) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0

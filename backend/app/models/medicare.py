from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

CONVERSION_FACTOR = 32.3465


class MedicareRate(Base):
    """RVU data from CMS PFS file."""
    __tablename__ = "medicare_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    cpt_code: Mapped[str] = mapped_column(String(10), index=True)
    modifier: Mapped[str | None] = mapped_column(String(10), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    work_rvu: Mapped[float] = mapped_column(Float, default=0.0)
    pe_rvu_facility: Mapped[float] = mapped_column(Float, default=0.0)
    pe_rvu_nonfacility: Mapped[float] = mapped_column(Float, default=0.0)
    mp_rvu: Mapped[float] = mapped_column(Float, default=0.0)
    status_code: Mapped[str | None] = mapped_column(String(5), nullable=True)


class GPCILocality(Base):
    """GPCI values by locality."""
    __tablename__ = "gpci_localities"

    id: Mapped[int] = mapped_column(primary_key=True)
    mac: Mapped[str | None] = mapped_column(String(10), nullable=True)
    locality_number: Mapped[str] = mapped_column(String(10), index=True)
    locality_name: Mapped[str] = mapped_column(String(255))
    state: Mapped[str | None] = mapped_column(String(5), nullable=True)
    work_gpci: Mapped[float] = mapped_column(Float)
    pe_gpci: Mapped[float] = mapped_column(Float)
    mp_gpci: Mapped[float] = mapped_column(Float)


class ZipLocality(Base):
    """ZIP code to GPCI locality crosswalk."""
    __tablename__ = "zip_localities"

    id: Mapped[int] = mapped_column(primary_key=True)
    zip_code: Mapped[str] = mapped_column(String(10), index=True)
    carrier: Mapped[str | None] = mapped_column(String(10), nullable=True)
    locality: Mapped[str] = mapped_column(String(10))
    state: Mapped[str | None] = mapped_column(String(5), nullable=True)


class LabFeeSchedule(Base):
    """Clinical Laboratory Fee Schedule (CLFS) rates."""
    __tablename__ = "lab_fee_schedule"

    id: Mapped[int] = mapped_column(primary_key=True)
    cpt_code: Mapped[str] = mapped_column(String(10), index=True)
    modifier: Mapped[str | None] = mapped_column(String(10), nullable=True)
    rate: Mapped[float] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Utilization(Base):
    """National Medicare utilization data — aggregated per HCPCS code."""
    __tablename__ = "utilization"

    id: Mapped[int] = mapped_column(primary_key=True)
    cpt_code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    total_services: Mapped[int] = mapped_column(Integer, default=0)
    total_allowed: Mapped[float] = mapped_column(Float, default=0.0)
    total_payment: Mapped[float] = mapped_column(Float, default=0.0)
    avg_allowed: Mapped[float] = mapped_column(Float, default=0.0)


class CommercialBenchmark(Base):
    """Commercial payer negotiated rates from Transparency in Coverage data."""
    __tablename__ = "commercial_benchmarks"

    id: Mapped[int] = mapped_column(primary_key=True)
    cpt_code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    avg_rate: Mapped[float] = mapped_column(Float)
    std_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(50), default="UHC-TiC")

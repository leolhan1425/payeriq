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

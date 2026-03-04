from datetime import datetime

from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Date, Enum, Boolean, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class ContractStatus(str, enum.Enum):
    uploading = "uploading"
    extracting = "extracting"
    review = "review"
    compared = "compared"
    error = "error"


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    payer_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus), default=ContractStatus.uploading
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    practice_id: Mapped[int] = mapped_column(ForeignKey("practices.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Contract term fields (populated by two-pass extraction)
    effective_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    fee_schedule_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    medicare_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    auto_renewal: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    unilateral_amendment: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    termination_notice_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lesser_of_clause: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    timely_filing_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_extraction: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    practice: Mapped["Practice"] = relationship(back_populates="contracts")
    rates: Mapped[list["ContractRate"]] = relationship(back_populates="contract", cascade="all, delete-orphan")

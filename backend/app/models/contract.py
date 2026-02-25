from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum, Text, func
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

    practice: Mapped["Practice"] = relationship(back_populates="contracts")
    rates: Mapped[list["ContractRate"]] = relationship(back_populates="contract", cascade="all, delete-orphan")

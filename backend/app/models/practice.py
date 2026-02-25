from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Practice(Base):
    __tablename__ = "practices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    zip_code: Mapped[str] = mapped_column(String(10))
    gpci_locality: Mapped[str | None] = mapped_column(String(10), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="practices")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="practice")

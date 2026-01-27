from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from datetime import datetime

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role: Mapped[str] = mapped_column(String)  # 'patient', 'doctor'
    full_name: Mapped[str] = mapped_column(String, nullable=True)

class Consultation(Base):
    __tablename__ = "consultations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), nullable=True)
    
    # Статусы: 'queued' (в очереди), 'active' (идет), 'closed' (завершена)
    status: Mapped[str] = mapped_column(String, default="queued", index=True)
    symptoms: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
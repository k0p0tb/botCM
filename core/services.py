from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from database.models import User, Consultation
from time import *

class ConsultationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user_if_not_exists(self, telegram_id: int, role: str, name: str):
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id, role=role, full_name=name)
            self.session.add(user)
            await self.session.commit()
        return user

    async def add_to_queue(self, patient_id: int, symptoms: str) -> int:
        consultation = Consultation(patient_id=patient_id, symptoms=symptoms, status="queued")
        self.session.add(consultation)
        await self.session.commit()
        return consultation.id

    async def get_queue(self):
        """Возвращает список свободных заявок"""
        query = select(Consultation).where(Consultation.status == "queued")
        result = await self.session.execute(query)
        return result.scalars().all()

    async def assign_doctor(self, consultation_id: int, doctor_id: int) -> bool:
        """
        АТОМАРНАЯ ОПЕРАЦИЯ:
        Пытаемся назначить врача ТОЛЬКО если статус всё еще 'queued'.
        Возвращает True, если успешно, False — если кто-то успел раньше.
        """
        stmt = (
            update(Consultation)
            .where(
                and_(
                    Consultation.id == consultation_id,
                    Consultation.status == "queued"  # <-- Защита от гонки
                )
            )
            .values(doctor_id=doctor_id, status="active")
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0 # 1 если успешно обновили, 0 если нет
    # ... (предыдущие методы остаются без изменений)

    async def get_active_partner(self, user_id: int) -> int | None:
        """
        Ищет активную консультацию и возвращает ID собеседника.
        Если user_id - пациент, вернет ID врача.
        Если user_id - врач, вернет ID пациента.
        """
        query = select(Consultation).where(
            and_(
                (Consultation.patient_id == user_id) | (Consultation.doctor_id == user_id),
                Consultation.status == "active"
            )
        )
        result = await self.session.execute(query)
        consultation = result.scalar_one_or_none()

        if not consultation:
            return None

        # Возвращаем ID "другого" участника
        if consultation.patient_id == user_id:
            return consultation.doctor_id
        return consultation.patient_id

    async def finish_consultation(self, user_id: int) -> int | None:
        """
        Завершает активную консультацию для пользователя.
        Возвращает ID собеседника, чтобы уведомить его о конце чата.
        """
        # 1. Находим собеседника
        partner_id = await self.get_active_partner(user_id)
        if not partner_id:
            return None

        # 2. Закрываем консультацию в БД
        stmt = (
            update(Consultation)
            .where(
                and_(
                    (Consultation.patient_id == user_id) | (Consultation.doctor_id == user_id),
                    Consultation.status == "active"
                )
            )
            .values(status="closed", created_at=datetime.utcnow()) # Можно добавить поле closed_at в модель, но пока так
        )
        await self.session.execute(stmt)
        await self.session.commit()
        
        return partner_id
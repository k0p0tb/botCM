from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from database.models import User, Consultation
from datetime import datetime

class ConsultationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user_if_not_exists(self, telegram_id: int, username: str, role: str, full_name: str):
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id, username=username, role=role, full_name=full_name)
            self.session.add(user)
            await self.session.commit()
        else:
            if user.username != username or user.full_name != full_name:
                user.username = username
                user.full_name = full_name
                await self.session.commit()
        return user

    async def get_user_by_username(self, username: str) -> User | None:
        if not username: return None
        clean_username = username.replace("@", "").strip()
        query = select(User).where(func.lower(User.username) == clean_username.lower())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def set_user_role(self, telegram_id: int, new_role: str):
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.role = new_role
        else:
            user = User(telegram_id=telegram_id, username=None, role=new_role, full_name="Unknown")
            self.session.add(user)
        await self.session.commit()

    # --- НОВЫЕ МЕТОДЫ ДЛЯ ЗАВЕРШЕНИЯ ---

    async def request_finish(self, user_id: int) -> int | None:
        """Врач запросил завершение. Ставим метку времени."""
        # Ищем активную консультацию врача
        query = select(Consultation).where(
            and_(Consultation.doctor_id == user_id, Consultation.status == "active")
        )
        result = await self.session.execute(query)
        consultation = result.scalar_one_or_none()
        
        if consultation:
            consultation.finish_requested_at = datetime.utcnow()
            await self.session.commit()
            return consultation.patient_id
        return None

    async def cancel_finish_request(self, user_id: int):
        """Пациент написал сообщение или нажал НЕТ -> Снимаем метку."""
        stmt = (
            update(Consultation)
            .where(
                and_(
                    (Consultation.patient_id == user_id) | (Consultation.doctor_id == user_id),
                    Consultation.status == "active"
                )
            )
            .values(finish_requested_at=None)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_consultation_status(self, consultation_id: int):
        """Получаем текущие данные (для проверки таймера)"""
        result = await self.session.execute(select(Consultation).where(Consultation.id == consultation_id))
        return result.scalar_one_or_none()

    # ------------------------------------

    async def add_to_queue(self, patient_id: int, symptoms: str) -> int:
        consultation = Consultation(patient_id=patient_id, symptoms=symptoms, status="queued")
        self.session.add(consultation)
        await self.session.commit()
        return consultation.id

    async def get_queue(self):
        query = select(Consultation).where(Consultation.status == "queued")
        result = await self.session.execute(query)
        return result.scalars().all()

    async def assign_doctor(self, consultation_id: int, doctor_id: int) -> str:
        # Проверка занятости врача
        busy_query = select(Consultation).where(and_(Consultation.doctor_id == doctor_id, Consultation.status == "active"))
        result = await self.session.execute(busy_query)
        if result.scalar_one_or_none():
            return "busy"

        stmt = update(Consultation).where(and_(Consultation.id == consultation_id, Consultation.status == "queued")).values(doctor_id=doctor_id, status="active")
        result = await self.session.execute(stmt)
        await self.session.commit()
        return "success" if result.rowcount > 0 else "taken"

    async def get_active_partner(self, user_id: int) -> int | None:
        query = select(Consultation).where(and_((Consultation.patient_id == user_id) | (Consultation.doctor_id == user_id), Consultation.status == "active"))
        result = await self.session.execute(query)
        consultation = result.scalar_one_or_none()
        if not consultation: return None
        if consultation.patient_id == user_id: return consultation.doctor_id
        return consultation.patient_id

    async def finish_consultation(self, user_id: int) -> int | None:
        """Принудительное завершение"""
        partner_id = await self.get_active_partner(user_id)
        if not partner_id: return None
        
        stmt = update(Consultation).where(and_((Consultation.patient_id == user_id) | (Consultation.doctor_id == user_id), Consultation.status == "active")).values(status="closed", created_at=datetime.utcnow(), finish_requested_at=None)
        await self.session.execute(stmt)
        await self.session.commit()
        return partner_id
import os
from aiogram.filters import BaseFilter
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from core.services import ConsultationService

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        # Получаем ID из настроек
        admin_id_str = os.getenv("ADMIN_ID", "0")
        admin_id = int(admin_id_str)
        
        # Получаем ваш реальный ID
        user_id = message.from_user.id
        
        # ПЕЧАТАЕМ В КОНСОЛЬ (ДЛЯ ОТЛАДКИ)
        print(f"DEBUG: Ваш ID={user_id}, ID в настройках={admin_id}")

        return user_id == admin_id
    

class IsDoctor(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession) -> bool:
        # Админ автоматически считается врачом (для тестов), либо уберите 'or', если хотите разделять
        admin_id = int(os.getenv("ADMIN_ID", 0))
        if message.from_user.id == admin_id:
            return True

        service = ConsultationService(session)
        role = await service.get_user_role(message.from_user.id)
        return role == "doctor"
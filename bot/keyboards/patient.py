from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_start_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="📝 Начать консультацию", callback_data="start_triage")
        ],
        [
            InlineKeyboardButton(text="ℹ️ О проекте", callback_data="about_project")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_symptoms_keyboard():
    """Инлайн-кнопки (под сообщением) с выбором симптомов"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🤕 Головная боль", callback_data="Головная боль"),
                InlineKeyboardButton(text="🌡 Температура", callback_data="Температура")
            ],
            [
                InlineKeyboardButton(text="🤢 Тошнота", callback_data="Тошнота"),
                InlineKeyboardButton(text="🦴 Боль в суставах", callback_data="Боль в суставах")
            ],
            [
                InlineKeyboardButton(text="Другое", callback_data="Другое")
            ]
        ]
    )

def get_consultation_choice_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="👨‍⚕️ Нужен врач", callback_data="req_doctor"),
            InlineKeyboardButton(text="✅ Спасибо, не надо", callback_data="no_doctor")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
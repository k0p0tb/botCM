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

def get_consultation_choice_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="👨‍⚕️ Нужен врач", callback_data="req_doctor"),
            InlineKeyboardButton(text="✅ Спасибо, не надо", callback_data="no_doctor")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
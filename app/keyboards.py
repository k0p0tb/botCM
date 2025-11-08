from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.types import CallbackQuery

main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Врач", callback_data='doctor')],
    [InlineKeyboardButton(text="Пациент", callback_data='patient')]
])

reg_authorise = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Регистрация', callback_data='regist')],
    [InlineKeyboardButton(text="Авторизация", callback_data='authorise')]
])

telnum = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отправить номер', request_contact=True)]
], resize_keyboard=True)


consultation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Завершить консультацию", callback_data='end_consultation')]
])

admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Статистика", callback_data='admin_stats')],
    [InlineKeyboardButton(text="Управление пользователями", callback_data='admin_users')],
    [InlineKeyboardButton(text="Выйти", callback_data='admin_exit')]
])

accept_consultation = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Принять консультацию", callback_data='accept_consultation')],
    [InlineKeyboardButton(text="Отклонить", callback_data='reject_consultation')]
])

# Новая клавиатура для выбора консультации
consultation_choice = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Да, запросить консультацию", callback_data='request_consultation')],
    [InlineKeyboardButton(text="Нет, только предварительный диагноз", callback_data='no_consultation')]
])

# Добавьте в keyboards.py
consultation_start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Начать консультацию", callback_data='accept_consultation')],
    [InlineKeyboardButton(text="❌ Отклонить", callback_data='reject_consultation')]
])
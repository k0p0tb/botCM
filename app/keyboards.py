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

reg_end = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Регистрация завершена', callback_data='authorise')]
])
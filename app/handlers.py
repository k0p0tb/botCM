import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext


from app import keyboards as kb
from app import states as st

router = Router()

async def typing(message: Message):
    await message.bot.send_chat_action(chat_id=message.from_user.id, action=ChatAction.TYPING)

@router.message(F.text == 'check')
async def check(message: Message):
    await message.answer('na suka')

@router.message(CommandStart())
async def start(message: Message):
    await typing(message=message)
    await asyncio.sleep(0.35)
    await message.answer(text=f'Здравствуйте, {message.from_user.first_name}, это нейро-врач healthGPT,\nВыберите из списка ваше амплуа',
                         reply_markup=kb.main)
    
@router.callback_query(F.data == 'patient')
async def patient(callback: CallbackQuery, state: FSMContext):
    await state.set_state(st.AuthP.fio)
    await callback.answer(text='Скажите, как к вам обращаться')

@router.message(st.AuthP.fio)
async def auth_fio(message: Message, state: FSMContext):
    await state.update_data(fio = message.text)
    await state.set_state(st.AuthP.age)
    await message.answer(text='Скажите ваш год рождения')

@router.message(st.AuthP.age)
async def auth_age(message: Message, state: FSMContext):
    await state.update_data(age = message.text)
    data_patient = await state.get_data()
    await state.set_state(st.Appeal.appeal1)
    await message.answer(text= 'Скажите, что вас беспокоит?')

@router.message(st.Appeal.appeal1)
async def appeal_1(message: Message, state: FSMContext):
    await state.update_data(appeal1 = message.text)


@router.callback_query(F.data == 'doctor')
async def doc1(callback: CallbackQuery):
    await callback.message.edit_text(text='Если вы зарегистрированы, авторизуйтесь, в противном случае - зарегистрируйтесь', reply_markup=kb.reg_authorise)

@router.callback_query(F.data == 'regist')
async def RegD(callback: CallbackQuery):
    await callback.message.edit_text(text='Свяжитесь с дежурным администратором для регистрации\n @ALEXADLLL')

@router.callback_query(F.data == "authorise")
async def AuthDoc(callback: CallbackQuery, state: FSMContext):
    await state.set_state(st.AuthD.fio)
    await callback.message.edit_text(text="Введите ваше ФИО")

@router.message(st.AuthD.fio)
async def AuthDoc_fio(message: Message, state: FSMContext):
    await state.update_data(fio = message.text)
    await state.set_state(st.AuthD.number)
    await message.answer(text='Введите номер телефона', reply_markup=kb.telnum)


@router.message(st.AuthD.number, F.contact)
async def AuthDoc_num(message: Message, state: FSMContext):
    await state.update_data(number=message.contact.phone_number)
    data = await state.get_data()
    print(data)
    await state.clear()
    await message.answer(text=f"Авторизация завершена,\nВаше ФИО: {data['fio']},\nВаш номер телефона: {data["number"]}", reply_markup=ReplyKeyboardRemove())
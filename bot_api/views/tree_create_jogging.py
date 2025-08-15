from aiogram import Router, types
from aiogram.filters import Command

import logging
from aiogram import Bot, types, Dispatcher
from aiogram.filters import Command
from aiogram import types
import asyncio
import os
from dotenv import load_dotenv
from aiogram import F
from bot_api.set_path import set_path
import backend.session
from datepicker import DatePicker, DpCallback
from aiogram.filters.callback_data import CallbackQuery
from datetime import date, time
from bot_api.state import User
from aiogram.fsm.context import FSMContext


datepicker = DatePicker()


create_jogging_router = Router()



@create_jogging_router.message(User.CreateJoggingState.set_description)
async def set_title_jogging(message: types.Message, state: FSMContext):
    print('Шаг 3: Получение названия пробежки')
    await state.update_data(set_jogging_description=message.text)
    try:
        await message.answer(
            'Выберете дату пробежки:',
            reply_markup=await datepicker.start_calendar()
        )
        await state.set_state(User.CreateJoggingState.set_date)

    except Exception as e:
        print(f"Ошибка: {e}")



@create_jogging_router.callback_query(DpCallback.filter())
async def process_dialog_calendar(callback: CallbackQuery, callback_data: DpCallback, state: FSMContext):
    print('Шаг 4: Получение даты пробежки')
    date_result = await datepicker.process_selection(callback, callback_data)
    if date_result:
        await callback.message.edit_text(f"Выбрана дата: {date_result} ✅")
        date_result = list(map(int, date_result.split('.')))
        await state.update_data(set_jogging_date=date_result)
        print(await state.get_data())
        await callback.message.answer("Введите время пробежки в формате: ЧЧ:ММ", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(User.CreateJoggingState.set_time)


@create_jogging_router.message(User.CreateJoggingState.set_time)
async def process_time_input(message: types.Message, state: FSMContext):
    print('Шаг 4: Получение времени пробежки')
    try:
        time1 = message.text.split(':')
        await state.update_data(set_jogging_time=time1)

        info = await state.get_data()
        tim = time(hour=int(info['set_jogging_time'][0]), minute=int(info['set_jogging_time'][1]))
        print(tim.hour, tim.minute)
        await message.answer("Хотите ли вы добавить фотографию к пробежке?", reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="Да, добавить фотографию к пробежке")],
                    [types.KeyboardButton(text="Нет, без фотографии")],
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            ))
        await state.set_state(User.CreateJoggingState.ans_photo)
    except Exception as e:
        print(e)


@create_jogging_router.message(User.CreateJoggingState.ans_photo)
async def process_photo_input(message: types.Message, state: FSMContext):
    print('Шаг 5: Вопрос с фотографией')
    if message.text == "Да, добавить фотографию к пробежке":
        await message.answer("Отправьте фотографию", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(User.CreateJoggingState.set_photo)

    elif message.text == "Нет, без фотографии":
        await message.answer("Пробежка успешно создана!")
        info = await state.get_data()
        start_coord = await backend.session.get_start_coord_for_user(message.from_user.id)
        start_coord = f'{start_coord[0]},{start_coord[1]}'
        dat = date(day=info['set_jogging_date'][0], month=info['set_jogging_date'][1], year=info['set_jogging_date'][2])
        tim = time(hour=int(info['set_jogging_time'][0]), minute=int(info['set_jogging_time'][1]))
        print(time.hour, time.minute)
        user_id = await backend.session.get_user_id(message.from_user.id)
        description = info['set_jogging_description']

        jogging = await backend.session.create_jogging(user_id, start_coord, description, date_start=dat, time_start=tim)
        text = await backend.session.get_info_for_jogging(jogging, only_text=True)
        await message.answer(caption=text,
            reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[
                        [types.KeyboardButton(text="На главную")],
                        ],
                    resize_keyboard=True,
                    one_time_keyboard=True
                    )
            )
        await state.set_state(User.over)


@create_jogging_router.message(User.CreateJoggingState.set_photo)
async def set_photo_jogging(message: types.Message, state: FSMContext):
    print('Шаг 6: Получение фотографии к пробежке')
    try:
        photo = message.photo[0].file_id
        user_id = await backend.session.get_user_id(message.from_user.id)
        start_coord = await backend.session.get_start_coord_for_user(message.from_user.id)
        start_coord = f'{start_coord[0]},{start_coord[1]}'
    
        info = await state.get_data()
        dat = date(day=info['set_jogging_date'][0], month=info['set_jogging_date'][1], year=info['set_jogging_date'][2])
        tim = time(hour=int(info['set_jogging_time'][0]), minute=int(info['set_jogging_time'][1]))
        description = info['set_jogging_description']
        jogging = await backend.session.create_jogging(user_id, start_coord, description, date_start=dat, time_start=tim, photo=photo)
        await message.answer("Пробежка успешно создана!")

        image, text = await backend.session.get_info_for_jogging(jogging)
        await message.answer_photo(image, caption=text, parse_mode='Markdown', 
                                   reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[
                        [types.KeyboardButton(text="На главную")],
                        ],
                    resize_keyboard=True,
                    one_time_keyboard=True
            ))
        await state.set_state(User.over)


    except Exception as e:
        print(e)

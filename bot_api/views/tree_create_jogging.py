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
from backend.validators import check_description, check_date, check_time
import asyncio


datepicker = DatePicker()


create_jogging_router = Router()



@create_jogging_router.message(User.CreateJoggingState.set_description)
async def set_title_jogging(message: types.Message, state: FSMContext):
    print('Шаг 3: Получение названия пробежки')
    ch_desc = check_description(message.text)
    if ch_desc == True:
        await state.update_data(set_jogging_description=message.text)
        try:
            data = await state.get_data()
            msg_id = data.get('delete_msg_id')
            await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
            await message.delete()
            await message.answer(
                'Выберете дату пробежки:',
                reply_markup=await datepicker.start_calendar()
            )
            await state.set_state(User.CreateJoggingState.set_date)

        except Exception as e:
            print(f"Ошибка: {e}")
    else:
        await message.answer(ch_desc)



@create_jogging_router.callback_query(DpCallback.filter())
async def process_dialog_calendar(callback: CallbackQuery, callback_data: DpCallback, state: FSMContext):
    print('Шаг 4.1: Получение даты пробежки')
    date_result = await datepicker.process_selection(callback, callback_data)
    if date_result:
        ch_date = check_date(date_result)
        if ch_date == True:
            msg = await callback.message.edit_text(f"Выбрана дата: {date_result} ✅")
            date_result = list(map(int, date_result.split('.')))
            await state.update_data(set_jogging_date=date_result)
            await asyncio.sleep(2)
            await msg.delete()
            del_msg = await callback.message.answer("Введите время пробежки в формате: ЧЧ:ММ", reply_markup=types.ReplyKeyboardRemove())
            await state.set_state(User.CreateJoggingState.set_time)
            await state.update_data(delete_msg_id=del_msg.message_id)
        else:
            await callback.message.edit_text(ch_date)
            await asyncio.sleep(3)
            print(1)
            await callback.message.delete()
            await callback.message.answer(
                'Выберете дату пробежки:',
                reply_markup=await datepicker.start_calendar()
            )


@create_jogging_router.message(User.CreateJoggingState.set_time)
async def process_time_input(message: types.Message, state: FSMContext):
    print('Шаг 4.2: Получение времени пробежки')
    
    try:
        ch_time = check_time(message.text)
        if ch_time == True:
            time1 = message.text.split(':')
            await state.update_data(set_jogging_time=time1)

            info = await state.get_data()
            tim = time(hour=int(info['set_jogging_time'][0]), minute=int(info['set_jogging_time'][1]))
            data = await state.get_data()
            msg_id = data.get('delete_msg_id')
            await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
            await message.delete()
            msg = await message.answer(f"Выбрано время: {message.text} ✅")
            await asyncio.sleep(2)
            await msg.delete()
            await message.answer("Хотите ли вы добавить фотографию к пробежке?", 
                    reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [types.InlineKeyboardButton(text="Да, добавить фотографию к пробежке", callback_data="set_photo")],
                        [types.InlineKeyboardButton(text="Нет, без фотографии", callback_data="no_photo")],
                    ],
                    resize_keyboard=True,
                    one_time_keyboard=True
                ))
            await state.set_state(User.CreateJoggingState.ans_photo)
        else:
            await message.answer(ch_time)
    except Exception as e:
        print(e)


@create_jogging_router.callback_query(User.CreateJoggingState.ans_photo)
async def process_photo_input(callback: CallbackQuery, state: FSMContext):
    print('Шаг 5: Вопрос с фотографией')
    callback_data = callback.data
    await callback.message.delete()
    if callback_data == "set_photo":
        del_msg = await callback.message.answer("Отправьте фотографию", reply_markup=types.ReplyKeyboardRemove())
        await state.update_data(delete_msg_id=del_msg.message_id)
        await state.set_state(User.CreateJoggingState.set_photo)

    elif callback_data == "no_photo":
        info = await state.get_data()
        start_coord = await backend.session.get_start_coord_for_user(callback.from_user.id)
        start_coord = f'{start_coord[0]},{start_coord[1]}'
        dat = date(day=info['set_jogging_date'][0], month=info['set_jogging_date'][1], year=info['set_jogging_date'][2])
        tim = time(hour=int(info['set_jogging_time'][0]), minute=int(info['set_jogging_time'][1]))
        print(time.hour, time.minute)
        user_id = await backend.session.get_user_id(callback.from_user.id)
        description = info['set_jogging_description']

        jogging = await backend.session.create_jogging(user_id, start_coord, description, date_start=dat, time_start=tim)
        text = await backend.session.get_info_for_jogging(jogging, only_text=True)
        await callback.message.answer("Пробежка успешно создана!")
        await callback.message.answer(text,
            reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [types.InlineKeyboardButton(text="На главную", callback_data="main_menu")],
                        ],
                    resize_keyboard=True,
                    one_time_keyboard=True
                    )
            )
        await state.set_state(User.over)
        await callback.message.delete()


@create_jogging_router.message(lambda message: message.photo, User.CreateJoggingState.set_photo)
async def set_photo_jogging(message: types.Message, state: FSMContext):
    print('Шаг 6: Получение фотографии к пробежке')
    data = await state.get_data()
    msg_id = data.get('delete_msg_id')
    await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
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
        msg = await message.answer("Пробежка успешно создана!")
        asyncio.sleep(1)
        await msg.delete()

        image, text = await backend.session.get_info_for_jogging(jogging)
        await message.delete()
        del_msg = await message.answer_photo(image, caption=text, parse_mode='Markdown', 
                                   reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [types.InlineKeyboardButton(text="На главную", callback_data="main_menu")],
                        ],
                    resize_keyboard=True,
                    one_time_keyboard=True
            ))
        await state.update_data(delete_final_msg_id=del_msg.message_id)
        await state.set_state(User.over)


    except Exception as e:
        print(e)

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
from backend.validators import check_distance_km

set_path_jogging_router = Router()


@set_path_jogging_router.message(User.PathJoggingState.set_distance)
async def get_distance(message: types.Message, state: FSMContext):
    print('Шаг 3: Получение расстояния пробежки')
    distance = message.text.replace(',', '.')
    chc = check_distance_km(message.text)
    if  chc != True:
        await message.answer(chc)
        return
    state.update_data(set_distance=distance)
    try:
        distance = float(message.text)
        await message.answer(f"Вы указали расстояние пробежки: {distance} км +- 500 м. Ждите маршрут...")
        coord = await backend.session.get_start_coord_for_user(message.from_user.id)
        link = None
        count = 0
        while link is None and count < 50:
            link = set_path(coord, distance * 1000)
            count += 1
        if link is not None:
            await message.answer(
                f"вот ваша cсылка на [маршрут]({link})",
                parse_mode='Markdown',
                    reply_markup=types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [types.InlineKeyboardButton(text="На главную", callback_data='main_menu')],
                            ],
                        resize_keyboard=True,
                        one_time_keyboard=True
                )
            )
            await state.set_state(User.over)
        else:
            await message.answer("Маршрут не найден. Попробуйте еще раз.",
                                 reply_markup=types.InlineKeyboardMarkup(
                                     inline_keyboard=[
                                         [types.InlineKeyboardButton(text="Назад", callback_data='back')],
                                         ],
                                     resize_keyboard=True,
                                     one_time_keyboard=True
                                 )
                                 )
            await state.set_state(User.confirm_coordinates)
    except Exception as e:
        print(f"Ошибка: {e}")
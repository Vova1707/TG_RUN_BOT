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


set_path_jogging_router = Router()


@set_path_jogging_router.message(User.PathJoggingState.set_distance)
async def get_distance(message: types.Message, state: FSMContext):
    print('Шаг 3: Получение расстояния пробежки')
    state.update_data(set_distance=message.text)
    try:
        distance = int(message.text)
        await message.answer(f"Вы указали расстояние пробежки: {distance} км +- 500 м. Ждите маршрута...")
        coord = await backend.session.get_start_coord_for_user(message.from_user.id)
        link = None
        while link is None:
            link = set_path(coord, distance * 1000)
        await message.answer(
            f"ссылка: \n{link}",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[
                        [types.KeyboardButton(text="На главную")],
                        ],
                    resize_keyboard=True,
                    one_time_keyboard=True
            )
        )
        await state.set_state(User.over)
    except Exception as e:
        print(f"Ошибка: {e}")
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



join_jogging_router = Router()
joggins = None


async def next_join_jogging(message: types.Message, state: FSMContext):
    user_coord = await backend.session.get_start_coord_for_user(message.from_user.id)
    joggins = await backend.session.search_near_jogging(user_coord)
 
    data = await state.get_data()
    print(joggins, data['join_joggins_index'])
    if data['join_joggins_index'] <= len(joggins) - 1:
        info = list(await backend.session.get_info_for_jogging(joggins[data['join_joggins_index']]))
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="👍")],
                [types.KeyboardButton(text="👎")],
                [types.KeyboardButton(text="💤")],
                ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        if len(info) == 2:
            await message.answer_photo(info[0], caption=info[1], parse_mode='Markdown',
                                       reply_markup=reply_markup)
        else:
            await message.answer(info[0], parse_mode='Markdown', 
                                 reply_markup=reply_markup)

        data['join_joggins_index'] += 1
        await state.update_data(join_joggins_index=data['join_joggins_index'])
    else:
        await state.set_state(User.over)
        await message.answer(
            "Пробежки не найдены. Попробуйте позже", 
                reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="На главную")],
                    ],
                resize_keyboard=True,
                one_time_keyboard=True
        ))



@join_jogging_router.message(User.JoinJoggingState.run_search)
async def join_jogging(message: types.Message, state: FSMContext):
    await next_join_jogging(message, state)
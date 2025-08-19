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
import asyncio



join_jogging_router = Router()
joggins = None



async def next_join_jogging(message: types.Message, state: FSMContext, user_tg_id=False):
    global joggins
    user_telegram_id = user_tg_id if user_tg_id else message.from_user.id
    if joggins is None:
        joggins = await backend.session.search_near_jogging(user_telegram_id)

        '''
        if joggins is None or joggins == []:
            await backend.session.delete_all_other_user_joggings(message.from_user.id)
            joggins = await backend.session.search_near_jogging(message.from_user.id)
            print(joggins)
        '''

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
        if not user_tg_id:
            await message.delete()
        if len(info) == 2:
            del_msg =await message.answer_photo(info[0], caption=info[1], parse_mode='Markdown',
                                       reply_markup=reply_markup)
        else:
            del_msg = await message.answer(info[0], parse_mode='Markdown', 
                                 reply_markup=reply_markup)
        
        await state.update_data(delete_msg_id=del_msg.message_id)
        data['join_joggins_index'] += 1
        await state.update_data(join_joggins_index=data['join_joggins_index'])
    else:
        if not user_tg_id:
            await message.delete()
        msg = await message.answer(
            "Не можем найти ещё...",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await asyncio.sleep(1)
        await msg.delete()
        joggins = None
        await message.answer(
            "Пробежки не найдены. Попробуйте позже", 
                reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="На главную", callback_data="main_menu")],
                    ],
                resize_keyboard=True,
                one_time_keyboard=True
        ))
        await state.set_state(User.over)
        



@join_jogging_router.message(User.JoinJoggingState.run_search)
async def join_jogging(message: types.Message, state: FSMContext):
    global joggins
    data = await state.get_data()
    if message.text == "💤":
        await message.delete()
        await state.set_state(User.over)
        msg = await message.answer(
            "Просмотр пробежек завершён",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await asyncio.sleep(1)
        await msg.delete()
        await message.answer("Будем ждать откликов", 
                             reply_markup=types.InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [types.InlineKeyboardButton(text="На главную", callback_data="main_menu")],
                                     ],
                                 resize_keyboard=True,
                                 one_time_keyboard=True
                             ))
        joggins = None
        await message.bot.delete_message(chat_id=message.chat.id, message_id=data.get('delete_msg_id'))
        return

    elif message.text == "👍":
        jogging_id = joggins[data['join_joggins_index'] - 1].id
        user_id = await backend.session.get_user_id(message.from_user.id)
        user = await backend.session.get_user_by_id(user_id)
        print('user_id', user_id, 'jogging_id', jogging_id)
        await backend.session.join_jogging(user_id, jogging_id, like=True)
        creator_id = await backend.session.get_jogging_creator(jogging_id)
        creator = await backend.session.get_user_by_id(creator_id)
        creator_telegram_id = creator.telegram_id
        print(creator_telegram_id)
        await message.bot.send_message(creator_telegram_id, f"{user.nickname} хочет присоединиться к вашей пробежке.")

    elif message.text == "👎":
        jogging_id = joggins[data['join_joggins_index'] - 1].id
        user_id = await backend.session.get_user_id(message.from_user.id)
        await backend.session.join_jogging(user_id, jogging_id, like=False)


    data = await state.get_data()
    await next_join_jogging(message, state)

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


from bot_api.views.tree_join_jogging import join_jogging_router, next_join_jogging
from bot_api.views.tree_set_path_jogging import set_path_jogging_router
from bot_api.views.tree_create_jogging import create_jogging_router



router = Router()

@router.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    await message.answer(
        "Привет! Я бот...",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="Начать", callback_data="main_menu")]
            ]
        )
    )
    await state.set_state(User.over)
    


@router.callback_query(User.over)
async def send_welcome(callback: types.CallbackQuery, state: FSMContext):


    data = await state.get_data()
    id_final_message = data.get('id_final_message')
    if id_final_message is not None:
        await callback.bot.delete_message(callback.from_user.id, id_final_message)
        await state.update_data(id_final_message=None)
    callback.message.delete()
    await state.clear()
    print("Команда /start получена!")
    username = '@' + callback.from_user.username if callback.from_user.username else callback.from_user.first_name
    user = await backend.session.get_user_by_telegram_id(callback.from_user.id)
    print(f'Верификация пользователя {username}')
    
    if user is None:
        print('Пользователь не найден, создаем нового')
        user = await backend.session.create_user(
            username, 
            callback.from_user.id
        )
    await callback.message.delete()
    await callback.message.answer(
        "Выберите действие для работы с ботом:",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="Составить маршрут пробежки", callback_data="action_plan")],
                [types.InlineKeyboardButton(text="Создать и позвать на пробежку", callback_data="action_create")],
                [types.InlineKeyboardButton(text="Присоединиться к пробежке", callback_data="action_join")]
            ]
        )
    )
    await state.set_state(User.chose_action)





@router.callback_query(User.chose_action)
async def choose_action(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data

    # Валидируем доступные действия
    valid_actions = ["action_plan", "action_create", "action_join"]
    if action not in valid_actions:
        await callback.answer("Некорректное действие")
        return
    await state.update_data(choose_action=action)
    print('Шаг 1: Выбрано действие', action)
    await callback.message.delete()
    await callback.message.answer(
        "Давайте определимся с вашем местоположением:",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text="Отправить координаты", request_location=True, callback_data="return_new_coord")],
                      [types.InlineKeyboardButton(text="Оставить текущие координаты", callback_data="return_old_coord")],],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await state.set_state(User.get_coordinates)
    await backend.session.refresh_user_last_message(callback.from_user.id, action)



async def geocoder(message, lat, lon):
    '''
    params = {
        'format': 'json',
        'apikey': APIKEY_GEOCODER,
        'geocode': f'{lat},{lon}'
    }
    response = requests.get(GEOCODER_URL, params=params)
    data = response.json()
            
    place = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['Address']['formatted']
    await message.answer(f"Ваше местоположение {place}")
    '''
    await message.delete()
    await message.answer(
        "Всё верно?",
        reply_markup=types.InlineKeyboardMarkup(
        inline_keyboard=[
                    [types.InlineKeyboardButton(text="Да. Продолжить", callback_data='ok')],
                    [types.InlineKeyboardButton(text="Нет. Отправить координаты заново", callback_data="return_new_coord")],
                ],
        resize_keyboard=True,
        one_time_keyboard=True
            )
    )



@router.callback_query(User.get_coordinates)
async def get_coordinates(callback: types.CallbackQuery, state: FSMContext):
    print('Шаг 2: Получение координат')
    action = callback.data
    location = await backend.session.get_start_coord_for_user(callback.from_user.id)
    await state.update_data(action_coords=action)
    if action == "return_old_coord":
        if location is None:
            await callback.message.delete()
            delete_msg = await callback.message.answer(
                "Невозможно получить ваши предыдущие координаты. Отправьте их",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[
                        [types.KeyboardButton(
                            text="Отправить координаты",
                            request_location=True,
                            callback_data="return_new_coord")],
                    ],
                    resize_keyboard=True,
                    one_time_keyboard=True
                    )
                )
            await state.update_data(delete_msg_id=delete_msg.message_id)
            return
        await geocoder(callback.message, location[0], location[1])
        await state.set_state(User.confirm_coordinates)

    else:
        await callback.message.delete()
        msg = await callback.message.answer(
            "Отправьте ваши координаты",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(
                        text="Отправить координаты",
                            request_location=True,
                            )],
                ],
                    resize_keyboard=True,
                    one_time_keyboard=True
                    )
        )
        await state.update_data(delete_msg_id=msg.message_id)
        await state.set_state(User.get_coordinates)


@router.message(lambda message: message.location is not None and User.get_coordinates)
async def get_coordinates(message: types.Message, state: FSMContext):
    location = message.location
    lat, lon = location.longitude, location.latitude
    await backend.session.set_start_coord_for_user(message.from_user.id, lat, lon)
    msg = await message.answer("Координаты сохранены ✅", reply_markup=types.ReplyKeyboardRemove())
    await msg.delete()
    await geocoder(message, lat, lon)

    data = await state.get_data()
    msg_id = data.get('delete_msg_id')
    await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
    await state.set_state(User.confirm_coordinates)





@router.callback_query(User.confirm_coordinates)
async def confirm_coordinates(callback: types.CallbackQuery, state: FSMContext):
    action_data = callback.data
    if action_data == "return_new_coord":
        await state.set_state(User.get_coordinates)
        return

    action = await state.get_data()
    action = action['choose_action']
    actions = {'action_plan': [User.PathJoggingState.set_distance, 'Введите дистанцию в км'], 
               'action_create': [User.CreateJoggingState.set_description, 'Введите описание пробежки'], 
               'action_join': [User.JoinJoggingState.run_search, 'Ищем пробежки...']}

    await state.set_state(actions[action][0])
    await callback.message.delete()

    msg = await callback.message.answer(actions[action][1],
                         reply_markup=types.ReplyKeyboardRemove())
    if action == 'action_join':
        await asyncio.sleep(2)
        await msg.delete()
        await state.update_data(join_joggins_index=0)
        await next_join_jogging(callback.message, state, user_tg_id=callback.from_user.id)
    else:
        await state.update_data(delete_msg_id=msg.message_id)



def register_handlers_default(dp: Dispatcher):
    dp.include_router(router)
    dp.include_router(join_jogging_router)
    dp.include_router(set_path_jogging_router)
    dp.include_router(create_jogging_router)

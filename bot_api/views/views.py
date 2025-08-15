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


from bot_api.views.tree_join_jogging import join_jogging_router, next_join_jogging
from bot_api.views.tree_set_path_jogging import set_path_jogging_router
from bot_api.views.tree_create_jogging import create_jogging_router



router = Router()

@router.message(Command("start"))
@router.message(User.over)
async def send_welcome(message: types.Message, state: FSMContext):
    await state.clear()
    print("Команда /start получена!")
    user = await backend.session.get_user_by_telegram_id(message.from_user.id)
    print(f'Верификация пользователя {message.from_user.username}')
    
    if user is None:
        print('Пользователь не найден, создаем нового')
        user = await backend.session.create_user(
            message.from_user.username, 
            message.from_user.id
        )
    
    await message.answer(
        "Выберите действие",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Составить маршрут пробежки")],
                [types.KeyboardButton(text="Создать и позвать на пробежку")],
                [types.KeyboardButton(text="Присоединиться к пробежке")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await state.set_state(User.chose_action)


@router.message(F.text, User.chose_action)
async def choose_action(message: types.Message, state: FSMContext):
    action = message.text
    await state.update_data(choose_action=message.text)
    print('Шаг 1: Выбрано действие', action)

    await message.answer(
        "Отправьте свои координаты",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Отправить координаты", request_location=True)],
                      [types.KeyboardButton(text="Оставить текущие координаты")],],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await state.set_state(User.get_coordinates)
    await backend.session.refresh_user_last_message(message.from_user.id, message.text)


#@router.message(lambda message: message.text == "Оставить текущие координаты" or message.location is not None)
@router.message(User.get_coordinates)
async def get_coordinates(message: types.Message, state: FSMContext):
    print('Шаг 2: Получение координат')

    if message.text == "Оставить текущие координаты":
            try:
                lat, lon = await backend.session.get_start_coord_for_user(message.from_user.id)
            except Exception as e:
                print(e)
                await message.answer(
                    "Невозможно получить ваши предыдущие координаты. Отправьте их",
                    reply_markup=types.ReplyKeyboardMarkup(
                        keyboard=[[types.KeyboardButton(text="Отправить координаты", request_location=True)],],
                        resize_keyboard=True,
                        one_time_keyboard=True
                        )
                    )
                return

    elif message.location:
        location = message.location
        lat, lon = location.longitude, location.latitude
        await backend.session.set_start_coord_for_user(message.from_user.id, lat, lon)

    # Этот код - геокодер. Ограниченное количество использования
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

    await message.answer(
        "Всё верно?",
        reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[
                    [types.KeyboardButton(text="Да. Продолжить")],
                    [types.KeyboardButton(text="Нет. Отправить координаты заново", request_location=True)]
                ],
        resize_keyboard=True,
        one_time_keyboard=True
            )
    )
    await state.set_state(User.confirm_coordinates)


@router.message(User.confirm_coordinates)
async def confirm_coordinates(message: types.Message, state: FSMContext):
    if message.text == "Нет. Отправить координаты заново":
        await state.set_state(User.get_coordinates)
        return
    action = await state.get_data()
    action = action['choose_action']
    actions = {'Составить маршрут пробежки': [User.PathJoggingState.set_distance, 'Введите дистанцию в км'], 
               'Создать и позвать на пробежку': [User.CreateJoggingState.set_description, 'Введите описание пробежки'], 
               'Присоединиться к пробежке': [User.JoinJoggingState.run_search, 'Ищем пробежки...']}

    await state.set_state(actions[action][0])

    await message.answer(actions[action][1],
                         reply_markup=types.ReplyKeyboardRemove())
    if action == 'Присоединиться к пробежке':
        await state.update_data(join_joggins_index=0)
        await next_join_jogging(message, state)



def register_handlers_default(dp: Dispatcher):
    dp.include_router(router)
    dp.include_router(join_jogging_router)
    dp.include_router(set_path_jogging_router)
    dp.include_router(create_jogging_router)

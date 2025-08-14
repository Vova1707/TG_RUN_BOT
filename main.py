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
from bot_api.state import JoggingState
from aiogram.fsm.context import FSMContext


load_dotenv()
GEOCODER_URL = os.getenv('GEOCODER_URL')
APIKEY_GEOCODER = os.getenv('APIKEY_GEOCODER')
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()
datepicker = DatePicker()


#Логгирование
logging.basicConfig(level=logging.INFO)


log_dir = 'logging'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, 'bot.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Загрузка текстов сообщений из файла
with open('bot_api/messages.txt', 'r', encoding='utf-8') as f:
    messages = {}
    for line in f:
        key, value = line.strip().split('=')
        messages[key] = value




# АССИНХРОННЫЕ ФУНКЦИИ
async def on_startup(_):
    logging.info('Бот вышел в онлайн')

async def on_shutdown(_):
    logging.info('Бот вышел в офлайн')


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    print("Команда /start получена!")
    # Верификация пользователя
    user = await backend.session.get_user_by_telegram_id(message.from_user.id)
    print('Верификация пользователя', message.from_user.username)
    if user is None:

        print('Пользователь не найден, создаем нового')
        user = await backend.session.create_user(message.from_user.username, message.from_user.id)
    #refresh_user_last_message(message.from_user.id, message.text)

    await message.answer(
        "Выберите действие",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Составить маршрут пробежки")],
                [types.KeyboardButton(text="Создать и позвать на пробежку")],
                [types.KeyboardButton(text="Присоединиться к пробежке")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )




@dp.message(lambda message: message.text in ["Составить маршрут пробежки", "Создать и позвать на пробежку", "Присоединиться к пробежке"])
async def choose_action(message: types.Message):
    action = message.text
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
    await backend.session.refresh_user_last_message(message.from_user.id, message.text)


@dp.message(lambda message: message.text == "Оставить текущие координаты" or message.location is not None)
async def get_coordinates(message: types.Message):
    print('Шаг 2: Получение координат')

    if message.text == "Оставить текущие координаты" and await backend.session.get_start_coord_for_user(message.from_user.id) is None:
        await message.answer(
            "Отправьте свои координаты",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="Отправить координаты", request_location=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return

    good_action = ['Составить маршрут пробежки', 'Создать и позвать на пробежку', 'Присоединиться к пробежке']
    action = await backend.session.get_user_last_message(message.from_user.id)
    if action in good_action:
        try:
            if message.text == "Оставить текущие координаты":
                lat, lon = await backend.session.get_start_coord_for_user(message.from_user.id)
            elif message.location:
                location = message.location
                lat, lon = location.longitude, location.latitude
                await backend.session.set_start_coord_for_user(message.from_user.id, lat, lon)
            print(3)
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

            if action == good_action[0]:
                await message.answer(
                    "Всё верно?",
                    reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[
                            [types.KeyboardButton(text="Да. Сейчас напишу расстояние")],
                            [types.KeyboardButton(text="Нет. Отправить координаты заново", request_location=True)]
                    ],
                    resize_keyboard=True,
                    one_time_keyboard=True
                    )
                )
            elif action == good_action[1]:
                    await message.answer(
                    "Всё верно?",
                    reply_markup=types.ReplyKeyboardMarkup(
                        keyboard=[
                                [types.KeyboardButton(text="Да. Продолжаем создавать пробежку")],
                                [types.KeyboardButton(text="Нет. Отправить координаты заново", request_location=True)]
                        ],
                        resize_keyboard=True,
                        one_time_keyboard=True
                    )
                )
            elif action == good_action[2]:
                await message.answer(
                    "Всё верно?",
                    reply_markup=types.ReplyKeyboardMarkup(
                        keyboard=[
                                [types.KeyboardButton(text="Да. Присоединиться к пробежке")],
                                [types.KeyboardButton(text="Нет. Отправить координаты заново", request_location=True)]
                        ],
                        resize_keyboard=True,
                        one_time_keyboard=True
                    )
                )
        except Exception as e:
            print(f"Ошибка: {e}")


# Ветвь - Составить  маршрут
@dp.message(lambda message: message.text == "Да. Сейчас напишу расстояние")
async def confirm_distance(message: types.Message):
    await backend.session.refresh_user_last_message(message.from_user.id, message.text)
    await message.answer("Введите расстояние пробежки в км", reply_markup=types.ReplyKeyboardRemove())


async def get_distance(message: types.Message):
    print('Шаг 3: Получение расстояния пробежки')
    try:
        distance = int(message.text)
        await message.answer(f"Вы указали расстояние пробежки: {distance} км +- 500 м. Ждите маршрута...")
        coord = await backend.session.get_start_coord_for_user(message.from_user.id)
        link = None
        while link is None:
            link = set_path(coord, distance * 1000)
        await message.answer(f"ссылка: \n{link}")
    except Exception as e:
        print(f"Ошибка: {e}")


# Ветвь - Создать и позвать на пробежку
@dp.message(lambda message: message.text == "Да. Продолжаем создавать пробежку")
async def confirm_title_jogging(message: types.Message, state: FSMContext):
    await backend.session.refresh_user_last_message(message.from_user.id, message.text)
    await  state.set_state(JoggingState.set_jogging_data)
    await message.answer("Напишите что-то про пробежку(может план маршрута или ещё что-то)", reply_markup=types.ReplyKeyboardRemove())


async def set_title_jogging(message: types.Message, state: FSMContext):
    print('Шаг 3: Получение названия пробежки')
    try:
        description = message.text
        coord = await backend.session.get_start_coord_for_user(message.from_user.id)
        coord = f'{coord[0]},{coord[1]}'
        user_id = await backend.session.get_user_id(message.from_user.id)
        await backend.session.create_jogging(description, coord, user_id)
        print(user_id)


        await message.answer(
            'Выберете дату пробежки:',
            reply_markup=await datepicker.start_calendar()
        )

    except Exception as e:
        print(f"Ошибка: {e}")



@dp.callback_query(DpCallback.filter())
async def process_dialog_calendar(callback: CallbackQuery, callback_data: DpCallback, state: FSMContext):
    date_result = await datepicker.process_selection(callback, callback_data)
    if date_result:
        await callback.message.edit_text(f"Выбрана дата: {date_result} ✅")
        print(callback.from_user.id)
        user = await backend.session.get_user_by_telegram_id(callback.from_user.id)
        user_id = user.id
        print(user_id)
        jogging = await backend.session.get_last_jogging(user_id)

        date_result = list(map(int, date_result.split('.')))
        await backend.session.set_jogging_date_and_time(jogging.id, date=date(day=date_result[0], month=date_result[1], year=date_result[2]))
        await callback.message.answer("Введите время пробежки в формате: ЧЧ:ММ", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(JoggingState.set_jogging_time)
        await state.update_data({'state': 'set_jogging_time'})


@dp.message(lambda message:  message.photo)
async def set_photo_jogging(message: types.Message):
    print('Шаг 5: Получение фотографии к пробежке')
    try:
        photo = message.photo[0].file_id
        user_id = await backend.session.get_user_id(message.from_user.id)
        jogging = await backend.session.get_last_jogging(user_id)
        jogging = await backend.session.set_photo_for_jogging(jogging.id, photo)
        await message.answer("Пробежка успешно создана!")
        image, text = await backend.session.get_info_for_jogging(jogging)
        await message.answer_photo(image, caption=text)
    except Exception as e:
        print(e)



@dp.message(lambda message: len(message.text.split(':')) == 2)
async def process_time_input(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        print(data)
        if data.get('state') == 'set_jogging_time':
            print(message.text)
            await message.answer("Хотите ли вы добавить фотографию к пробежке?", reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="Да, добавить фотографию к пробежке")],
                    [types.KeyboardButton(text="Нет, без фотографии")],
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            ))
            await state.clear()
    except Exception as e:
        print(e)

@dp.message(lambda message: message.text == "Да, добавить фотографию к пробежке")
async def add_photo(message: types.Message):
    print('Шаг 4: Добавление фотографии к пробежке')
    await message.answer("Отправьте фотографию", reply_markup=types.ReplyKeyboardRemove())



# Ветвь - Присоединиться к пробежке
@dp.message(lambda message: message.text == "Да. Присоединиться к пробежке")
async def join_jogging(message: types.Message):
    print('Шаг 3: Присоединение к пробежке')
    user_coord = await backend.session.get_start_coord_for_user(message.from_user.id)
    joggings = await backend.session.search_near_jogging(user_coord)
    if len(joggings) == 0:
        await message.answer("Пробежки не найдены. Попробуйте позже")
    else:
        await message.answer(f"{[jogging for jogging in joggings]}")


# Функция для обработки введёных пользователем текстов

@dp.message()
async def all_text_message(message: types.Message, state: FSMContext):
    print('Заход в функцию all_text_message')
    try:
        if message.reply_markup is None and (await backend.session.get_user_last_message(message.from_user.id)) == 'Да. Продолжаем создавать пробежку':
            await set_title_jogging(message, state)
        elif message.reply_markup is None and (await backend.session.get_user_last_message(message.from_user.id)) == 'Да. Сейчас напишу расстояние':
            await get_distance(message)

    except Exception as e:
        print(e)


if __name__ == '__main__':
    print('Bot is running...')
    asyncio.run(dp.start_polling(bot, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown))

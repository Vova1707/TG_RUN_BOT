import logging
from aiogram import Bot, types, Dispatcher
from aiogram.filters import Command
from aiogram import types
import asyncio
import os
from dotenv import load_dotenv
from aiogram import F
import requests
from bot_api.set_path import set_path
from backend.session import get_user_by_telegram_id, create_user, refresh_user_last_message, get_user_last_message, set_start_coord_for_user, get_start_coord_for_user



load_dotenv()
GEOCODER_URL = os.getenv('GEOCODER_URL')
APIKEY_GEOCODER = os.getenv('APIKEY_GEOCODER')
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()


#Логгирование
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
    user = await get_user_by_telegram_id(message.from_user.id)
    print('Верификация пользователя', message.from_user.username)
    if user is None:

        print('Пользователь не найден, создаем нового')
        user = await create_user(message.from_user.username, message.from_user.id)
    #refresh_user_last_message(message.from_user.id, message.text)

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



@dp.message(lambda message: message.text in ["Составить маршрут пробежки", "Создать и позвать на пробежку", "Присоединиться к пробежке"])
async def choose_action(message: types.Message):
    action = message.text
    print('Шаг 1: Выбрано действие', action)
    await message.answer(
        "Отправьте свои координаты",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Отправить координаты", request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await refresh_user_last_message(message.from_user.id, message.text)


@dp.message(F.location)
async def get_coordinates(message: types.Message):
    print('Шаг 2: Получение координат')
    good_action = ['Составить маршрут пробежки', 'Создать и позвать на пробежку', 'Присоединиться к пробежке']
    action = await get_user_last_message(message.from_user.id)
    if action in good_action:
        try:
            location = message.location
            lat, lon = location.longitude, location.latitude
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
            await set_start_coord_for_user(message.from_user.id, lat, lon)

            if action == good_action[0] or action:
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
                pass
            elif action == good_action[2]:
                pass
        except Exception as e:
            print(f"Ошибка: {e}")


@dp.message(lambda message: message.text == "Да. Сейчас напишу расстояние")
async def confirm_distance(message: types.Message):
    await refresh_user_last_message(message.from_user.id, message.text)
    await message.answer("Введите расстояние пробежки в км", reply_markup=types.ReplyKeyboardRemove())


@dp.message(lambda message: message.text.isdigit())
async def get_distance(message: types.Message):
    print('Шаг 3: Получение расстояния пробежки')
    action = await get_user_last_message(message.from_user.id)
    print(action)
    if action == 'Да. Сейчас напишу расстояние':
        try:
            distance = int(message.text)
            await message.answer(f"Вы указали расстояние пробежки: +-{distance} км. Ждите маршрута...")
            coord = await get_start_coord_for_user(message.from_user.id)
            await message.answer(f"ссылка: {set_path(coord, distance * 1000)}")
        except Exception as e:
            print(f"Ошибка: {e}")



if __name__ == '__main__':
    print('Bot is running...')
    asyncio.run(dp.start_polling(bot, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown))

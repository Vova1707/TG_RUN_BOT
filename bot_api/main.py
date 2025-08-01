import logging
from aiogram import Bot, types, Dispatcher
from aiogram.filters import Command
from aiogram import types
import asyncio
import os
from dotenv import load_dotenv
from aiogram import F
import requests


# Чтение переменных окружения
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


async def on_startup(_):
    logging.info('Бот вышел в онлайн')

async def on_shutdown(_):
    logging.info('Бот вышел в офлайн')


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    print("Команда /start получена!")
    try:
        # Отправка сообщения
        await message.answer(
            "Отправьте свои координаты",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="Отправить координаты", request_location=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
    except Exception as e:
        print(f"Ошибка: {e}")


@dp.message(F.location)
async def get_coordinates(message: types.Message):
    print('Шаг 2: Получены координаты')
    try:
        location = message.location
        lat, lon = location.longitude, location.latitude
        print(lat, lon)
        params = {
            'format': 'json',
            'apikey': APIKEY_GEOCODER,
            'geocode': f'{lat},{lon}'
        }
        response = requests.get(GEOCODER_URL, params=params)
        data = response.json()
        place = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['Address']['formatted']
        await message.answer(f"Вы находитесь в {place}, Верно?", reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == '__main__':
    print('Bot is running...')
    asyncio.run(dp.start_polling(bot, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown))
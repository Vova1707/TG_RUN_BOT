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
from bot_api.views.views import register_handlers_default


load_dotenv()
GEOCODER_URL = os.getenv('GEOCODER_URL')
APIKEY_GEOCODER = os.getenv('APIKEY_GEOCODER')
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

register_handlers_default(dp)


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


if __name__ == '__main__':
    print('Bot is running...')
    asyncio.run(dp.start_polling(bot, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown))

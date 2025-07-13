import logging
from aiogram import Bot, types, Dispatcher
from aiogram.filters import Command
import asyncio
import os

# Создание папки для логов, если она не существует
log_dir = 'logging'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)


log_file = os.path.join(log_dir, 'bot.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = '7531340636:AAHQjDPmxmJJKvGfY0yBqVHrUwUdBBaMspg'

bot = Bot(token=TOKEN)
dp = Dispatcher()

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

@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.answer(messages['start_message'])

if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown))
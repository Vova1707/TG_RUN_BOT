from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

from backend.models import Base, User

# Подключение к базе данных
load_dotenv()
engine = create_engine(
    f"postgresql://{os.getenv('POSTGRES_USERNAME')}"
    f":{os.getenv('POSTGRES_PASSWORD')}@localhost:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DATABASE')}")

# Создание таблиц
#Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# Создание сессии
Session = sessionmaker(bind=engine)
session = Session()


try:
    result = session.query(User).all()
    print(result)
except Exception as e:
    print(e)



async def get_user_by_telegram_id(telegram_id):
    return session.query(User).filter_by(telegram_id=telegram_id).first()

async def create_user(nickname, telegram_id):
    try:
        user = User(nickname=nickname, telegram_id=telegram_id, last_message='/start')
        session.add(user)
        session.commit()
        return user
    except Exception as e:
        print(e)

async def refresh_user_last_message(telegram_id, last_message):
    user = await get_user_by_telegram_id(telegram_id)
    user.last_message = last_message
    session.commit()


async def get_user_last_message(telegram_id):
    user = await get_user_by_telegram_id(telegram_id)
    return user.last_message.strip()


async def set_start_coord_for_user(telegram_id, lat, lon):
    user = await get_user_by_telegram_id(telegram_id)
    user.start_coord = f"{lat},{lon}"
    session.commit()


async def get_start_coord_for_user(telegram_id):
    user = await get_user_by_telegram_id(telegram_id)
    return list(map(float, user.start_coord.split(',')))
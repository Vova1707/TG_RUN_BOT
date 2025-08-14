from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from sqlalchemy import func
from backend.models import Base, User, Jogging
from sqlalchemy import Float
from datetime import date, time

# Подключение к базе данных
load_dotenv()
engine = create_engine(
    f"postgresql://{os.getenv('POSTGRES_USERNAME')}"
    f":{os.getenv('POSTGRES_PASSWORD')}@localhost:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DATABASE')}")

# Создание таблиц
#Base.metadata.drop_all(engine) - всё дропнуть
Base.metadata.create_all(engine)

# Создание сессии
Session = sessionmaker(bind=engine)
session = Session()


try:
    result = session.query(User).all()
    print(result)
except Exception as e:
    print(e)


# User - поьзователь
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
    try:
        user = await get_user_by_telegram_id(telegram_id)
        return user.last_message.strip()
    except Exception as e:
        print(e)


async def get_user_id(telegram_id):
    try:
        user = await get_user_by_telegram_id(telegram_id)
        return user.id
    except Exception as e:
        print(e)


async def set_start_coord_for_user(telegram_id, lat, lon):
    user = await get_user_by_telegram_id(telegram_id)
    user.start_coord = f"{lat},{lon}"
    session.commit()


async def get_start_coord_for_user(telegram_id):
    user = await get_user_by_telegram_id(telegram_id)
    return list(map(float, user.start_coord.split(',')))


# Jogging - пробежка
async def create_jogging(description, start_coord, user_id, photo=None):
    try:
        jogging = Jogging(description=description, start_coord=start_coord, user_id=user_id, image=photo)
        session.add(jogging)
        session.commit()
    except Exception as e:
        print(e)


async def get_last_jogging(user_id):
    try:
        jogging = session.query(Jogging).filter(Jogging.user_id == user_id).order_by(Jogging.id.desc()).first()
        print(jogging, user_id)
        return jogging
    except Exception as e:
        print(e)

async def set_photo_for_jogging(jogging_id, photo):
    try:
        jogging = session.query(Jogging).filter(Jogging.id == jogging_id).first()
        jogging.image = photo
        session.commit()
        return jogging
    except Exception as e:
        print(e)


async def search_near_jogging(user_coord):
    try:
        joggings = session.query(Jogging).filter(Jogging.complete == False).filter(
            (func.abs(func.split_part(Jogging.start_coord, ',', 1).cast(Float) - user_coord[0]) < 0.1),
            (func.abs(func.split_part(Jogging.start_coord, ',', 2).cast(Float) - user_coord[1]) < 0.1),
        ).all()
        return joggings
    except Exception as e:
        print(e)


async def set_jogging_date_and_time(jogging_id, date=None, time=None):
    jogging = session.query(Jogging).filter(Jogging.id == jogging_id).first()
    if date is not None:
        jogging.date_start = date
        session.commit()
    if time is not None:
        jogging.time_start = time
        session.commit()


async def get_info_for_jogging(jogging: Jogging):
    longitude, latitude = jogging.start_coord.split(',')
    user_nicname = '@' + session.query(User).filter(User.id == jogging.user_id).first().nickname
    location_link = f'https://yandex.ru/maps/?ll={longitude},{latitude}&z=12&mode=whatshere&whatshere=1&source=serp'
    text = '''Создатель: {}\nОписание: {}\nМестоположение: {}\nЗапланировано на: {}'''.format(user_nicname, jogging.description, location_link, jogging.time_start)
    return jogging.image, text
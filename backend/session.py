from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from sqlalchemy import func
from backend.models import Base, User, Jogging, OtherUserJogging
from sqlalchemy import Float
from datetime import date, time
from sqlalchemy import cast, String

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


# User - пользователь
async def get_user_by_id(user_id) -> User:
    return session.query(User).filter_by(id=user_id).first()


async def get_user_by_telegram_id(telegram_id) -> User:
    return session.query(User).filter_by(telegram_id=telegram_id).first()


async def create_user(nickname, telegram_id):
    try:
        user = User(
            nickname=nickname,
            telegram_id=telegram_id, 
            last_message='/start',
            )
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
    try:
        user = await get_user_by_telegram_id(telegram_id)
        return list(map(float, user.start_coord.split(',')))
    except Exception as e:
        return None


# Jogging - пробежка
async def create_jogging(user_id, start_coord, description, date_start=None, time_start=None, photo=None):
    try:
        jogging = Jogging(description=description, start_coord=start_coord, user_id=user_id, date_start=date_start, time_start=time_start, image=photo)
        session.add(jogging)
        session.commit()
        return jogging
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


async def search_near_jogging(telegram_id):
    user_coord = await get_start_coord_for_user(telegram_id)
    user_id = await get_user_id(telegram_id)
    try:
        joggings = session.query(Jogging).filter(
            Jogging.complete == False,
            Jogging.user_id != user_id,
            ).order_by(
            func.abs(func.split_part(Jogging.start_coord, ',', 1).cast(Float) - user_coord[0]) +
            func.abs(func.split_part(Jogging.start_coord, ',', 2).cast(Float) - user_coord[1])
        ).all()
        sd = []
        if joggings is not None:
            for jogging in joggings:
                otheruserjoggig = session.query(OtherUserJogging).filter(OtherUserJogging.user_id == user_id, OtherUserJogging.jogging_id == jogging.id).first()
                if otheruserjoggig is None:
                    sd.append(jogging)

        return sd
    except Exception as e:
        print(e, 12345)
        return []




async def set_jogging_date_and_time(jogging_id, date=None, time=None):
    jogging = session.query(Jogging).filter(Jogging.id == jogging_id).first()
    if date is not None:
        jogging.date_start = date
        session.commit()
    if time is not None:
        jogging.time_start = time
        session.commit()



async def get_info_for_jogging(jogging: Jogging, only_text=False):
    try:
        print(jogging.start_coord)
        longitude, latitude = jogging.start_coord.split(',')
        user_nicname = session.query(User).filter(User.id == jogging.user_id).first().nickname
        location_link = f'https://yandex.ru/maps/?ll={longitude},{latitude}&z=12&mode=whatshere&whatshere=1&source=serp'
        date_time = jogging.date_start.strftime('%d.%m.%Y') + ' в ' + jogging.time_start.strftime('%H:%M')
        text = f'''Создатель: {user_nicname}\n{jogging.description}\nТочка сбора: [ссылка]({location_link})\nЗапланировано на: {date_time}'''
        if jogging.image is None or only_text:
            return text
        return jogging.image, text
    except Exception as e:
        print(e)


async def join_jogging(user_id, jogging_id, like=False):
    other_user_jogging = OtherUserJogging(user_id=user_id, jogging_id=jogging_id, like=like)
    session.add(other_user_jogging)
    session.commit()


async def delete_all_other_user_joggings(user_id):
    session.query(OtherUserJogging).filter(OtherUserJogging.user_id == user_id).delete()
    session.commit()


async def get_jogging_creator(jogging_id):
    jogging = session.query(Jogging).filter(Jogging.id == jogging_id).first()
    return jogging.user_id
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    nickname = Column(String, nullable=False)
    telegram_id = Column(Integer, nullable=False)
    last_message = Column(String, nullable=False, default=None)
    start_coord = Column(String, nullable=True) 
    tokens = relationship("Token", backref="user")

    def __repr__(self):
        return f"User(id={self.id}, nickname='{self.nickname}', telegram_id={self.telegram_id})"


class Token(Base):
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"Token(id={self.id}, user_id={self.user_id}, amount={self.amount})"

class Jogging(Base):
    __tablename__ = 'jogging'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    distance = Column(Integer, nullable=False)
    complete = Column(Boolean, nullable=False, default=False)
    image = Column(String, nullable=True)
    start_coord = Column(String, nullable=True)  # координаты начала пробежки
    time_start = Column(DateTime, nullable=True)  # время начала пробежки
    user_id = Column(Integer, ForeignKey('users.id'))

    def __repr__(self):
        return f"Jogging(id={self.id}, title='{self.title}', distance={self.distance}, complete={self.complete}, image={self.image})"
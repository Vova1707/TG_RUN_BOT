from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, Time, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    nickname = Column(String, nullable=False)
    telegram_id = Column(BigInteger, nullable=False)
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
    description= Column(String, nullable=False)
    distance = Column(Integer, nullable=False, default=0)
    complete = Column(Boolean, nullable=False, default=False)
    image = Column(String, nullable=True)
    start_coord = Column(String, nullable=True)  # координаты начала пробежки
    date_start = Column(Date, nullable=True)
    time_start = Column(Time, nullable=True)  # время начала пробежки
    user_id = Column(Integer, ForeignKey('users.id'))

    def __repr__(self):
        return f"Jogging(id={self.id}, description='{self.description}', distance={self.distance}, complete={self.complete}, image={self.image}), date={self.date_start}, time={self.time_start})"
    


class OtherUserJogging(Base):
    __tablename__ = 'user_jogging'

    id = Column(Integer, primary_key=True)
    jogging_id = Column(Integer, ForeignKey('jogging.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    like = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"UserJogging(id={self.id}, jogging_id={self.jogging_id}, user_id={self.user_id})"
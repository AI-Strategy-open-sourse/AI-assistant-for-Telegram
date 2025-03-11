from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# Создание подключения к базе данных SQLite
DATABASE_URL = "sqlite:///as_human_userbot/telegram_users.db"
engine = create_engine(DATABASE_URL, echo=True)

# Создание базового класса для декларативного определения моделей
Base = declarative_base()


# Определение модели пользователя
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False)
    thread_id = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    chat_id = Column(Integer, nullable=True)


# Создание таблицы в базе данных
# Base.metadata.create_all(engine)

# Создание сессии для взаимодействия с базой данных
Session = sessionmaker(bind=engine)
session = Session()

# user = session.query(User).filter_by(user_id=1223).first()
# # new_user = User(user_id=1223, username="Danilka")
# # session.add(new_user)
# user.username = "Danil"
# session.commit()

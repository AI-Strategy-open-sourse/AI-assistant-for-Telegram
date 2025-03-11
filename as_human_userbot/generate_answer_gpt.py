import json

# from utils.telegram_start_dialogue import gpts_dia_resp

from pyrogram import Client
from .db_config import User, session
from .assistant_userbot import answer_response, answer_response_new
# from as_human_userbot.db_config import session


async def generate_answer(
    dialogue,
    user_id,
    client: Client,
    # private_assistant,
):
    """
    Открываем Базу данных и проверяем,
    есть ли в ней уже данный пользователь(бота в ChatGPT).
    ---
    Если есть, то генерируем ответ для него в GPT со старым диалогом.
    Если нет, то генерируем ответ для нового пользователя
    с занесением нового ассистента в БД.
    """
    try:
        # promt = (
        #     "Напиши ответ на сообщение, только текст 1 сообщение в формате строки без префикса json: "
        #     + dialogue
        # )
        user = session.query(User).filter_by(user_id=user_id).first()
        # print(client.name, "отправляю вопрос в gpt")
        print("user, thread_id", user.thread_id)
        if user.thread_id is None:
            print("прошла проверка на none, отправляем на генерацию нового ответа")
            reanswer, thread_id = answer_response_new(promt=dialogue)
            user.thread_id = thread_id
            print("thread_id", thread_id)
        else:
            print(client.name, "отправляю вопрос в gpt")
            reanswer = answer_response(
                promt=dialogue,
                user_thread_id=user.thread_id,
            )
        print(client.name, "закончил генерацию ответа.")
        return reanswer
    except Exception as e:
        print(f"Ошибка в generate_answer: {e}")

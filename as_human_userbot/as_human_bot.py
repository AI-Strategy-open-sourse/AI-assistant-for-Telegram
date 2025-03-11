import asyncio
import datetime
import os

# import queue
from collections import deque
from random import randint

from pyrogram import Client, errors, idle
from pyrogram.types import Message
from pyrogram.enums import ChatAction

from lngc_responder import generate_answer

session_name_bot = "as_human_bot"
dir = os.path.dirname(os.path.abspath(__file__))
session_path_bot = f"{dir}/sessions"
# print(session_path)


class AsHumanBot:

    def __init__(
        self,
        session_name,
        session_path,
    ):
        self.session_name = session_name
        self.session_path = session_path
        self.queue_private = deque()
        self.pause_between_messages = 60

        try:
            self.client = Client(
                name=session_name,
                workdir=session_path,
            )
        except errors.UserBlocked:
            return {"mistake": "Аккаунт забанен."}

    async def start_bot(self):
        """Старт бота и получение сообщений."""
        try:
            await self.client.start()
            print("Бот запущен.")
        except errors.UserBlocked:
            return {"mistake": "Аккаунт забанен."}

        @self.client.on_message()
        async def private_handler(client: Client, message: Message):
            if message.text:
                self.queue_private.append(message)
                print(f"Сообщение добавлено в очередь: {message.text}")

        await self.queue_checking_loop()
        await idle()
        # await self.client.idle()
        await self.client.stop()

    async def remove_from_queue(self, user_id: int):
        """
        Удаление сообщений из очереди.
        """
        self.message_queue = deque(
            message for message in self.message_queue if message.from_user.id != user_id
        )

    async def check_message_queue(self, queue: deque):
        """
        Проверка очереди на наличие сообщений.
        Если есть, то возвращает список сообщений,
        id чата и последнее сообщение.
        Проверяется групповая и приватная очереди.
        """
        try:
            if len(queue) > 0:
                print(self.client.name, "Очередь не пустая")
                temp_messages = []
                last_message: Message = queue.popleft()
                temp_messages.append(last_message.text)

                while len(queue) > 0:
                    print("Очередь не пустая, проверяет")
                    message: Message = queue.popleft()
                    if message.from_user == last_message.from_user:
                        temp_messages.append(message.text)
                    else:
                        queue.appendleft(message)
                        break

                print("Возвращаем очередь.")
                return (
                    temp_messages,
                    last_message.chat.id,
                    # last_message.id,
                    # last_message.from_user.id,
                )
            else:
                print(self.client.name, "Очередь пустая")
                return None, None
        except Exception as e:
            print(f"Ошибка в check_message_queue: {e}")
            return None, None

    async def process_messages(self, message_from_queue, chat_id_from_queue):
        while True:
            try:
                await self.client.read_chat_history(chat_id_from_queue)
                phrase = ""
                for i in message_from_queue:
                    if isinstance(i, str):
                        phrase += i + ". "
                if phrase:
                    answer = generate_answer(phrase, "AsHumanDB")
                    # answer = "Я ответил на ваш вопрос."
                await self.client.send_chat_action(
                    chat_id=chat_id_from_queue,
                    action=ChatAction.TYPING,
                )
                asyncio.sleep(5)
                await self.client.send_message(
                    chat_id=chat_id_from_queue,
                    text=answer,
                )
                break
            except errors.exceptions.bad_request_400.PeerIdInvalid:
                print(f"{self.client.name}Бот забанен в телеграм")
                break

            except errors.exceptions.forbidden_403.Forbidden:
                print(f"Бот забанен в чате {chat_id_from_queue}")
                await self.remove_from_queue(chat_id_from_queue)
                break

            except errors.exceptions.bad_request_400.UserBannedInChannel:
                print(f"Бот забанен в чате {chat_id_from_queue}")
                await self.remove_from_queue(chat_id_from_queue)
                break

            except errors.exceptions.flood_420.FloodWait as e:
                print(f"Слишком много запросов. Ожидание {e.value} секунд.")

            except TimeoutError:
                print("Request timed out. Retrying...")

            except (OSError, ConnectionError) as es_error:
                print(f"Потеряно соединение: {es_error}. Переподключение...")

            except Exception as e:
                print(f"Возникла ошибка: {e}")
                break
            return

    async def queue_checking_loop(self):
        while True:
            try:
                (
                    message_from_queue,
                    chat_id_from_queue,
                ) = await self.check_message_queue(self.queue_private)
                print(
                    "Проверяем очередь личных сообщений",
                    self.client.name,
                    message_from_queue,
                    chat_id_from_queue,
                )
                formatted_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if message_from_queue:
                    print(
                        f"Запуск обращения приватного сообщения {self.client.name}, время: {formatted_time}"
                    )
                    await self.process_messages(
                        message_from_queue,
                        chat_id_from_queue,
                    )

                await asyncio.sleep(
                    randint(
                        self.pause_between_messages - 15,
                        self.pause_between_messages + 15,
                    )
                )
            except Exception as e:
                print(f"Ошибка в queue_checking_loop: {e}")


async def start_up_bot(name, path):
    bot = AsHumanBot(
        session_name=name,
        session_path=path,
    )
    await bot.start_bot()


if __name__ == "__main__":
    asyncio.run(
        start_up_bot(
            name=session_name_bot,
            path=session_path_bot,
        )
    )

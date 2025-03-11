import asyncio
import datetime
import os

from collections import deque
import re
from asgiref.sync import sync_to_async

from pyrogram import Client, errors, idle
from pyrogram.types import Message
from pyrogram.enums import ChatAction, ChatType

from as_human_userbot.generate_answer_gpt import generate_answer
from as_human_userbot.db_config import session, User
from as_human_userbot.voice_to_text_gen import listen_voice

session_name_bot = "as_human_bot"
dir = os.path.dirname(os.path.abspath(__file__))
session_path_bot = f"{dir}/as_human_userbot/sessions"
print(session_path_bot)


class AsHumanBot:

    def __init__(
        self,
        session_name,
        session_path,
    ):
        self.session_name = session_name
        self.session_path = session_path
        self.queue_private = deque()

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
        me = await self.client.get_me()
        print(me.id, "me")
        self.my_chat_id = me.id
        print("client", self.client.name)

        @self.client.on_message()
        async def private_handler(client: Client, message: Message):
            # print(message)
            if message.text:
                if (
                    message.chat.type == ChatType.PRIVATE
                    and not message.chat.is_support
                    and message.chat.id == message.from_user.id
                ):
                    self.queue_private.append(message)
                    print(f"Сообщение добавлено в очередь: {message.text}")
            elif message.voice:
                text = await listen_voice(self.client, message)
                self.queue_private.append(Message(
                    id=message.chat.id,
                    date=message.date,
                    chat=message.chat,
                    text=text,
                    from_user=message.from_user,
                    via_bot=message.via_bot,
                    reply_to_message=message.reply_to_message,
                    edit_date=message.edit_date,
                    media_group_id=message.media_group_id,
                    author_signature=message.author_signature
                ))
                print(f"Голосовое сообщение добавлено в очередь: {text}")

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
                username = last_message.from_user.username

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
                    username,
                    # last_message.id,
                    # last_message.from_user.id,
                )
            else:
                print(self.client.name, "Очередь пустая")
                return None, None, None
        except Exception as e:
            print(f"Ошибка в check_message_queue: {e}")
            return None, None, None

    async def process_messages(self, message_from_queue, chat_id_from_queue):
        user = session.query(User).filter_by(user_id=chat_id_from_queue).first()
        while True:
            try:
                await self.client.read_chat_history(chat_id_from_queue)
                await self.client.send_chat_action(
                    chat_id=chat_id_from_queue,
                    action=ChatAction.TYPING,
                )
                phrase = ""
                for i in message_from_queue:
                    if isinstance(i, str):
                        phrase += i + ". "
                if phrase:
                    # answer = generate_answer(phrase, f"{self.my_chat_id}/AsHumanDB")
                    # answer = generate_answer(phrase, "6115423781/AsHumanDB")

                    # answer = "Я ответил на ваш вопрос."
                    answer = await generate_answer(
                        dialogue=phrase,
                        user_id=chat_id_from_queue,
                        client=self.client,
                    )
                # task_description = None
                task_description_pattern = r"task_description: (.*?)(\n|$)"
                match = re.search(task_description_pattern, answer, re.DOTALL)
                if match:
                    task_description = match.group(1).strip()
                    answer = re.sub(
                        task_description_pattern,
                        "",
                        answer,
                        flags=re.DOTALL,
                    ).strip()
                    print("task_description:", task_description)

                    # Отправка task_description в личную группу
                    print("Отправляю сообщение в группу")
                    await self.client.send_chat_action(
                        chat_id=chat_id_from_queue,
                        action=ChatAction.TYPING,
                    )
                    await self.client.send_message(
                        chat_id="-1002067812915",  # Замените на ID вашей группы
                        text=f"@{user.username}: {task_description}",
                    )
                    print("Отправил сообщение в группу")
                await self.client.send_chat_action(
                    chat_id=chat_id_from_queue,
                    action=ChatAction.TYPING,
                )
                # await asyncio.sleep(2)
                await self.client.send_message(
                    chat_id=chat_id_from_queue,
                    text=answer,
                )
                print("отправили сообщение пользователю", chat_id_from_queue)
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

    def check_user_in_db(self, chat_id, username):
        new_user = session.query(User).filter_by(user_id=chat_id).first()
        if new_user is None:
            new_user = User(user_id=chat_id, username=username)
            session.add(new_user)
        session.commit()
        return new_user

    async def queue_checking_loop(self):
        while True:
            try:
                (
                    message_from_queue,
                    chat_id_from_queue,
                    username,
                ) = await self.check_message_queue(self.queue_private)
                print(
                    "Проверяем очередь личных сообщений",
                    self.client.name,
                    message_from_queue,
                    chat_id_from_queue,
                    username,
                )

                formatted_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if message_from_queue:
                    user = await sync_to_async(self.check_user_in_db)(
                        chat_id_from_queue,
                        username,
                    )
                    # user = self.check_user_in_db(chat_id_from_queue)
                    print(user)
                    print(
                        f"Запуск обращения приватного сообщения {self.client.name}, время: {formatted_time}"
                    )
                    await self.process_messages(
                        message_from_queue,
                        chat_id_from_queue,
                    )

                await asyncio.sleep(1)
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

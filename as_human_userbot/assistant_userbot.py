import random
import httpx
import openai
import time
import os

from dotenv import load_dotenv

# from as_human_userbot.db_config import session

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
proxy_url = os.getenv("PROXY")
assisant_bot = os.getenv("ASSISTANT")
print("assistant", assisant_bot)
print("key_open_ai", openai_api_key)

ANWER_FAIL = [
    "Извините, я не совсем понял ваш вопрос. Не могли бы вы повторить его, пожалуйста?",
    "Простите, я не уловил смысл вашего вопроса. Не могли бы вы перефразировать его для меня?",
    "Прошу прощения, но я не совсем понял, о чем вы спрашиваете. Не могли бы вы еще раз озвучить ваш вопрос?",
    "Извините, я немного запутался в вашем вопросе. Не могли бы вы повторить его, чтобы я мог лучше понять?",
    "Простите, я не совсем уверен, что правильно понял ваш вопрос. Не могли бы вы его повторить, пожалуйста?",
    "Прошу прощения, но я не совсем уловил суть вашего вопроса. Не могли бы вы еще раз его сформулировать?",
    "Извините, я немного запутался в вашем вопросе. Не могли бы вы повторить его, чтобы я мог лучше разобраться?"
]


def clean_answer(answer: str):
    answer = answer.replace('"', "")
    answer = answer.replace("'", "")
    answer = answer.replace("{", "")
    answer = answer.replace("}", "")
    answer = answer.replace("text:", "")
    answer = answer.replace("bot:", "")
    answer = answer.replace("Bot:", "")
    answer = answer.replace("json:", "")
    answer = answer.replace("error:", "")
    answer = answer.replace("answer:", "")
    answer = answer.replace("response_1:", "")
    answer = answer.replace("response:", "")
    answer = answer.replace("message:", "")
    answer = answer.replace("messages:", "")
    answer = answer.replace("[", "")
    answer = answer.replace("]", "")
    answer = answer.replace("message1:", "")
    answer = answer.replace("message_1:", "")
    answer = answer.replace("message_2:", "")
    answer = answer.replace("message2:", "")
    answer = answer.replace("message3:", "")
    answer = answer.replace("Message1:", "")
    answer = answer.replace("Message2:", "")
    answer = answer.replace("Message3:", "")
    answer = answer.replace("video:", "")
    answer = answer.replace("video.mp4", "")
    answer = answer.replace("photo:", "")
    answer = answer.replace("photo.jpg", "")
    answer = answer.replace("  ", " ")
    answer = answer.replace("```", "")
    answer = answer.replace("json", "")
    return answer


def answer_response_new(
    promt="Напиши ответ на сообщение только текст в формате строки на сообщение 'Привет, хочу заказать вашу продукцию'",
    # assistant="asst_wJxOW9St50JIX0wcPcRwVGJb",
    # proxy_url="http://KDfUkP:h15JuC@79.143.19.150:8000",
):
    """
    Загружаем подготовленную фразу с сообщениями для GPT,
    Инициализируем клиента GPT, там же инициализируем личного ассистента.
    Создаем новый тред в GPT и запускаем его.
    Отпраляем сообщение GPT и ожидаем его завершения.
    Забираем ответ GPT, очищаем его и возвращаем ответ.
    """
    try:
        # Настраиваем клиент с прокси
        print("Начинаем генерацию ответа")
        transport = httpx.Client(
            proxies={
                "http://": proxy_url,
                "https://": proxy_url,
            }
        )

        # client = openai.OpenAI(http_client=transport)
        print("Создаем клиента")
        client = openai.Client(
            api_key=openai_api_key,
            http_client=transport,
        )
        print("Клиент создан, ассиетент")
        my_assistant = client.beta.assistants.retrieve(assisant_bot)  # alina
        print("создаем тред")
        thread = client.beta.threads.create(
            messages=[{"role": "user", "content": promt}]
        )
        print("запускаем создание сообщения")
        run = client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=my_assistant.id
        )

        print("Проверяем статус в gpt:")
        count_status_fail = 0
        count_status_queued = 0
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
            print(run.status)
            if run.status == "failed":
                count_status_fail += 1
            if run.status == "queued":
                count_status_queued += 1
            if count_status_fail == 10:
                return random.choice(ANWER_FAIL), thread.id
            if count_status_queued == 15:
                return random.choice(ANWER_FAIL), thread.id
            time.sleep(5)

        thread_messages = client.beta.threads.messages.list(thread.id)
        answer = thread_messages.data[0].content[0].text.value
        answer = clean_answer(answer)
        print(answer)
        count_status_fail = 0
        count_status_queued = 0
        return answer, thread.id
    except openai.APIConnectionError as e:
        # Handle connection error here
        print(f"Failed to connect to OpenAI API: {e}")
        pass
    except openai.RateLimitError as e:
        # Handle rate limit error (we recommend using exponential backoff)
        print(f"OpenAI API request exceeded rate limit: {e}")
        pass
    except openai.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        pass


def answer_response(
    promt,
    user_thread_id,

):
    """
    Загружаем подготовленную фразу с сообщениями для GPT,
    Инициализируем клиента GPT, там же инициализируем личного ассистента.
    Отпраляем сообщение GPT и ожидаем его завершения.
    Забираем ответ GPT, очищаем его и возвращаем ответ.
    """
    try:
        transport = httpx.Client(
            proxies={
                "http://": proxy_url,
                "https://": proxy_url,
            }
        )

        # client = openai.OpenAI(http_client=transport)
        client = openai.Client(
            api_key=openai_api_key,
            http_client=transport,
            # request_session=session,
        )
        my_assistant = client.beta.assistants.retrieve(
            # "asst_Z0le9K7GbqhZVRYDDakgWmDv" # dialogue
            # "asst_NEzH9Ip1Z3w3B5uMeA0Cnw5k" # andrey
            assisant_bot  # alina
        )
        thread = client.beta.threads.retrieve(thread_id=user_thread_id)
        client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=promt
        )
        run = client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=my_assistant.id
        )
        count_status_fail = 0
        count_status_queued = 0
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
            print(run.status)
            if run.status == "failed":
                count_status_fail += 1
            if run.status == "queued":
                count_status_queued += 1
            if count_status_fail == 10:
                return random.choice(ANWER_FAIL)
            if count_status_queued == 15:
                return random.choice(ANWER_FAIL)
            time.sleep(5)

        thread_messages = client.beta.threads.messages.list(thread.id)
        answer = thread_messages.data[0].content[0].text.value
        answer = clean_answer(answer)
        print(answer)
        count_status_fail = 0
        count_status_queued = 0
        return answer

    except openai.APIConnectionError as e:
        # Handle connection error here
        print(f"Failed to connect to OpenAI API: {e}")
        pass
    except openai.RateLimitError as e:
        # Handle rate limit error (we recommend using exponential backoff)
        print(f"OpenAI API request exceeded rate limit: {e}")
        pass
    except openai.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        pass


if __name__ == "__main__":
    answer = answer_response_new(
        'Напиши ответ на сообщение только текст в формате строки без префикса json "а ты что ли бот?", до этого в чате говорили: "кто откуда?" "я с москвы, работаю в твине" "прикольно, а еще люди есть?" "я в айти, люблю технологии и новшества, а ты?"',
        "asst_QIF6bU1TaSoily8fat7GBUmP",
    )
    print(answer)

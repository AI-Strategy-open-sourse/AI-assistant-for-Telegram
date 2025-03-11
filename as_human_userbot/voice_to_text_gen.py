import os
import requests
import asyncio
import time
from asgiref.sync import sync_to_async
from pyrogram import Client
from pyrogram.types import Message


async def speechflow_audio_transcribe(
    file_path,
):
    print(file_path)
    headers = {"keyId": "RdJQfIkdC6q1RbC6", "keySecret": "XXPRreVgbOXwB0CE"}
    # create_data = {
    #     "lang": lang,
    # }
    # files = {}
    create_url = "https://api.speechflow.io/asr/file/v1/create"
    create_url += "?lang=ru"
    # files["file"] = open(file_path, "rb")
    files = {"file": open(file_path, "rb")}
    response = await sync_to_async(requests.post)(
        create_url, headers=headers, files=files
    )
    if response.status_code == 200:
        create_result = response.json()
        if create_result["code"] == 10000:
            task_id = create_result["taskId"]
        else:
            print("create error:")
            print(create_result["msg"])
            task_id = ""
    else:
        print("create request failed: ", response.status_code)
        task_id = ""
    query_url = (
        "https://api.speechflow.io/asr/file/v1/query?taskId="
        + task_id
        + "&resultType=4"
    )
    files["file"].close()
    while True:
        response = await sync_to_async(requests.get)(
            query_url,
            headers=headers,
        )
        if response.status_code == 200:
            query_result = response.json()
            if query_result["code"] == 11000:
                print(query_result["result"].replace("\n", " "))
                break
            elif query_result["code"] == 11001:
                await asyncio.sleep(3)
                continue
            else:
                print(query_result)
                print("transcription error:")
                print(query_result["msg"])
                break
        else:
            print("query request failed: ", response.status_code)
    return query_result["result"].replace("\n", " ")


async def listen_voice(bot: Client, message: Message) -> str:
    audio = message.voice
    file_id = audio.file_id
    print("file_id:", file_id)

    local_name = "d" + str(round(time.time())) + ".wav"
    print(local_name)

    await bot.download_media(file_id, file_name=local_name)
    file_path = f"downloads/{local_name}"
    text = await speechflow_audio_transcribe(file_path=file_path)

    os.remove(file_path)
    return text

from telethon import TelegramClient, events
from telethon.tl.custom import Button
import subprocess

api_id = 26554125
api_hash = 'b92aced74e1dd82a4f31d1a47304c8e1'
bot_token = '6821695338:AAHoPQyvBEKWFhaNPZj4c0J_dDYjcu6jr_c'

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Словник для відстеження активних трансляцій
active_streams = {}

stream_url = "rtmp://langate.tv/live/c4_1080"
telegram_url = "rtmps://dc4-1.rtmp.t.me/s/2131192661:Y5Phl0qgLyRfdPjHJnp6SQ"
youtube_url = "rtmp://a.rtmp.youtube.com/live2/10zt-k3er-cy6j-fsx5-f4bh"


async def start_streaming(stream_url, rtmp_url):
    cool_command = [
        'ffmpeg',
        '-i', stream_url,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-ar', '48000',
        '-async', '1',
        '-f', 'flv',
        rtmp_url
    ]
    process = subprocess.Popen(cool_command)
    return process


last_message = None


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    global last_message
    # Видалення попереднього повідомлення з кнопками, якщо воно існує
    if last_message:
        await client.delete_messages(event.chat_id, [last_message])
    # Відправка нового повідомлення з кнопками
    last_message = await event.respond('Ласкаво просимо до зали трансляцій!', buttons=[
        [Button.inline('Ввімкнути трансляцію', b'turn_on')],
        [Button.inline('Вимкнути трансляцію', b'turn_off')],
        [Button.inline('Статус трансляцій', b'status')]
    ])


@client.on(events.CallbackQuery())
async def callback_query_handler(event):
    callback_data = event.data
    if callback_data == b'turn_on':
        await event.edit('Виберіть опцію:', buttons=[
            [Button.inline('Ввімкнути всі трансляції', b'stream_all')],
            [Button.inline('Ввімкнути Telegram', b'stream_telegram')],
            [Button.inline('Ввімкнути YouTube', b'stream_youtube')],
            [Button.inline('Назад', b'back_main')]
        ])
    elif callback_data == b'turn_off':
        await event.edit('Виберіть опцію:', buttons=[
            [Button.inline('Вимкнути всі трансляції', b'stop_all')],
            [Button.inline('Вимкнути Telegram', b'stop_telegram')],
            [Button.inline('Вимкнути YouTube', b'stop_youtube')],
            [Button.inline('Назад', b'back_main')]
        ])
    elif callback_data in [b'stream_all', b'stream_telegram', b'stream_youtube']:
        # Викликайте тут відповідну функцію для ввімкнення трансляції
        # Наприклад, для ввімкнення всіх трансляцій:
        if callback_data == b'stream_all':
            await stream_all(event)
        elif callback_data == b'stream_telegram':
            await stream_telegram(event)
        elif callback_data == b'stream_youtube':
            await stream_youtube(event)
    elif callback_data in [b'stop_all', b'stop_telegram', b'stop_youtube']:
        # Викликайте тут відповідну функцію для вимкнення трансляції
        if callback_data == b'stop_all':
            await stop_all(event)
        elif callback_data == b'stop_telegram':
            await stop_telegram(event)
        elif callback_data == b'stop_youtube':
            await stop_youtube(event)
    elif callback_data == b'status':
        await status(event)
        await start(event)
    elif callback_data == b'back_main':
        await start(event)


async def handle_stream_start(event, rtmp_url):
    # Перевірка, чи вже існує активний процес для даної URL
    if rtmp_url in active_streams:
        await event.respond(f'Трансляція до {rtmp_url} вже запущена.')
    else:
        process = await start_streaming(stream_url, rtmp_url)
        active_streams[rtmp_url] = process
        await event.respond(f'Починаю трансляцію до {rtmp_url}... Трансляція запущена!')


@client.on(events.NewMessage(pattern='/stream_telegram'))
async def stream_telegram(event):
    await handle_stream_start(event, telegram_url)


@client.on(events.NewMessage(pattern='/status'))
async def status(event):
    streams = list(active_streams.keys())
    answer = ""
    for i in streams:
        if i == telegram_url:
            answer += "Telegram транслюється.\n"
        if i == youtube_url:
            answer += "YouTube транслюється.\n"
    if answer == "":
        answer = "Нема активних трансляцій."
    await event.respond(answer)


@client.on(events.NewMessage(pattern='/stream_youtube'))
async def stream_youtube(event):
    await handle_stream_start(event, youtube_url)


@client.on(events.NewMessage(pattern='/stream_all'))
async def stream_all(event):
    await stream_youtube(event)
    await stream_telegram(event)


@client.on(events.NewMessage(pattern='/stop_telegram'))
async def stop_telegram(event):
    if telegram_url in active_streams:
        active_streams[telegram_url].terminate()
        del active_streams[telegram_url]
        await event.respond('Трансляцію до Telegram було зупинено.')
    else:
        await event.respond('Відсутня активна трансляція на Telegram, котру можна зупинити.')


@client.on(events.NewMessage(pattern='/stop_youtube'))
async def stop_youtube(event):
    if youtube_url in active_streams:
        active_streams[youtube_url].terminate()
        del active_streams[youtube_url]
        await event.respond('Трансляцію до YouTube було зупинено.')
    else:
        await event.respond('Відсутня активна трансляція на YouTube, котру можна зупинити.')


@client.on(events.NewMessage(pattern='/stop_all'))
async def stop_all(event):
    if active_streams:
        for rtmp_url, process in active_streams.items():
            process.terminate()
        active_streams.clear()
        await event.respond('Всі трансляції зупинено.')
    else:
        await event.respond('Відсутні активні трансляції, котрі можна зупинити.')


client.run_until_disconnected()

import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from fastapi import FastAPI
import uvicorn

# 🔹 Логирование (помогает в Render видеть работу)
logging.basicConfig(level=logging.INFO)

# 🔹 Получаем токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Переменная окружения BOT_TOKEN не установлена!")

# 🔹 Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🔹 Обработчик команды /start
@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("Привет! Я работаю на Render 🛠️")

# 🔹 Асинхронный запуск polling
async def start_bot():
    logging.info("🤖 Запускается polling бота...")
    await dp.start_polling(bot)

# 🔹 FastAPI-заглушка для Render (открытие порта)
app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Telegram Bot is running on Render"}

# 🔹 Запуск и бота, и веб-сервера
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())  # запустить бота в фоне
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))  # порт для Render

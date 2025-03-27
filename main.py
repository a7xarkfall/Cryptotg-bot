import os
import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Настройки
TOKEN = "8162219271:AAEhKmeNRLzORbDwXyLKH4tbUMMmtU-ypsw"
CRYPTOBOT_INVOICE = "IVGMYQSAqfgn"
CRYPTOBOT_LINK = f"https://t.me/send?start={CRYPTOBOT_INVOICE}"
ADMIN_ID = 6170133844  # Твой Telegram ID
FILE_PATH = "example.txt"
VIDEO_PATH = "rickroll.mp4"
LOG_FILE = "paid_users.txt"

# Telegram бот
telegram_app = Application.builder().token(TOKEN).build()

# FastAPI сервер
fastapi_app = FastAPI()
received_users = set()

# Логирование
logging.basicConfig(level=logging.INFO)


# === Telegram: Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить 0.1 USDT", url=CRYPTOBOT_LINK)],
        [InlineKeyboardButton("📩 Поддержка", callback_data="support")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ])
    await update.message.reply_text(
        "Привет! Чтобы получить файл, оплати 0.1 USDT через CryptoBot и получишь приз 🎁",
        reply_markup=keyboard
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        with open(VIDEO_PATH, "rb") as vid:
            await update.message.reply_video(vid, caption="🎶 Никогда тебя не подведу...")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Не понимаю такую команду 😅")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "support":
        await query.edit_message_text("📩 Пиши на почту: a7xspurius@gmail.com")
    elif query.data == "about":
        await query.edit_message_text("У каджита есть для тебя скума, если у тебя есть монеты для каджита, друг.")


# === FastAPI: Обработка оплаты ===
@fastapi_app.post("/webhook")
async def payment_webhook(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    invoice_id = data.get("invoice_id")

    if invoice_id != CRYPTOBOT_INVOICE:
        return JSONResponse(content={"status": "ignored"}, status_code=200)

    if user_id in received_users:
        return JSONResponse(content={"status": "already_received"}, status_code=200)

    received_users.add(user_id)

    try:
        # Отправка текстового файла
        file = InputFile(FILE_PATH)
        await telegram_app.bot.send_document(chat_id=user_id, document=file, caption="📄 Лови свой приз, ковбой")

        # Уведомление тебе
        await telegram_app.bot.send_message(chat_id=ADMIN_ID, text=f"✅ Оплата от юзера: {user_id}")
    except Exception as e:
        await telegram_app.bot.send_message(chat_id=ADMIN_ID, text=f"❌ Ошибка при отправке: {e}")
        return JSONResponse(content={"status": "error"}, status_code=500)

    return JSONResponse(content={"status": "ok"}, status_code=200)


# === Главная функция ===
async def main():
    # Запускаем FastAPI
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)

    # Инициализируем Telegram-бота
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

    # Запускаем FastAPI и Telegram-бота параллельно
    await asyncio.gather(
        server.serve(),
        telegram_app.updater.wait_for_stop(),  # ждём завершения
    )


import logging
import os
import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
import httpx

TOKEN = "8162219271:AAEhKmeNRLzORbDwXyLKH4tbUMMmtU-ypsw"
CRYPTOBOT_LINK = "https://t.me/send?start=IVGMYQSAqfgn"
INVOICE_ID = "IVGMYQSAqfgn"
OWNER_ID = 5803903142  # сюда будут приходить уведомления
FILE_PATH = "example.txt"
GIF_PATH = "rickroll.mp4"
LOG_FILE = "paid_users.txt"

app = FastAPI()
telegram_app = Application.builder().token(TOKEN).build()

paid_users = set()
recent_tx_ids = set()


def load_paid_users():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            for line in f:
                paid_users.add(int(line.strip()))


def save_paid_user(user_id: int):
    paid_users.add(user_id)
    with open(LOG_FILE, "a") as f:
        f.write(f"{user_id}\n")


@telegram_app.command_handler("start")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить 0.1 USDT (ERC-20)", url=CRYPTOBOT_LINK)],
        [InlineKeyboardButton("📩 Поддержка", callback_data="support")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ])
    await update.message.reply_text(
        "Привет! Чтобы получить файл, оплати 0.1 USDT через CryptoBot и нажми кнопку.\n\nПосле этого я пришлю тебе 🔥",
        reply_markup=keyboard
    )


@telegram_app.callback_query_handler()
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "support":
        await query.message.reply_text("📩 По всем вопросам оплаты пиши на a7xspurius@gmail.com")
    elif query.data == "about":
        await query.message.reply_text("У каджита есть для тебя скума, если у тебя есть монеты для каджита, друг")


@telegram_app.message_handler(filters.TEXT & ~filters.COMMAND)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if os.path.exists(GIF_PATH):
        with open(GIF_PATH, "rb") as f:
            await update.message.reply_video(f, caption="🎶 Никогда тебя не подведу...")
    else:
        await update.message.reply_text("Я ничего не понял, ковбой 🤠")


@telegram_app.message_handler(filters.COMMAND)
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Не знаю такую команду, ковбой 😅")


@app.post("/webhook")
async def crypto_webhook(request: Request):
    data = await request.json()
    invoice_id = data.get("invoice_id")
    telegram_user_id = data.get("user", {}).get("id")

    if invoice_id == INVOICE_ID and telegram_user_id:
        if int(telegram_user_id) not in paid_users:
            # Отправка файла
            try:
                await telegram_app.bot.send_document(
                    chat_id=telegram_user_id,
                    document=InputFile(FILE_PATH),
                    caption="📁 Лови свой приз, ковбой!"
                )
                if os.path.exists(GIF_PATH):
                    with open(GIF_PATH, "rb") as gif:
                        await telegram_app.bot.send_video(chat_id=telegram_user_id, video=gif)

                # Уведомление владельца
                await telegram_app.bot.send_message(
                    chat_id=OWNER_ID,
                    text=f"💸 Новый платёж от пользователя [{telegram_user_id}](tg://user?id={telegram_user_id})",
                    parse_mode="Markdown"
                )

                save_paid_user(int(telegram_user_id))
                return PlainTextResponse("✅ Отправлено")
            except Exception as e:
                return PlainTextResponse(f"❌ Ошибка отправки: {e}")
        else:
            return PlainTextResponse("📂 Пользователь уже получал файл")
    return PlainTextResponse("⚠️ Неизвестный запрос")


async def main():
    load_paid_users()

    # Параллельно запускаем FastAPI и Telegram polling
    async def start_fastapi():
        import uvicorn
        config = uvicorn.Config(app=app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def start_telegram():
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        await telegram_app.updater.idle()

    await asyncio.gather(start_fastapi(), start_telegram())


if __name__ == "__main__":
    asyncio.run(main())

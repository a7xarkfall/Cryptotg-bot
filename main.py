import os
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, ContextTypes
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# === Конфигурация ===
TOKEN = "8162219271:AAEhKmeNRLzORbDwXyLKH4tbUMMmtU-ypsw"
CRYPTOBOT_INVOICE = "IVGMYQSAqfgn"
CRYPTOBOT_LINK = f"https://t.me/send?start={CRYPTOBOT_INVOICE}"
ADMIN_ID = 427325039
FILE_PATH = "app/example.txt"

telegram_app = Application.builder().token(TOKEN).build()
fastapi_app = FastAPI()
received_users = set()

# === Telegram Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить", url=CRYPTOBOT_LINK)],
        [InlineKeyboardButton("📩 Поддержка", callback_data="support")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ])
    await update.message.reply_text("Привет!", reply_markup=keyboard)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Неизвестное сообщение")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команда не найдена")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "support":
        await query.edit_message_text("📩 Пиши на почту: a7xspurius@gmail.com")
    elif query.data == "about":
        await query.edit_message_text("У каджита есть для тебя скума.")

# === FastAPI Webhook ===
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
        file = InputFile(FILE_PATH)
        await telegram_app.bot.send_document(chat_id=user_id, document=file, caption="📄 Лови файл")
        await telegram_app.bot.send_message(chat_id=ADMIN_ID, text=f"✅ Оплата от юзера: {user_id}")
    except Exception as e:
        await telegram_app.bot.send_message(chat_id=ADMIN_ID, text=f"❌ Ошибка при отправке: {e}")
        return JSONResponse(content={"status": "error"}, status_code=500)

    return JSONResponse(content={"status": "ok"}, status_code=200)

def setup_telegram_handlers():
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(button_callback))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    telegram_app.add_handler(MessageHandler(filters.COMMAND, unknown))

setup_telegram_handlers()

@fastapi_app.on_event("startup")
async def startup_event():
    # Инициализируем и запускаем Telegram-бота
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

@fastapi_app.on_event("shutdown")
async def shutdown_event():
    # Корректно останавливаем Telegram-бота
    await telegram_app.updater.stop()
    await telegram_app.shutdown()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(fastapi_app, host="0.0.0.0", port=port, log_level="info")

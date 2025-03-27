import os
import asyncio
import uvicorn

from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, ContextTypes
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# === Configuration ===
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
    main_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Получить файл", callback_data="get_file")],
        [InlineKeyboardButton("📩 Поддержка", callback_data="support")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ])
    await update.message.reply_text(
        "Привет, путник! 🧙‍♂️\n\n"
        "Я каджит-бот. Тут можно обменять криптомонеты на магические файлы.\n\n"
        "Выбирай, что тебе нужно ⤵️",
        reply_markup=main_keyboard
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Same as start message
    main_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Получить файл", callback_data="get_file")],
        [InlineKeyboardButton("📩 Поддержка", callback_data="support")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ])
    await update.message.reply_text(
        "Главное меню:\n\n"
        "Выбирай, что тебе нужно ⤵️",
        reply_markup=main_keyboard
    )

async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pay_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить — 0.1 USDT", url=CRYPTOBOT_LINK)]
    ])
    await update.message.reply_text(
        "Чтобы получить файл, сначала оплати ⬇️",
        reply_markup=pay_keyboard
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные команды:\n"
        "/start - Запустить бота и получить приветствие\n"
        "/menu - Показать главное меню\n"
        "/pay - Инструкция по оплате\n"
        "/about - Информация о боте\n"
        "/help - Эта справка"
    )
    await update.message.reply_text(help_text)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "ℹ️ Этот бот создан для обмена криптомонет на магические файлы.\n\n"
        "Просто следуй инструкциям после оплаты.\n"
        "Если возникнут вопросы — всегда на связи!"
    )
    await update.message.reply_text(about_text)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "support":
        await query.edit_message_text(
            "📩 Если что-то не работает — пиши на почту:\n"
            "`a7xspurius@gmail.com`\n\n"
            "Каджит ответит, как только прикончит эту скуму."
        )
    elif query.data == "about":
        await query.edit_message_text(
            "ℹ️ Этот бот создан для обмена криптомонет на магические файлы.\n\n"
            "Просто нажми «Оплатить», и после оплаты я пришлю тебе твой файл.\n\n"
            "Если возникнут вопросы — всегда на связи!"
        )
    elif query.data == "get_file":
        if query.from_user.id in received_users:
            file = InputFile(FILE_PATH)
            await query.message.reply_document(document=file, caption="📄 Вот твой файл, как и договаривались.")
        else:
            await query.message.reply_text(
                "❌ Нет оплаты - нет товара, соси бибу, чепух! И плати!"
            )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Неизвестное сообщение")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команда не найдена")

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
        await telegram_app.bot.send_message(
            chat_id=user_id,
            text="✅ Успешная оплата!\n\nВот твой файл. Спасибо за доверие ✨"
        )
        await telegram_app.bot.send_document(
            chat_id=user_id, document=file, caption="📄 Лови файл"
        )
        await telegram_app.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"✅ Оплата от юзера: {user_id}"
        )
    except Exception as e:
        await telegram_app.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❌ Ошибка при отправке: {e}"
        )
        return JSONResponse(content={"status": "error"}, status_code=500)

    return JSONResponse(content={"status": "ok"}, status_code=200)

def setup_telegram_handlers():
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("menu", menu_command))
    telegram_app.add_handler(CommandHandler("pay", pay_command))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("about", about_command))
    telegram_app.add_handler(CallbackQueryHandler(button_callback))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    telegram_app.add_handler(MessageHandler(filters.COMMAND, unknown))

setup_telegram_handlers()

# === Main Function ===
async def main():
    await telegram_app.initialize()
    await telegram_app.start()

    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)

    # Start Telegram polling as a background task
    telegram_polling_task = asyncio.create_task(telegram_app.updater.start_polling())
    uvicorn_task = asyncio.create_task(server.serve())

    await asyncio.gather(telegram_polling_task, uvicorn_task)

if __name__ == "__main__":
    asyncio.run(main())


import asyncio
import os
from fastapi import FastAPI, Request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = "8162219271:AAEhKmeNRLzORbDwXyLKH4tbUMMmtU-ypsw"
CRYPTOBOT_LINK = "https://t.me/send?start=IVGMYQSAqfgn"
EXPECTED_PAYLOAD = "IVGMYQSAqfgn"
ADMIN_ID = 519105945  # @a7xark

FILE_PATH = "app/example.txt"
GIF_PATH = "app/success.gif"
LOG_FILE = "app/paid_users.txt"

app = FastAPI()
bot = Bot(token=TOKEN)
telegram_app = Application.builder().token(TOKEN).build()


def user_already_received(user_id):
    if not os.path.exists(LOG_FILE):
        return False
    with open(LOG_FILE, "r") as f:
        return str(user_id) in f.read()


def log_user(user_id):
    with open(LOG_FILE, "a") as f:
        f.write(f"{user_id}\n")


@app.post("/crypto-webhook")
async def crypto_webhook(request: Request):
    try:
        data = await request.json()
        print("🔥 Получено от CryptoBot:", data)

        if data.get("event") == "payment" and data.get("status") == "success":
            payload = data.get("invoice_payload")
            telegram_id = data.get("user", {}).get("telegram_id")
            username = data.get("user", {}).get("username", "неизвестен")

            if payload == EXPECTED_PAYLOAD and telegram_id:
                await bot.send_message(chat_id=ADMIN_ID, text=f"💸 Оплата от @{username} (ID: {telegram_id}) получена!")

                if user_already_received(telegram_id):
                    await bot.send_message(chat_id=telegram_id, text="📁 Вы уже получали файл. Спасибо за оплату!")
                else:
                    if os.path.exists(FILE_PATH):
                        await bot.send_document(chat_id=telegram_id, document=InputFile(FILE_PATH),
                                                caption="📄 Лови свой приз, ковбой 🤠")

                        if os.path.exists(GIF_PATH):
                            with open(GIF_PATH, "rb") as gif:
                                await bot.send_animation(chat_id=telegram_id, animation=gif, caption="🎉 Великий успех!")

                        log_user(telegram_id)
                    else:
                        await bot.send_message(chat_id=telegram_id, text="❌ Файл не найден. Обратитесь в поддержку.")

        return {"ok": True}
    except Exception as e:
        print(f"❌ Ошибка в webhook: {e}")
        return {"error": str(e)}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu(update, context)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить", callback_data="pay"),
         InlineKeyboardButton("📁 Получить", callback_data="get")],
        [InlineKeyboardButton("📩 Поддержка", callback_data="support"),
         InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("💬 Выберите действие:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "pay":
        keyboard = [[InlineKeyboardButton("💳 Оплатить 0.1 USDT (ERC-20)", url=CRYPTOBOT_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💰 Отправьте 0.1 USDT через CryptoBot. После оплаты файл будет выдан автоматически.",
                                      reply_markup=reply_markup)

    elif query.data == "get":
        telegram_id = query.from_user.id
        if user_already_received(telegram_id):
            await bot.send_document(chat_id=telegram_id, document=InputFile(FILE_PATH),
                                    caption="📄 Лови свой приз, ковбой 🤠")
        else:
            await bot.send_message(chat_id=telegram_id, text="❌ Вы ещё не оплачивали. Сначала нажмите «Оплатить».")

    elif query.data == "support":
        await query.edit_message_text("📩 По всем вопросам пишите на: a7xspurius@gmail.com")

    elif query.data == "about":
        await query.edit_message_text("У каджита есть для тебя скума, если у тебя есть монеты для каджита, друг 😼")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Извини, я не знаю такой команды 😅")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("app/rickroll.mp4", "rb") as video:
            await update.message.reply_video(video, caption="🎶 Никогда тебя не подведу...")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Видео не найдено: {e}")


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("menu", menu))
telegram_app.add_handler(CallbackQueryHandler(button_handler))
telegram_app.add_handler(MessageHandler(filters.COMMAND, unknown))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


async def main():
    tg_task = telegram_app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)
    await tg_task


if __name__ == "__main__":
    asyncio.run(main())

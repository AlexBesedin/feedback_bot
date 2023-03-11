import os
import psycopg2
import logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')

conn = psycopg2.connect(
    host=DATABASE_HOST,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD,
    database=DATABASE_NAME
)

with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            user_id INT,
            name VARCHAR(255) NOT NULL,
            text TEXT,
            email TEXT,
            created_at timestamp
        );
    """)


def start(update: Update, context: CallbackContext):
    """Отправка сообщения при выполнении команды /start"""
    message = 'Привет. Вы можете оставить отзыв. Напишите его сюда:'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    context.user_data['state'] = 'review'


def help(update: Update, context: CallbackContext):
    """Отправка сообщения при выполнении команды /help."""
    update.message.reply_text('Данный бот, может быть')


def review_handler(update: Update, context: CallbackContext):
    message = "Спасибо за отзыв! Оставьте свой email:"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    review = context.user_data.get('review', None)
    if review is not None:
        context.user_data.pop('review')
    context.user_data['review'] = update.message.text
    context.user_data['state'] = 'email'


def email_handler(update: Update, context: CallbackContext):
    message = "Спасибо! Ваш отзыв и email сохранены"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    name = update.message.from_user.name
    user_id = update.effective_user.id
    review = context.user_data.get('review', None)
    email = update.message.text

    with conn.cursor() as cur:
        cur.execute('INSERT INTO feedback (user_id, name, text, email, created_at) VALUES (%s, %s, %s, %s, now())',
                    (user_id, name, review, email))
        conn.commit()
    update.message.reply_text('Спасибо за отзыв! Если у вас остались вопросы, выполни команду /help')


def message_handler(update: Update, context: CallbackContext):
    user_state = context.user_data.get('state')

    if user_state == 'review':
        review_handler(update, context)
    elif user_state == 'email':
        email_handler(update, context)
    else:
        message = 'Извините, я не понимаю ваш запрос. Напишите /help, чтобы получить справку.'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    updater = Updater(bot=bot, use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, message_handler))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()


#pip install python-telegram-bot
#pip install psycopg2-binary
#pip install python-dotenv
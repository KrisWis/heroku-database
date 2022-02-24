import random
import os
import telebot


import logging
from config import *
from flask import Flask, request
import psycopg2




bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)

db_connection = psycopg2.connect(DB_URI, sslmode="require")
db_object = db_connection.cursor()


name_subject = ''
class_subject = ''
author = ''




@bot.message_handler(content_types=['text'])

def start(message):
    global stop
    id = message.from_user.id
    db_object.execute(f"SELECT id FROM users WHERE id = {user_id}")
    result = db_object.fetchone()

    if not result:
        db_object.execute("INSERT INTO users(id, username, messages) VALUES (%s, %s, %s)", (user_id, username, 0))
        db_connection.commit()

    if message.text == '/start':
        bot.send_message(message.from_user.id, 'Привет! Я бот, который поможет тебе с учёбой! \nТебе всего лишь надо ввести название учебника, его автора и номер, который нужно решить. '
                                               'Попробуй!')
        bot.send_message(message.from_user.id, 'Напиши название предмета, класс, автора и номер, по которому надо найти ГДЗ.'
                                               '\n\nНапример: Русский язык, 7 класс, Быстрова Е.А, упражнение 255; '
                                               'Математика, 5 класс, А.Г. Мерзляк, номер 120)')

        bot.register_next_step_handler(message, get_result_func)
    else:
        bot.send_message(message.from_user.id,
                         'Привет! Напиши /start для начала')


@server.route(f'/{BOT_TOKEN}', methods=['POST'])

def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))

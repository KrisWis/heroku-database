import random
import os
import telebot
import requests
import mechanicalsoup
import selenium
from selenium.webdriver.common.by import By
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

browser = mechanicalsoup.Browser()
URL = 'https://gdz.ru/'
HEADERS = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.116 YaBrowser/22.1.1.1544 Yowser/2.5 Safari/537.36'}




login_page = browser.get(URL)
login_html = login_page.soup
num = 1



chrome_options = selenium.webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

driver = selenium.webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)


def gdz_API(result):

    form = login_html.select('form')[0]
    form.select('input')[0]['value'] = result
    profiles_page = browser.submit(form, URL)

    driver.get(profiles_page.url)

    items = driver.find_elements(By.CLASS_NAME, 'gs-title')


    driver.get(items[num].get_attribute('href'))
    elem = driver.find_element(By.CLASS_NAME, 'with-overtask')
    item = elem.find_element(By.TAG_NAME, 'img')
    url = item.get_attribute('src')


    img_data = requests.get(url).content
    with open('gdz_image.jpg', 'wb') as handler:
        handler.write(img_data)

def update_messages_count(user_id):
    db_object.execute(f"UPDATE users SET messages = messages + 1 WHERE id = {user_id}")
    db_connection.commit()


@bot.message_handler(commands=["start"])
def start(message):
    global stop
    user_id = message.from_user.id
    username = message.from_user.username

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

    update_messages_count(user_id)


@bot.message_handler(commands=["stats"])
def get_stats(message):
    db_object.execute("SELECT * FROM users ORDER BY messages DESC LIMIT 10")
    result = db_object.fetchall()

    if not result:
        bot.reply_to(message, "No data...")
    else:
        reply_message = "- Top flooders:\n"
        for i, item in enumerate(result):
            reply_message += f"[{i + 1}] {item[1].strip()} ({item[0]}) : {item[2]} messages.\n"
        bot.reply_to(message, reply_message)

    update_messages_count(message.from_user.id)


@bot.message_handler(func=lambda message: True, content_types=["text"])
def message_from_user(message):
    user_id = message.from_user.id
    update_messages_count(user_id)


@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
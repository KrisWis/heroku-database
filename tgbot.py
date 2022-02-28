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




@bot.message_handler(content_types=['text'])

def start(message):
    global stop


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






def get_result_func(message):
    global name_subject
    global result


    result = message.text
    db_object.execute(f"SELECT user_request FROM users WHERE user_request = {result}")
    result2 = db_object.fetchone()

    if not result2:
        db_object.execute("INSERT INTO users(user_result, user_request) VALUES (%s, %s)", (0, result))
        db_connection.commit()

    if len(result) >= 10:
        answer = 'Ты хочешь найти ГДЗ по запросу "{}"?'.format(result)
        keyboard = telebot.types.InlineKeyboardMarkup()
        key_yes = telebot.types.InlineKeyboardButton(text='Да', callback_data='yes')
        keyboard.add(key_yes)
        key_no = telebot.types.InlineKeyboardButton(text='Нет', callback_data='no')
        keyboard.add(key_no)
        bot.send_message(message.from_user.id, text=answer, reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, 'Напиши больше информации')
        bot.register_next_step_handler(message, get_result_func)

@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

    if call.data == "yes":
        bot.send_message(call.message.chat.id, 'Начинаю поиск... '
                                               '\nПоиск завершится примерно через 9 секунд')
        gdz_API(result)
        photo = open('gdz_image.jpg', 'rb')
        bot.send_photo(call.message.chat.id, photo, 'Это то, что ты искал?')
        bot.register_next_step_handler(call.message,recheck)

    else:
        bot.send_message(call.message.chat.id, 'Попробуй ввести данные ещё раз (/start) ')
        bot.register_next_step_handler(call.message, start)

def recheck(message):
    global num
    if message.text in ['Да','да','Дп','дп']:
        bot.send_message(message.from_user.id, 'Отлично! До скорого!')
        bot.register_next_step_handler(message,start)

    else:
        rand_phrase = random.choice(['Хм... поищу ещё', "Пойду искать дальше...", 'Поищу поглубже', "Подключаю свои лучшие навыки", "Продолжаю искать...", "Продолжаю поиск..."])
        bot.send_message(message.from_user.id, rand_phrase)
        num += 4
        gdz_API(result)
        photo = open('gdz_image.jpg', 'rb')
        rand_phrase2 = random.choice(['Может быть это?', "Хм.. Может это?", 'Это то, что надо?', "May be это?", "Как насчёт этого?", "Это подойдёт?"])
        bot.send_photo(message.chat.id, photo, rand_phrase2)
        bot.register_next_step_handler(message,recheck)

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
import os
import telebot
from config import  TELEGRAM_CONFIG
from telebot import types
import time
# Импорт модулей с функциями
from datetime import datetime
import sqlite3
# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_CONFIG['TOKEN'])
db_path_cloud= os.path.join(os.getcwd(),  '1.2_WeatherData_VS-1_2024-03-20_.db')
def run_bot():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            print("Перезапуск бота через 10 мин")
            print(datetime.now())
            time.sleep(60*10)
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    get_data_button = types.InlineKeyboardButton(text="📊 Получить данные БД", callback_data='getdataBD')
    status_button = types.InlineKeyboardButton(text="📈 Статус системы", callback_data='status')

    markup.row( get_data_button, status_button)
    bot.send_message(message.chat.id, "Привет! Я ваш датчиковый бот. Выберите действие:", reply_markup=markup)

# Добавим обработчик для кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    command = call.data

    # Теперь проверяем значение callback_data
    if command == 'condition':
        # Отправляем сообщение с командой /condition
        bot.send_message(call.message.chat.id, "/condition")
    elif command == 'getdataBD':
        # Отправляем сообщение с командой /getdataBD
        bot.send_message(call.message.chat.id, "/getdataBD")
    elif command == 'status':
        # Отправляем сообщение с командой /status
        bot.send_message(call.message.chat.id, "/status")
    elif command == 'relay_st':
        # Отправляем сообщение с командой /relay_st
        bot.send_message(call.message.chat.id, "/relay_st")
    elif command == 'relay_on':
        # Отправляем сообщение с командой /relay_on
        bot.send_message(call.message.chat.id, "/relay_on")
    elif command == 'relay_off':
        # Отправляем сообщение с командой /relay_off
        bot.send_message(call.message.chat.id, "/relay_off")
    elif command == 'ip':
        # Отправляем сообщение с командой /ip
        bot.send_message(call.message.chat.id, "/ip")

@bot.message_handler(commands=['getdataBD'])
def get_data(message):
    database_path = '1.3_SolarData_ExpU.db'
    if os.path.exists(database_path):
        with open(database_path, 'rb') as db_file:
            bot.send_document(message.chat.id, db_file)
    else:
        bot.reply_to(message,
                     "Файл базы данных не найден. Пожалуйста, убедитесь, что файл 'solar_data.db' находится в корне программы.")
@bot.message_handler(commands=['get_cloud_data'])
def send_cloud_data(message):
    date_text = message.text.split()  # предполагаем, что команда будет в формате /get_cloud_data 2024-03-20
    if len(date_text) > 1:
        date = date_text[1]
        try:
            # Проверка корректности формата даты
            datetime.strptime(date, '%Y-%m-%d')
            # Получение данных из БД
            conn = sqlite3.connect(db_path_cloud)
            cursor = conn.cursor()
            cursor.execute("SELECT datetime, clouds FROM screenshots WHERE datetime LIKE ?", (f'{date}%',))
            data = cursor.fetchall()
            conn.close()
            if data:
                response = f"Данные облачности за {date}:\n"
                response += "\n".join([f"{datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')} - {row[1]}" for row in data])
                bot.reply_to(message, response)
            else:
                bot.reply_to(message, "Нет данных за указанную дату.")
        except ValueError:
            bot.reply_to(message, "Неправильный формат даты. Используйте YYYY-MM-DD.")
    else:
        bot.reply_to(message, "Пожалуйста, укажите дату.")

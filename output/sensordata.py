# -*- coding: utf-8 -*-
import minimalmodbus
import time
import os
import csv
import smtplib
import logging
import telebot
import threading
import dateparser
import subprocess
import requests
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from configurate import SENSOR_TH_CONFIG, SENSOR_PYRANOMETER_CONFIG, Mail_CONFIG, DATA_PATH_Conf, TELEGRAM_CONFIG, \
    ALLOWED_USERS, OPENVPN_CONFIG, REALVNC_CONFIG, NOTIFICATION_CONFIG, RELAY_CONFIG
from datetime import datetime, timedelta
from telebot import types
from clicker import run_clicker
from threading import Thread

# Настройка логирования
logging.basicConfig(filename='program_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
last_sent_timestamp = None
last_high_temperature_notification_sent = None
last_low_temperature_notification_sent = None
# Получение имени файла лога из настроек логирования
log_file_path = logging.getLogger().handlers[0].baseFilename
# Путь для сохранения данных
DATA_PATH = os.path.join(os.getcwd(), DATA_PATH_Conf['DownloadedAttachments'])

if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)


# Функция для конфигурации датчика
def configure_sensor(config):
    sensor = minimalmodbus.Instrument(config['port'], config['address'])
    sensor.serial.baudrate = config['baudrate']
    sensor.serial.bytesize = config['bytesize']
    sensor.serial.parity = config['parity']
    sensor.serial.stopbits = config['stopbits']
    sensor.serial.timeout = config['timeout']
    return sensor


# Функция для сохранения данных в CSV
def save_data_to_csv(data, file_path):
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)


# Функция для отправки письма с вложением на почту
def send_email(subject, body, attachment_path):
    global last_sent_timestamp
    smtp_server = Mail_CONFIG['smtp_server']
    smtp_port = Mail_CONFIG['smtp_port']
    login = Mail_CONFIG['login']
    password = Mail_CONFIG['password']

    msg = MIMEMultipart()
    msg['From'] = login
    msg['To'] = login
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(attachment_path))
            msg.attach(part)
    except FileNotFoundError:
        error_message = "Вложение не найдено. Отправка без него."
        logging.warning(error_message)

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(login, password)
        text = msg.as_string()
        server.sendmail(login, login, text)
        server.quit()
        logging.info("Письмо успешно отправлено.")
        last_sent_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        error_message = f"Ошибка при отправке письма: {str(e)}"
        logging.error(error_message)


sensorTH = configure_sensor(SENSOR_TH_CONFIG)
pyranometer = configure_sensor(SENSOR_PYRANOMETER_CONFIG)
relay = configure_sensor(RELAY_CONFIG)


# Функция подключения нагрузки
def load(freq):
    channel_number = RELAY_CONFIG['channel']  # Номер канала релейного модуля
    work_time = (freq * RELAY_CONFIG['fill_factor'] / 100)
    sleep_time = freq - work_time

    while True:
        try:
            relay.write_register(int(channel_number), 256, 0, 6)  # Открываем канал релейного модуля
            time.sleep(int(work_time))
            relay.write_register(int(channel_number), 512, 0, 6)  # Закрываем канал релейного модуля
            time.sleep(int(sleep_time))
            relay.clear_buffers_before_each_transaction = True
        except Exception as e:
            print(f"Ошибка работы релейного модуля: {str(e)}")
        finally:
            relay.clear_buffers_before_each_transaction = True


# Функция для сбора данных с датчиков температуры
def collect_sensor_data(sensor, sensor_name):
    try:
        raw_value = sensor.read_register(1, 1)
        converted_value = convert_temperature(raw_value)
        return converted_value
    except Exception as e:
        logging.error(f"Ошибка при чтении данных с {sensor_name}: {str(e)}")
        return None


def convert_temperature(temperature):
    # Преобразование 16-битного числа в знаковое целое
    signed_int_value = (temperature - 6553.6) if temperature >= 3276.8 else temperature
    return signed_int_value


# Функция для сбора данных с датчика солнечной радиации
def collect_solar_radiation_data(sensor, sensor_name):
    try:
        value = sensor.read_register(0, 0)
        return value
    except Exception as e:
        logging.error(f"Ошибка при чтении данных с {sensor_name}: {str(e)}")
        return None


# Функция для сбора данных с датчика влажности
def collect_humidity_data(sensor, sensor_name):
    try:
        value = sensor.read_register(0, 1)
        return value
    except Exception as e:
        logging.error(f"Ошибка при чтении данных с {sensor_name}: {str(e)}")
        return None


def log_disconnect(last_sent_datetime, timestamp, allowed_users):
    if last_sent_datetime is not None and (timestamp - last_sent_datetime) >= timedelta(hours=1):
        # Уведомление в Telegram
        disconnect_message = f"Отключение обнаружено. Последняя отправка: {last_sent_datetime}, Текущая дата: {timestamp}, Разница: {timestamp - last_sent_datetime}"
        for user_id in allowed_users:
            bot.send_message(user_id, disconnect_message)

        # Запись информации в базу данных
        with open("disconnect_log.txt", "a") as log_file:
            log_file.write(
                f"Последняя отправка: {last_sent_datetime}, Текущая дата: {timestamp}, Разница: {timestamp - last_sent_datetime}\n")


def get_last_sent_datetime(data_path):
    latest_file = max([os.path.join(data_path, f) for f in os.listdir(data_path)], key=os.path.getctime)
    with open(latest_file, "r") as file:
        last_line = file.readlines()[-1]
        last_sent_datetime = dateparser.parse(last_line.split(',')[0])
        return last_sent_datetime


# Основная функция для сбора данных с датчиков, сохранения и отправки на почту
def main(sensor_delay):
    global sensorTH, pyranometer, last_sent_hour, last_csv_file_path, current_hour
    last_sent_hour = None
    last_csv_file_path = None  # Добавляем переменную для хранения пути к файлу предыдущего часа

    while True:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_hour = datetime.now().strftime("%Y-%m-%d %H")
            # last_sent_datetime = get_last_sent_datetime(DATA_PATH)
            # log_disconnect(last_sent_datetime, timestamp, ALLOWED_USERS)

            temperature = collect_sensor_data(sensorTH, "датчик температуры")
            solar_radiation = collect_solar_radiation_data(pyranometer, "датчик солнечной радиации")
            humidity = collect_humidity_data(sensorTH, "датчик влажности")

            if temperature is not None and solar_radiation is not None:
                logging.info(
                    f"Текущий час: {current_hour}, Температура: {temperature}°C, Влажность: {humidity}%, Солнечное излучение: {solar_radiation} W/m²")
                # Разбор и сохранение значений
                result_from_second_program = run_clicker()
                numeric_keys = ["Solar Input V", "Solar Input I", "Solar Input W", "Solar Input KwH", "Extern Input V",
                                "Wind Average DC V", "Wind Average DC I", "Wind Input DC W", "Wind Input KwH",
                                "Motor Rev", "Wind Run Status", "BatV", "Bat Charge I", "Bat Charge W", "Bat Total KwH",
                                "Bat Capacity"]

                numeric_values = [result_from_second_program.get(key, None) for key in numeric_keys]

                csv_filename = datetime.now().strftime("%Y%m%d_%H.csv")
                csv_file_path = os.path.join(DATA_PATH, csv_filename)
                # Добавление заголовков в данные для CSV файла
                headers = [
                    "Timestamp", "Temperature °C", "Humidity %", "Solar Radiation W/m²",
                    "Solar Input V", "Solar Input I", "Solar Input W", "Solar Input KwH",
                    "Extern Input V", "Wind Average DC V", "Wind Average DC I", "Wind Input DC W",
                    "Wind Input KwH", "Motor Rev", "Wind Run Status", "BatV", "Bat Charge I",
                    "Bat Charge W", "Bat Total KwH", "Bat Capacity"
                ]
                # Проверяем, существует ли файл
                file_exists = os.path.isfile(csv_file_path)
                if not file_exists:
                    # Если файл не существует, записываем заголовки
                    with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                data_to_save = [timestamp, temperature, humidity, solar_radiation] + numeric_values

                save_data_to_csv(data_to_save, csv_file_path)

                if last_sent_hour is None:
                    last_sent_hour = current_hour 
                elif current_hour != last_sent_hour:
                    if last_csv_file_path is not None:
                        # Отправляем данные из файла предыдущего часа
                        send_email("Данные с датчиков", "Во вложении данные с датчиков.", last_csv_file_path)
                    last_sent_hour = current_hour
                last_csv_file_path = csv_file_path  # Сохраняем путь к файлу текущего часа
        except Exception as e:
            error_message = f"Ошибка при чтении данных: {str(e)}"
            logging.error(error_message)
        finally:
            sensorTH.clear_buffers_before_each_transaction = True
            pyranometer.clear_buffers_before_each_transaction = True
            sensorTH.clear_buffers_before_each_transaction = True
            time.sleep(sensor_delay)


# Функция для отправки уведомления в Telegram
def send_notification(subject, message):
    try:
        for user_id in ALLOWED_USERS:
            bot.send_message(user_id, f"{subject} {message}")
        logging.info("Уведомление отправлено.")
    except Exception as e:
        error_message = f"Ошибка при отправке уведомления: {str(e)}"
        logging.error(error_message)


# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_CONFIG['token'])


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    condition_button = types.InlineKeyboardButton(text="🌡️ Показания датчиков", callback_data='condition')
    get_data_button = types.InlineKeyboardButton(text="📊 Получить данные", callback_data='getdata')
    status_button = types.InlineKeyboardButton(text="📈 Статус системы", callback_data='status')
    relay_status_button = types.InlineKeyboardButton(text="🖥️ Проверить реле", callback_data='relay_st')
    lamp_on_button = types.InlineKeyboardButton(text="💡 Включить лампу (5 Вт)", callback_data='relay_on')
    lamp_off_button = types.InlineKeyboardButton(text="🚫 Выключить лампу", callback_data='relay_off')
    ip_button = types.InlineKeyboardButton(text="🌐 Получить IP", callback_data='ip')

    markup.row(condition_button, get_data_button, status_button)
    markup.row(relay_status_button, lamp_on_button, lamp_off_button)
    markup.row(ip_button)

    bot.send_message(message.chat.id, "Привет! Я ваш датчиковый бот. Выберите действие:", reply_markup=markup)


# Добавим обработчик для кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    command = call.data

    # Теперь проверяем значение callback_data
    if command == 'condition':
        # Отправляем сообщение с командой /condition
        bot.send_message(call.message.chat.id, "/condition")
    elif command == 'getdata':
        # Отправляем сообщение с командой /getdata
        bot.send_message(call.message.chat.id, "/getdata")
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

@bot.message_handler(commands=['contrinfo'])
def contrinfo_command(message):
    try:
        # Разбор и сохранение значений
        result_from_second_program = run_clicker()

        # Задать порядок ключей, который соответствует порядку в заголовках
        keys_order = [
            "Solar Input V", "Solar Input I", "Solar Input W", "Solar Input KwH",
            "Extern Input V", "Wind Average DC V", "Wind Average DC I", "Wind Input DC W",
            "Wind Input KwH", "Motor Rev", "Wind Run Status", "BatV",
            "Bat Charge I", "Bat Charge W", "Bat Total KwH", "Bat Capacity"
        ]

        # Преобразование числовых значений и формирование строки с данными
        data_str = f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        for key in keys_order:
            value = result_from_second_program[key]
            if isinstance(value, (float, int)):
                data_str += f"{key}: {value}\n"
            else:
                data_str += f"{key}: {value}\n"

        # Отправка красивого сообщения с смайлами
        bot.send_message(message.chat.id, text="🌞 Состояние с контроллера 🌞\n\n" + data_str)

    except Exception as e:
        bot.send_message(message.chat.id, text=f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
       🌡️ /condition - получить текущие показания датчиков
       📊 /getdata - получить данные в формате CSV
       📈 /status - проверить статус системы
       🖥️ /relay_st - проверить статус реле
       💡 /relay_on - включить реле (лампа 5 Вт) 
       🚫 /relay_off - выключить реле (лампа 5 Вт)
       🌐 /ip - получить IP

       Примеры ввода дат:
       📊 /getdata 20231010
       📊 /getdata 20231010 - 20231011
       """
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['getdata'])
def get_data(message):
    user_request = message.text.split()[1:]
    if not user_request:
        bot.reply_to(message, "Пожалуйста, укажите дату или диапазон дат для получения данных. ⏳")
        return

    if user_request[0] == "all":
        for file_name in os.listdir(DATA_PATH):
            file_path = os.path.join(DATA_PATH, file_name)
            with open(file_path, 'rb') as file:
                bot.send_document(message.chat.id, file)
        return

    if user_request[0] == "сегодня":
        today = datetime.now().date()
        start_date = datetime(today.year, today.month, today.day)
        end_date = start_date + timedelta(days=1)
    elif user_request[0] == "вчера":
        yesterday = datetime.now().date() - timedelta(days=1)
        start_date = datetime(yesterday.year, yesterday.month, yesterday.day)
        end_date = start_date + timedelta(days=1)
    else:
        requested_date = user_request[0]

        # Пробуем найти файлы в формате "ггггммдд_чч"
        requested_datetime = None
        if '_' in requested_date:
            try:
                requested_datetime = datetime.strptime(requested_date, "%Y%m%d_%H")
            except ValueError:
                requested_datetime = None

        # Модифицируем запрос, чтобы добавить символ '_' в конце, чтобы искать все файлы, начинающиеся с этой даты
        modified_request = requested_date + "_"

        for file_name in os.listdir(DATA_PATH):
            if file_name.startswith(requested_date) or (requested_datetime and file_name.startswith(modified_request)):
                file_path = os.path.join(DATA_PATH, file_name)
                with open(file_path, 'rb') as file:
                    bot.send_document(message.chat.id, file)
        return

    for file_name in os.listdir(DATA_PATH):
        if file_name.startswith(user_request[0]):
            file_path = os.path.join(DATA_PATH, file_name)
            with open(file_path, 'rb') as file:
                bot.send_document(message.chat.id, file)
    bot.reply_to(message, "Неверный формат запроса. Пожалуйста, проверьте и попробуйте снова. ⚠️")


@bot.message_handler(commands=['condition'])
def get_condition(message):
    try:
        temperature = collect_sensor_data(sensorTH, "датчик температуры")
        solar_radiation = collect_solar_radiation_data(pyranometer, "датчик солнечной радиации")
        humidity = collect_humidity_data(sensorTH, "датчик влажности")

        if temperature is not None and solar_radiation is not None:
            bot.reply_to(
                message,
                f"🌡️ Текущие показания: Температура: {temperature}°C, Влажность: {humidity}%,  Солнечное излучение: {solar_radiation} W/m²"
            )
        else:
            bot.reply_to(message, "Ошибка при чтении данных. Попробуйте позже. ⚠️")
    except Exception as e:
        bot.reply_to(message, f"Ошибка при чтении данных: {str(e)} ⚠️")


@bot.message_handler(commands=['status'])
def get_status(message):
    global last_sent_timestamp, last_high_temperature_notification_sent, last_low_temperature_notification_sent
    status_message = "Статус системы: ✅ Всё в порядке. Программа работает."

    if last_sent_timestamp:
        status_message += f"\nПоследние данные были отправлены на почту: {last_sent_timestamp}."
    else:
        status_message += "\nДанные ещё не отправлялись на почту."

    if (
            last_high_temperature_notification_sent
            and datetime.now() - last_high_temperature_notification_sent < timedelta(
        hours=NOTIFICATION_CONFIG['notification_interval_hours'])
    ):
        status_message += f"\nПоследнее уведомление о высокой температуре было отправлено {last_high_temperature_notification_sent}."

    if (
            last_low_temperature_notification_sent
            and datetime.now() - last_low_temperature_notification_sent < timedelta(
        hours=NOTIFICATION_CONFIG['notification_interval_hours'])
    ):
        status_message += f"\nПоследнее уведомление о низкой температуре было отправлено {last_low_temperature_notification_sent}."

    bot.reply_to(message, status_message)


@bot.message_handler(commands=['ip'])
def get_ip_command(message):
    if message.from_user.id in ALLOWED_USERS:
        ip_address = get_current_ip()
        bot.reply_to(message, f"Текущий IP-адрес: {ip_address} 🌐")
    else:
        bot.reply_to(message, "У вас нет разрешения на выполнение этой команды.")


@bot.message_handler(commands=['relay_st'])
def relay_status(message):
    channel_number = RELAY_CONFIG['channel']  # Номер канала релейного модуля
    relay_state = relay.read_register(int(channel_number), 0)  # Читаем состояние канала релейного модуля
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    relay_status = (f"Relay channel {channel_number} is {'On' if relay_state == 1 else 'Off'} at {timestamp}")
    bot.reply_to(message, relay_status)


@bot.message_handler(commands=['relay_on'])
def relay_on(message):
    channel_number = RELAY_CONFIG['channel']  # Номер канала релейного модуля
    relay.write_register(int(channel_number), 256, 0, 6)  # Открываем канал релейного модуля
    time.sleep(1)
    relay_state = relay.read_register(int(channel_number), 0)  # Читаем состояние канала релейного модуля
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    relay_status = (f"Relay channel {channel_number} is {'On' if relay_state == 1 else 'Off'} at {timestamp}")
    relay.clear_buffers_before_each_transaction = True
    bot.reply_to(message, relay_status)


@bot.message_handler(commands=['relay_off'])
def relay_off(message):
    channel_number = RELAY_CONFIG['channel']  # Номер канала релейного модуля
    relay.write_register(int(channel_number), 512, 0, 6)  # Закрываем канал релейного модуля
    time.sleep(1)
    relay_state = relay.read_register(int(channel_number), 0)  # Читаем состояние канала релейного модуля
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    relay_status = (f"Relay channel {channel_number} is {'On' if relay_state == 1 else 'Off'} at {timestamp}")
    relay.clear_buffers_before_each_transaction = True
    bot.reply_to(message, relay_status)


@bot.message_handler(commands=['downloadlog'])
def download_log(message):
    try:
        # Проверяем, существует ли файл лога
        if os.path.exists(log_file_path):
            # Отправляем лог-файл как документ
            with open(log_file_path, 'rb') as log_file:
                bot.send_document(message.chat.id, log_file)
        else:
            bot.reply_to(message, "Файл лога не найден.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка при скачивании лога: {str(e)}")


def get_current_ip():
    try:
        response = requests.get("http://ipinfo.io/ip")
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "Error: Unable to fetch IP address"
    except Exception as e:
        return f"Error: {str(e)}"


def run_bot():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Ошибка с Telegram ботом: {e}")
            time.sleep(10)


if __name__ == "__main__":
    t1 = Thread(target=main, args=(SENSOR_TH_CONFIG['delay'],))
    t1.start()
    t2 = Thread(target=run_bot)
    t2.start()
    t3 = Thread(target=load, args=(60,))
    # t3.start()
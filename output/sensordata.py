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
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from configurate import SENSOR_TH_CONFIG, SENSOR_PYRANOMETER_CONFIG, Mail_CONFIG, DATA_PATH_Conf, TELEGRAM_CONFIG, ALLOWED_USERS, OPENVPN_CONFIG, REALVNC_CONFIG, NOTIFICATION_CONFIG
from datetime import datetime, timedelta
from telebot import types

# Настройка логирования
logging.basicConfig(filename='program_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
last_sent_timestamp = None
last_high_temperature_notification_sent = None
last_low_temperature_notification_sent = None

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

# Функция для сбора данных с датчиков температуры и влажности
def collect_sensor_data(sensor, sensor_name):
    try:
        value = sensor.read_register(1, 1)
        return value
    except Exception as e:
        logging.error(f"Ошибка при чтении данных с {sensor_name}: {str(e)}")
        return None

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

# Основная функция для сбора данных с датчиков, сохранения и отправки на почту
# Основная функция для сбора данных с датчиков, сохранения и отправки на почту
def main(sensor_delay):
    global sensorTH, pyranometer
    last_sent_hour = None
    while True:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_hour = datetime.now().hour

            temperature = collect_sensor_data(sensorTH, "датчик температуры")
            solar_radiation = collect_solar_radiation_data(pyranometer, "датчик солнечной радиации")
            humidity = collect_humidity_data(sensorTH, "датчик влажности")

            if temperature is not None and solar_radiation is not None:
                logging.info(f"Текущий час: {current_hour}, Температура: {temperature}°C, Влажность: {humidity}%, Солнечное излучение: {solar_radiation} W/m²")

                # Сохранение данных в CSV файл
                data_to_save = [timestamp, temperature, humidity, solar_radiation]
                csv_filename = f"sensor_data_{timestamp.split()[0]}.csv"
                csv_file_path = os.path.join(DATA_PATH, csv_filename)
                save_data_to_csv(data_to_save, csv_file_path)
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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    condition_button = types.KeyboardButton("🌡️ Показания датчиков")
    data_button = types.KeyboardButton("📊 Получить данные")
    status_button = types.KeyboardButton("📈 Статус системы")
    openvpn_button = types.KeyboardButton("🔒 Запустить VPN")
    vnc_button = types.KeyboardButton("🖥️ Запустить VNC")
    ip_button = types.KeyboardButton("🌐 Получить IP")

    markup.row(condition_button, data_button, status_button)
    markup.row(openvpn_button, vnc_button, ip_button)

    bot.send_message(message.chat.id, "Привет! Я ваш датчиковый бот. Выберите действие:", reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
       Это справка:
       🌡️ /condition - получить текущие показания датчиков
       📊 /getdata - получить данные в формате CSV
       📈 /status - проверить статус системы
       🔒 /openvpn - запустить VPN
       🖥️ /vnc - запустить VNC
       🌐 /ip - получить IP
       🔄 /restartpi - перезапустить Raspberry Pi

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

    date_format = dateparser.parse(user_request[0])

    if date_format:
        for file_name in os.listdir(DATA_PATH):
            file_timestamp = datetime.strptime(file_name.split("_")[0], "%Y%m%d")
            if file_timestamp.date() == date_format.date():
                file_path = os.path.join(DATA_PATH, file_name)
                with open(file_path, 'rb') as file:
                    bot.send_document(message.chat.id, file)
        return

    if len(user_request) == 1:
        bot.reply_to(message, "Не удалось найти данные для указанной даты. ⚠️")
    else:
        start_date_format = dateparser.parse(user_request[0])
        end_date_format = dateparser.parse(user_request[1])

        if start_date_format and end_date_format:
            for file_name in os.listdir(DATA_PATH):
                file_timestamp = datetime.strptime(file_name.split("_")[0], "%Y%m%d")
                if start_date_format.date() <= file_timestamp.date() <= end_date_format.date():
                    file_path = os.path.join(DATA_PATH, file_name)
                    with open(file_path, 'rb') as file:
                        bot.send_document(message.chat.id, file)
            return

        bot.reply_to(message, "Неверный формат запроса. Пожалуйста, проверьте и попробуйте снова. ⚠️")

@bot.message_handler(commands=['condition'])
def get_condition(message):
    try:
        temperature = collect_sensor_data(sensorTH, "датчик температуры")
        solar_radiation = collect_solar_radiation_data(pyranometer, "датчик солнечной радиации")
        humidity = collect_sensor_data(sensorTH, "датчик влажности")

        if temperature is not None and solar_radiation is not None:
            bot.reply_to(
                message, f"🌡️ Текущие показания: Температура: {temperature}°C, Влажность: {humidity}%,  Солнечное излучение: {solar_radiation} W/m²"
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
        and datetime.now() - last_high_temperature_notification_sent < timedelta(hours=NOTIFICATION_CONFIG['notification_interval_hours'])
    ):
        status_message += f"\nПоследнее уведомление о высокой температуре было отправлено {last_high_temperature_notification_sent}."

    if (
        last_low_temperature_notification_sent
        and datetime.now() - last_low_temperature_notification_sent < timedelta(hours=NOTIFICATION_CONFIG['notification_interval_hours'])
    ):
        status_message += f"\nПоследнее уведомление о низкой температуре было отправлено {last_low_temperature_notification_sent}."

    bot.reply_to(message, status_message)

@bot.message_handler(commands=['openvpn'])
def run_openvpn_command(message):
    threading.Thread(target=run_openvpn).start()
    bot.reply_to(message, "Запущен процесс подключения к VPN. Ожидайте... 🔒")

@bot.message_handler(commands=['ip'])
def get_ip_command(message):
    if message.from_user.id in ALLOWED_USERS:
        ip_address = get_current_ip()
        bot.reply_to(message, f"Текущий IP-адрес: {ip_address} 🌐")
    else:
        bot.reply_to(message, "У вас нет разрешения на выполнение этой команды.")
@bot.message_handler(commands=['getip'])
def get_ip_command(message):
    if message.from_user.id in ALLOWED_USERS:
        ip_address = get_current_ip()
        bot.reply_to(message, f"Текущий IP-адрес: {ip_address} 🌐")
    else:
        bot.reply_to(message, "У вас нет разрешения на выполнение этой команды.")
@bot.message_handler(commands=['openvpn'])
def run_openvpn_command(message):
    if message.from_user.id in ALLOWED_USERS:
        threading.Thread(target=run_openvpn).start()
        bot.reply_to(message, "Запущен процесс подключения к VPN. Ожидайте... 🔒")
    else:
        bot.reply_to(message, "У вас нет разрешения на выполнение этой команды.")

@bot.message_handler(commands=['vnc'])
def run_vnc_command(message):
    if message.from_user.id in ALLOWED_USERS:
        threading.Thread(target=run_realvnc_and_send_ip, args=(message,)).start()
    else:
        bot.reply_to(message, "У вас нет разрешения на выполнение этой команды.")
@bot.message_handler(commands=['restartpi'])
def restart_raspberry_pi(message):
    if message.from_user.id in ALLOWED_USERS:
        os.system("sudo reboot")
        bot.reply_to(message, "Перезапуск Raspberry Pi запущен. Пожалуйста, подождите...")
    else:
        bot.reply_to(message, "У вас нет разрешения на выполнение этой команды. Только администраторы могут перезапустить Raspberry Pi.")

def run_realvnc_and_send_ip(message):
    try:
        command = REALVNC_CONFIG['command']
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   universal_newlines=True)

        # Заведем флаг для определения, был ли IP-адрес найден
        ip_found = False

        # Сюда будем записывать все выводы для отладки
        full_output = ""

        # Ждем, пока RealVNC Server выдаст IP-адрес и порт
        for line in process.stdout:
            # Записываем полный вывод для отладки
            full_output += line

            if "New desktop is" in line:
                # Извлекаем IP-адрес и порт из строки
                parts = line.strip().split()
                if len(parts) >= 3:
                    ip_address = parts[-1]
                    ip_found = True
                    break

        if ip_found:
            bot.send_message(message.chat.id, f"RealVNC Server запущен. IP-адрес и порт: {ip_address}")
        else:
            bot.send_message(message.chat.id, "Не удалось извлечь IP-адрес из RealVNC Server.")

        # Записываем полный вывод в лог
        logging.info("Полный вывод RealVNC Server:\n" + full_output)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при запуске RealVNC Server: {e}")
        logging.error(f"Ошибка при запуске RealVNC Server: {e}")
def run_realvnc():
    try:
        command = REALVNC_CONFIG['command']
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        # Ждем, пока RealVNC Server выдаст IP-адрес и порт
        ip_address = None
        for line in process.stdout:
            if "New desktop is" in line:
                # Извлекаем IP-адрес и порт из строки
                parts = line.strip().split()
                if len(parts) >= 3:
                    ip_address = parts[-1]

        if ip_address:
            # Отправляем IP-адрес и порт в Telegram
            bot.send_message(TELEGRAM_CONFIG['your_chat_id'], f"RealVNC Server запущен. IP-адрес и порт: {ip_address}")
        else:
            logging.error("Не удалось извлечь IP-адрес из RealVNC Server.")
    except Exception as e:
        logging.error(f"Ошибка при запуске RealVNC Server: {e}")

def run_openvpn():
    try:
        command = OPENVPN_CONFIG['command']
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   universal_newlines=True)

        output, _ = process.communicate()

        if process.returncode == 0:
            logging.info("OpenVPN успешно запущен.")
        else:
            logging.error(f"Ошибка при запуске OpenVPN. Ошибка: {output}")
    except Exception as e:
        logging.error(f"Ошибка при запуске OpenVPN: {e}")
def get_current_ip():
    try:
        # Получаем IP-адрес хоста
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        return host_ip
    except Exception as e:
        return str(e)

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Ошибка с Telegram ботом: {e}")
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=main, args=(SENSOR_TH_CONFIG['delay'],)).start()
    threading.Thread(target=run_bot).start()

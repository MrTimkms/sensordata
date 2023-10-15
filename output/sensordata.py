import minimalmodbus
import time
import os
import csv
import smtplib
import logging
import telebot
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from configurate import SENSOR_TH_CONFIG, SENSOR_PYRANOMETER_CONFIG, Mail_CONFIG, DATA_PATH_Conf, TELEGRAM_CONFIG, ALLOWED_USERS, OPENVPN_CONFIG, REALVNC_CONFIG
from datetime import datetime
from telebot import types

# Настройка логирования
logging.basicConfig(filename='program_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
last_sent_timestamp = None  # глобальная переменная для хранения времени последней отправки данных

# Путь для сохранения данных
DATA_PATH = os.path.join(os.getcwd(), DATA_PATH_Conf['DownloadedAttachments'])

# Проверка и создание папки для данных, если ее нет
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
    msg['To'] = login  # Отправка письма себе
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
# Основная функция для сбора данных с датчиков, сохранения и отправки на почту
def main(sensor_delay):
    global sensorTH, pyranometer
    last_sent_hour = None  # Час последней отправки
    while True:  # Бесконечный цикл
        try:
            current_hour = datetime.now().hour

            if last_sent_hour is None:
                last_sent_hour = (current_hour - 1) % 24  # Используйте % 24, чтобы перейти к предыдущему часу в цикле 24 часа

            if current_hour != last_sent_hour:  # Если текущий час не равен предыдущему часу, то отправляем данные
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                temperature = sensorTH.read_register(1, 1)
                humidity = sensorTH.read_register(0, 1)
                solar_radiation = pyranometer.read_register(0, 0)

                logging.info(
                    f"Текущий час: {current_hour}, Температура: {temperature}, Влажность: {humidity}, Солнечное излучение: {solar_radiation}")

                file_name = datetime.now().strftime("%Y%m%d_%H.csv")
                file_path = os.path.join(DATA_PATH, file_name)
                save_data_to_csv([timestamp, temperature, humidity, solar_radiation], file_path)

                # Если текущий час отличается от часа последней отправки, отправляем данные на почту
                send_email("Данные с датчиков", "Во вложении данные с датчиков.", file_path)
                last_sent_hour = current_hour

        except Exception as e:
            error_message = f"Ошибка при чтении данных: {str(e)}"
            logging.error(error_message)

        finally:
            sensorTH.clear_buffers_before_each_transaction = True
            pyranometer.clear_buffers_before_each_transaction = True
            time.sleep(sensor_delay)

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_CONFIG['TOKEN'])

# Создание клавиатур
def create_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    command_button = types.KeyboardButton('/commands')
    condition_button = types.KeyboardButton('📈 /condition')
    status_button = types.KeyboardButton('📊 /status')
    getdata_button = types.KeyboardButton('📂 /getdata')
    openvpn_button = types.KeyboardButton('🔒 /openvpn')
    ip_button = types.KeyboardButton('🌐 /ip')
    realvnc_button = types.KeyboardButton('💻 /realvnc')
    keyboard.add(command_button, condition_button, status_button, getdata_button, openvpn_button, ip_button, realvnc_button)
    return keyboard

# Обработчики команд
@bot.message_handler(commands=['start'])
def send_welcome(message):
    logging.info(f"Received command: /start or /help from chat ID: {message.chat.id}")
    bot.reply_to(message, "Привет! Я ваш датчиковый бот. Используйте кнопки или команды для взаимодействия.", reply_markup=create_main_keyboard())

@bot.message_handler(commands=['commands'])
def send_commands(message):
    bot.reply_to(message, "Доступные команды: /commands, /condition, /status, /getdata, /openvpn, /ip, /realvnc")

# Остальные обработчики остаются без изменений

# Запуск бота
if __name__ == "__main__":
    threading.Thread(target=main, args=(5,)).start()
    threading.Thread(target=run_bot).start()

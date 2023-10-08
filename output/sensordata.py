# -*- coding: utf-8 -*-
import minimalmodbus
import time
from datetime import datetime
import os
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from configurate import SENSOR_TH_CONFIG, SENSOR_PYRANOMETER_CONFIG, Mail_CONFIG, DATA_PATH_Conf

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
        print("Вложение не найдено. Отправка без него.")
    
    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(login, password)
        text = msg.as_string()
        server.sendmail(login, login, text)
        server.quit()
        print("Письмо успешно отправлено.")
    except Exception as e:
        print("Ошибка при отправке письма: {}".format(str(e)))

# Основная функция для сбора данных с датчиков, сохранения и отправки на почту
def main(sensor_delay):
    sensorTH = configure_sensor(SENSOR_TH_CONFIG)
    pyranometer = configure_sensor(SENSOR_PYRANOMETER_CONFIG)
    last_sent_hour = None  # Час последней отправки
    
    while True:  # Бесконечный цикл
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_hour = datetime.now().hour
            
            temperature = sensorTH.read_register(1, 1)
            humidity = sensorTH.read_register(0, 1)
            solar_radiation = pyranometer.read_register(0, 0)
            
            print("Текущий час: {}, Температура: {}, Влажность: {}, Солнечное излучение: {}".format(current_hour, temperature, humidity, solar_radiation))
            
            file_name = datetime.now().strftime("%Y%m%d_%H.csv")
            file_path = os.path.join(DATA_PATH, file_name)
            save_data_to_csv([timestamp, temperature, humidity, solar_radiation], file_path)
            
            # Если текущий час отличается от часа последней отправки, отправляем данные на почту
            if last_sent_hour != current_hour:
                send_email("Данные с датчиков", "Во вложении данные с датчиков.", file_path)
                last_sent_hour = current_hour
              
        except Exception as e:
            print("Ошибка при чтении данных: {}".format(str(e)))
        
        finally:
            sensorTH.clear_buffers_before_each_transaction = True
            pyranometer.clear_buffers_before_each_transaction = True
            time.sleep(sensor_delay)

if __name__ == "__main__":
    main(5)  # Задержка 5 секунд
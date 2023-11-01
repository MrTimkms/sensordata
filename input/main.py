import imaplib
import email
import os
import re
import time
import sqlite3
import csv
import dash
import plotly.express as px
from dash import dcc, html
from config import IMAP_CONFIG, DOWNLOAD_PATH
# Путь к базе данных SQLite
DATABASE_PATH = os.path.join(os.getcwd(), "solar_data.db")
# Проверка и создание папки для вложений, если ее нет

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)
def download_all_attachments():
    # Подключение к почтовому серверу
    mail = imaplib.IMAP4_SSL(IMAP_CONFIG['server'], IMAP_CONFIG['port'])
    mail.login(IMAP_CONFIG['login'], IMAP_CONFIG['password'])
    mail.select('inbox')

    # Поиск всех непрочитанных писем от gisknastu@yandex.ru
    result, email_ids = mail.search(None, '(UNSEEN FROM "gisknastu@yandex.ru")')
    if result != "OK":
        print("Ошибка при поиске писем.")
        return

    for email_id in email_ids[0].split():
        mail_data = mail.fetch(email_id, '(RFC822)')[1]
        raw_email = mail_data[0][1]
        email_message = email.message_from_bytes(raw_email)

        # Если у письма есть вложения, сохраняем их
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            file_name = part.get_filename()
            print(f"Попытка скачать вложение: {file_name}")

            # Проверяем, соответствует ли имя файла нужному формату (годмесяцдень_час.csv)
            if re.match(r'\d{8}_\d{2}\.csv', file_name):
                file_path = os.path.join(DOWNLOAD_PATH, file_name)
                with open(file_path, 'wb') as file:
                    file.write(part.get_payload(decode=True))
                print(f"Вложение {file_name} сохранено")

                # Читаем данные из файла и вставляем их в базу данных
                with open(file_path, 'r') as csv_file:
                    csv_reader = csv.reader(csv_file)
                    for row in csv_reader:
                        if len(row) < 4:
                            print(f"Пропущена строка CSV из-за недостаточного количества столбцов: {row}")
                            continue

                        datetime = row[0]

                        try:
                            temperature = float(row[1])
                            humidity = float(row[2])
                            solar_radiation = float(row[3])
                        except ValueError:
                            print(f"Пропущена строка CSV из-за неверных данных: {row}")
                            continue

                        insert_solar_data(city_id=4853, datetime=datetime, temperature=temperature, humidity=humidity,
                                          solar_radiation=solar_radiation)

    # Закрытие соединения с почтовым сервером
    mail.logout()
def create_solar_data_table():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # Создание таблицы weathergis
    c.execute('''CREATE TABLE IF NOT EXISTS weathergis (
                    unique_id INTEGER PRIMARY KEY NOT NULL,
                    city_id INTEGER NOT NULL,
                    datetime DATETIME NOT NULL,
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL,
                    solar_radiation REAL NOT NULL
                )''')

    conn.commit()
    conn.close()
def insert_solar_data(city_id, datetime, temperature, humidity, solar_radiation):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # Создание уникального идентификатора для записи без пробелов и разделителей
    original_unique_id = f"{city_id}{datetime}"
    compact_unique_id = original_unique_id.replace(" ", "").replace("-", "").replace(":", "")

    c.execute(
        "INSERT OR IGNORE INTO weathergis (unique_id, city_id, datetime, temperature, humidity, solar_radiation) VALUES (?, ?, ?, ?, ?, ?)",
        (compact_unique_id, city_id, datetime, temperature, humidity, solar_radiation))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_solar_data_table()  # Создать таблицу перед использованием
    app.run_server(debug=True)
    while True:
        download_all_attachments()
        print("Ожидание следующей проверки...")
        time.sleep(3600)  # Пауза в 1 час (3600 секунд)

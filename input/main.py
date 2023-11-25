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
import shutil
from config import IMAP_CONFIG, DOWNLOAD_PATH
from multiprocessing import Process
import threading
# Путь к базе данных SQLite
DATABASE_PATH = os.path.join(os.getcwd(), "solar_data.db")
DATABASE_PATH_dash = os.path.join(os.getcwd(), "solar_data_dash.db")
# Установка соединения с базой данных SQLite
#conn = sqlite3.connect('solar_data.db')
#cursor = conn.cursor()

# Создание экземпляра Dash приложения
app = dash.Dash(__name__)
def copy_database():
    original_db_path = 'solar_data.db'
    backup_db_path = 'solar_data_dash.db'
    shutil.copy(original_db_path, backup_db_path)

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

def download_all_attachments():
    print("Попытка загрузить вложения...")
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

def create_graphs():
    # Установка соединения с базой данных SQLite
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Здесь создайте графики fig1, fig2 и fig3 с использованием данных из базы данных
    # Пример:
    cursor.execute("SELECT datetime, temperature, humidity, solar_radiation FROM weathergis")
    rows = cursor.fetchall()

    # Разделение данных на списки
    dates, temperatures, humidities, solar_radiations = zip(*rows)

    # Создание графика для солнечной радиации
    fig1 = px.line(x=dates, y=solar_radiations, title='Солнечная радиация')
    fig1.update_xaxes(title_text='Дата')
    fig1.update_yaxes(title_text='Солнечная радиация (W/m²)')

    # Создание графика для температуры
    fig2 = px.line(x=dates, y=temperatures, title='Температура')
    fig2.update_xaxes(title_text='Дата')
    fig2.update_yaxes(title_text='Температура (°C)')

    # Создание графика для влажности
    fig3 = px.line(x=dates, y=humidities, title='Влажность')
    fig3.update_xaxes(title_text='Дата')
    fig3.update_yaxes(title_text='Влажность (%)')

    # Закрытие соединения с базой данных
    conn.close()

    return fig1, fig2, fig3
def main_process():
    while True:
        download_all_attachments()
        print("Ожидание следующей проверки...")
        time.sleep(3600)  # Пауза в 1 час (3600 секунд)

if __name__ == "__main__":
    #copy_database()  # Копировать базу данных
    #create_solar_data_table()  # Создать таблицу перед использованием
    fig1, fig2, fig3 = create_graphs()  # Создать графики
    # Определите атрибут layout до запуска сервера
    app.layout = html.Div([
        dcc.Graph(figure=fig1),
        dcc.Graph(figure=fig2),
        dcc.Graph(figure=fig3)
    ])
    threading.Thread(target=app.run_server).start()
    threading.Thread(target=main_process()).start()

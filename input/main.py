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
def create_additional_table():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS additional_data (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     unique_id INTEGER NOT NULL,
                     datetime DATETIME NOT NULL,
                     solar_input_1 TEXT,
                     solar_input_w TEXT,
                     solar_input_kwh TEXT,
                     extern_input_v TEXT,
                     batv TEXT,
                     bat_charge_1 TEXT,
                     bat_charge_w TEXT,
                     bat_total_kwh TEXT,
                     bat_capacity TEXT,
                     FOREIGN KEY (unique_id) REFERENCES weathergis(unique_id)
                 )''')

    conn.commit()
    conn.close()

def insert_solar_data(city_id, datetime, temperature, humidity, solar_radiation, solar_input_1, solar_input_w, solar_input_kwh, extern_input_v, batv, bat_charge_1, bat_charge_w, bat_total_kwh, bat_capacity):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # Создание уникального идентификатора для записи без пробелов и разделителей
    original_unique_id = f"{city_id}{datetime}"
    compact_unique_id = original_unique_id.replace(" ", "").replace("-", "").replace(":", "")

    # Вставка данных в основную таблицу
    c.execute(
        "INSERT OR IGNORE INTO weathergis (unique_id, city_id, datetime, temperature, humidity, solar_radiation) VALUES (?, ?, ?, ?, ?, ?)",
        (compact_unique_id, city_id, datetime, temperature, humidity, solar_radiation))

    # Вставка данных в дополнительную таблицу
    c.execute(
        "INSERT OR IGNORE INTO additional_data (unique_id, datetime, solar_input_1, solar_input_w, solar_input_kwh, extern_input_v, batv, bat_charge_1, bat_charge_w, bat_total_kwh, bat_capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (compact_unique_id, datetime, solar_input_1, solar_input_w, solar_input_kwh, extern_input_v, batv, bat_charge_1, bat_charge_w, bat_total_kwh, bat_capacity))

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

                    # Если заголовка нет, создайте заголовок со старыми полями
                    header = next(csv_reader, None)
                    if not header:
                        header = ["datetime", "temperature", "humidity", "solar_radiation"]

                    for row in csv_reader:
                        datetime = row[0]

                        # Если есть новые поля в файле, используйте их значения
                        if len(row) >= 13:
                            solar_input_1 = row[4]
                            solar_input_w = row[5]
                            solar_input_kwh = row[6]
                            extern_input_v = row[7]
                            batv = row[8]
                            bat_charge_1 = row[9]
                            bat_charge_w = row[10]
                            bat_total_kwh = row[11]
                            bat_capacity = row[12]
                        else:
                            # Если нет новых полей, оставьте их значения пустыми
                            solar_input_1 = solar_input_w = solar_input_kwh = extern_input_v = batv = bat_charge_1 = bat_charge_w = bat_total_kwh = bat_capacity = ""

                        try:
                            temperature = float(row[1])
                            humidity = float(row[2])
                            solar_radiation = float(row[3])
                        except ValueError:
                            print(f"Пропущена строка CSV из-за неверных данных: {row}")
                            continue

                        insert_solar_data(city_id=4853, datetime=datetime, temperature=temperature, humidity=humidity,
                                          solar_radiation=solar_radiation, solar_input_1=solar_input_1,
                                          solar_input_w=solar_input_w,
                                          solar_input_kwh=solar_input_kwh, extern_input_v=extern_input_v, batv=batv,
                                          bat_charge_1=bat_charge_1, bat_charge_w=bat_charge_w,
                                          bat_total_kwh=bat_total_kwh,
                                          bat_capacity=bat_capacity)

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

    # Здесь создайте графики для новой таблицы additional_data
    cursor.execute(
        "SELECT datetime, solar_input_1, solar_input_w, solar_input_kwh, extern_input_v, batv, bat_charge_1, bat_charge_w, bat_total_kwh, bat_capacity FROM additional_data")
    rows_additional = cursor.fetchall()

    # Разделение данных на списки
    (
        dates_additional,
        solar_input_1,
        solar_input_w,
        solar_input_kwh,
        extern_input_v,
        batv,
        bat_charge_1,
        bat_charge_w,
        bat_total_kwh,
        bat_capacity,
    ) = zip(*rows_additional)

    # Создание графика для Solar Input 1 (Scatter с линиями)
    fig4 = px.scatter(x=dates_additional, y=solar_input_1, title='Solar Input 1 (additional_data)',
                      labels={'x': 'Дата', 'y': 'Solar Input 1'})
    fig4.update_xaxes(title_text='Дата')
    fig4.update_yaxes(title_text='Solar Input 1')

    # Создание графика для Solar Input W (круговая диаграмма)
    fig5 = px.pie(names=dates_additional, values=solar_input_w, title='Solar Input W (additional_data)')

    # Создание графика для Solar Input KwH (Scatter с линиями)
    fig6 = px.scatter(x=dates_additional, y=solar_input_kwh, title='Solar Input KwH (additional_data)',
                      labels={'x': 'Дата', 'y': 'Solar Input KwH'})
    fig6.update_xaxes(title_text='Дата')
    fig6.update_yaxes(title_text='Solar Input KwH')

    # Создание графика для Extern Input V (Гистограмма)
    fig7 = px.histogram(x=dates_additional, y=extern_input_v, title='Extern Input V (additional_data)',
                        labels={'x': 'Дата', 'y': 'Extern Input V'}, nbins=20)
    fig7.update_xaxes(title_text='Дата')
    fig7.update_yaxes(title_text='Extern Input V')

    # Создание графика для BatV (Scatter с линиями)
    fig8 = px.scatter(x=dates_additional, y=batv, title='BatV (additional_data)', labels={'x': 'Дата', 'y': 'BatV'})
    fig8.update_xaxes(title_text='Дата')
    fig8.update_yaxes(title_text='BatV')

    # Создание графика для Bat Charge 1 (Линейный график)
    fig9 = px.line(x=dates_additional, y=bat_charge_1, title='Bat Charge 1 (additional_data)',
                   labels={'x': 'Дата', 'y': 'Bat Charge 1'})
    fig9.update_xaxes(title_text='Дата')
    fig9.update_yaxes(title_text='Bat Charge 1')

    # Создание графика для Bat Charge W (Линейный график)
    fig10 = px.line(x=dates_additional, y=bat_charge_w, title='Bat Charge W (additional_data)',
                    labels={'x': 'Дата', 'y': 'Bat Charge W'})
    fig10.update_xaxes(title_text='Дата')
    fig10.update_yaxes(title_text='Bat Charge W')

    # Создание графика для Bat Total KwH (Scatter 3D)
    fig11 = px.scatter_3d(x=dates_additional, y=bat_total_kwh, z=[0] * len(bat_total_kwh),
                          title='Bat Total KwH (additional_data)',
                          labels={'x': 'Дата', 'y': 'Bat Total KwH', 'z': 'Dummy'})

    # Создание графика для Bat Capacity (Scatter с линиями)
    fig12 = px.scatter(x=dates_additional, y=bat_capacity, title='Bat Capacity (additional_data)',
                       labels={'x': 'Дата', 'y': 'Bat Capacity'})
    fig12.update_xaxes(title_text='Дата')
    fig12.update_yaxes(title_text='Bat Capacity')

    # Закрытие соединения с базой данных
    conn.close()

    return fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11, fig12
def main_process():
    while True:
        download_all_attachments()
        print("Ожидание следующей проверки...")
        time.sleep(3600)  # Пауза в 1 час (3600 секунд)

if __name__ == "__main__":
    #copy_database()  # Копировать базу данных
    #create_solar_data_table()  # Создать таблицу перед использованием
    #create_additional_table()
    fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11, fig12 = create_graphs()  # Создать графики
    # Определите атрибут layout до запуска сервера
    app.layout = html.Div([
        dcc.Graph(figure=fig1),
        dcc.Graph(figure=fig2),
        dcc.Graph(figure=fig3),
        dcc.Graph(figure=fig4),
        dcc.Graph(figure=fig5),
        dcc.Graph(figure=fig6),
        dcc.Graph(figure=fig7),
        dcc.Graph(figure=fig8),
        dcc.Graph(figure=fig9),
        dcc.Graph(figure=fig10),
        dcc.Graph(figure=fig11),
        dcc.Graph(figure=fig12)
    ])
    threading.Thread(target=app.run_server).start()
    threading.Thread(target=main_process()).start()

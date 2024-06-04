import logging
import os
import sqlite3
import requests

DATABASE_PATH = os.path.join(os.getcwd(), '1.3_SolarData_ExpU.db')
db_path_cloud= os.path.join(os.getcwd(),  '1.2_WeatherData_VS-1_2024-03-20_.db')
def create_solar_data_table():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # Создание таблицы weathergis
    c.execute('''CREATE TABLE "weathergis" (
                "unique_id"	INTEGER NOT NULL,
                "city_id"	INTEGER NOT NULL,
                "datetime"	DATETIME NOT NULL,
                "temperature"	REAL NOT NULL,
                "humidity"	REAL NOT NULL,
                "solar_radiation"	REAL NOT NULL,
                PRIMARY KEY("unique_id")
            );''')

    conn.commit()
    conn.close()
def create_additional_table():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE "additional_data" (
                    "id"	INTEGER,
                    "unique_id"	INTEGER NOT NULL,
                    "datetime"	DATETIME NOT NULL,
                    "solar_input_I"	TEXT,
                    "solar_input_W"	TEXT,
                    "solar_input_kWh"	TEXT,
                    "extern_input_V"	TEXT,
                    "bat_charge_V"	TEXT,
                    "bat_charge_I"	TEXT,
                    "bat_charge_W"	TEXT,
                    "bat_total_kWh"	TEXT,
                    "bat_capacity"	TEXT,
                    PRIMARY KEY("id" AUTOINCREMENT),
                    FOREIGN KEY("unique_id") REFERENCES "weathergis"("unique_id")
                );''')

    conn.commit()
    conn.close()
def insert_solar_data(city_id, datetime, temperature, humidity, solar_radiation, solar_input_I, solar_input_W, solar_input_kWh, extern_input_V, bat_charge_V, bat_charge_I, bat_charge_W, bat_total_kWh, bat_capacity):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        original_unique_id = f"{city_id}{datetime}"
        compact_unique_id = original_unique_id.replace(" ", "").replace("-", "").replace(":", "")

        # Обработка данных
        temperature = process_data(temperature)
        humidity = process_data(humidity)
        solar_radiation = process_data(solar_radiation)
        solar_input_I = process_data(solar_input_I)
        solar_input_W = process_data(solar_input_W)
        solar_input_kWh = process_data(solar_input_kWh)
        extern_input_V = process_data(extern_input_V)
        bat_charge_V = process_data(bat_charge_V)
        bat_charge_I = process_data(bat_charge_I)
        bat_charge_W = process_data(bat_charge_W)
        bat_total_kWh = process_data(bat_total_kWh)
        bat_capacity = process_data(bat_capacity)

        data_to_insert = [
            temperature, humidity, solar_radiation, solar_input_I, solar_input_W,
            solar_input_kWh, extern_input_V, bat_charge_V, bat_charge_I,
            bat_charge_W, bat_total_kWh, bat_capacity
        ]

        # Проверка на наличие None после обработки
        if any(d is None for d in data_to_insert):
            logging.error(f"Ошибка: один из параметров является None после обработки данных: {data_to_insert}")
            return

        # Вставка данных в основную таблицу
        c.execute(
            "INSERT OR IGNORE INTO weathergis (unique_id, city_id, datetime, temperature, humidity, solar_radiation) VALUES (?, ?, ?, ?, ?, ?)",
            (compact_unique_id, city_id, datetime, temperature, humidity, solar_radiation))

        # Вставка данных в дополнительную таблицу
        c.execute(
            "INSERT OR IGNORE INTO additional_data (unique_id, datetime, solar_input_I, solar_input_W, solar_input_kWh, extern_input_V, bat_charge_V, bat_charge_I, bat_charge_W, bat_total_kWh, bat_capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (compact_unique_id, datetime, solar_input_I, solar_input_W, solar_input_kWh, extern_input_V, bat_charge_V, bat_charge_I, bat_charge_W, bat_total_kWh, bat_capacity))

        conn.commit()
        logging.info(f"Data inserted successfully for unique_id: {compact_unique_id}")
    except Exception as e:
        logging.error(f"Error inserting data for unique_id {compact_unique_id}: {e}")
    finally:
        conn.close()


def process_data(data):
    if data is None:
        return 0.0

    if isinstance(data, (int, float)):
        return data

    if isinstance(data, str):
        filtered_data = ''.join(
            '0' if char.lower() == 'o' else char for char in data if
            char.isdigit() or char.lower() == 'o' or char == '.')
        try:
            if not filtered_data:
                logging.warning(f"Empty data after processing: original data='{data}'")
                return 0.0
            return float(filtered_data)
        except ValueError as e:
            logging.error(f"Error converting data to float: '{filtered_data}' from original data='{data}' - {e}")
            return 0.0

    logging.warning(f"Unsupported data type: {type(data)} with value: {data}")
    return 0.0


def fetch_and_store_cloud_data(api_url_base, date):
    # Формирование полного URL с датой
    print("я тут")
    full_url = f"{api_url_base}?date={date}"

    # Подключение к базе данных
    conn = sqlite3.connect(db_path_cloud)
    cursor = conn.cursor()
    print(full_url)

    # Заголовки запроса
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        'Cache-Control': 'max-age=0',
        'Cookie': 'abuse_interstitial=d900-178-218-103-59.ngrok-free.app',
        'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    # Получение данных с API
    response = requests.get(full_url, headers=headers)
    if response.status_code == 200:
        cloud_data = response.json()
        for item in cloud_data:
            cursor.execute("INSERT INTO screenshots (datetime, clouds) VALUES (?, ?)", (item['datetime'], item['clouds']))

            # Фиксируем изменения и закрываем соединение
            conn.commit()
        print("Data fetched and stored successfully.")
    else:
        print(f"Failed to fetch data: Status code {response.status_code}")

    # Закрытие соединения с базой данных
    conn.close()
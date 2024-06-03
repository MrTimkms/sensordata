import os
import dash
import concurrent.futures
import telebot
from config import IMAP_CONFIG, DOWNLOAD_PATH, TELEGRAM_CONFIG, ALLOWED_USERS, Mail_CONFIG, localDASH_CONFIG
import logging
import dash_bootstrap_components as dbc
import time
# Импорт модулей с функциями
from database_utils import create_solar_data_table, create_additional_table, insert_solar_data, fetch_and_store_cloud_data
from attachment_utils import download_all_attachments
from bot_utils import run_bot
from datetime import datetime, timedelta
from dashboard_utils import run_server
# Отключение логирования Dash
logging.getLogger('dash').setLevel(logging.ERROR)
# Отключение логирования Dash и Flask
logging.getLogger('dash').setLevel(logging.CRITICAL)
logging.getLogger('werkzeug').setLevel(logging.CRITICAL)

# Путь к базе данных SQLite
DATABASE_PATH = os.path.join(os.getcwd(), '1.3_SolarData_ExpU.db')


# Переменная локальности.
NOlocalDASH=localDASH_CONFIG["NOlocalDASH"]
def fetch_data_daily():
    data_fetched_today = False
    while True:
        now = datetime.now()
        next_run = (now + timedelta(days=1)).replace(hour=0, minute=1, second=0, microsecond=0)

        # Определяем, нужно ли загружать данные
        if now.time() > datetime.strptime("00:01", "%H:%M").time() and not data_fetched_today:
            previous_day = now - timedelta(days=1)
            date_str = previous_day.strftime("%Y-%m-%d")
            print(f"Выполняется загрузка данных за {date_str}")
            # Вставьте сюда вызов функции для загрузки данных
            fetch_and_store_cloud_data('https://d900-178-218-103-59.ngrok-free.app/clouds/', date_str)
            data_fetched_today = True
        elif now.time() < datetime.strptime("00:01", "%H:%M").time():
            data_fetched_today = False  # Сброс флага после полуночи

        # Рассчитываем время до следующего выполнения задачи
        wait_seconds = (next_run - now).total_seconds()
        print(f"Ожидание {wait_seconds // 3600} часов и {(wait_seconds % 3600) // 60} минут до следующего выполнения")
        time.sleep(wait_seconds)
def main():
    # Подготовка базы данных
    #create_solar_data_table()
    #create_additional_table()
    # Создание и запуск всех необходимых сервисов в разных потоках
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(run_server)  # Запуск сервера Dash
        if localDASH_CONFIG["NOlocalDASH"]:  # Проверка конфигурации на локальность
            executor.submit(main_process)  # Запуск процесса скачивания вложений и обработки данных
            executor.submit(run_bot)  # Запуск бота Telegram, если это необходимо
            # Запуск задачи по загрузке данных каждый день
            executor.submit(fetch_data_daily)
def main_process():
    while True:
        try:
            success = download_all_attachments()
            if not success:
                print("Ошибка при загрузке вложений.")
            else:
                print("Вложения успешно обработаны.")
            print("Ожидание следующей проверки...")
            time.sleep(3600)
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            print("Перезапуск бота через 10 мин")
            print(datetime.now())
            time.sleep(60*10)
if __name__ == "__main__":
    main()
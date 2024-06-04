import imaplib
import email
import os
import re
import csv
from config import IMAP_CONFIG, DOWNLOAD_PATH, localDASH_CONFIG
# Импорт модулей с функциями
from email_utils import send_email, notify_users
from database_utils import insert_solar_data, process_data
from datetime import datetime
# Глобальная переменная для счетчика попыток
attempt_count = 0
# Переменная локальности.
NOlocalDASH=localDASH_CONFIG["NOlocalDASH"]
def download_all_attachments():
    print("Попытка загрузить вложения...")
    if NOlocalDASH:
        global attempt_count
        max_attempts = 2
        success = attempt_download()
        if success:
            print("Вложения успешно загружены.")
            attempt_count = 0
            return True
        else:
            print("Не удалось загрузить вложения.")
            attempt_count += 1
            if attempt_count >= max_attempts:
                notify_users()
                send_email("Ошибка", "Не найдены вложения csv файлов, срочно проверить установку", "", "gtimjob@gmail.com")
            return False
    return False

def attempt_download():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_CONFIG['server'], IMAP_CONFIG['port'])
        mail.login(IMAP_CONFIG['login'], IMAP_CONFIG['password'])
        mail.select('inbox')

        result, email_ids = mail.search(None, '(UNSEEN)')
        if result != "OK":
            print("Ошибка при поиске писем:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return False

        for email_id in email_ids[0].split():
            mail_data = mail.fetch(email_id, '(RFC822)')[1]
            raw_email = mail_data[0][1]
            email_message = email.message_from_bytes(raw_email)

            for part in email_message.walk():
                if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                    continue

                file_name = part.get_filename()
                print(f"Попытка скачать вложение: {file_name}")
                if re.match(r'\d{8}_\d{2}\.csv', file_name):
                    file_path = os.path.join(DOWNLOAD_PATH, file_name)
                    with open(file_path, 'wb') as file:
                        file.write(part.get_payload(decode=True))
                    print(f"Вложение {file_name} сохранено")

                    with open(file_path, 'r') as csv_file:
                        csv_reader = csv.reader(csv_file)
                        header = next(csv_reader, None)
                        if not header:
                            header = ["datetime", "temperature", "humidity", "solar_radiation"]

                        for row in csv_reader:
                            datetime_row = row[0]
                            try:
                                temperature = float(row[1])
                                humidity = float(row[2])
                                solar_radiation = float(row[3])
                                solar_input_I = row[4]
                                solar_input_W = row[5]
                                solar_input_kWh = row[6]
                                extern_input_V = row[7]
                                bat_charge_V = row[8]
                                bat_charge_I = row[9]
                                bat_charge_W = row[10]
                                bat_total_kWh = row[11]
                                bat_capacity = row[12]
                                insert_solar_data(city_id=4853, datetime=datetime_row, temperature=temperature,
                                                  humidity=humidity, solar_radiation=solar_radiation,
                                                  solar_input_I=solar_input_I, solar_input_W=solar_input_W,
                                                  solar_input_kWh=solar_input_kWh, extern_input_V=extern_input_V,
                                                  bat_charge_V=bat_charge_V, bat_charge_I=bat_charge_I,
                                                  bat_charge_W=bat_charge_W, bat_total_kWh=bat_total_kWh,
                                                  bat_capacity=bat_capacity)
                            except (ValueError, IndexError) as e:
                                print(f"Пропущена строка CSV из-за неверных данных: {row} - {e}")
        return True
    except Exception as e:
        print(f"Произошла ошибка при загрузке вложений: {e}")
        return False
    finally:
        mail.logout()

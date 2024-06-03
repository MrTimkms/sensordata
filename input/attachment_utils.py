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
        global attempt_count  # Объявляем, что используем глобальную переменную
        max_attempts = 2  # Максимальное количество попыток
        success = attempt_download()
        if success:
            print("Вложения успешно загружены.")
            attempt_count = 0
            return True  # Успешно загружено
            # Если неудачно, увеличиваем счетчик
        else:
            print("Не удалось загрузить вложения.")
            attempt_count += 1
            if attempt_count >= max_attempts:
                notify_users()
                send_email("Ошибка", "Не найдены вложения csv файлов, срочно проверить установку", "",
                           "gtimjob@gmail.com")
            return False  # Неудачная попытка после максимального количества попыток
    return False

def attempt_download():
    try:
        # Подключение к почтовому серверу
        mail = imaplib.IMAP4_SSL(IMAP_CONFIG['server'], IMAP_CONFIG['port'])
        mail.login(IMAP_CONFIG['login'], IMAP_CONFIG['password'])
        mail.select('inbox')

        # Поиск всех непрочитанных писем
        result, email_ids = mail.search(None, '(UNSEEN)')
        if result != "OK":
            print("Ошибка при поиске писем:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return False  # Возврат False, если поиск писем не удался

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
                            temperature = float(row[1])
                            humidity = float(row[2])
                            solar_radiation = float(row[3])
                            if len(row) >= 13:
                                continue
                            try:
                                solar_input_1 = process_data(row[4])
                                solar_input_w = process_data(row[5])
                                solar_input_kwh = process_data(row[6])
                                extern_input_v = process_data(row[7])
                                batv = process_data(process_data(row[8]))
                                bat_charge_1 = process_data(row[9])
                                bat_charge_w = process_data(row[10])
                                bat_total_kwh = process_data(row[11])
                                bat_capacity = process_data(row[12])
                                insert_solar_data(city_id=4853, datetime=datetime_row, temperature=temperature,
                                                  humidity=humidity,
                                                  solar_radiation=solar_radiation, solar_input_1=solar_input_1,
                                                  solar_input_w=solar_input_w,
                                                  solar_input_kwh=solar_input_kwh, extern_input_v=extern_input_v,
                                                  batv=batv,
                                                  bat_charge_1=bat_charge_1, bat_charge_w=bat_charge_w,
                                                  bat_total_kwh=bat_total_kwh,
                                                  bat_capacity=bat_capacity)
                            except ValueError:
                                print(f"Пропущена строка CSV из-за неверных данных: {row}")
        return True
    except Exception as e:
        print(f"Произошла ошибка при загрузке вложений: {e}")
        return False
    finally:
        mail.logout()

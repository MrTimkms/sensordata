import imaplib
import email
import os
import time
from config import IMAP_CONFIG, DOWNLOAD_PATH

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
            if bool(file_name):
                file_path = os.path.join(DOWNLOAD_PATH, file_name)
                with open(file_path, 'wb') as file:
                    file.write(part.get_payload(decode=True))
                print(f"Вложение {file_name} сохранено")

    # Закрытие соединения с почтовым сервером
    mail.logout()


if __name__ == "__main__":
    while True:
        download_all_attachments()
        print("Ожидание следующей проверки...")
        time.sleep(3600)  # Пауза в 1 час (3600 секунд)

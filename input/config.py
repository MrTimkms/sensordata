import os

# Конфигурация почтового сервера
IMAP_CONFIG = {
    'server': "imap.yandex.ru",
    'port': 993,
    'login': "gisknastu@yandex.ru",
    'password': "lbehqvlictarghue"
}

# Путь для сохранения вложений
DOWNLOAD_PATH = os.path.join(os.getcwd(), "DownloadedAttachments")

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

TELEGRAM_CONFIG = {
    'TOKEN': '6962678880:AAHGIszQFawNxYpBSixKh9b1rDLdE_xn2zk'
}

ALLOWED_USERS = [379666033, 916609592]  # ID пользователей
#конфигурация логина и пароля
Mail_CONFIG = {
    'smtp_server': 'smtp.yandex.ru',                # сервер почты
    'smtp_port': '465',                             # порт, используем ssl
    'login': 'gisknastu@yandex.ru',                 # почта
    'password': 'lbehqvlictarghue'                  # пароль
}
localDASH_CONFIG = {
    'NOlocalDASH': True
}
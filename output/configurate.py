import os
# Конфигурация Modbus датчика температуры и влажности
SENSOR_TH_CONFIG = {
    'port': '/dev/ttyUSB0',                         # COM-порт к которому подключен датчик
    'address': 1,                                   # адрес датчика на шине
    'baudrate': 9600,                               # скорость обмена данными бит/с
    'bytesize': 8,                                  # количество бит данных
    'parity': minimalmodbus.serial.PARITY_NONE,     # контроль четности
    'stopbits': 1,                                  # количество стоповых бит
    'timeout': 1,                                    # максимальное время ожидания ответа, сек
    'delay': 300                                      # Задержка между измерениями (в секундах)
}

# Конфигурация Modbus пиранометра (датчика уровня солнечного излучения)
SENSOR_PYRANOMETER_CONFIG = {
    'port': '/dev/ttyUSB0',                         # COM-порт к которому подключен датчик
    'address': 2,                                   # адрес датчика на шине
    'baudrate': 9600,                               # скорость обмена данными бит/с
    'bytesize': 8,                                  # количество бит данных
    'parity': minimalmodbus.serial.PARITY_NONE,     # контроль четности
    'stopbits': 1,                                  # количество стоповых бит
    'timeout': 1                                    # максимальное время ожидания ответа, сек
}
#конфигурация логина и пароля
Mail_CONFIG = {
    'smtp_server': 'smtp.yandex.ru',                # сервер почты
    'smtp_port': '465',                             # порт, используем ssl
    'login': '[ваша почта]',                 # почта
    'password': '[ваш пароль]'                  # пароль       
}

DATA_PATH_Conf = {
    'DownloadedAttachments': 'SensorData',          # путь куда сохранять файлы локально
}
TELEGRAM_CONFIG = {
    'TOKEN': '[ваш токен]'
}

ALLOWED_USERS = [123456789, 987654321]  # Замените на реальные ID пользователей
OPENVPN_CONFIG = {
    'command': 'sudo openvpn your_vpn_config.ovpn'  # Команда для запуска OpenVPN
}

REALVNC_CONFIG = {
    'command': 'sudo vncserver-virtual'  # Команда для запуска RealVNC Server
}

NOTIFICATION_CONFIG = {
    'high_temperature_threshold': 30,  # Порог для уведомления о высокой температуре
    'low_temperature_threshold': -20,   # Порог для уведомления о низкой температуре
    'notification_interval_hours': 1  # Интервал для отправки уведомлений (в часах)
}
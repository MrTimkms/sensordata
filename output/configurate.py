import os
# Конфигурация Modbus датчика температуры и влажности
SENSOR_TH_CONFIG = {
    'port': '/dev/ttyUSB0',                         # COM-порт к которому подключен датчик
    'address': 1,                                   # адрес датчика на шине
    'baudrate': 9600,                               # скорость обмена данными бит/с
    'bytesize': 8,                                  # количество бит данных
    'parity': minimalmodbus.serial.PARITY_NONE,     # контроль четности
    'stopbits': 1,                                  # количество стоповых бит
    'timeout': 1                                    # максимальное время ожидания ответа, сек
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
    'login': 'gisknastu@yandex.ru',                 # почта
    'password': 'lbehqvlictarghue'                  # пароль       
}

DATA_PATH_Conf = {
    'DownloadedAttachments': 'SensorData',          # путь куда сохранять файлы локально
}
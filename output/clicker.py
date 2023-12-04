import subprocess
import pyautogui
import time
import pyperclip
def run_clicker():
    # Сохраняем текущее значение FAILSAFE
    old_failsafe: bool = pyautogui.FAILSAFE

    # Отключаем FAILSAFE
    pyautogui.FAILSAFE = False
    # Путь к исполняемому файлу ABBYY Screenshot Reader
    abbyy_path = "C:\\Program Files (x86)\\ABBYY Screenshot Reader 11\\ScreenshotReader.exe"

    # Путь к файлу лога
    log_file_path = "C:\\gisknastu\\log.txt"
    # Координаты области экрана для сканирования
    start_x, start_y = 400, 65
    end_x, end_y = 810, 445 # Пример для экрана размером 1920x1080
    # Запускаем ABBYY Screenshot Reader
    subprocess.Popen(abbyy_path)
    time.sleep(7) # Даем время для запуска приложения

    # Получаем список всех окон с заголовком "ABBYY"
    windows = pyautogui.getWindowsWithTitle("ABBYY")

    # Если список не пуст, активируем первое окно в списке
    if windows:
        windows[0].activate()
        time.sleep(3) # Даем время для активации окна
        # Нажимаем Alt + Enter
        pyautogui.hotkey('alt', 'enter')

    # Переходим к области экрана для сканирования
    pyautogui.moveTo(start_x, start_y, duration=1)
    pyautogui.dragTo(end_x, end_y, duration=1)
    time.sleep(7)


    # Запускаем сканирование текста с экрана
    pyautogui.press('enter')
    time.sleep(13)
    # Скопируем текст из буфера обмена в файл лога
    with open(log_file_path, 'a', encoding='utf-8') as f:
        f.write(pyperclip.paste() + '\n')
    # Получаем результат сканирования из буфера обмена
    scan_result = pyperclip.paste()

    # Разделяем результат сканирования по строкам
    scan_lines = scan_result.split('\n')

    # Инициализируем переменные для значений
    value1, value2, value3, value4, value5, value6, value7, value8, value9 = [None] * 9

    # Проходим по каждой строке и ищем соответствующие значения
    for line in scan_lines:
        if "Solar Input 1:" in line:
            value1 = line.split(":")[-1].strip()
        elif "Solar Input W:" in line:
            value2 = line.split(":")[-1].strip()
        elif "Solar Input KwH:" in line:
            value3 = line.split(":")[-1].strip()
        elif "Extern Input V:" in line:
            value4 = line.split(":")[-1].strip()
        elif "BatV:" in line:
            value5 = line.split(":")[-1].strip()
        elif "Bat Charge 1:" in line:
            value6 = line.split(":")[-1].strip()
        elif "Bat Charge W:" in line:
            value7 = line.split(":")[-1].strip()
        elif "Bat Total KwH:" in line:
            value8 = line.split(":")[-1].strip()
        elif "Bat Capacity:" in line:
            value9 = line.split(":")[-1].strip()

    # Восстанавливаем старое значение FAILSAFE
    pyautogui.FAILSAFE = old_failsafe

    # Выводим результат сканирования в стандартный вывод, разделяя значения запятыми
    #return print(f"Solar Input 1: {value1}, Solar Input W: {value2}, Solar Input KwH: {value3}, Extern Input V: {value4}, BatV: {value5}, Bat Charge 1: {value6}, Bat Charge W: {value7}, Bat Total KwH: {value8}, Bat Capacity: {value9}")
    # Возвращаем результат сканирования в виде кортежа значений
    return value1, value2, value3, value4, value5, value6, value7, value8, value9

# Ждем 15 минут перед следующим запуском
#time.sleep(900)

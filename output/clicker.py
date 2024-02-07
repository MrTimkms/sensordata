import subprocess
import pyautogui
import time
import pyperclip
def extract_numeric_value(value):
    try:
        # Если строка не пуста, удалим символы, которые не являются частью числа, и преобразуем в float
        if value.strip():
            numeric_value = float(''.join(filter(lambda x: x.isdigit() or x in '.-', value)))
            return numeric_value
    except ValueError:
        pass

    # Если не удается преобразовать в float или строка пуста, вернем исходное значение
    return value.strip()

def run_clicker():
    # Сохраняем текущее значение FAILSAFE
    old_failsafe: bool = pyautogui.FAILSAFE

    # Отключаем FAILSAFE
    pyautogui.FAILSAFE = False
    # Путь к исполняемому файлу ABBYY Screenshot Reader
    abbyy_path = "C:\\Program Files (x86)\\ABBYY Screenshot Reader 11\\ScreenshotReader.exe"
    fields = {
        "Solar Input V": "",
        "Solar Input I": "",
        "Solar Input W": "",
        "Solar Input KwH": "",
        "Extern Input V": "",
        "Wind Average DC V": "",
        "Wind Average DC I": "",
        "Wind Input DC W": "",
        "Wind Input KwH": "",
        "Motor Rev": "",
        "Wind Run Status": "",
        "BatV": "",
        "Bat Charge I": "",
        "Bat Charge W": "",
        "Bat Total KwH": "",
        "Bat Capacity": ""
    }

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

    for line in scan_lines:
        if "Solar Input V:" in line:
            fields["Solar Input V"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Solar Input I:" in line:
            fields["Solar Input I"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Solar Input W:" in line:
            fields["Solar Input W"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Solar Input KwH:" in line:
            fields["Solar Input KwH"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Extern Input V:" in line:
            fields["Extern Input V"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Wind Average DC V:" in line:
            fields["Wind Average DC V"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Wind Average DC I:" in line:
            fields["Wind Average DC I"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Wind Input DC W:" in line:
            fields["Wind Input DC W"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Wind Input KwH:" in line:
            fields["Wind Input KwH"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Motor Rev:" in line:
            fields["Motor Rev"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Wind Run Status:" in line:
            fields["Wind Run Status"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "BatV:" in line:
            fields["BatV"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Bat Charge I:" in line:
            fields["Bat Charge I"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Bat Charge W:" in line:
            fields["Bat Charge W"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Bat Total KwH:" in line:
            fields["Bat Total KwH"] = extract_numeric_value(line.split(":")[-1].strip())
        elif "Bat Capacity:" in line:
            fields["Bat Capacity"] = extract_numeric_value(line.split(":")[-1].strip())
    # Восстанавливаем старое значение FAILSAFE
    pyautogui.FAILSAFE = old_failsafe

    # Выводим результат сканирования в стандартный вывод, разделяя значения запятыми
    #return print(f"Solar Input 1: {value1}, Solar Input W: {value2}, Solar Input KwH: {value3}, Extern Input V: {value4}, BatV: {value5}, Bat Charge 1: {value6}, Bat Charge W: {value7}, Bat Total KwH: {value8}, Bat Capacity: {value9}")
    # Возвращаем результат сканирования в виде кортежа значений
    print (fields)
    return fields

# Ждем 15 минут перед следующим запуском
#time.sleep(900)

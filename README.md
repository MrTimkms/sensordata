# Сбор и обработка данных с датчиков и автоматическое скачивание вложений из электронной почты

Этот репозиторий содержит две программы:
1. Программа для сбора данных с датчиков, их сохранения и автоматической отправки на электронную почту.
2. Программа для автоматического скачивания вложений из электронной почты.

## Содержание

- [Описание программ](#описание-программ)
  - [Программа Сбора и Отправки Данных с Датчиков](#Программа-Сбора-и-Отправки-Данных-с-Датчиков)
  - [Программа для автоматического скачивания вложений из электронной почты](#Программа-для-автоматического-скачивания-вложений-из-электронной-почты)
  - [Сбор данных с датчиков](#сбор-данных-с-датчиков)
  - [Скачивание вложений из почты](#скачивание-вложений-из-почты)
- [Настройка](#настройка)
- [Запуск](#запуск)

## Описание программ
### Программа Сбора и Отправки Данных с Датчиков

1. Настройка и Инициализация:

Программа начинает свою работу с настройки параметров для двух датчиков: датчика температуры и влажности, а также пиранометра (датчика уровня солнечного излучения).
Для каждого датчика задается порт подключения, адрес устройства, скорость обмена данными, количество байт в пакете, режим проверки четности, количество стоповых бит и максимальное время ожидания ответа.
Программа также настраивает параметры для отправки данных по электронной почте через сервер Yandex.
2. Сбор Данных:

Программа входит в бесконечный цикл сбора данных.
Каждые 5 секунд программа считывает данные с обоих датчиков.
Считанные данные включают в себя текущую температуру, влажность и уровень солнечного излучения.
Эти данные записываются в CSV-файл, имя которого формируется на основе текущей даты и часа.
3. Отправка Данных:

Каждый час программа автоматически отправляет текущий CSV-файл на заранее заданный электронный адрес.
После успешной отправки данных, программа создает новый CSV-файл для записи данных следующего часа.
4. Обработка Ошибок:

Если в процессе считывания данных с датчиков происходит ошибка, программа выводит соответствующее сообщение об ошибке, но продолжает свою работу, пытаясь снова считать данные через 5 секунд.
Если в процессе отправки данных на почту происходит ошибка, программа также выводит сообщение об ошибке и пытается отправить данные снова через 1 час.


### Программа для автоматического скачивания вложений из электронной почты

Описание:
Программа автоматически проверяет почтовый ящик на наличие новых писем от определенного отправителя и скачивает вложения из этих писем в локальную директорию.

Основные функции:

Подключение к почтовому серверу: Программа использует протокол IMAP для подключения к почтовому серверу Yandex. Для этого используются логин и пароль, указанные в конфигурационном файле.

Поиск непрочитанных писем: Программа ищет все непрочитанные письма от определенного отправителя.

Скачивание вложений: Если у найденных писем есть вложения, программа автоматически скачивает их в локальную директорию "DownloadedAttachments".

Периодическая проверка: Программа автоматически проверяет почтовый ящик каждый час на наличие новых писем и скачивает вложения, если они есть.

Конфигурация:
Все настройки программы, включая данные для входа в почтовый ящик и путь для сохранения вложений, хранятся в отдельном конфигурационном файле. Это делает программу гибкой и позволяет легко изменять настройки без необходимости вмешательства в основной код.


### Сбор данных с датчиков

Эта программа автоматически собирает данные с датчиков температуры, влажности и уровня солнечного излучения. Данные сохраняются в формате CSV и автоматически отправляются на указанный электронный адрес каждый час.

### Скачивание вложений из почты

Эта программа автоматически проверяет указанный почтовый ящик на наличие новых писем от определенного отправителя и скачивает вложения из этих писем в локальную директорию.

## Настройка

Для корректной работы программ необходимо настроить конфигурационные файлы, указав в них необходимые параметры, такие как логин, пароль, адреса датчиков и т.д.
1. Клонируйте этот репозиторий.
2. Установите все необходимые библиотеки.
3. Настройте файлы конфигурации в соответствии с вашими требованиями.
4. Запустите нужную программу.

## Запуск

1. Настройте параметры вашего почтового сервера в файле конфигурации.
2. Запустите программу.
3. Все вложения из непрочитанных писем будут автоматически загружены в указанную директорию.


```bash
main.py для получения данных с почты и sensordata.py для получения данных с разбери


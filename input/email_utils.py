from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import os
import telebot
from config import IMAP_CONFIG, DOWNLOAD_PATH, TELEGRAM_CONFIG, ALLOWED_USERS, Mail_CONFIG, localDASH_CONFIG
import logging
from datetime import datetime
# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_CONFIG['TOKEN'])
def send_email(subject, body, attachment_path, From):
    global last_sent_timestamp
    smtp_server = Mail_CONFIG['smtp_server']
    smtp_port = Mail_CONFIG['smtp_port']
    login = Mail_CONFIG['login']
    password = Mail_CONFIG['password']

    msg = MIMEMultipart()
    msg['From'] = From
    msg['To'] = login
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(attachment_path))
            msg.attach(part)
    except FileNotFoundError:
        error_message = "Вложение не найдено. Отправка без него."
        logging.warning(error_message)

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(login, password)
        text = msg.as_string()
        server.sendmail(login, login, text)
        server.quit()
        logging.info("Письмо успешно отправлено.")
        last_sent_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        error_message = f"Ошибка при отправке письма: {str(e)}"
        logging.error(error_message)
def notify_users():
    for user_id in ALLOWED_USERS:
        bot.send_message(user_id, "Ошибка: файл почты не найден после неудачной попытки в течение часа.")

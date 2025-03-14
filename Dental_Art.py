import telebot
from telebot import types
from datetime import datetime, timedelta
import time
import threading
import os

TOKEN = "8077781373:AAEOdodckCaZxXy-OHDaH0p_SwckKZUzR9Q"
bot = telebot.TeleBot(TOKEN)

BASE_IMG_PATH = "/home/sdasdasdasdas/Dental_Bot/img/"

appointments = {}
reminders = {}
user_states = {}

doctors = {
    "consultation": [
        {"name": "Доктор Иванова А.П.", "photo": "doctor1.jpg",
         "specialization": "Терапевтическая стоматология", "experience": "10 лет"},
        {"name": "Доктор Петров С.И.", "photo": "doctor2.jpg",
         "specialization": "Хирургическая стоматология", "experience": "8 лет"}
    ],
    "children": [
        {"name": "Доктор Сидорова Е.В.", "photo": "doctor3.jpg",
         "specialization": "Детская стоматология", "experience": "12 лет"},
        {"name": "Доктор Кузнецова М.А.", "photo": "doctor4.jpg",
         "specialization": "Детская стоматология", "experience": "7 лет"}
    ],
    "clean": [
        {"name": "Доктор Смирнов Д.О.", "photo": "doctor5.jpg",
         "specialization": "Гигиена и профилактика", "experience": "9 лет"},
        {"name": "Доктор Васильева И.Н.", "photo": "doctor6.jpg",
         "specialization": "Гигиена полости рта", "experience": "6 лет"}
    ],
    "ort": [
        {"name": "Доктор Николаев П.Р.", "photo": "doctor7.jpg",
         "specialization": "Ортодонтия", "experience": "15 лет"},
        {"name": "Доктор Федорова Л.Д.", "photo": "doctor8.jpg",
         "specialization": "Ортодонтия", "experience": "11 лет"}
    ],
    "protez": [
        {"name": "Доктор Громов А.С.", "photo": "doctor9.jpg",
         "specialization": "Ортопедическая стоматология", "experience": "14 лет"},
        {"name": "Доктор Белова Т.П.", "photo": "doctor10.jpg",
         "specialization": "Протезирование", "experience": "13 лет"}
    ]
}

price_list = """
💰 Прайс-лист стоматологической клиники "Denta":

🦷 Консультация:
• Первичная консультация - Бесплатно
• Повторная консультация - 500 руб.

👶 Детская стоматология:
• Лечение кариеса молочного зуба - от 2500 руб.
• Лечение кариеса постоянного зуба - от 3500 руб.
• Герметизация фиссур - 1500 руб./зуб
• Удаление молочного зуба - 1500 руб.

🧼 Чистка зубов:
• Профессиональная гигиена полости рта - 3500 руб.
• Air Flow - 2500 руб.
• Ультразвуковая чистка - 2000 руб.
• Комплексная чистка (ультразвук + Air Flow + полировка) - 4500 руб.

🦷 Ортодонтия:
• Консультация ортодонта - 1000 руб.
• Установка брекет-системы (металлической) - от 35000 руб.
• Установка брекет-системы (керамической) - от 50000 руб.
• Каппы для выравнивания зубов - от 40000 руб.
• Ретейнер - 5000 руб.

🦷 Протезирование:
• Металлокерамическая коронка - от 12000 руб.
• Безметалловая коронка (E-max) - от 20000 руб.
• Винир керамический - от 25000 руб.
• Съемный протез (полный) - от 25000 руб.
• Съемный протез (частичный) - от 18000 руб.
• Имплантация (под ключ) - от 45000 руб.

* Цены указаны для ознакомления, точная стоимость определяется на приеме у врача.
"""


@bot.message_handler(commands=["start"])
def start_message(message):
    welcome_text = "🦷 Здравствуйте! Это бот для записи на прием к стоматологу клиники 'Denta'."
    bot.send_message(message.chat.id, welcome_text)
    show_main_menu(message.chat.id)


def show_main_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but1 = types.KeyboardButton("Запись на приём")
    but2 = types.KeyboardButton("Отменить или перенести")
    but3 = types.KeyboardButton("Информация и цены")
    but4 = types.KeyboardButton("Чат с клиникой")
    keyboard.add(but1, but2, but3, but4)
    bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)


@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if message.text == "Запись на приём":
        handle_appointment(message)
    elif message.text == "Отменить или перенести":
        handle_cancel_reschedule(message)
    elif message.text == "Информация и цены":
        bot.send_message(message.chat.id, price_list)
    elif message.text == "Чат с клиникой":
        handle_clinic_chat(message)


def handle_appointment(message):
    user_states[message.chat.id] = "choosing_service"
    inline_keyboard = types.InlineKeyboardMarkup()
    but1 = types.InlineKeyboardButton("Консультация (Бесплатно)", callback_data="consultation")
    but2 = types.InlineKeyboardButton("Детская стоматология", callback_data="children")
    but3 = types.InlineKeyboardButton("Чистка", callback_data="clean")
    but4 = types.InlineKeyboardButton("Ортодонтия", callback_data="ort")
    but5 = types.InlineKeyboardButton("Протезирование", callback_data="protez")
    inline_keyboard.add(but1, but2, but3, but4, but5)
    bot.send_message(message.chat.id, "Выберите тип услуги:", reply_markup=inline_keyboard)


def handle_cancel_reschedule(message):
    if message.chat.id in appointments:
        appointment = appointments[message.chat.id]
        inline_keyboard = types.InlineKeyboardMarkup()
        but1 = types.InlineKeyboardButton("Отменить запись", callback_data=f"cancel_{message.chat.id}")
        but2 = types.InlineKeyboardButton("Перенести запись", callback_data=f"reschedule_{message.chat.id}")
        inline_keyboard.add(but1, but2)
        bot.send_message(message.chat.id,
                         f"Ваша текущая запись:\nУслуга: {appointment['service']}\nВрач: {appointment['doctor']}\nДата: {appointment['date']}\nВремя: {appointment['time']}",
                         reply_markup=inline_keyboard)
    else:
        bot.send_message(message.chat.id, "У вас нет активных записей.")


def handle_clinic_chat(message):
    user_states[message.chat.id] = "chat_with_clinic"
    bot.send_message(message.chat.id,
                     "Напишите ваше сообщение для клиники. Наш администратор ответит вам в ближайшее время.")


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("cancel_"):
        user_id = int(call.data.split("_")[1])
        if user_id in appointments:
            del appointments[user_id]
            bot.answer_callback_query(call.id, "Ваша запись успешно отменена.")
            bot.send_message(user_id, "Ваша запись была отменена.")
        else:
            bot.answer_callback_query(call.id, "Запись не найдена.")

    elif call.data.startswith("reschedule_"):
        user_id = int(call.data.split("_")[1])
        user_states[user_id] = "rescheduling"
        bot.send_message(user_id, "Пожалуйста, выберите новую дату и время для записи.")
        show_doctors_for_service(user_id, appointments[user_id]['service'])

    elif call.data in ["consultation", "children", "clean", "ort", "protez"]:
        user_states[call.message.chat.id] = f"choosing_doctor_{call.data}"
        show_doctors_for_service(call.message.chat.id, call.data)

    elif call.data.startswith("doctor_"):
        parts = call.data.split("_")
        service = parts[2]
        doctor_index = int(parts[1])
        user_id = call.message.chat.id
        user_states[user_id] = f"choosing_date_{service}_{doctor_index}"

        available_dates = ["2025-04-01", "2025-04-02", "2025-04-03"]
        inline_keyboard = types.InlineKeyboardMarkup()
        for date in available_dates:
            inline_keyboard.add(types.InlineKeyboardButton(date, callback_data=f"date_{date}_{service}_{doctor_index}"))
        bot.send_message(user_id, "Выберите дату:", reply_markup=inline_keyboard)

    elif call.data.startswith("date_"):
        parts = call.data.split("_")
        date = parts[1]
        service = parts[2]
        doctor_index = int(parts[3])
        user_id = call.message.chat.id
        user_states[user_id] = f"choosing_time_{date}_{service}_{doctor_index}"

        available_times = ["10:00", "12:00", "14:00", "16:00"]
        inline_keyboard = types.InlineKeyboardMarkup()
        for time in available_times:
            inline_keyboard.add(
                types.InlineKeyboardButton(time, callback_data=f"time_{time}_{date}_{service}_{doctor_index}"))
        bot.send_message(user_id, "Выберите время:", reply_markup=inline_keyboard)

    elif call.data.startswith("time_"):
        parts = call.data.split("_")
        time = parts[1]
        date = parts[2]
        service = parts[3]
        doctor_index = int(parts[4])
        user_id = call.message.chat.id

        doctor = doctors[service][doctor_index]
        appointment = {
            "service": service,
            "doctor": doctor["name"],
            "date": date,
            "time": time,
            "timestamp": datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        }

        appointments[user_id] = appointment
        schedule_reminders(user_id, appointment["timestamp"])

        bot.send_message(user_id,
                         f"✅ Вы успешно записаны!\n\nУслуга: {service}\nВрач: {doctor['name']}\nДата: {date}\nВремя: {time}\n\nМы напомним вам о визите заранее.")
        show_main_menu(user_id)


def show_doctors_for_service(chat_id, service):
    inline_keyboard = types.InlineKeyboardMarkup()
    for i, doctor in enumerate(doctors[service]):
        photo_path = os.path.join(BASE_IMG_PATH, doctor["photo"])
        try:
            with open(photo_path, 'rb') as photo:
                bot.send_photo(chat_id, photo,
                               caption=f"{doctor['name']}\n{doctor['specialization']}\nОпыт: {doctor['experience']}")
        except FileNotFoundError:
            bot.send_message(chat_id, f"Фото врача {doctor['name']} недоступно")

        btn = types.InlineKeyboardButton(
            f"Выбрать {doctor['name']}",
            callback_data=f"doctor_{i}_{service}")
        inline_keyboard.add(btn)
    bot.send_message(chat_id, "Выберите врача:", reply_markup=inline_keyboard)


def schedule_reminders(user_id, appointment_time):
    reminder_24h = appointment_time - timedelta(hours=24)
    reminders[(user_id, "24h")] = reminder_24h
    reminder_1h = appointment_time - timedelta(hours=1)
    reminders[(user_id, "1h")] = reminder_1h


def check_reminders():
    while True:
        now = datetime.now()
        to_remove = []

        for (user_id, reminder_type), reminder_time in reminders.items():
            if now >= reminder_time:
                appointment = appointments.get(user_id)
                if appointment:
                    if reminder_type == "24h":
                        bot.send_message(user_id,
                                         f"⏰ Напоминание: завтра в {appointment['time']} у вас запись к стоматологу.\nУслуга: {appointment['service']}\nВрач: {appointment['doctor']}")
                    elif reminder_type == "1h":
                        bot.send_message(user_id,
                                         f"⏰ Напоминание: через час в {appointment['time']} у вас запись к стоматологу.\nУслуга: {appointment['service']}\nВрач: {appointment['doctor']}")
                to_remove.append((user_id, reminder_type))

        for key in to_remove:
            reminders.pop(key, None)

        time.sleep(60)


reminder_thread = threading.Thread(target=check_reminders)
reminder_thread.daemon = True
reminder_thread.start()

bot.polling()
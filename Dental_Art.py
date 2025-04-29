import telebot
from telebot import types
from datetime import datetime, timedelta
import time
import threading
import os
import json
import pytz
ADMIN_CHAT_ID = 5065171515
TOKEN = "8077781373:AAEOdodckCaZxXy-OHDaH0p_SwckKZUzR9Q"
bot = telebot.TeleBot(TOKEN)

BASE_IMG_PATH = r"D:\Users\Администратор\PycharmProjects\Dental Art Bot\img"
DATA_FILE = "appointments_data.json"
REVIEWS_FILE = "reviews_data.json"
BONUS_FILE = "bonus_data.json"


def load_data():
    try:
        with open(DATA_FILE, "r", encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"appointments": {}, "history": {}}


def load_reviews():
    try:
        with open(REVIEWS_FILE, "r", encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"reviews": {}}


def load_bonus():
    try:
        with open(BONUS_FILE, "r", encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"bonuses": {}}


def save_data(data):
    with open(DATA_FILE, "w", encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def save_reviews(reviews):
    with open(REVIEWS_FILE, "w", encoding='utf-8') as file:
        json.dump(reviews, file, indent=4, ensure_ascii=False)


def save_bonus(bonus):
    with open(BONUS_FILE, "w", encoding='utf-8') as file:
        json.dump(bonus, file, indent=4, ensure_ascii=False)


data = load_data()
appointments = data.get("appointments", {})
history = data.get("history", {})
reviews_data = load_reviews()
reviews = reviews_data.get("reviews", {})
bonus_data = load_bonus()
bonuses = bonus_data.get("bonuses", {})

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
<b>💰 Прайс-лист стоматологической клиники "Denta"</b>

<b>🦷 Консультация:</b>
• Первичная консультация - <b>Бесплатно</b>
• Повторная консультация - <b>500 руб.</b>

<b>👶 Детская стоматология:</b>
• Лечение кариеса молочного зуба - <b>от 2500 руб.</b>
• Лечение кариеса постоянного зуба - <b>от 3500 руб.</b>
• Герметизация фиссур - <b>1500 руб./зуб</b>
• Удаление молочного зуба - <b>1500 руб.</b>

<b>🧼 Профессиональная гигиена:</b>
• Комплексная чистка (ультразвук + Air Flow + полировка) - <b>4500 руб.</b>
• Профессиональная гигиена полости рта - <b>3500 руб.</b>
• Air Flow - <b>2500 руб.</b>
• Ультразвуковая чистка - <b>2000 руб.</b>

<b>🦷 Ортодонтия (исправление прикуса):</b>
• Консультация ортодонта - <b>1000 руб.</b>
• Установка брекет-системы (металлической) - <b>от 35000 руб.</b>
• Установка брекет-системы (керамической) - <b>от 50000 руб.</b>
• Каппы для выравнивания зубов - <b>от 40000 руб.</b>
• Ретейнер - <b>5000 руб.</b>

<b>🦷 Протезирование зубов:</b>
• Металлокерамическая коронка - <b>от 12000 руб.</b>
• Безметалловая коронка (E-max) - <b>от 20000 руб.</b>
• Винир керамический - <b>от 25000 руб.</b>
• Съемный протез (полный) - <b>от 25000 руб.</b>
• Имплантация (под ключ) - <b>от 45000 руб.</b>

<i>Цены указаны для ознакомления, точная стоимость определяется на приеме у врача.</i>
"""

faq = {
    "location": {
        "question": "📍 Где вы находитесь?",
        "answer": "Мы находимся по адресу: г. Москва, ул. Стоматологическая, д. 15, 3 этаж.\nБлижайшая станция метро - «Зубовская»."
    },
    "working_hours": {
        "question": "⏰ Часы работы",
        "answer": "График работы:\nПн-Пт: 9:00 - 21:00\nСб: 10:00 - 18:00\nВс: выходной"
    },
    "emergency": {
        "question": "🆘 Скорая помощь",
        "answer": "В случае острой боли звоните по телефону +7 (495) 123-45-67 - мы постараемся принять вас вне очереди."
    },
    "clean_price": {
        "question": "🧼 Стоимость чистки",
        "answer": "Профессиональная гигиена - 3500 руб.\nAir Flow - 2500 руб.\nКомплексная чистка - 4500 руб."
    },
    "children": {
        "question": "👶 Детский прием",
        "answer": "Первый визит ребенка к стоматологу лучше запланировать в возрасте 1 года или при появлении первых зубов."
    },
    "payment": {
        "question": "💳 Способы оплаты",
        "answer": "Мы принимаем:\n- Наличные\n- Банковские карты\n- Бесконтактные платежи\n- Бонусные баллы"
    },
    "bonus": {
        "question": "🎁 Бонусная система",
        "answer": "За каждый визит вы получаете 100 баллов\nЗа приведенного друга - 500 баллов\n1 балл = 1 рубль при оплате"
    }
}


@bot.message_handler(commands=["start"])
def start_message(message):
    welcome_text = """
🦷 <b>Добро пожаловать в стоматологическую клинику "Denta"!</b>

Мы предлагаем качественное и безболезненное лечение зубов для взрослых и детей. 

✨ <i>Специальное предложение для новых клиентов - бесплатная консультация!</i>
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🆓 Записаться на бесплатную консультацию", callback_data="consultation"))
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=markup)
    show_main_menu(message.chat.id)


def show_main_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("📋 Мои записи"),
        types.KeyboardButton("📝 Запись на приём"),
        types.KeyboardButton("💬 Чат с клиникой"),
        types.KeyboardButton("🔄 Отменить или перенести"),
        types.KeyboardButton("💰 Информация и цены"),
        types.KeyboardButton("❓ FAQ"),
        types.KeyboardButton("🎁 Мои бонусы")
    ]
    keyboard.add(*buttons)
    bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)


@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == "chat_with_clinic")
def handle_clinic_message(message):
    try:
        user_info = (f"👤 {message.from_user.first_name} "
                     f"{message.from_user.last_name or ''} "
                     f"(@{message.from_user.username})" if message.from_user.username else "")

        bot.send_message(
            ADMIN_CHAT_ID,
            f"✉️ Новое сообщение от пользователя:\n"
            f"{user_info}\n"
            f"ID: {message.chat.id}\n\n"
            f"<b>Сообщение:</b>\n"
            f"{message.text}",
            parse_mode='HTML'
        )

        bot.send_message(
            message.chat.id,
            "✅ Ваше сообщение отправлено администратору. Ожидайте ответа.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                types.KeyboardButton("🔙 На главную")
            )
        )

        user_states[message.chat.id] = {}

    except Exception as e:
        print(f"Ошибка пересылки: {e}")
        bot.send_message(
            message.chat.id,
            "❌ Ошибка отправки. Пожалуйста, попробуйте позже."
        )


@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if message.text == "📝 Запись на приём":
        handle_appointment(message)
    elif message.text == "🔄 Отменить или перенести":
        handle_cancel_reschedule(message)
    elif message.text == "💰 Информация и цены":
        bot.send_message(message.chat.id, price_list, parse_mode='HTML')
    elif message.text == "💬 Чат с клиникой":
        handle_clinic_chat(message)
    elif message.text == "📋 Мои записи":
        show_my_appointments(message.chat.id)
    elif message.text == "❓ FAQ":
        show_faq_menu(message.chat.id)
    elif message.text == "🎁 Мои бонусы":
        show_bonus_balance(message.chat.id)
    elif message.text == "🔙 На главную":
        show_main_menu(message.chat.id)
        return
    else:
        handle_faq(message)


def show_my_appointments(chat_id):
    now = datetime.now(pytz.timezone('Europe/Moscow'))
    user_id = str(chat_id)

    if user_id in appointments:
        appointment = appointments[user_id]
        app_time = datetime.fromtimestamp(appointment['timestamp'], tz=pytz.timezone('Europe/Moscow'))

        status = "✅ Посещение состоялось" if now > app_time else " Запланировано"

        service_emoji = {
            "consultation": "🦷",
            "children": "👶",
            "clean": "🧼",
            "ort": "🦷",
            "protez": "🦷"
        }.get(appointment['service'], "📅")

        formatted_date = app_time.strftime("%d.%m.%Y")
        bot.send_message(chat_id,
                         f"📋 <b>Ваша текущая запись:</b>\n\n"
                         f"<b>🕒Статус:</b> {status}\n"
                         f"<b>{service_emoji}Услуга:</b>  {appointment['service']}\n"
                         f"<b>⚕️Врач:</b>  {appointment['doctor']}\n"
                         f"<b>📅Дата:</b>  {formatted_date}\n"
                         f"<b>Время:</b> {appointment['time']}",
                         parse_mode='HTML')
    else:
        bot.send_message(chat_id, "📭 У вас нет активных записей.")

    show_history(chat_id)


def show_history(chat_id):
    user_history = history.get(str(chat_id), [])
    if not user_history:
        return

    history_text = "📚 <b>История ваших посещений:</b>\n\n"
    for i, visit in enumerate(user_history, 1):
        service_emoji = {
            "consultation": "🦷",
            "children": "👶",
            "clean": "🧼",
            "ort": "🦷",
            "protez": "🦷"
        }.get(visit['service'], "📅")

        visit_date = datetime.strptime(visit['date'], "%Y-%m-%d").strftime("%d.%m.%Y")
        history_text += f"<b>{i}.{service_emoji} Услуга:</b>  {visit['service']}\n"
        history_text += f"<b>⚕️Врач:</b>  {visit['doctor']}\n"
        history_text += f"<b>📅Дата:</b>  {visit_date} в {visit.get('time', 'время не указано')}\n"

        if 'review' in visit:
            history_text += f"<b>Оценка:</b> {'⭐' * visit['review']['rating']}\n"
            if visit['review']['comment']:
                history_text += f"<b>Отзыв:</b> 💬 {visit['review']['comment']}\n"
        history_text += "\n"

    bot.send_message(chat_id, history_text, parse_mode='HTML')

def show_bonus_balance(chat_id):
    user_id = str(chat_id)
    balance = bonuses.get(user_id, 0)
    bot.send_message(chat_id,
                     f"🎁 <b>Ваш бонусный баланс:</b> {balance} баллов\n\n"
                     f"1 балл = 1 рубль при оплате услуг\n"
                     f"Приведите друга и получите 500 баллов!",
                     parse_mode='HTML')


def show_faq_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton(item["question"]) for item in faq.values()]
    buttons.append(types.KeyboardButton("🔙 Назад"))
    keyboard.add(*buttons)
    bot.send_message(chat_id, "Выберите вопрос:", reply_markup=keyboard)


def handle_faq(message):
    if message.text == "🔙 Назад":
        show_main_menu(message.chat.id)
        return

    for item in faq.values():
        if message.text == item["question"]:
            bot.send_message(message.chat.id, item["answer"])
            return

    bot.send_message(message.chat.id, "Пожалуйста, выберите вопрос из меню.")


def handle_appointment(message):
    user_states[message.chat.id] = "choosing_service"
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton("🦷 Консультация стоматолога (Бесплатно)", callback_data="consultation"),
        types.InlineKeyboardButton("👶 Детская стоматология", callback_data="children"),
        types.InlineKeyboardButton("🧼 Профессиональная чистка зубов", callback_data="clean"),
        types.InlineKeyboardButton("🦷 Ортодонтия (исправление прикуса)", callback_data="ort"),
        types.InlineKeyboardButton("🦷 Протезирование зубов", callback_data="protez")
    ]
    inline_keyboard.add(*buttons)
    bot.send_message(message.chat.id, "Выберите тип услуги:", reply_markup=inline_keyboard)


def handle_cancel_reschedule(message):
    if str(message.chat.id) in appointments:
        appointment = appointments[str(message.chat.id)]
        inline_keyboard = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton("❌ Отменить запись", callback_data=f"cancel_{message.chat.id}"),
            types.InlineKeyboardButton("🔄 Перенести запись", callback_data=f"reschedule_{message.chat.id}")
        ]
        inline_keyboard.add(*buttons)

        formatted_date = datetime.strptime(appointment['date'], "%Y-%m-%d").strftime("%d.%m.%Y")
        bot.send_message(message.chat.id,
                         f"<b>Ваша текущая запись:</b>\n\n"
                         f"<b>Услуга:</b> {appointment['service']}\n"
                         f"<b>Врач:</b> {appointment['doctor']}\n"
                         f"<b>Дата:</b> {formatted_date}\n"
                         f"<b>Время:</b> {appointment['time']}",
                         parse_mode='HTML', reply_markup=inline_keyboard)
    else:
        bot.send_message(message.chat.id, "У вас нет активных записей.")


def handle_clinic_chat(message):
    user_states[message.chat.id] = {"state": "chat_with_clinic"}

    bot.send_message(message.chat.id,
                     "Напишите ваше сообщение для клиники. Наш администратор ответит вам в ближайшее время.",
                     reply_markup=types.ReplyKeyboardRemove())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("cancel_"):
        user_id = int(call.data.split("_")[1])
        if str(user_id) in appointments:
            del appointments[str(user_id)]
            save_data({"appointments": appointments, "history": history})
            bot.answer_callback_query(call.id, "Ваша запись успешно отменена.")
            bot.send_message(user_id, "❌ Ваша запись была отменена.")
        else:
            bot.answer_callback_query(call.id, "Запись не найдена.")


    elif call.data.startswith("reschedule_"):
        user_id = int(call.data.split("_")[1])
        user_states[user_id] = "rescheduling"
        bot.send_message(user_id, "Пожалуйста, выберите новую дату и время для записи.")
        show_doctors_for_service(user_id, appointments[str(user_id)]['service'])

    elif call.data in ["consultation", "children", "clean", "ort", "protez"]:
        user_states[call.message.chat.id] = f"choosing_doctor_{call.data}"
        show_doctors_for_service(call.message.chat.id, call.data)

    elif call.data.startswith("doctor_"):
        parts = call.data.split("_")
        service = parts[2]
        doctor_index = int(parts[1])
        user_id = call.message.chat.id
        user_states[user_id] = f"choosing_date_{service}_{doctor_index}"

        available_dates = []
        today = datetime.now(pytz.timezone('Europe/Moscow'))
        for i in range(1, 8):
            date = today + timedelta(days=i)
            if date.weekday() < 5:
                available_dates.append(date.strftime("%Y-%m-%d"))

        inline_keyboard = types.InlineKeyboardMarkup()
        for date in available_dates:
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
            inline_keyboard.add(
                types.InlineKeyboardButton(formatted_date, callback_data=f"date_{date}_{service}_{doctor_index}"))
        bot.send_message(user_id, "📅 Выберите дату:", reply_markup=inline_keyboard)

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
        bot.send_message(user_id, "🕒 Выберите время:", reply_markup=inline_keyboard)

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
            "timestamp": datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").timestamp()
        }

        appointments[str(user_id)] = appointment
        schedule_reminders(user_id, datetime.fromtimestamp(appointment["timestamp"]))
        save_data({"appointments": appointments, "history": history})

        if str(user_id) not in bonuses:
            bonuses[str(user_id)] = 0

        formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        bot.send_message(user_id,
                         f"""
✅ <b>Вы успешно записаны!</b>

<b>Услуга:</b> {service}
<b>Врач:</b> {doctor['name']}
<b>Дата:</b> {formatted_date}
<b>Время:</b> {time}

Мы напомним вам о визите заранее.
Адрес: ул. Стоматологическая, д. 15, 3 этаж.
Телефон: +79999999999
                         """, parse_mode='HTML')
        show_main_menu(user_id)

    elif call.data.startswith("review_"):
        parts = call.data.split("_")
        action = parts[1]
        user_id = int(parts[2])

        if action == "request":
            keyboard = types.InlineKeyboardMarkup()
            for i in range(1, 6):
                keyboard.add(types.InlineKeyboardButton(f"{i} ⭐", callback_data=f"review_rate_{i}_{user_id}"))
            bot.send_message(user_id, "Пожалуйста, оцените ваше посещение от 1 до 5 звезд:", reply_markup=keyboard)

        elif action.startswith("rate_"):
            rating = int(action.split("_")[1])
            user_states[user_id] = {"state": "waiting_review_comment", "rating": rating}
            bot.send_message(user_id,
                             f"Спасибо за оценку {rating} звезд! Хотите оставить комментарий? Напишите его или нажмите /skip чтобы пропустить.")


def add_to_history(user_id, appointment):
    user_id_str = str(user_id)
    if user_id_str not in history:
        history[user_id_str] = []

    appointment_copy = appointment.copy()
    if 'timestamp' in appointment_copy:
        del appointment_copy['timestamp']

    history[user_id_str].append(appointment_copy)
    save_data({"appointments": appointments, "history": history})

    if str(user_id) in bonuses:
        bonuses[str(user_id)] += 100
    else:
        bonuses[str(user_id)] = 100
    save_bonus({"bonuses": bonuses})


def schedule_reminders(user_id, appointment_time):
    if appointment_time.tzinfo is None:
        appointment_time = appointment_time.replace(tzinfo=pytz.timezone('Europe/Moscow'))

    reminder_24h = appointment_time - timedelta(hours=24)
    reminders[(user_id, "24h")] = reminder_24h
    reminder_1h = appointment_time - timedelta(hours=1)
    reminders[(user_id, "1h")] = reminder_1h
    review_time = appointment_time + timedelta(hours=2)
    reminders[(user_id, "review")] = review_time


def check_reminders():
    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        to_remove = []

        for (user_id, reminder_type), reminder_time in reminders.items():
            if now >= reminder_time:
                appointment = appointments.get(str(user_id))
                if appointment:
                    if reminder_type == "24h":
                        bot.send_message(user_id,
                                         f"""
⏰ <b>Напоминание о записи</b>

Завтра в <b>{appointment['time']}</b> у вас запись к стоматологу.

<b>Услуга:</b> {appointment['service']}
<b>Врач:</b> {appointment['doctor']}
                                         """, parse_mode='HTML')
                    elif reminder_type == "1h":
                        bot.send_message(user_id,
                                         f"""
⏰ <b>Напоминание о записи</b>

Через час в <b>{appointment['time']}</b> у вас запись к стоматологу.

<b>Услуга:</b> {appointment['service']}
<b>Врач:</b> {appointment['doctor']}
                                         """, parse_mode='HTML')

                if reminder_type == "review":
                    user_history = history.get(str(user_id), [])
                    last_visit = user_history[-1] if user_history else None
                    if last_visit and 'review' not in last_visit:
                        inline_keyboard = types.InlineKeyboardMarkup()
                        inline_keyboard.add(
                            types.InlineKeyboardButton("✍️ Оставить отзыв", callback_data=f"review_request_{user_id}"))
                        bot.send_message(user_id,
                                         "Пожалуйста, оцените ваше посещение стоматологической клиники:",
                                         reply_markup=inline_keyboard)

                to_remove.append((user_id, reminder_type))

        for key in to_remove:
            reminders.pop(key, None)

        time.sleep(60)


@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("state") == "waiting_review_comment")
def handle_review_comment(message):
    user_id = message.chat.id
    rating = user_states[user_id]["rating"]
    comment = message.text if message.text != "/skip" else ""

    user_history = history.get(str(user_id), [])
    if user_history:
        last_visit = user_history[-1]
        last_visit['review'] = {
            "rating": rating,
            "comment": comment,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        if str(user_id) not in reviews:
            reviews[str(user_id)] = []
        reviews[str(user_id)].append({
            "service": last_visit['service'],
            "doctor": last_visit['doctor'],
            "rating": rating,
            "comment": comment,
            "date": last_visit['date']
        })

        save_data({"appointments": appointments, "history": history})
        save_reviews({"reviews": reviews})

        bot.send_message(user_id, "🙏 Спасибо за ваш отзыв! Мы ценим ваше мнение.")
    else:
        bot.send_message(user_id, "Не удалось найти информацию о вашем последнем посещении.")

    del user_states[user_id]
    show_main_menu(user_id)


def show_doctors_for_service(chat_id, service):
    for i, doctor in enumerate(doctors[service]):
        photo_path = os.path.join(BASE_IMG_PATH, doctor["photo"])
        try:
            with open(photo_path, 'rb') as photo:
                inline_keyboard = types.InlineKeyboardMarkup()
                btn = types.InlineKeyboardButton(
                    f"Выбрать {doctor['name']}",
                    callback_data=f"doctor_{i}_{service}"
                )
                inline_keyboard.add(btn)

                bot.send_photo(
                    chat_id,
                    photo,
                    caption=f"<b>{doctor['name']}</b>\n"
                            f"{doctor['specialization']}\n"
                            f"Опыт работы: {doctor['experience']}",
                    parse_mode='HTML',
                    reply_markup=inline_keyboard
                )
        except FileNotFoundError:
            inline_keyboard = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton(
                f"Записаться к {doctor['name']}",
                callback_data=f"doctor_{i}_{service}"
            )
            inline_keyboard.add(btn)
            bot.send_message(
                chat_id,
                f"<b>{doctor['name']}</b>\n"
                f"{doctor['specialization']}\n"
                f"Опыт работы: {doctor['experience']}",
                parse_mode='HTML',
                reply_markup=inline_keyboard
            )


reminder_thread = threading.Thread(target=check_reminders)
reminder_thread.daemon = True
reminder_thread.start()

bot.polling()
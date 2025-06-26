import telebot
from telebot import types
from datetime import datetime, timedelta
import time
import threading
import os
import json
import pytz
import sqlite3
import random

TOKEN = "8077781373:AAEOdodckCaZxXy-OHDaH0p_SwckKZUzR9Q"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 5065171515
BASE_IMG_PATH = r"D:\Users\Администратор\PycharmProjects\Dental Art Bot\img"
DATA_FILE = "appointments_data.json"
REVIEWS_FILE = "reviews_data.json"
BONUS_FILE = "bonus_data.json"
DB_FILE = "user_states.db"

active_chats = {}
admin_active_chats = {}


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS user_states (user_id INTEGER PRIMARY KEY, state TEXT, data TEXT)')
    conn.commit()
    conn.close()


init_db()


def get_user_state(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT state, data FROM user_states WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None)


def set_user_state(user_id, state, data=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO user_states (user_id, state, data) VALUES (?, ?, ?)',
                   (user_id, state, json.dumps(data) if data else None))
    conn.commit()
    conn.close()


def clear_user_state(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_states WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


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


def find_user_by_phone(phone):
    for user_id, user_data in bonuses.items():
        if isinstance(user_data, dict) and "phone" in user_data and user_data["phone"] == phone:
            return user_id
    return None


data = load_data()
appointments = data.get("appointments", {})
history = data.get("history", {})
reviews_data = load_reviews()
reviews = reviews_data.get("reviews", {})
bonus_data = load_bonus()
bonuses = bonus_data.get("bonuses", {})
reminders = {}

doctors = {
    "consultation": [
        {"name": "Доктор Иванова А.П.", "photo": "doctor1.jpg", "specialization": "Терапевтическая стоматология",
         "experience": "10 лет"},
        {"name": "Доктор Петров С.И.", "photo": "doctor2.jpg", "specialization": "Хирургическая стоматология",
         "experience": "8 лет"}
    ],
    "children": [
        {"name": "Доктор Сидорова Е.В.", "photo": "doctor1.jpg", "specialization": "Детская стоматология",
         "experience": "12 лет"},
        {"name": "Доктор Кузнецова М.А.", "photo": "doctor2.jpg", "specialization": "Детская стоматология",
         "experience": "7 лет"}
    ],
    "clean": [
        {"name": "Доктор Смирнов Д.О.", "photo": "doctor1.jpg", "specialization": "Гигиена и профилактика",
         "experience": "9 лет"},
        {"name": "Доктор Васильева И.Н.", "photo": "doctor2.jpg", "specialization": "Гигиена полости рта",
         "experience": "6 лет"}
    ],
    "ort": [
        {"name": "Доктор Николаев П.Р.", "photo": "doctor1.jpg", "specialization": "Ортодонтия",
         "experience": "15 лет"},
        {"name": "Доктор Федорова Л.Д.", "photo": "doctor2.jpg", "specialization": "Ортодонтия", "experience": "11 лет"}
    ],
    "protez": [
        {"name": "Доктор Громов А.С.", "photo": "doctor1.jpg", "specialization": "Ортопедическая стоматология",
         "experience": "14 лет"},
        {"name": "Доктор Белова Т.П.", "photo": "doctor2.jpg", "specialization": "Протезирование",
         "experience": "13 лет"}
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

<b>🎁 Бонусная система:</b>
• За регистрацию - <b>500 баллов</b>
• За каждый визит - <b>100 баллов</b>
• За приведенного друга - <b>500 баллов</b>
• 1 балл = 1 рубль при оплате
"""

faq = {
    "location": {"question": "📍 Где вы находитесь?",
                 "answer": "Мы находимся по адресу: г. Москва, ул. Стоматологическая, д. 15, 3 этаж.\nБлижайшая станция метро - «Зубовская»."},
    "working_hours": {"question": "⏰ Часы работы",
                      "answer": "График работы:\nПн-Пт: 9:00 - 21:00\nСб: 10:00 - 18:00\nВс: выходной"},
    "emergency": {"question": "🆘 Скорая помощь",
                  "answer": "В случае острой боли звоните по телефону +7 (495) 123-45-67 - мы постараемся принять вас вне очереди."},
    "clean_price": {"question": "🧼 Стоимость чистки",
                    "answer": "Профессиональная гигиена - 3500 руб.\nAir Flow - 2500 руб.\nКомплексная чистка - 4500 руб."},
    "children": {"question": "👶 Детский прием",
                 "answer": "Первый визит ребенка к стоматологу лучше запланировать в возрасте 1 года или при появлении первых зубов."},
    "payment": {"question": "💳 Способы оплаты",
                "answer": "Мы принимаем:\n- Наличные\n- Банковские карты\n- Бесконтактные платежи\n- Бонусные баллы"},
    "bonus": {"question": "🎁 Бонусная система",
              "answer": "За регистрацию - 500 баллов\nЗа каждый визит - 100 баллов\nЗа приведенного друга - 500 баллов\n1 балл = 1 рубль при оплате"}
}


@bot.message_handler(commands=["start"])
def start_message(message):
    user_id = str(message.chat.id)
    if user_id not in bonuses:
        consultation_doctor = random.choice(doctors["consultation"])

        welcome_text = f"""
🦷 <b>Добро пожаловать в стоматологическую клинику "Denta"!</b>

🎉 <b>Вы записаны на консультацию к доктору {consultation_doctor['name']}</b>

Для получения 500 бонусов за регистрацию подтвердите ваш аккаунт:
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📱 Отправить номер телефона", callback_data="register_with_phone"),
            types.InlineKeyboardButton("✉️ Зарегистрироваться без номера", callback_data="register_without_phone")
        )
        bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=markup)
    else:
        balance = bonuses[user_id]["balance"] if isinstance(bonuses[user_id], dict) else bonuses[user_id]
        welcome_text = f"""
🦷 <b>С возвращением в стоматологическую клинику "Denta"!</b>

Ваш текущий бонусный баланс: {balance} баллов
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🆓 Записаться на консультацию", callback_data="consultation"))
        bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=markup)
        show_main_menu(message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data in ["register_with_phone", "register_without_phone"])
def handle_registration_choice(call):
    user_id = str(call.message.chat.id)
    if call.data == "register_with_phone":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("📱 Отправить номер телефона", request_contact=True))
        bot.send_message(call.message.chat.id, "Нажмите кнопку ниже, чтобы отправить номер телефона:",
                         reply_markup=markup)
    else:
        bonuses[user_id] = {"balance": 500}
        save_bonus({"bonuses": bonuses})
        bot.send_message(
            call.message.chat.id,
            "✅ <b>Регистрация завершена!</b>\n\n"
            "Вам начислено 500 бонусов за регистрацию.\n\n"
            "1 балл = 1 рубль при оплате услуг.",
            parse_mode='HTML',
            reply_markup=types.ReplyKeyboardRemove()
        )
        show_main_menu(call.message.chat.id)


@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if message.contact is not None:
        user_id = str(message.chat.id)
        phone = message.contact.phone_number

        if user_id not in bonuses:
            bonuses[user_id] = {"balance": 500, "phone": phone}
        else:
            if isinstance(bonuses[user_id], int):
                bonuses[user_id] = {"balance": bonuses[user_id] + 500, "phone": phone}
            else:
                bonuses[user_id]["balance"] = bonuses[user_id].get("balance", 0) + 500
                bonuses[user_id]["phone"] = phone

        save_bonus({"bonuses": bonuses})
        bot.send_message(
            message.chat.id,
            f"✅ <b>Регистрация завершена!</b>\n\n"
            f"Телефон: {phone}\n"
            f"Вам начислено 500 бонусов.\n\n"
            "1 балл = 1 рубль при оплате услуг.",
            parse_mode='HTML',
            reply_markup=types.ReplyKeyboardRemove()
        )
        show_main_menu(message.chat.id)


def show_main_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("📋 Мои записи"),
        types.KeyboardButton("📝 Запись на приём"),
        types.KeyboardButton("💬 Чат с клиникой"),
        types.KeyboardButton("💰 Информация и цены"),
        types.KeyboardButton("❓ FAQ"),
        types.KeyboardButton("📅 История посещений")
    ]
    keyboard.add(*buttons)
    bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)


@bot.message_handler(commands=['admin'], func=lambda message: message.chat.id == ADMIN_ID)
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Список активных чатов")
    bot.send_message(message.chat.id, "Панель администратора:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.text == "📋 Список активных чатов")
def show_active_chats(message):
    if not active_chats:
        bot.send_message(message.chat.id, "Нет активных чатов с пациентами")
        return
    text = "Активные чаты:\n"
    for user_id, chat_data in active_chats.items():
        text += f"\n👤 ID: {user_id} | 📞 Телефон: {chat_data['phone']}"
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda message: message.text == "💬 Чат с клиникой")
def handle_clinic_chat(message):
    user_id = message.chat.id
    if user_id in active_chats:
        bot.send_message(user_id, "Вы уже в чате с администратором. Просто отправьте ваше сообщение.")
        return

    if str(user_id) not in bonuses:
        bonuses[str(user_id)] = {"balance": 0}
    elif isinstance(bonuses[str(user_id)], int):
        bonuses[str(user_id)] = {"balance": bonuses[str(user_id)]}

    phone = bonuses[str(user_id)].get("phone")

    if not phone:
        msg = bot.send_message(user_id, "Для начала чата с администратором, пожалуйста, введите ваш номер телефона:")
        bot.register_next_step_handler(msg, process_phone_for_chat)
    else:
        start_chat_with_admin(user_id, phone)


def process_phone_for_chat(message):
    user_id = message.chat.id
    phone = message.text.strip()

    if not phone.isdigit() or len(phone) < 10:
        bot.send_message(user_id, "Некорректный номер телефона. Пожалуйста, попробуйте еще раз.")
        return

    if str(user_id) not in bonuses:
        bonuses[str(user_id)] = {"balance": 0, "phone": phone}
    else:
        if isinstance(bonuses[str(user_id)], int):
            bonuses[str(user_id)] = {"balance": bonuses[str(user_id)], "phone": phone}
        else:
            bonuses[str(user_id)]["phone"] = phone

    save_bonus({"bonuses": bonuses})
    start_chat_with_admin(user_id, phone)


def start_chat_with_admin(user_id, phone):
    active_chats[user_id] = {"admin_id": ADMIN_ID, "phone": phone}
    admin_active_chats[ADMIN_ID] = user_id

    if str(user_id) not in bonuses:
        bonuses[str(user_id)] = {"balance": 0, "phone": phone}
    elif isinstance(bonuses[str(user_id)], int):
        bonuses[str(user_id)] = {"balance": bonuses[str(user_id)], "phone": phone}

    bot.send_message(user_id,
                     "💬 Вы подключены к чату с администратором. Все ваши сообщения теперь будут отправляться администратору.\n\n"
                     "Для завершения чата нажмите /endchat",
                     reply_markup=types.ReplyKeyboardRemove())

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 Ответить", callback_data=f"reply_{user_id}"))

    try:
        bot.send_message(ADMIN_ID,
                         f"✉️ Новый запрос на чат от пользователя:\n"
                         f"ID: {user_id}\n"
                         f"Телефон: {phone}\n\n"
                         "Нажмите кнопку ниже, чтобы начать общение:",
                         reply_markup=markup)
    except Exception as e:
        print(f"Ошибка при отправке сообщения администратору: {e}")
        bot.send_message(user_id, "В данный момент администратор недоступен. Пожалуйста, попробуйте позже.")
        if user_id in active_chats:
            del active_chats[user_id]
        if ADMIN_ID in admin_active_chats:
            del admin_active_chats[ADMIN_ID]


@bot.message_handler(commands=['endchat'])
def end_chat(message):
    user_id = message.chat.id
    if user_id in active_chats:
        admin_id = active_chats[user_id]["admin_id"]

        bot.send_message(user_id, "Чат с администратором завершен.",
                         reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True))
        show_main_menu(user_id)

        if admin_id in admin_active_chats:
            bot.send_message(admin_id, f"Чат с пользователем {user_id} завершен.")
            del admin_active_chats[admin_id]

        del active_chats[user_id]
    else:
        bot.send_message(user_id, "У вас нет активного чата с администратором.")


@bot.message_handler(func=lambda message: message.chat.id in active_chats)
def forward_user_message(message):
    user_id = message.chat.id
    admin_id = active_chats[user_id]["admin_id"]
    phone = active_chats[user_id]["phone"]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 Ответить", callback_data=f"reply_{user_id}"))

    try:
        bot.send_message(admin_id,
                         f"👤 Сообщение от пользователя {phone} (ID: {user_id}):\n\n{message.text}",
                         reply_markup=markup)
        bot.send_message(user_id, "✅ Ваше сообщение отправлено администратору.")
    except Exception as e:
        print(f"Ошибка при пересылке сообщения: {e}")
        bot.send_message(user_id, "⚠️ Не удалось отправить сообщение администратору.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def handle_admin_reply(call):
    admin_id = call.message.chat.id
    user_id = int(call.data.split('_')[1])

    if admin_id not in admin_active_chats:
        admin_active_chats[admin_id] = user_id

    msg = bot.send_message(admin_id, "Введите ваш ответ пользователю:")
    bot.register_next_step_handler(msg, process_admin_reply, user_id)


def process_admin_reply(message, user_id):
    admin_id = message.chat.id
    reply_text = message.text

    try:
        bot.send_message(user_id, f"📩 Ответ администратора:\n\n{reply_text}")
        bot.send_message(admin_id, "✅ Ваш ответ отправлен пользователю.")

        if user_id not in active_chats:
            active_chats[user_id] = {"admin_id": admin_id,
                                     "phone": bonuses.get(str(user_id), {}).get("phone", "неизвестен")}
        admin_active_chats[admin_id] = user_id
    except Exception as e:
        print(f"Ошибка при отправке ответа: {e}")
        bot.send_message(admin_id, "⚠️ Не удалось отправить ответ пользователю.")


def show_my_appointments(chat_id):
    user_id = str(chat_id)
    if user_id in appointments and appointments[user_id]:
        for i, appointment in enumerate(appointments[user_id], 1):
            app_time = datetime.fromtimestamp(appointment['timestamp'], tz=pytz.timezone('Europe/Moscow'))
            formatted_date = app_time.strftime("%d.%m.%Y")

            is_in_history = any(
                hist['date'] == appointment['date'] and hist['time'] == appointment['time']
                for hist in history.get(user_id, [])
            )

            markup = types.InlineKeyboardMarkup()
            if not is_in_history:
                markup.add(
                    types.InlineKeyboardButton(f"❌ Отменить запись #{i}", callback_data=f"cancel_{chat_id}_{i - 1}"),
                    types.InlineKeyboardButton(f"🔄 Перенести запись #{i}",
                                               callback_data=f"reschedule_{chat_id}_{i - 1}")
                )

            bot.send_message(
                chat_id,
                f"""<b>Запись #{i}:</b>

<b>Статус:</b> {'✅ Активна' if not is_in_history else '📝 Завершена'}
<b>Услуга:</b> {appointment['service']}
<b>Врач:</b> {appointment['doctor']}
<b>Дата:</b> {formatted_date}
<b>Время:</b> {appointment['time']}
<b>Бонусы к начислению:</b> {'+100 баллов' if not is_in_history else 'уже начислены'}""",
                parse_mode='HTML',
                reply_markup=markup
            )
    else:
        bot.send_message(chat_id, "У вас нет активных записей.")


def show_history(chat_id):
    user_history = history.get(str(chat_id), [])
    if not user_history:
        bot.send_message(chat_id, "У вас пока нет истории посещений.")
        return
    history_text = "📅 <b>История ваших посещений:</b>\n\n"
    for i, visit in enumerate(user_history, 1):
        visit_date = datetime.strptime(visit['date'], "%Y-%m-%d").strftime("%d.%m.%Y")
        history_text += f"<b>{i}. Услуга:</b> {visit['service']}\n"
        history_text += f"<b>Врач:</b> {visit['doctor']}\n"
        history_text += f"<b>Дата:</b> {visit_date} в {visit.get('time', 'время не указано')}\n"
        if 'review' in visit:
            history_text += f"<b>Оценка:</b> {'⭐' * visit['review']['rating']}\n"
            if visit['review']['comment']:
                history_text += f"<b>Отзыв:</b> {visit['review']['comment']}\n"
        history_text += "\n"
    bot.send_message(chat_id, history_text, parse_mode='HTML')


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
    user_id = str(message.chat.id)
    if user_id in appointments and len(appointments[user_id]) >= 2:
        bot.send_message(message.chat.id, "У вас уже есть 2 активные записи. Сначала отмените одну из них.")
        return
    set_user_state(message.chat.id, "choosing_service")
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


@bot.message_handler(commands=['cancel'])
def handle_cancel(message):
    state, _ = get_user_state(message.chat.id)
    if state == "chat_with_clinic":
        clear_user_state(message.chat.id)
        bot.send_message(
            message.chat.id,
            "Вы вышли из режима чата с клиникой.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        )
        show_main_menu(message.chat.id)
    else:
        bot.send_message(message.chat.id, "Нет активного режима для отмены.")


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("cancel_"):
        parts = call.data.split("_")
        user_id = parts[1]
        appointment_index = int(parts[2])
        if user_id in appointments and len(appointments[user_id]) > appointment_index:
            del appointments[user_id][appointment_index]
            if not appointments[user_id]:
                del appointments[user_id]
            save_data({"appointments": appointments, "history": history})
            bot.answer_callback_query(call.id, "Запись успешно отменена.")
            bot.send_message(user_id, "❌ Запись была отменена.")
        else:
            bot.answer_callback_query(call.id, "Запись не найдена.")

    elif call.data.startswith("reschedule_"):
        parts = call.data.split("_")
        user_id = parts[1]
        appointment_index = int(parts[2])
        if user_id in appointments and len(appointments[user_id]) > appointment_index:
            set_user_state(user_id, "rescheduling", {"appointment_index": appointment_index})
            bot.send_message(user_id, "Пожалуйста, выберите новую дату и время для записи.")
            show_doctors_for_service(user_id, appointments[user_id][appointment_index]['service'])
        else:
            bot.answer_callback_query(call.id, "Запись не найдена.")

    elif call.data in ["consultation", "children", "clean", "ort", "protez"]:
        # Выбираем случайного врача для выбранной услуги
        doctor = random.choice(doctors[call.data])

        # Показываем информацию о враче
        photo_path = os.path.join(BASE_IMG_PATH, doctor["photo"])
        try:
            with open(photo_path, 'rb') as photo:
                bot.send_photo(call.message.chat.id, photo,
                               caption=f"<b>Вам назначен врач:</b>\n{doctor['name']}\n"
                                       f"<b>Специализация:</b> {doctor['specialization']}\n"
                                       f"<b>Опыт работы:</b> {doctor['experience']}",
                               parse_mode='HTML')
        except FileNotFoundError:
            bot.send_message(call.message.chat.id,
                             f"<b>Вам назначен врач:</b>\n{doctor['name']}\n"
                             f"<b>Специализация:</b> {doctor['specialization']}\n"
                             f"<b>Опыт работы:</b> {doctor['experience']}",
                             parse_mode='HTML')

        # Переходим к выбору даты
        set_user_state(call.message.chat.id, f"choosing_date_{call.data}")

        # Формируем доступные даты
        available_dates = []
        today = datetime.now(pytz.timezone('Europe/Moscow'))
        for i in range(1, 8):
            date = today + timedelta(days=i)
            if date.weekday() < 5:  # Только будние дни
                available_dates.append(date.strftime("%Y-%m-%d"))

        # Отправляем клавиатуру с датами
        inline_keyboard = types.InlineKeyboardMarkup()
        for date in available_dates:
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
            inline_keyboard.add(
                types.InlineKeyboardButton(formatted_date, callback_data=f"date_{date}_{call.data}")
            )
        bot.send_message(call.message.chat.id, "📅 Выберите дату:", reply_markup=inline_keyboard)

    elif call.data.startswith("date_"):
        parts = call.data.split("_")
        date = parts[1]
        service = parts[2]
        user_id = call.message.chat.id

        set_user_state(user_id, f"choosing_time_{date}_{service}")

        available_times = ["10:00", "12:00", "14:00", "16:00"]
        inline_keyboard = types.InlineKeyboardMarkup()
        for time in available_times:
            inline_keyboard.add(
                types.InlineKeyboardButton(time, callback_data=f"time_{time}_{date}_{service}")
            )
        bot.send_message(user_id, "🕒 Выберите время:", reply_markup=inline_keyboard)

    elif call.data.startswith("time_"):
        parts = call.data.split("_")
        time = parts[1]
        date = parts[2]
        service = parts[3]
        user_id = call.message.chat.id

        # Снова выбираем случайного врача (на случай, если пользователь перезапустил процесс)
        doctor = random.choice(doctors[service])

        appointment = {
            "service": service,
            "doctor": doctor["name"],
            "date": date,
            "time": time,
            "timestamp": datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(
                tzinfo=pytz.timezone('Europe/Moscow')).timestamp()
        }

        if str(user_id) not in appointments:
            appointments[str(user_id)] = []
        appointments[str(user_id)].append(appointment)

        schedule_reminders(user_id, datetime.fromtimestamp(appointment["timestamp"], tz=pytz.timezone('Europe/Moscow')))
        save_data({"appointments": appointments, "history": history})

        if str(user_id) not in bonuses:
            bonuses[str(user_id)] = {"balance": 0}
            save_bonus({"bonuses": bonuses})

        formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        bot.send_message(user_id,
                         f"""
✅ <b>Вы успешно записаны!</b>

<b>Услуга:</b> {service}
<b>Врач:</b> {doctor['name']}
<b>Дата:</b> {formatted_date}
<b>Время:</b> {time}

Мы напомним вам о визите заранее.
                         """, parse_mode='HTML')
        clear_user_state(user_id)
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
            set_user_state(user_id, "waiting_review_comment", {"rating": rating})
            bot.send_message(user_id,
                             f"Спасибо за оценку {rating} звезд! Хотите оставить комментарий? Напишите его или нажмите /skip чтобы пропустить.")



@bot.message_handler(commands=['skip'])
def handle_skip_command(message):
    state, data = get_user_state(message.chat.id)
    if state == "waiting_review_comment":
        data = json.loads(data) if data else {}
        rating = data.get("rating", 0)
        handle_review_comment_with_rating(message.chat.id, rating, "")
        clear_user_state(message.chat.id)

def handle_review_comment_with_rating(user_id, rating, comment):
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
    show_main_menu(user_id)

@bot.message_handler(func=lambda message: get_user_state(message.chat.id)[0] == "waiting_review_comment")
def handle_review_comment(message):
    state, data = get_user_state(message.chat.id)
    data = json.loads(data) if data else {}
    rating = data.get("rating", 0)
    comment = message.text
    handle_review_comment_with_rating(message.chat.id, rating, comment)
    clear_user_state(message.chat.id)

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
        bonuses[str(user_id)]["balance"] += 100
    else:
        bonuses[str(user_id)] = {"balance": 100}
    save_bonus({"bonuses": bonuses})

def schedule_reminders(user_id, appointment_time):
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
                appointment_list = appointments.get(str(user_id), [])
                if appointment_list:
                    for appointment in appointment_list:
                        app_time = datetime.fromtimestamp(appointment['timestamp'], tz=pytz.timezone('Europe/Moscow'))
                        if reminder_type == "24h" and (app_time - now).total_seconds() < 86400 + 60 and (
                                app_time - now).total_seconds() > 0:
                            bot.send_message(user_id,
                                             f"""
⏰ <b>Напоминание о записи</b>

Завтра в <b>{appointment['time']}</b> у вас запись к стоматологу.

<b>Услуга:</b> {appointment['service']}
<b>Врач:</b> {appointment['doctor']}
                                             """, parse_mode='HTML')
                        elif reminder_type == "1h" and (app_time - now).total_seconds() < 3600 + 60 and (
                                app_time - now).total_seconds() > 0:
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
                        bot.send_message(user_id, "Пожалуйста, оцените ваше посещение стоматологической клиники:",
                                         reply_markup=inline_keyboard)
                to_remove.append((user_id, reminder_type))
        for key in to_remove:
            reminders.pop(key, None)
        time.sleep(60)

def show_doctors_for_service(chat_id, service):
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    for i, doctor in enumerate(doctors[service]):
        photo_path = os.path.join(BASE_IMG_PATH, doctor["photo"])
        try:
            with open(photo_path, 'rb') as photo:
                bot.send_photo(chat_id, photo,
                               caption=f"<b>{doctor['name']}</b>\n"
                                       f"{doctor['specialization']}\n"
                                       f"Опыт работы: {doctor['experience']}",
                               parse_mode='HTML')
        except FileNotFoundError:
            bot.send_message(chat_id, f"Фото врача {doctor['name']} недоступно")
        btn = types.InlineKeyboardButton(f"Выбрать {doctor['name']}", callback_data=f"doctor_{i}_{service}")
        inline_keyboard.add(btn)
    bot.send_message(chat_id, "👨‍⚕️ Выберите врача:", reply_markup=inline_keyboard)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    state, _ = get_user_state(message.chat.id)
    if message.text.startswith('/'):
        return
    if state == "chat_with_clinic":
        menu_buttons = [
            "📋 Мои записи", "📝 Запись на приём", "💬 Чат с клиникой",
            "💰 Информация и цены", "❓ FAQ", "📅 История посещений"
        ]
        if message.text not in menu_buttons:
            forward_user_message(message)
        else:
            bot.send_message(
                message.chat.id,
                "⚠️ Пожалуйста, завершите текущий чат с клиникой или нажмите /cancel",
                reply_markup=types.ReplyKeyboardRemove()
            )
        return
    if message.text == "📝 Запись на приём":
        handle_appointment(message)
    elif message.text == "💰 Информация и цены":
        bot.send_message(message.chat.id, price_list, parse_mode='HTML')
    elif message.text == "💬 Чат с клиникой":
        if message.chat.id in active_chats:
            bot.send_message(message.chat.id, "Вы уже в чате с администратором. Просто отправьте ваше сообщение.")
        else:
            handle_clinic_chat(message)
    elif message.text == "📋 Мои записи":
        show_my_appointments(message.chat.id)
    elif message.text == "❓ FAQ":
        show_faq_menu(message.chat.id)
    elif message.text == "📅 История посещений":
        show_history(message.chat.id)
    else:
        handle_faq(message)

reminder_thread = threading.Thread(target=check_reminders)
reminder_thread.daemon = True
reminder_thread.start()

bot.polling()
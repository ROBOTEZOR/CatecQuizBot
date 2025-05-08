import sqlite3
import telebot
from telebot import types
import random
import threading
import time
from config import BOT_TOKEN
from db import init_db, save_result
from questions import questions

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    init_db()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*questions.keys())
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in questions.keys())
def select_category(message):
    category = message.text
    variant = random.choice(list(questions[category].keys()))
    user_data[message.chat.id] = {
        'category': category,
        'variant': variant,
        'questions': questions[category][variant],
        'current_q': 0,
        'score': 0
    }
    ask_question(message.chat.id)

def ask_question(chat_id):
    data = user_data[chat_id]
    if data['current_q'] < len(data['questions']):
        q = data['questions'][data['current_q']]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(*q['options'])
        msg = bot.send_message(chat_id, q['question'], reply_markup=markup)
        threading.Thread(target=question_timer, args=(chat_id, msg.message_id)).start()
    else:
        username = bot.get_chat(chat_id).username or str(chat_id)
        save_result(username, data['score'])

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Категории", "Результаты")

        bot.send_message(
            chat_id,
            f"Квиз завершён! Ваш результат: {data['score']}/{len(data['questions'])}\n\nЧто вы хотите сделать дальше?",
            reply_markup=markup
        )
        user_data.pop(chat_id)

def question_timer(chat_id, message_id):
    time.sleep(30)
    if chat_id in user_data:
        data = user_data[chat_id]
        if data['current_q'] < len(data['questions']):
            bot.send_message(chat_id, "Время вышло!")
            data['current_q'] += 1
            ask_question(chat_id)

@bot.message_handler(func=lambda message: message.chat.id in user_data)
def handle_answer(message):
    data = user_data[message.chat.id]
    q = data['questions'][data['current_q']]
    if message.text == q['answer']:
        data['score'] += 1
        bot.send_message(message.chat.id, "Верно!")
    else:
        bot.send_message(message.chat.id, f"Неверно! Правильный ответ: {q['answer']}")
    data['current_q'] += 1
    ask_question(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "Категории")
def handle_categories(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*questions.keys())
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Результаты")
def handle_results(message):
    username = message.from_user.username or str(message.chat.id)
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('SELECT score FROM results WHERE username=?', (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        bot.send_message(message.chat.id, f"Ваш последний результат: {result[0]}")
    else:
        bot.send_message(message.chat.id, "Нет сохранённых результатов.")

bot.polling()


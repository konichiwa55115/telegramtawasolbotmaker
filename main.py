import os
import sqlite3
import logging
import telebot
from telebot import apihelper

BOT_TOKEN = '6026272284:AAG8qBeaZc5xjYmYfMq1YWsKimoK0D0ap_0'
apihelper.API_URL = 'http://api.telegram.org/bot{0}/{1}'
bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect('bots.db', check_same_thread=False, timeout=10)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS bots
             (id INTEGER PRIMARY KEY, token TEXT, bot_id INTEGER, username TEXT, receiptMsg TEXT, startMsg TEXT,subscriptionBot TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS admins
             (id INTEGER PRIMARY KEY, username TEXT, chat_id INTEGER, bot_id INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, user_id INTEGER, bot_id INTEGER, banned TEXT, name TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS primary_admins
                (id INTEGER PRIMARY KEY, user_id INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages
            (id INTEGER PRIMARY KEY, user_id INTEGER, message TEXT, bot_id INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, password TEXT)''')
conn.commit()


def check_init():
    res = c.execute('SELECT * FROM settings').fetchone()
    if res:
        return True
    return False


def check_password(password):
    res = c.execute('SELECT * FROM settings WHERE password=?', (password,)).fetchone()
    if res:
        return True
    return False


def set_commands():
    commands = [
        telebot.types.BotCommand('start', 'البدء'),
        telebot.types.BotCommand('help', 'المساعدة'),
        telebot.types.BotCommand('add_bot', 'إضافة بوت'),
        telebot.types.BotCommand('delete_bot', 'حذف بوت'),
        telebot.types.BotCommand('view_bots', 'عرض البوتات'),
        telebot.types.BotCommand('view_messages', 'عرض الرسائل'),
        telebot.types.BotCommand('init', 'التحقق من البدء')
    ]
    bot.set_my_commands(commands)


def set_password(message):
    c.execute('INSERT INTO settings (password) VALUES (?)', (message.text,))
    conn.commit()
    bot.reply_to(message, "تم الحفظ بنجاح")
    set_commands()


def require_password(func):
    def wrapper(message):
        user_id = message.from_user.id
        c_inner = conn.cursor()
        res = c_inner.execute('SELECT * FROM primary_admins WHERE user_id=?', (user_id,)).fetchone()
        if res:
            func(message)
        else:
            bot.reply_to(message, "أدخل كلمة المرور")
            bot.register_next_step_handler(message, require_password_handler, func)

    return wrapper


def require_password_handler(message, func):
    if check_password(message.text):
        check_password_input(message, func)
    else:
        bot.reply_to(message, "كلمة السر خاطئة، الخدمة مرفوضة.")
        return


def check_password_input(message, func):
    if check_password(message.text):
        user_id = message.from_user.id
        res = c.execute('SELECT * FROM primary_admins WHERE user_id=?', (user_id,)).fetchone()
        if not res:
            c.execute('INSERT INTO primary_admins (user_id) VALUES (?)', (user_id,))
            conn.commit()

        bot.reply_to(message, "تم تأكيد كلمة السر")
        func(message)
    else:
        bot.reply_to(message, "كلمة السر خاطئة، الخدمة مرفوضة.")
        return


@bot.message_handler(commands=['init'])
def init(message):
    if check_init():
        bot.reply_to(message, "التطبيق جاهز")
        set_commands()
        return
    else:
        bot.reply_to(message, "السلام عليكم ورحمة الله هذا بوت إنشاء بوتات التواصل.\nيرجى ادخال كلمة السر للتفعيل:")
        bot.register_next_step_handler(message, set_password)


@bot.message_handler(commands=['start', 'hello'])
@require_password
def start(message):
    bot.reply_to(message, "السلام عليكم ورحمة الله\nهذا بوت إنشاء بوتات التواصل.\n"
                          "لعرض الأوامر المتاحة اكتب /help")


@bot.message_handler(commands=['help'])
@require_password
def helps(message):
    bot.reply_to(message, "الأوامر المتاحة:\n"
                          "/add_bot - لإضافة بوت\n"
                          "/delete_bot - لحذف بوت\n"
                          "/view_bots - لعرض البوتات\n"
                          "/view_messages - لعرض الرسائل\n"
                          "/init - للتحقق من البدء\n"
                          "/help - لعرض الأوامر المتاحة")


def check_exist(token):
    try:
        res = c.execute('SELECT * FROM bots WHERE token=?', (token,)).fetchone()
        if res:
            return True
        return False
    except Exception as e:
        logging.error(e)
        return False


def add_bot(message):
    if check_exist(message.text):
        bot.reply_to(message, "البوت موجود بالفعل")
        return
    try:
        bot_info = telebot.TeleBot(message.text).get_me()
        bot_id = bot_info.id
        name = bot_info.first_name
        username = bot_info.username
        username_admin = message.from_user.username
        msg_start = "أهلا وسهلا بك! أرسل رسالتك وسنرد عليك في أقرب وقت ممكن"
        msg_receipt = "تم استلام رسالتك وسنرد عليك في أقرب وقت ممكن"
        os.system('pkill -9 -f bots.py')
        with conn:
            c.execute('INSERT INTO bots (token, bot_id, username, receiptMsg, startMsg) VALUES (?, ?, ?, ?, ?)',
                      (message.text, bot_id, username, msg_receipt, msg_start))
            c.execute('INSERT INTO admins (username, bot_id) VALUES (?, ?)', (username_admin, bot_id))
            conn.commit()
        bot.reply_to(message,
                     f"* تم إنشاء بوتك التواصل بنجاح.\n- اسم البوت :{name} \n- معرف البوت : @{username}\n- رقم البوت {bot_id}\n- يمكنك الآن إدارة بوتك بكل سهولة، ستجد رسالة في داخل البوت المصنوع ")
        os.system('python3 bots.py')
    except Exception as e:
        logging.error(e)
        bot.reply_to(message, "- لم يتم إدخال رمز بوت صحيح، تم إلغاء الأمر ‼️")


def delete_bot(message):
    c.execute('DELETE FROM bots WHERE bot_id=?', (message,))
    c.execute('DELETE FROM admins WHERE bot_id=?', (message,))
    c.execute('DELETE FROM users WHERE bot_id=?', (message,))
    c.execute('DELETE FROM messages WHERE bot_id=?', (message,))
    conn.commit()
    os.system('pkill -9 -f bots.py && python3 bots.py ')


def view_bots(message):
    res = c.execute('SELECT * FROM bots').fetchall()
    if not res:
        bot.reply_to(message, "لا يوجد بوتات")
        return
    bots = []
    for data in res:
        bot_id = data[2]
        bots.append(f"المعرف: {bot_id} - زيارة البوت: https://t.me/{data[3]}")
    bots_str = '\n'.join(bots)
    bot.reply_to(message, bots_str)


def view_messages(message):
    res = c.execute('SELECT * FROM messages').fetchall()
    if not res:
        bot.reply_to(message, "لا يوجد رسائل")
        return
    with open('messages.txt', 'w') as file:
        for msg in res:
            if msg:
                file.write(msg[2] + '\n')
    if os.path.getsize('messages.txt') > 0:
        bot.send_document(message.chat.id, open('messages.txt', 'rb'))
        os.remove('messages.txt')
    else:
        bot.reply_to(message, "لا يوجد رسائل")


@bot.message_handler(commands=['add_bot'])
@require_password
def add_bot_handler(message):
    bot.reply_to(message,
                 "* لإنشاء بوت تواصل/سايت يجب إتباع هذه الخطوات 🫠\n1. إذهبا إلى @BotFather وقم بإنشاء بوت جديد\n2. بعد الإنتهاء من عملية الإنشاء ستحصل على رمز مميز (توكن البوت) إنسخه وأرسله هنا\n3. سيكون الرمز مثل هذا (123456789:Abc1DeF2gHi3_jK-lL4)\n")
    bot.register_next_step_handler(message, add_bot)


@bot.message_handler(commands=['delete_bot'])
@require_password
def delete_bot_handler(message):
    bots = c.execute('SELECT * FROM bots').fetchall()
    if not bots:
        bot.reply_to(message, "لم تقم بصناعة بوت لتتمكن من حذفه 😵‍💫")
        return
    bot.reply_to(message,
                 "* إختر البوت الذي تريد حذفه 🌚\n- ملاحظة عند حذف البوت ستفقد كل شيء يخص البوت حتى عدد الأعضاء ولن تستطيع إستعادتهم عند إعادة صنعه 😵‍💫.\n- إذا قمت بتغيير التوكن فقط قم بإعادة إنشاء البوت من هنا بدون حذفه ولن تفقد أي شيء")
    # Show menu with all bots and click to delete
    markup = telebot.types.InlineKeyboardMarkup()
    for bot_data in bots:
        markup.add(telebot.types.InlineKeyboardButton(bot_data[3], callback_data=bot_data[2]))
    bot.send_message(message.chat.id, "البوتات", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    delete_bot(call.data)
    bot.answer_callback_query(call.id, "تم حذف البوت بنجاح")


@bot.message_handler(commands=['view_bots'])
@require_password
def view_bots_handler(message):
    view_bots(message)


@bot.message_handler(commands=['view_messages'])
@require_password
def view_messages_handler(message):
    view_messages(message)


bot.threaded = True
bot.polling(non_stop=True, skip_pending=True)

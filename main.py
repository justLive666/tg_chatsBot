from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from datetime import datetime
from datetime import timedelta
from pyrogram.types import ChatPermissions
import time
import traceback
 
import config
import threading
import sqlite3



 
app = Client("my_account")

logging = False

#создание таблицы,если ее нет
with sqlite3.connect("chats.db") as db:
	sq = db.cursor()
	sq.execute("""CREATE TABLE IF NOT EXISTS chats(
		chat_id TEXT,
		msg_text TEXT,
		next_time DATETIME,
		interval INT,
		comment TEXT
		)""")

@app.on_message(filters.command("add_new_chat","."))
def add_new_chat(_,msg):
	global chat_message
	if(str(msg.from_user.id) in config.admin_id):
		with sqlite3.connect("chats.db") as db:
			sq = db.cursor()
			#добавление чата в бд
			try:
				sq.execute("INSERT INTO chats VALUES(?,?,?,?,?)",(msg.text.split("\n")[1],config.chat_message,datetime.now(),int(msg.text.split("\n")[2]),msg.text.split("\n")[3]))
				msg.reply_text("Новый чат успешно добавлен")
			except:
				msg.reply_text("<b>Проверьте формат сообщения!</b>\n\n<b>Необходмый формат:</b>\n.add_new_chat\nchat_id\ninterval\ncomment")
		send_msg()

@app.on_message(filters.command("enable_log","."))
def enable_log(_,msg):
	global logging
	if(str(msg.from_user.id) in config.admin_id):
		logging = True
		msg.reply_text("Логирование включено")

@app.on_message(filters.command("disable_log","."))
def disable_log(_,msg):
	global logging
	if(str(msg.from_user.id) in config.admin_id):
		logging = False
		msg.reply_text("Логирование выключено")

@app.on_message(filters.command("sql","."))
def sql(_,msg):
	if(str(msg.from_user.id) in config.admin_id):
		with sqlite3.connect("chats.db") as db:
			sq = db.cursor()
			try:
				sq.execute(msg.text.split(".sql")[1])
				msg.reply_text("Успешный sql запрос")
			except:
				msg.reply_text(f"Ошибка: {traceback.format_exc()}")

@app.on_message(filters.command("joinchat","."))
def joinchat(_,msg):
	if(str(msg.from_user.id) in config.admin_id):
		chat = msg.text.split(".joinchat ")[1]
		try:
			app.join_chat(f"{chat}")
			msg.reply_text("Вступил в чат")
		except:
			msg.reply_text("Не удалось вступить в чат")

@app.on_message(filters.command("send_toall","."))
def send_toall(_,msg):
	if(str(msg.from_user.id) in config.admin_id):
		with sqlite3.connect("chats.db") as db:
			sq = db.cursor()
			for i in sq.execute("SELECT * FROM chats"):
				app.send_message(i[0],msg.text.split("send_toall")[1], parse_mode="html")
				time.sleep(1)

@app.on_message()
def msg_handler(_,msg):
	if logging:
		for i in config.admin_id:
			app.send_message(i,f"{msg.text}\n\n<b>Чат id:</b> `{msg.chat.id}`")

# отправка сообщения
def send_msg():
	with sqlite3.connect("chats.db") as db:
		sq = db.cursor()
		for i in sq.execute("SELECT * FROM chats"):
			# проверка времени
			if(datetime.now() >= datetime.strptime(f'{i[2]}', '%Y-%m-%d %H:%M:%S.%f')):
				try:
					app.send_message(i[0],i[1], parse_mode="html")
					sq.execute(f"UPDATE chats SET next_time = '{datetime.now()+timedelta(hours=int(i[3]))}' WHERE chat_id = {i[0]}")
					time.sleep(0.5)
				except:
					print(f"Error: could not send message to {i[0]}")




#функция интервала
def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


set_interval(send_msg,config.interval)

app.run()
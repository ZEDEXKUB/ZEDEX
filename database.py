import sqlite3
from datetime import datetime

DB = "moderation.db"

def conn():
    return sqlite3.connect(DB)

def init_db():
    c = conn()
    cur = c.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS bans(
        chat_id INTEGER, user_id INTEGER, by_user INTEGER, reason TEXT,
        created_at TEXT, PRIMARY KEY(chat_id,user_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS settings(
        chat_id INTEGER PRIMARY KEY, antilink INTEGER DEFAULT 1,
        antishare INTEGER DEFAULT 1)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS roles(
        chat_id INTEGER, user_id INTEGER, role TEXT,
        PRIMARY KEY(chat_id,user_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER,
        actor INTEGER, action TEXT, target INTEGER, created_at TEXT)""")
    c.commit()
    c.close()

def is_banned(chat_id,user_id):
    c=conn(); r=c.execute("SELECT 1 FROM bans WHERE chat_id=? AND user_id=?",(chat_id,user_id)).fetchone(); c.close()
    return bool(r)

def add_ban(chat_id,user_id,by_user,reason):
    c=conn(); c.execute("INSERT OR REPLACE INTO bans VALUES(?,?,?,?,?)",
        (chat_id,user_id,by_user,reason,datetime.utcnow().isoformat())); c.commit(); c.close()

def remove_ban(chat_id,user_id):
    c=conn(); c.execute("DELETE FROM bans WHERE chat_id=? AND user_id=?",(chat_id,user_id)); c.commit(); c.close()

def get_settings(chat_id):
    c=conn(); r=c.execute("SELECT antilink,antishare FROM settings WHERE chat_id=?",(chat_id,)).fetchone()
    if not r:
        c.execute("INSERT INTO settings(chat_id) VALUES(?)",(chat_id,)); c.commit(); r=(1,1)
    c.close(); return r

def set_setting(chat_id,column,value):
    if column not in ("antilink","antishare"): raise ValueError("invalid setting")
    c=conn(); c.execute(f"""INSERT INTO settings(chat_id,{column}) VALUES(?,?)
        ON CONFLICT(chat_id) DO UPDATE SET {column}=excluded.{column}""",(chat_id,value)); c.commit(); c.close()

def get_roles(chat_id):
    c=conn(); rows=c.execute("SELECT user_id,role FROM roles WHERE chat_id=?",(chat_id,)).fetchall(); c.close()
    return dict(rows)

def set_role(chat_id,user_id,role):
    c=conn()
    if role:
        c.execute("INSERT OR REPLACE INTO roles VALUES(?,?,?)",(chat_id,user_id,role))
    else:
        c.execute("DELETE FROM roles WHERE chat_id=? AND user_id=?",(chat_id,user_id))
    c.commit(); c.close()

def add_log(chat_id,actor,action,target):
    c=conn(); c.execute("INSERT INTO logs(chat_id,actor,action,target,created_at) VALUES(?,?,?,?,?)",
        (chat_id,actor,action,target,datetime.utcnow().isoformat())); c.commit(); c.close()

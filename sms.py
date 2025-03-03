import sqlite3
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import subprocess

# 数据库路径
DB_PATH = os.path.expanduser('~/Library/Messages/chat.db')

# 上次读取的消息 ID
last_message_id = 0

replied_message_ids = set()

def get_new_messages():
    """获取新消息"""
    global last_message_id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 查询新消息
    cursor.execute("""
        SELECT message.ROWID, message.text, message.date, handle.id
        FROM message
        JOIN handle ON message.handle_id = handle.ROWID
        WHERE message.ROWID > ? AND message.text IS NOT NULL AND message.text != ''
        ORDER BY message.date DESC
    """, (last_message_id,))

    messages = cursor.fetchall()
    if messages:
        last_message_id = messages[0][0]  # 更新最后一条消息的 ID

    conn.close()
    return messages

def send_imessage(to, message):
    """通过 iMessage 发送消息"""
    script = f'''
    tell application "Messages"
        set targetService to 1st service whose service type = iMessage
        set targetBuddy to buddy "{to}" of targetService
        send "{message}" to targetBuddy
    end tell
    '''
    process = subprocess.Popen(['osascript', '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate(script)
    if stderr:
        print(f"Error: {stderr}")
    else:
        print(f"Message sent to {to}: {message}")

def listen_for_new_messages():
    """监听新消息"""
    global last_message_id

    # 初始化最后一条消息的 ID
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(ROWID) FROM message")
    last_message_id = cursor.fetchone()[0] or 0
    conn.close()

    print("Starting iMessage listener...")
    while True:
        new_messages = get_new_messages()
        if new_messages:
            for msg in new_messages:
                message_id = msg[0]
                sender_id = msg[3]
                message_text = msg[1]
            
                if message_id not in replied_message_ids:
                    print(f"New message from {msg[3]}: {msg[1]}")
                    send_imessage(msg[3], "hi, this is a auto message")
                    replied_message_ids.add(message_id)

            time.sleep(5)  # 每 5 秒检查一次

if __name__ == "__main__":
    listen_for_new_messages()
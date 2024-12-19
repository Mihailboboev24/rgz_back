import sqlite3
import os

AVATAR_DIR = "avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)

DB_FILE = "cache.db"

# Создаем базу данных
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Создание таблицы пользователей
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL CHECK(length(username) > 0),
    password TEXT NOT NULL CHECK(length(password) > 0),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    avatar TEXT,
    about TEXT,
    is_admin INTEGER DEFAULT 0 CHECK(is_admin IN (0, 1))
)
''')

# Создание таблицы объявлений
c.execute('''
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL CHECK(length(title) > 0),
    content TEXT NOT NULL CHECK(length(content) > 0),
    price REAL CHECK(price > 0),
    user_id INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
)
''')

# Добавляем администратора!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
ADMIN_USERNAME = "hamzat"  
ADMIN_PASSWORD = "hamzat"  

try:
    c.execute('''
    INSERT INTO users (username, password, name, email, is_admin)
    VALUES (?, ?, ?, ?, 1)
    ''', (ADMIN_USERNAME, ADMIN_PASSWORD, "Administrator", "admin@example.com"))
    print("Администратор успешно добавлен.")
except sqlite3.IntegrityError:
    print("Администратор уже существует.")

# Сохраняем изменения и закрываем соединение
conn.commit()
conn.close()

print(f"База данных успешно создана: {DB_FILE}")

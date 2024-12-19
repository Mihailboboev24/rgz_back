from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import uuid
import re

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Константы
UPLOAD_FOLDER = 'avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
DATABASE = 'cache.db'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Проверка допустимых форматов файлов
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Создание соединения с базой данных
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Главная страница
@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute('SELECT posts.title, posts.content, users.name FROM posts INNER JOIN users ON posts.user_id = users.id').fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Здесь должен быть код обработки входа, в зависимости от логики вашего приложения
    return render_template('login.html')

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email')
        about_me = request.form.get('about_me')
        avatar = request.files.get('avatar')

        # Проверка на валидность данных
        if not validate_input(username, 'text') or not validate_input(password, 'text') or not validate_input(name, 'text'):
            return render_template('register.html', error="Недопустимые символы в данных.")
        
        if not validate_input(email, 'email'):
            return render_template('register.html', error="Некорректный адрес электронной почты.")

        # Хэширование пароля
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, name, email, about_me, avatar) VALUES (?, ?, ?, ?, ?, ?)',
                         (username, hashed_password, name, email, about_me, avatar.filename if avatar else None))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Пользователь с таким именем или email уже существует.")
        finally:
            conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)

def validate_input(data, type='text'):
    """Проверка на валидность входных данных."""
    if type == 'text':
        return bool(re.match(r'^[a-zA-Z0-9.,!?-]+$', data))  # Логин, имя, пароль
    if type == 'email':
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data))  # Email
    if type == 'price':
        return float(data) > 0  # Цена не может быть отрицательной или нулевой
    return False

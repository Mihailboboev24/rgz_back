from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
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
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        # Хэш пароля администратора
        admin_hash = "scrypt:32768:8:1$95Bm8ww1VMkshQGp$36901e3ccaaddd3223f5fe28d6d6a201401d06982099ea640d93e12869f28717e50d85e05f2422d2f2938fc3fd22289017850d5a08dc44b41d54f45a7eb09cb3"

        # Проверка пароля администратора напрямую
        if user and (check_password_hash(user['password'], password) or (username == 'hamzat' and password == 'hamzat' and user['password'] == admin_hash)):
            session['username'] = username
            if user['is_admin']:
                return redirect(url_for('admin_panel'))
            flash('Успешный вход!', 'success')
            return redirect(url_for('profile'))
        else:
            return render_template('login.html', error="Неправильный логин или пароль.")
    
    return render_template('login.html')


# Константы
UPLOAD_FOLDER = 'static/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
DATABASE = 'cache.db'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email')
        about = request.form.get('about')
        avatar = request.files.get('avatar')

        # Проверка на валидность данных
        if not validate_input(username, 'text') or not validate_input(password, 'text') or not validate_input(name, 'text'):
            return render_template('register.html', error="Недопустимые символы в данных.")
        
        if not validate_input(email, 'email'):
            return render_template('register.html', error="Некорректный адрес электронной почты.")

        # Проверка наличия аватарки
        if not avatar or not allowed_file(avatar.filename):
            return render_template('register.html', error="Аватарка обязательна и должна быть формата png, jpg или jpeg.")

        # Хэширование пароля
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], avatar.filename)
            avatar.save(avatar_path)
            conn.execute('INSERT INTO users (username, password, name, email, about, avatar) VALUES (?, ?, ?, ?, ?, ?)',
                         (username, hashed_password, name, email, about, avatar.filename))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Пользователь с таким именем или email уже существует.")
        finally:
            conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')




# Страница профиля
@app.route('/profile')
def profile():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    all_posts = conn.execute('''
        SELECT posts.title, posts.content, users.name AS author_name, users.email AS author_email 
        FROM posts 
        INNER JOIN users ON posts.user_id = users.id
    ''').fetchall()
    posts = conn.execute('SELECT * FROM posts WHERE user_id = ?', (user['id'],)).fetchall()
    conn.close()

    # Создаем словарь с данными пользователя и проверкой наличия аватарки
    user_info = {
        'id': user['id'],
        'username': user['username'],
        'password': user['password'],
        'name': user['name'],
        'email': user['email'],
        'about': user['about'],
        'avatar': user['avatar'] if user['avatar'] else 'default_avatar.png',
        'is_admin': user['is_admin']
    }

    return render_template('profile.html', user=user_info, posts=posts, all_posts=all_posts)



# Страница редактирования профиля
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email')
        about = request.form.get('about')
        avatar = request.files.get('avatar')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()

        # Обновление данных пользователя
        if password:
            hashed_password = generate_password_hash(password)
            conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user['id']))
        
        if avatar and allowed_file(avatar.filename):
            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], avatar.filename)
            avatar.save(avatar_path)
            conn.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar.filename, user['id']))

        conn.execute('UPDATE users SET username = ?, name = ?, email = ?, about = ? WHERE id = ?',
                     (username, name, email, about, user['id']))
        
        conn.commit()
        conn.close()
        session['username'] = username
        return redirect(url_for('profile'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    conn.close()
    return render_template('edit_profile.html', user=user)





# Маршрут для добавления объявления
@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()

        conn.execute('INSERT INTO posts (title, content, user_id) VALUES (?, ?, ?)',
                     (title, content, user['id']))
        conn.commit()
        conn.close()

        return redirect(url_for('profile'))

    return render_template('add_post.html')

# Маршрут для редактирования объявления
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        conn.execute('UPDATE posts SET title = ?, content = ? WHERE id = ?',
                     (title, content, post_id))
        conn.commit()
        conn.close()

        if session['username'] == 'hamzat':
            return redirect(url_for('admin_panel'))
        else:
            return redirect(url_for('profile'))

    conn.close()
    return render_template('edit_post.html', post=post)

# Маршрут для редактирования пользователя
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email')
        about = request.form.get('about')
        avatar = request.files.get('avatar')

        # Обновление данных пользователя
        if password:
            hashed_password = generate_password_hash(password)
            conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
        
        if avatar and allowed_file(avatar.filename):
            avatar_path = os.path.join('static', 'avatars', avatar.filename)
            avatar.save(avatar_path)
            conn.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar.filename, user_id))

        conn.execute('UPDATE users SET username = ?, name = ?, email = ?, about = ? WHERE id = ?',
                     (username, name, email, about, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_panel'))

    conn.close()
    return render_template('edit_user.html', user=user)





# Маршрут для удаления объявления
@app.route('/delete_post/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# Маршрут для удаления аккаунта
@app.route('/delete_account', methods=['DELETE'])
def delete_account():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    conn.execute('DELETE FROM users WHERE id = ?', (user['id'],))
    conn.commit()
    conn.close()
    session.pop('username', None)
    return jsonify({'success': True})

# Маршрут для удаления пользователя
@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ? AND is_admin = 0', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# Страница админ-панели
@app.route('/admin_panel')
def admin_panel():
    conn = get_db_connection()
    posts = conn.execute('SELECT posts.id, posts.title, posts.content, users.name, users.email FROM posts INNER JOIN users ON posts.user_id = users.id').fetchall()
    users = conn.execute('SELECT id, username, email FROM users WHERE is_admin = 0').fetchall()
    conn.close()
    return render_template('admin_panel.html', posts=posts, users=users)

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Вы вышли из аккаунта.', 'info')
    return redirect(url_for('login'))

def validate_input(data, type='text'):
    """Проверка на валидность входных данных."""
    if type == 'text':
        return bool(re.match(r'^[a-zA-Z0-9.,!?-]+$', data))  # Логин, имя, пароль
    if type == 'email':
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data))  # Email
    return False

if __name__ == '__main__':
    app.run(debug=True)

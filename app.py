import os
from flask import Flask, request, jsonify, send_from_directory, abort
import mysql.connector

app = Flask(__name__)

# Serve static files (JS, CSS)
@app.route('/js/<path:filename>')
def serve_js(filename):
    js_dir = os.path.join(app.root_path, 'js')
    js_path = os.path.join(js_dir, filename)
    if os.path.isfile(js_path):
        return send_from_directory(js_dir, filename)
    fallback_path = os.path.join(app.root_path, filename)
    if os.path.isfile(fallback_path):
        return send_from_directory(app.root_path, filename)
    abort(404)

@app.route('/page/js/<path:filename>')
def serve_page_js(filename):
    return serve_js(filename)

@app.route('/style.css')
def serve_css():
    return send_from_directory(app.root_path, 'style.css')

@app.route('/css/<path:filename>')
def serve_css_dir(filename):
    css_file = os.path.join(app.root_path, filename)
    if os.path.isfile(css_file):
        return send_from_directory(app.root_path, filename)
    abort(404)

@app.route('/page/css/<path:filename>')
def serve_page_css(filename):
    return serve_css_dir(filename)

@app.route('/chart.js')
def serve_chartjs():
    return send_from_directory(app.root_path, 'chart.js')

@app.route('/images/<path:filename>')
def serve_images(filename):
    image_dir = os.path.join(app.root_path, 'images')
    image_path = os.path.join(image_dir, filename)
    if os.path.isfile(image_path):
        return send_from_directory(image_dir, filename)
    abort(404)

@app.route('/page/images/<path:filename>')
def serve_page_images(filename):
    return serve_images(filename)

# Serve HTML pages
@app.route('/')
def index():
    return send_from_directory(app.root_path, 'index.html')

@app.route('/page/<page_name>')
def serve_page(page_name):
    return send_from_directory(os.path.join(app.root_path, 'page'), page_name)

# Database connection
# Use environment variables if available.
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'nex_alem_db')

db = None


def connect_db():
    global db
    if db is not None:
        return db
    try:
        db = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connection_timeout=5,
        )
        return db
    except mysql.connector.Error as exc:
        print('MySQL connection failed:', exc)
        db = None
        return None


def get_db_connection():
    return connect_db()


def get_db_cursor():
    conn = get_db_connection()
    if conn is None:
        return None
    return conn.cursor(dictionary=True)


def query_db(query, params=None, one=False):
    params = params or ()
    cursor = get_db_cursor()
    if cursor is None:
        return None
    cursor.execute(query, params)
    result = cursor.fetchone() if one else cursor.fetchall()
    cursor.close()
    return result

@app.route('/students', methods=['GET'])
def get_students():
    students = query_db('SELECT * FROM students')
    if students is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(students)

@app.route('/students/<student_id>', methods=['GET'])
def get_student(student_id):
    student = query_db('SELECT * FROM students WHERE id = %s', (student_id,), one=True)
    if student is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if student:
        return jsonify(student)
    return jsonify({'error': 'Student not found'}), 404

@app.route('/users', methods=['GET'])
def get_users():
    users = query_db('SELECT * FROM users')
    if users is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(users)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = query_db(
        'SELECT * FROM users WHERE email = %s AND password = %s',
        (username, password),
        one=True
    )
    if user is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if user:
        return jsonify(user)
    return jsonify({'error': 'Invalid login'}), 401


if __name__ == "__main__":
    app.run(debug=True)
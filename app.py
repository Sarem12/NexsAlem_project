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
    try:
        cursor.execute(query, params)
        result = cursor.fetchone() if one else cursor.fetchall()
    except mysql.connector.Error as exc:
        print('MySQL query failed:', exc)
        cursor.close()
        return None
    cursor.close()
    if one and result is None:
        return {}
    return result


def modify_db(query, params=None):
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as exc:
        print('MySQL modify failed:', exc)
        return None
    finally:
        cursor.close()


def build_update_parts(data, allowed_fields):
    fields = []
    params = []
    for field in allowed_fields:
        if field in data:
            fields.append(f"{field} = %s")
            params.append(data[field])
    return fields, params

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

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = query_db('SELECT * FROM users WHERE id = %s', (user_id,), one=True)
    if user is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if user:
        return jsonify(user)
    return jsonify({'error': 'User not found'}), 404

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json or {}
    required = ['full_name', 'email', 'password', 'role']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required user fields'}), 400
    rowcount = modify_db(
        'INSERT INTO users (full_name, email, password, role) VALUES (%s, %s, %s, %s)',
        (data['full_name'], data['email'], data['password'], data['role'])
    )
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    user = query_db('SELECT * FROM users WHERE email = %s', (data['email'],), one=True)
    return jsonify(user), 201

@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json or {}
    allowed = ['full_name', 'email', 'password', 'role']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(user_id)
    rowcount = modify_db(f"UPDATE users SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'User not found'}), 404
    user = query_db('SELECT * FROM users WHERE id = %s', (user_id,), one=True)
    return jsonify(user)

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    rowcount = modify_db('DELETE FROM users WHERE id = %s', (user_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'message': 'User deleted'})

@app.route('/students', methods=['POST'])
def create_student():
    data = request.json or {}
    required = ['user_id', 'student_code', 'gender']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required student fields'}), 400
    rowcount = modify_db(
        'INSERT INTO students (user_id, student_code, gender, date_of_birth, parent_name, parent_phone) VALUES (%s, %s, %s, %s, %s, %s)',
        (
            data['user_id'],
            data['student_code'],
            data['gender'],
            data.get('date_of_birth'),
            data.get('parent_name'),
            data.get('parent_phone'),
        )
    )
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    student = query_db('SELECT * FROM students WHERE student_code = %s', (data['student_code'],), one=True)
    return jsonify(student), 201

@app.route('/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    data = request.json or {}
    allowed = ['student_code', 'gender', 'date_of_birth', 'parent_name', 'parent_phone', 'user_id']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(student_id)
    rowcount = modify_db(f"UPDATE students SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Student not found'}), 404
    student = query_db('SELECT * FROM students WHERE id = %s', (student_id,), one=True)
    return jsonify(student)

@app.route('/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    rowcount = modify_db('DELETE FROM students WHERE id = %s', (student_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Student not found'}), 404
    return jsonify({'message': 'Student deleted'})

@app.route('/teachers', methods=['GET'])
def get_teachers():
    teachers = query_db('SELECT * FROM teachers')
    if teachers is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(teachers)

@app.route('/teachers/<teacher_id>', methods=['GET'])
def get_teacher(teacher_id):
    teacher = query_db('SELECT * FROM teachers WHERE id = %s', (teacher_id,), one=True)
    if teacher is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if teacher:
        return jsonify(teacher)
    return jsonify({'error': 'Teacher not found'}), 404

@app.route('/teachers', methods=['POST'])
def create_teacher():
    data = request.json or {}
    required = ['user_id', 'qualification', 'phone']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required teacher fields'}), 400
    rowcount = modify_db(
        'INSERT INTO teachers (user_id, qualification, phone) VALUES (%s, %s, %s)',
        (data['user_id'], data['qualification'], data['phone'])
    )
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    teacher = query_db('SELECT * FROM teachers WHERE user_id = %s', (data['user_id'],), one=True)
    return jsonify(teacher), 201

@app.route('/teachers/<teacher_id>', methods=['PUT'])
def update_teacher(teacher_id):
    data = request.json or {}
    allowed = ['qualification', 'phone', 'user_id']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(teacher_id)
    rowcount = modify_db(f"UPDATE teachers SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Teacher not found'}), 404
    teacher = query_db('SELECT * FROM teachers WHERE id = %s', (teacher_id,), one=True)
    return jsonify(teacher)

@app.route('/teachers/<teacher_id>', methods=['DELETE'])
def delete_teacher(teacher_id):
    rowcount = modify_db('DELETE FROM teachers WHERE id = %s', (teacher_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Teacher not found'}), 404
    return jsonify({'message': 'Teacher deleted'})

@app.route('/classes', methods=['GET'])
def get_classes():
    classes = query_db('SELECT * FROM classes')
    if classes is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(classes)

@app.route('/classes/<class_id>', methods=['GET'])
def get_class(class_id):
    _class = query_db('SELECT * FROM classes WHERE id = %s', (class_id,), one=True)
    if _class is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if _class:
        return jsonify(_class)
    return jsonify({'error': 'Class not found'}), 404

@app.route('/classes', methods=['POST'])
def create_class():
    data = request.json or {}
    if 'name' not in data:
        return jsonify({'error': 'Missing class name'}), 400
    rowcount = modify_db('INSERT INTO classes (name) VALUES (%s)', (data['name'],))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    _class = query_db('SELECT * FROM classes WHERE name = %s ORDER BY id DESC LIMIT 1', (data['name'],), one=True)
    return jsonify(_class), 201

@app.route('/classes/<class_id>', methods=['PUT'])
def update_class(class_id):
    data = request.json or {}
    allowed = ['name']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(class_id)
    rowcount = modify_db(f"UPDATE classes SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Class not found'}), 404
    _class = query_db('SELECT * FROM classes WHERE id = %s', (class_id,), one=True)
    return jsonify(_class)

@app.route('/classes/<class_id>', methods=['DELETE'])
def delete_class(class_id):
    rowcount = modify_db('DELETE FROM classes WHERE id = %s', (class_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Class not found'}), 404
    return jsonify({'message': 'Class deleted'})

@app.route('/sections', methods=['GET'])
def get_sections():
    sections = query_db('SELECT * FROM sections')
    if sections is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(sections)

@app.route('/sections/<section_id>', methods=['GET'])
def get_section(section_id):
    section = query_db('SELECT * FROM sections WHERE id = %s', (section_id,), one=True)
    if section is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if section:
        return jsonify(section)
    return jsonify({'error': 'Section not found'}), 404

@app.route('/sections', methods=['POST'])
def create_section():
    data = request.json or {}
    required = ['class_id', 'name']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required section fields'}), 400
    rowcount = modify_db('INSERT INTO sections (class_id, name) VALUES (%s, %s)', (data['class_id'], data['name']))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    section = query_db('SELECT * FROM sections WHERE class_id = %s AND name = %s ORDER BY id DESC LIMIT 1', (data['class_id'], data['name']), one=True)
    return jsonify(section), 201

@app.route('/sections/<section_id>', methods=['PUT'])
def update_section(section_id):
    data = request.json or {}
    allowed = ['class_id', 'name']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(section_id)
    rowcount = modify_db(f"UPDATE sections SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Section not found'}), 404
    section = query_db('SELECT * FROM sections WHERE id = %s', (section_id,), one=True)
    return jsonify(section)

@app.route('/sections/<section_id>', methods=['DELETE'])
def delete_section(section_id):
    rowcount = modify_db('DELETE FROM sections WHERE id = %s', (section_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Section not found'}), 404
    return jsonify({'message': 'Section deleted'})

@app.route('/subjects', methods=['GET'])
def get_subjects():
    subjects = query_db('SELECT * FROM subjects')
    if subjects is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(subjects)

@app.route('/subjects/<subject_id>', methods=['GET'])
def get_subject(subject_id):
    subject = query_db('SELECT * FROM subjects WHERE id = %s', (subject_id,), one=True)
    if subject is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if subject:
        return jsonify(subject)
    return jsonify({'error': 'Subject not found'}), 404

@app.route('/subjects', methods=['POST'])
def create_subject():
    data = request.json or {}
    if 'name' not in data:
        return jsonify({'error': 'Missing subject name'}), 400
    rowcount = modify_db('INSERT INTO subjects (name) VALUES (%s)', (data['name'],))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    subject = query_db('SELECT * FROM subjects WHERE name = %s ORDER BY id DESC LIMIT 1', (data['name'],), one=True)
    return jsonify(subject), 201

@app.route('/subjects/<subject_id>', methods=['PUT'])
def update_subject(subject_id):
    data = request.json or {}
    allowed = ['name']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(subject_id)
    rowcount = modify_db(f"UPDATE subjects SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Subject not found'}), 404
    subject = query_db('SELECT * FROM subjects WHERE id = %s', (subject_id,), one=True)
    return jsonify(subject)

@app.route('/subjects/<subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    rowcount = modify_db('DELETE FROM subjects WHERE id = %s', (subject_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Subject not found'}), 404
    return jsonify({'message': 'Subject deleted'})

@app.route('/teacher_subjects', methods=['GET'])
def get_teacher_subjects():
    assignments = query_db('SELECT * FROM teacher_subjects')
    if assignments is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(assignments)

@app.route('/teacher_subjects/<assignment_id>', methods=['GET'])
def get_teacher_subject(assignment_id):
    assignment = query_db('SELECT * FROM teacher_subjects WHERE id = %s', (assignment_id,), one=True)
    if assignment is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if assignment:
        return jsonify(assignment)
    return jsonify({'error': 'Assignment not found'}), 404

@app.route('/teacher_subjects', methods=['POST'])
def create_teacher_subject():
    data = request.json or {}
    required = ['teacher_id', 'subject_id', 'class_id']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required teacher_subject fields'}), 400
    rowcount = modify_db(
        'INSERT INTO teacher_subjects (teacher_id, subject_id, class_id) VALUES (%s, %s, %s)',
        (data['teacher_id'], data['subject_id'], data['class_id'])
    )
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    assignment = query_db('SELECT * FROM teacher_subjects WHERE teacher_id = %s AND subject_id = %s AND class_id = %s ORDER BY id DESC LIMIT 1', (data['teacher_id'], data['subject_id'], data['class_id']), one=True)
    return jsonify(assignment), 201

@app.route('/teacher_subjects/<assignment_id>', methods=['PUT'])
def update_teacher_subject(assignment_id):
    data = request.json or {}
    allowed = ['teacher_id', 'subject_id', 'class_id']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(assignment_id)
    rowcount = modify_db(f"UPDATE teacher_subjects SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Assignment not found'}), 404
    assignment = query_db('SELECT * FROM teacher_subjects WHERE id = %s', (assignment_id,), one=True)
    return jsonify(assignment)

@app.route('/teacher_subjects/<assignment_id>', methods=['DELETE'])
def delete_teacher_subject(assignment_id):
    rowcount = modify_db('DELETE FROM teacher_subjects WHERE id = %s', (assignment_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Assignment not found'}), 404
    return jsonify({'message': 'Assignment deleted'})

@app.route('/enrollments', methods=['GET'])
def get_enrollments():
    enrollments = query_db('SELECT * FROM enrollments')
    if enrollments is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(enrollments)

@app.route('/enrollments/<enrollment_id>', methods=['GET'])
def get_enrollment(enrollment_id):
    enrollment = query_db('SELECT * FROM enrollments WHERE id = %s', (enrollment_id,), one=True)
    if enrollment is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if enrollment:
        return jsonify(enrollment)
    return jsonify({'error': 'Enrollment not found'}), 404

@app.route('/enrollments', methods=['POST'])
def create_enrollment():
    data = request.json or {}
    required = ['student_id', 'class_id', 'section_id', 'academic_year']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required enrollment fields'}), 400
    rowcount = modify_db(
        'INSERT INTO enrollments (student_id, class_id, section_id, academic_year) VALUES (%s, %s, %s, %s)',
        (data['student_id'], data['class_id'], data['section_id'], data['academic_year'])
    )
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    enrollment = query_db('SELECT * FROM enrollments WHERE student_id = %s AND class_id = %s AND section_id = %s AND academic_year = %s ORDER BY id DESC LIMIT 1', (data['student_id'], data['class_id'], data['section_id'], data['academic_year']), one=True)
    return jsonify(enrollment), 201

@app.route('/enrollments/<enrollment_id>', methods=['PUT'])
def update_enrollment(enrollment_id):
    data = request.json or {}
    allowed = ['student_id', 'class_id', 'section_id', 'academic_year']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(enrollment_id)
    rowcount = modify_db(f"UPDATE enrollments SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Enrollment not found'}), 404
    enrollment = query_db('SELECT * FROM enrollments WHERE id = %s', (enrollment_id,), one=True)
    return jsonify(enrollment)

@app.route('/enrollments/<enrollment_id>', methods=['DELETE'])
def delete_enrollment(enrollment_id):
    rowcount = modify_db('DELETE FROM enrollments WHERE id = %s', (enrollment_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Enrollment not found'}), 404
    return jsonify({'message': 'Enrollment deleted'})

@app.route('/attendance', methods=['GET'])
def get_attendance():
    attendance_rows = query_db('SELECT * FROM attendance')
    if attendance_rows is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(attendance_rows)

@app.route('/attendance/<attendance_id>', methods=['GET'])
def get_attendance_record(attendance_id):
    record = query_db('SELECT * FROM attendance WHERE id = %s', (attendance_id,), one=True)
    if record is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if record:
        return jsonify(record)
    return jsonify({'error': 'Attendance record not found'}), 404

@app.route('/attendance', methods=['POST'])
def create_attendance():
    data = request.json or {}
    required = ['student_id', 'date', 'status']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required attendance fields'}), 400
    rowcount = modify_db('INSERT INTO attendance (student_id, date, status) VALUES (%s, %s, %s)', (data['student_id'], data['date'], data['status']))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    record = query_db('SELECT * FROM attendance WHERE student_id = %s AND date = %s AND status = %s ORDER BY id DESC LIMIT 1', (data['student_id'], data['date'], data['status']), one=True)
    return jsonify(record), 201

@app.route('/attendance/<attendance_id>', methods=['PUT'])
def update_attendance(attendance_id):
    data = request.json or {}
    allowed = ['student_id', 'date', 'status']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(attendance_id)
    rowcount = modify_db(f"UPDATE attendance SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Attendance record not found'}), 404
    record = query_db('SELECT * FROM attendance WHERE id = %s', (attendance_id,), one=True)
    return jsonify(record)

@app.route('/attendance/<attendance_id>', methods=['DELETE'])
def delete_attendance(attendance_id):
    rowcount = modify_db('DELETE FROM attendance WHERE id = %s', (attendance_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Attendance record not found'}), 404
    return jsonify({'message': 'Attendance record deleted'})

@app.route('/exams', methods=['GET'])
def get_exams():
    exams = query_db('SELECT * FROM exams')
    if exams is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(exams)

@app.route('/exams/<exam_id>', methods=['GET'])
def get_exam(exam_id):
    exam = query_db('SELECT * FROM exams WHERE id = %s', (exam_id,), one=True)
    if exam is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if exam:
        return jsonify(exam)
    return jsonify({'error': 'Exam not found'}), 404

@app.route('/exams', methods=['POST'])
def create_exam():
    data = request.json or {}
    required = ['name', 'class_id', 'date']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required exam fields'}), 400
    rowcount = modify_db('INSERT INTO exams (name, class_id, date) VALUES (%s, %s, %s)', (data['name'], data['class_id'], data['date']))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    exam = query_db('SELECT * FROM exams WHERE name = %s AND class_id = %s AND date = %s ORDER BY id DESC LIMIT 1', (data['name'], data['class_id'], data['date']), one=True)
    return jsonify(exam), 201

@app.route('/exams/<exam_id>', methods=['PUT'])
def update_exam(exam_id):
    data = request.json or {}
    allowed = ['name', 'class_id', 'date']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(exam_id)
    rowcount = modify_db(f"UPDATE exams SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Exam not found'}), 404
    exam = query_db('SELECT * FROM exams WHERE id = %s', (exam_id,), one=True)
    return jsonify(exam)

@app.route('/exams/<exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    rowcount = modify_db('DELETE FROM exams WHERE id = %s', (exam_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Exam not found'}), 404
    return jsonify({'message': 'Exam deleted'})

@app.route('/results', methods=['GET'])
def get_results():
    results = query_db('SELECT * FROM results')
    if results is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(results)

@app.route('/results/<result_id>', methods=['GET'])
def get_result(result_id):
    result = query_db('SELECT * FROM results WHERE id = %s', (result_id,), one=True)
    if result is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if result:
        return jsonify(result)
    return jsonify({'error': 'Result not found'}), 404

@app.route('/results', methods=['POST'])
def create_result():
    data = request.json or {}
    required = ['student_id', 'subject_id', 'exam_id', 'score', 'grade']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required result fields'}), 400
    rowcount = modify_db('INSERT INTO results (student_id, subject_id, exam_id, score, grade) VALUES (%s, %s, %s, %s, %s)', (data['student_id'], data['subject_id'], data['exam_id'], data['score'], data['grade']))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    result = query_db('SELECT * FROM results WHERE student_id = %s AND subject_id = %s AND exam_id = %s ORDER BY id DESC LIMIT 1', (data['student_id'], data['subject_id'], data['exam_id']), one=True)
    return jsonify(result), 201

@app.route('/results/<result_id>', methods=['PUT'])
def update_result(result_id):
    data = request.json or {}
    allowed = ['student_id', 'subject_id', 'exam_id', 'score', 'grade']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(result_id)
    rowcount = modify_db(f"UPDATE results SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Result not found'}), 404
    result = query_db('SELECT * FROM results WHERE id = %s', (result_id,), one=True)
    return jsonify(result)

@app.route('/results/<result_id>', methods=['DELETE'])
def delete_result(result_id):
    rowcount = modify_db('DELETE FROM results WHERE id = %s', (result_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Result not found'}), 404
    return jsonify({'message': 'Result deleted'})

@app.route('/fees', methods=['GET'])
def get_fees():
    fees = query_db('SELECT * FROM fees')
    if fees is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(fees)

@app.route('/fees/<fee_id>', methods=['GET'])
def get_fee(fee_id):
    fee = query_db('SELECT * FROM fees WHERE id = %s', (fee_id,), one=True)
    if fee is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if fee:
        return jsonify(fee)
    return jsonify({'error': 'Fee not found'}), 404

@app.route('/fees', methods=['POST'])
def create_fee():
    data = request.json or {}
    required = ['class_id', 'amount', 'term']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fee fields'}), 400
    rowcount = modify_db('INSERT INTO fees (class_id, amount, term) VALUES (%s, %s, %s)', (data['class_id'], data['amount'], data['term']))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    fee = query_db('SELECT * FROM fees WHERE class_id = %s AND term = %s ORDER BY id DESC LIMIT 1', (data['class_id'], data['term']), one=True)
    return jsonify(fee), 201

@app.route('/fees/<fee_id>', methods=['PUT'])
def update_fee(fee_id):
    data = request.json or {}
    allowed = ['class_id', 'amount', 'term']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(fee_id)
    rowcount = modify_db(f"UPDATE fees SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Fee not found'}), 404
    fee = query_db('SELECT * FROM fees WHERE id = %s', (fee_id,), one=True)
    return jsonify(fee)

@app.route('/fees/<fee_id>', methods=['DELETE'])
def delete_fee(fee_id):
    rowcount = modify_db('DELETE FROM fees WHERE id = %s', (fee_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Fee not found'}), 404
    return jsonify({'message': 'Fee deleted'})

@app.route('/payments', methods=['GET'])
def get_payments():
    payments = query_db('SELECT * FROM payments')
    if payments is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(payments)

@app.route('/payments/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    payment = query_db('SELECT * FROM payments WHERE id = %s', (payment_id,), one=True)
    if payment is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if payment:
        return jsonify(payment)
    return jsonify({'error': 'Payment not found'}), 404

@app.route('/payments', methods=['POST'])
def create_payment():
    data = request.json or {}
    required = ['student_id', 'amount', 'payment_date', 'status']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required payment fields'}), 400
    rowcount = modify_db('INSERT INTO payments (student_id, amount, payment_date, status) VALUES (%s, %s, %s, %s)', (data['student_id'], data['amount'], data['payment_date'], data['status']))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    payment = query_db('SELECT * FROM payments WHERE student_id = %s AND amount = %s AND payment_date = %s ORDER BY id DESC LIMIT 1', (data['student_id'], data['amount'], data['payment_date']), one=True)
    return jsonify(payment), 201

@app.route('/payments/<payment_id>', methods=['PUT'])
def update_payment(payment_id):
    data = request.json or {}
    allowed = ['student_id', 'amount', 'payment_date', 'status']
    fields, params = build_update_parts(data, allowed)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    params.append(payment_id)
    rowcount = modify_db(f"UPDATE payments SET {', '.join(fields)} WHERE id = %s", tuple(params))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Payment not found'}), 404
    payment = query_db('SELECT * FROM payments WHERE id = %s', (payment_id,), one=True)
    return jsonify(payment)

@app.route('/payments/<payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    rowcount = modify_db('DELETE FROM payments WHERE id = %s', (payment_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Payment not found'}), 404
    return jsonify({'message': 'Payment deleted'})

@app.route('/announcements', methods=['GET'])
def get_announcements():
    announcements = query_db('SELECT * FROM announcements')
    if announcements is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    return jsonify(announcements)

@app.route('/announcements/<announcement_id>', methods=['GET'])
def get_announcement(announcement_id):
    announcement = query_db('SELECT * FROM announcements WHERE id = %s', (announcement_id,), one=True)
    if announcement is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if announcement:
        return jsonify(announcement)
    return jsonify({'error': 'Announcement not found'}), 404

@app.route('/announcements', methods=['POST'])
def create_announcement():
    data = request.json or {}
    required = ['title', 'message', 'created_by']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required announcement fields'}), 400
    rowcount = modify_db('INSERT INTO announcements (title, message, created_by) VALUES (%s, %s, %s)', (data['title'], data['message'], data['created_by']))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    announcement = query_db('SELECT * FROM announcements WHERE title = %s AND created_by = %s ORDER BY id DESC LIMIT 1', (data['title'], data['created_by']), one=True)
    return jsonify(announcement), 201

@app.route('/announcements/<announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    rowcount = modify_db('DELETE FROM announcements WHERE id = %s', (announcement_id,))
    if rowcount is None:
        return jsonify({'error': 'Database connection unavailable'}), 500
    if rowcount == 0:
        return jsonify({'error': 'Announcement not found'}), 404
    return jsonify({'message': 'Announcement deleted'})

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
-- =========================================
-- NEXS ALEM SCHOOL MANAGEMENT SYSTEM
-- =========================================

DROP DATABASE IF EXISTS nexs_alem_school;
CREATE DATABASE nexs_alem_school;
USE nexs_alem_school;

-- =========================================
-- USERS
-- =========================================
CREATE TABLE users (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('ADMIN','TEACHER','STUDENT') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- STUDENTS
-- =========================================
CREATE TABLE students (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36),
    student_code VARCHAR(50) UNIQUE,
    gender ENUM('MALE','FEMALE'),
    date_of_birth DATE,
    parent_name VARCHAR(100),
    parent_phone VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =========================================
-- TEACHERS
-- =========================================
CREATE TABLE teachers (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36),
    qualification VARCHAR(100),
    phone VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =========================================
-- CLASSES
-- =========================================
CREATE TABLE classes (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(50) NOT NULL
);

-- =========================================
-- SECTIONS
-- =========================================
CREATE TABLE sections (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    class_id CHAR(36),
    name VARCHAR(10),
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);

-- =========================================
-- SUBJECTS
-- =========================================
CREATE TABLE subjects (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(100) NOT NULL
);

-- =========================================
-- TEACHER SUBJECTS
-- =========================================
CREATE TABLE teacher_subjects (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    teacher_id CHAR(36),
    subject_id CHAR(36),
    class_id CHAR(36),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);

-- =========================================
-- ENROLLMENTS
-- =========================================
CREATE TABLE enrollments (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    student_id CHAR(36),
    class_id CHAR(36),
    section_id CHAR(36),
    academic_year VARCHAR(20),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
);

-- =========================================
-- ATTENDANCE
-- =========================================
CREATE TABLE attendance (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    student_id CHAR(36),
    date DATE,
    status ENUM('PRESENT','ABSENT','LATE'),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =========================================
-- EXAMS
-- =========================================
CREATE TABLE exams (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(50),
    class_id CHAR(36),
    date DATE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);

-- =========================================
-- RESULTS
-- =========================================
CREATE TABLE results (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    student_id CHAR(36),
    subject_id CHAR(36),
    exam_id CHAR(36),
    score DECIMAL(5,2),
    grade VARCHAR(5),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

-- =========================================
-- FEES
-- =========================================
CREATE TABLE fees (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    class_id CHAR(36),
    amount DECIMAL(10,2),
    term VARCHAR(20),
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);

-- =========================================
-- PAYMENTS
-- =========================================
CREATE TABLE payments (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    student_id CHAR(36),
    amount DECIMAL(10,2),
    payment_date DATE,
    status ENUM('PAID','PENDING'),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =========================================
-- ANNOUNCEMENTS
-- =========================================
CREATE TABLE announcements (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    title VARCHAR(255),
    message TEXT,
    created_by CHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- =========================================
-- INDEXES (PERFORMANCE)
-- =========================================
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_student_code ON students(student_code);
CREATE INDEX idx_attendance_date ON attendance(date);

-- =========================================
-- SEED DATA (STARTER DATA)
-- =========================================

-- Admin user
INSERT INTO users (full_name, email, password, role)
VALUES ('Admin User', 'admin@nexs.com', 'hashedpassword', 'ADMIN');

-- Sample classes
INSERT INTO classes (name) VALUES 
('Grade 9'),
('Grade 10');

-- Sample subjects
INSERT INTO subjects (name) VALUES 
('Mathematics'),
('English'),
('Physics');

-- Sample teacher
INSERT INTO users (full_name, email, password, role)
VALUES ('John Teacher', 'teacher@nexs.com', 'hashedpassword', 'TEACHER');

INSERT INTO teachers (user_id, qualification, phone)
SELECT id, 'BSc Mathematics', '0912345678' FROM users WHERE email='teacher@nexs.com';

-- Sample student
INSERT INTO users (full_name, email, password, role)
VALUES ('Student One', 'student@nexs.com', 'hashedpassword', 'STUDENT');

INSERT INTO students (user_id, student_code, gender)
SELECT id, 'STU001', 'MALE' FROM users WHERE email='student@nexs.com';
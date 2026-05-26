# app.py - Fresh Clean Version
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import DatabaseConfig
from datetime import date, datetime
import os
import uuid
from werkzeug.utils import secure_filename

# Optional PDF support: try to import reportlab; if unavailable, fall back to CSV responses.
try:
    from reportlab.platypus import SimpleDocTemplate, Table
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    pdf_available = True
except Exception:
    SimpleDocTemplate = None
    Table = None
    letter = None
    colors = None
    pdf_available = False

app = Flask(__name__)
app.secret_key = 'school_secret_2024'

RESOURCE_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'resources')
RESOURCE_URL_BASE = '/static/uploads/resources'
SUBMISSION_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'submissions')
SUBMISSION_URL_BASE = '/static/uploads/submissions'
ALLOWED_RESOURCE_EXTENSIONS = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.zip', '.png', '.jpg', '.jpeg'}
ALLOWED_SUBMISSION_EXTENSIONS = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.zip', '.png', '.jpg', '.jpeg'}

os.makedirs(RESOURCE_UPLOAD_DIR, exist_ok=True)
os.makedirs(SUBMISSION_UPLOAD_DIR, exist_ok=True)


def table_exists(cursor, table_name):
    try:
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", (table_name,))
        row = cursor.fetchone()
        return bool(row and row[0])
    except Exception:
        return False


def ensure_fee_tables(cursor):
    try:
        cursor.execute("""
            IF OBJECT_ID('dbo.FeeStructures', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.FeeStructures (
                    FeeStructureID INT IDENTITY(1,1) PRIMARY KEY,
                    ClassID INT NULL,
                    FeeName NVARCHAR(100) NOT NULL,
                    Amount DECIMAL(10, 2) NOT NULL,
                    FeeType NVARCHAR(50) NOT NULL,
                    Frequency NVARCHAR(50) NOT NULL,
                    DueDate DATE NULL,
                    AcademicYear NVARCHAR(20) NULL
                )
            END
        """)
        cursor.execute("""
            IF OBJECT_ID('dbo.FeePayments', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.FeePayments (
                    PaymentID INT IDENTITY(1,1) PRIMARY KEY,
                    StudentID INT NOT NULL,
                    FeeStructureID INT NOT NULL,
                    AmountPaid DECIMAL(10, 2) NOT NULL,
                    PaymentDate DATE NOT NULL,
                    PaymentMethod NVARCHAR(50) NOT NULL,
                    TransactionID NVARCHAR(100) NULL,
                    Remarks NVARCHAR(255) NULL,
                    ReceiptNumber NVARCHAR(50) NULL
                )
            END
        """)
    except Exception:
        pass


def ensure_grade_tables(cursor):
    try:
        cursor.execute("""
            IF OBJECT_ID('dbo.GradeHistory', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.GradeHistory (
                    HistoryID INT IDENTITY(1,1) PRIMARY KEY,
                    StudentID INT NOT NULL,
                    SubjectID INT NOT NULL,
                    OldGrade NVARCHAR(50) NULL,
                    NewGrade NVARCHAR(50) NOT NULL,
                    ChangedByFacultyID INT NULL,
                    ChangedAt DATETIME NOT NULL
                )
            END
        """)
        cursor.execute("""
            IF OBJECT_ID('dbo.GradeLocks', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.GradeLocks (
                    SubjectID INT PRIMARY KEY,
                    IsLocked BIT NOT NULL DEFAULT 0,
                    LockedByFacultyID INT NULL,
                    LockedAt DATETIME NULL
                )
            END
        """)
    except Exception:
        pass


def ensure_marks_tables(cursor):
    try:
        cursor.execute("""
            IF OBJECT_ID('dbo.GradeComponents', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.GradeComponents (
                    ComponentID INT IDENTITY(1,1) PRIMARY KEY,
                    SubjectID INT NOT NULL,
                    Name NVARCHAR(100) NOT NULL,
                    MaxMarks DECIMAL(10,2) NOT NULL DEFAULT 100,
                    WeightPercent DECIMAL(5,2) NOT NULL DEFAULT 0
                )
            END
        """)
        cursor.execute("""
            IF OBJECT_ID('dbo.StudentMarks', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.StudentMarks (
                    MarkID INT IDENTITY(1,1) PRIMARY KEY,
                    StudentID INT NOT NULL,
                    SubjectID INT NOT NULL,
                    ComponentID INT NOT NULL,
                    MarksObtained DECIMAL(10,2) NOT NULL
                )
            END
        """)
    except Exception:
        pass


def ensure_thresholds_table(cursor):
    try:
        cursor.execute("""
            IF OBJECT_ID('dbo.GradeThresholds', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.GradeThresholds (
                    ThresholdID INT IDENTITY(1,1) PRIMARY KEY,
                    Letter NVARCHAR(5) NOT NULL,
                    MinPercent DECIMAL(5,2) NOT NULL
                )
            END
        """)
    except Exception:
        pass


def ensure_institution_settings_table(cursor):
    try:
        cursor.execute("""
            IF OBJECT_ID('dbo.InstitutionSettings', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.InstitutionSettings (
                    SettingID INT IDENTITY(1,1) PRIMARY KEY,
                    InstitutionName NVARCHAR(120) NOT NULL DEFAULT 'School Management System',
                    InstitutionType NVARCHAR(20) NOT NULL DEFAULT 'School',
                    UpdatedAt DATETIME NULL
                )
            END
        """)
    except Exception:
        pass


def ensure_resource_tables(cursor):
    try:
        cursor.execute("""
            IF OBJECT_ID('dbo.CourseResources', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.CourseResources (
                    ResourceID INT IDENTITY(1,1) PRIMARY KEY,
                    SubjectID INT NOT NULL,
                    FacultyID INT NOT NULL,
                    Title NVARCHAR(200) NOT NULL,
                    ResourceType NVARCHAR(20) NOT NULL,
                    Description NVARCHAR(500) NULL,
                    DueDate DATE NULL,
                    MaxMarks DECIMAL(10,2) NULL,
                    FileName NVARCHAR(255) NOT NULL,
                    FileUrl NVARCHAR(500) NOT NULL,
                    UploadedAt DATETIME NOT NULL
                )
            END
        """)
    except Exception:
        pass


def ensure_submission_tables(cursor):
    try:
        cursor.execute("""
            IF OBJECT_ID('dbo.CourseSubmissions', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.CourseSubmissions (
                    SubmissionID INT IDENTITY(1,1) PRIMARY KEY,
                    ResourceID INT NOT NULL,
                    StudentID INT NOT NULL,
                    AnswerText NVARCHAR(1000) NULL,
                    FileName NVARCHAR(255) NOT NULL,
                    FileUrl NVARCHAR(500) NOT NULL,
                    SubmittedAt DATETIME NOT NULL,
                    Grade DECIMAL(10,2) NULL,
                    Feedback NVARCHAR(1000) NULL,
                    Status NVARCHAR(30) NOT NULL DEFAULT 'Submitted',
                    GradedAt DATETIME NULL
                )
            END
        """)
    except Exception:
        pass


def ensure_announcements_table(cursor):
    try:
        cursor.execute("""
            IF OBJECT_ID('dbo.ClassAnnouncements', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.ClassAnnouncements (
                    AnnouncementID INT IDENTITY(1,1) PRIMARY KEY,
                    SubjectID INT NOT NULL,
                    FacultyID INT NOT NULL,
                    Title NVARCHAR(200) NOT NULL,
                    Content NVARCHAR(MAX) NOT NULL,
                    CreatedAt DATETIME DEFAULT GETDATE(),
                    Priority NVARCHAR(20) DEFAULT 'Normal'
                )
            END
        """)
    except Exception:
        pass


def get_institution_settings(cursor):
    ensure_institution_settings_table(cursor)
    cursor.execute("SELECT TOP 1 SettingID, InstitutionName, InstitutionType FROM InstitutionSettings ORDER BY SettingID")
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            "INSERT INTO InstitutionSettings (InstitutionName, InstitutionType, UpdatedAt) VALUES (?, ?, ?)",
            ('School Management System', 'School', datetime.now())
        )
        cursor.execute("SELECT TOP 1 SettingID, InstitutionName, InstitutionType FROM InstitutionSettings ORDER BY SettingID")
        row = cursor.fetchone()

    return {
        'id': row[0],
        'institutionName': row[1] or 'School Management System',
        'institutionType': row[2] or 'School'
    }


def get_institution_grading_preset(institution_type):
    inst = (institution_type or 'School').strip().title()

    presets = {
        'School': {
            'components': [
                {'name': 'Mids', 'maxMarks': 100, 'weight': 20.0},
                {'name': 'Quiz', 'maxMarks': 100, 'weight': 15.0},
                {'name': 'Assignment', 'maxMarks': 100, 'weight': 15.0},
                {'name': 'Final', 'maxMarks': 100, 'weight': 40.0},
                {'name': 'Lab', 'maxMarks': 100, 'weight': 10.0}
            ],
            'thresholds': [('A+', 90.0), ('A', 80.0), ('B', 70.0), ('C', 60.0), ('D', 50.0), ('F', 0.0)]
        },
        'College': {
            'components': [
                {'name': 'Mids', 'maxMarks': 100, 'weight': 25.0},
                {'name': 'Quiz', 'maxMarks': 100, 'weight': 10.0},
                {'name': 'Assignment', 'maxMarks': 100, 'weight': 15.0},
                {'name': 'Final', 'maxMarks': 100, 'weight': 35.0},
                {'name': 'Lab', 'maxMarks': 100, 'weight': 15.0}
            ],
            'thresholds': [('A+', 90.0), ('A', 82.0), ('B+', 75.0), ('B', 68.0), ('C', 60.0), ('D', 50.0), ('F', 0.0)]
        },
        'University': {
            'components': [
                {'name': 'Mids', 'maxMarks': 100, 'weight': 20.0},
                {'name': 'Quiz', 'maxMarks': 100, 'weight': 10.0},
                {'name': 'Assignment', 'maxMarks': 100, 'weight': 20.0},
                {'name': 'Final', 'maxMarks': 100, 'weight': 35.0},
                {'name': 'Lab', 'maxMarks': 100, 'weight': 15.0}
            ],
            'thresholds': [('A', 85.0), ('A-', 80.0), ('B+', 75.0), ('B', 70.0), ('C+', 65.0), ('C', 60.0), ('D', 50.0), ('F', 0.0)]
        }
    }

    return presets.get(inst, presets['School'])


def ensure_default_components_for_subject(cursor, course_id, institution_type=None, strict=False):
    preset = get_institution_grading_preset(institution_type)
    target = preset['components']

    cursor.execute("SELECT ComponentID, Name FROM GradeComponents WHERE SubjectID = ? ORDER BY ComponentID", (course_id,))
    existing_rows = cursor.fetchall()

    alias = {
        'mids': ['mids', 'mid', 'midterm', 'mid-term'],
        'quiz': ['quiz', 'quizzes'],
        'assignment': ['assignment', 'assignments'],
        'final': ['final', 'finals', 'final exam'],
        'lab': ['lab', 'practical', 'practicals']
    }

    existing_map = {}
    for row in existing_rows:
        nm = (row[1] or '').strip().lower()
        existing_map[nm] = row[0]

    for comp in target:
        canonical = comp['name']
        key = canonical.strip().lower()
        comp_id = None
        for candidate in alias.get(key, [key]):
            if candidate in existing_map:
                comp_id = existing_map[candidate]
                break

        if comp_id:
            cursor.execute(
                "UPDATE GradeComponents SET Name = ?, MaxMarks = ?, WeightPercent = ? WHERE ComponentID = ?",
                (canonical, comp['maxMarks'], comp['weight'], comp_id)
            )
        else:
            cursor.execute(
                "INSERT INTO GradeComponents (SubjectID, Name, MaxMarks, WeightPercent) VALUES (?, ?, ?, ?)",
                (course_id, canonical, comp['maxMarks'], comp['weight'])
            )

    if strict:
        canonical_names = [comp['name'].strip().lower() for comp in target]
        if canonical_names:
            placeholders = ','.join(['?'] * len(canonical_names))
            params = [course_id] + canonical_names
            cursor.execute(
                f"UPDATE GradeComponents SET WeightPercent = 0 WHERE SubjectID = ? AND LOWER(Name) NOT IN ({placeholders})",
                params
            )
        else:
            cursor.execute("UPDATE GradeComponents SET WeightPercent = 0 WHERE SubjectID = ?", (course_id,))


def apply_institution_grading_criteria(cursor, institution_type):
    ensure_marks_tables(cursor)
    ensure_thresholds_table(cursor)

    preset = get_institution_grading_preset(institution_type)

    cursor.execute("DELETE FROM GradeThresholds")
    for letter, min_pct in preset['thresholds']:
        cursor.execute("INSERT INTO GradeThresholds (Letter, MinPercent) VALUES (?, ?)", (letter, min_pct))

    cursor.execute("SELECT SubjectID FROM Subjects")
    subject_rows = cursor.fetchall()
    for row in subject_rows:
        ensure_default_components_for_subject(cursor, row[0], institution_type, strict=True)


def recompute_and_store_letter_grade(cursor, course_id, student_id):
    cursor.execute("SELECT ComponentID, MaxMarks, WeightPercent FROM GradeComponents WHERE SubjectID = ? ORDER BY ComponentID", (course_id,))
    comps = cursor.fetchall()

    total_score = 0.0
    total_weight = 0.0

    for c in comps:
        cid, maxm, wt = c[0], float(c[1] or 0), float(c[2] or 0)
        if maxm <= 0 or wt <= 0:
            continue

        cursor.execute("SELECT MarksObtained FROM StudentMarks WHERE StudentID = ? AND SubjectID = ? AND ComponentID = ?", (student_id, course_id, cid))
        m = cursor.fetchone()
        if not m or m[0] is None:
            continue

        total_score += (float(m[0]) / maxm) * wt
        total_weight += wt

    pct = (total_score / total_weight * 100.0) if total_weight > 0 else 0.0

    cursor.execute("SELECT Letter, MinPercent FROM GradeThresholds ORDER BY MinPercent DESC")
    thrs = cursor.fetchall()
    letter = None
    for t in thrs:
        if pct >= float(t[1]):
            letter = t[0]
            break

    if letter:
        cursor.execute("UPDATE Enrollments SET Grade = ? WHERE StudentID = ? AND SubjectID = ?", (letter, student_id, course_id))


def allowed_resource_file(filename):
    _, ext = os.path.splitext(filename or '')
    return ext.lower() in ALLOWED_RESOURCE_EXTENSIONS


def allowed_submission_file(filename):
    _, ext = os.path.splitext(filename or '')
    return ext.lower() in ALLOWED_SUBMISSION_EXTENSIONS


def uploaded_file_path_from_url(file_url):
    if not file_url:
        return None

    if file_url.startswith(RESOURCE_URL_BASE + '/'):
        local_name = file_url.replace(RESOURCE_URL_BASE + '/', '', 1)
        return os.path.join(RESOURCE_UPLOAD_DIR, local_name)

    if file_url.startswith(SUBMISSION_URL_BASE + '/'):
        local_name = file_url.replace(SUBMISSION_URL_BASE + '/', '', 1)
        return os.path.join(SUBMISSION_UPLOAD_DIR, local_name)

    return None


def format_date(value):
    if not value:
        return None
    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d')
    return str(value)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user_type = data.get('userType')
    email = data.get('email')
    password = data.get('password')
    
    conn = DatabaseConfig.get_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'})
    
    cursor = conn.cursor()
    
    try:
        if user_type == 'student':
            cursor.execute("SELECT StudentID, FirstName, LastName FROM Students WHERE Email = ? AND Password = ?", (email, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user[0]
                session['user_type'] = 'student'
                session['user_name'] = f"{user[1]} {user[2]}"
                return jsonify({'success': True, 'redirect': '/student/dashboard'})
                
        elif user_type == 'faculty':
            cursor.execute("SELECT FacultyID, FirstName, LastName FROM Faculty WHERE Email = ? AND Password = ?", (email, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user[0]
                session['user_type'] = 'faculty'
                session['user_name'] = f"Prof. {user[1]} {user[2]}"
                return jsonify({'success': True, 'redirect': '/faculty/dashboard'})
                
        elif user_type == 'admin':
            cursor.execute("SELECT AdminID, FullName FROM Admins WHERE Username = ? AND Password = ?", (email, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user[0]
                session['user_type'] = 'admin'
                session['user_name'] = user[1]
                return jsonify({'success': True, 'redirect': '/admin/dashboard'})
        
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('index'))
    return render_template('student_dashboard.html', user_name=session['user_name'])

@app.route('/faculty/dashboard')
def faculty_dashboard():
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return redirect(url_for('index'))
    return render_template('faculty_dashboard.html', user_name=session['user_name'])

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('index'))
    return render_template('admin_dashboard.html', user_name=session['user_name'])

@app.route('/api/student/profile')
def get_student_profile():
    if 'user_type' not in session or session['user_type'] != 'student':
        return jsonify({'success': False})
    
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    student = None
    try:
        cursor.execute("""
            SELECT s.FirstName, s.LastName, s.Email, s.PhoneNumber, s.Address, s.DateOfBirth, s.EnrollmentDate,
                   c.ClassName, c.Section, c.RoomNumber
            FROM Students s
            LEFT JOIN Classes c ON s.ClassID = c.ClassID
            WHERE s.StudentID = ?
        """, (session['user_id'],))
        student = cursor.fetchone()
    except Exception:
        cursor.execute("""
            SELECT s.FirstName, s.LastName, s.Email, s.PhoneNumber, s.Address,
                   c.ClassName, c.Section, c.RoomNumber
            FROM Students s
            LEFT JOIN Classes c ON s.ClassID = c.ClassID
            WHERE s.StudentID = ?
        """, (session['user_id'],))
        student = cursor.fetchone()
    conn.close()
    
    if student:
        has_extended_columns = len(student) >= 10
        return jsonify({
            'success': True,
            'data': {
                'firstName': student[0],
                'lastName': student[1],
                'email': student[2],
                'phone': student[3] or 'N/A',
                'address': student[4] or 'N/A',
                'dob': format_date(student[5]) if has_extended_columns else None,
                'enrollmentDate': format_date(student[6]) if has_extended_columns else None,
                'className': student[7] if has_extended_columns else student[5] or 'Not Assigned',
                'section': student[8] if has_extended_columns else student[6] or 'N/A',
                'roomNumber': student[9] if has_extended_columns else student[7] or 'N/A'
            }
        })
    return jsonify({'success': False})

@app.route('/api/student/subjects')
def get_student_subjects():
    if 'user_type' not in session or session['user_type'] != 'student':
        return jsonify({'success': False})
    
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.SubjectID, s.SubjectName, s.SubjectCode, s.Credits, 
               s.SubjectType, f.FirstName + ' ' + f.LastName as Faculty, e.Grade
        FROM Enrollments e
        JOIN Subjects s ON e.SubjectID = s.SubjectID
        LEFT JOIN Faculty f ON s.FacultyID = f.FacultyID
        WHERE e.StudentID = ?
    """, (session['user_id'],))
    
    subjects = cursor.fetchall()
    conn.close()
    
    result = []
    for s in subjects:
        result.append({
            'id': s[0], 'name': s[1], 'code': s[2], 'credits': s[3],
            'type': s[4], 'faculty': s[5] or 'N/A', 'grade': s[6] or 'Pending'
        })
    
    return jsonify({'success': True, 'data': result})


@app.route('/api/admin/student/<int:student_id>/final-year-result')
def get_final_year_result(student_id):
    # Admins can view any student's final-year aggregated result; students can view their own
    if 'user_type' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    if session['user_type'] != 'admin' and not (session['user_type'] == 'student' and session.get('user_id') == student_id):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    year = request.args.get('year')
    by_credits = request.args.get('byCredits', '0') == '1'

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()

    try:
        # find enrollments for the student optionally filtering by class AcademicYear
        if year:
            cursor.execute("""
                SELECT e.SubjectID, s.SubjectName, s.Credits, c.AcademicYear
                FROM Enrollments e
                JOIN Subjects s ON e.SubjectID = s.SubjectID
                LEFT JOIN Classes c ON s.ClassID = c.ClassID
                WHERE e.StudentID = ? AND c.AcademicYear = ?
            """, (student_id, year))
        else:
            cursor.execute("""
                SELECT e.SubjectID, s.SubjectName, s.Credits, c.AcademicYear
                FROM Enrollments e
                JOIN Subjects s ON e.SubjectID = s.SubjectID
                LEFT JOIN Classes c ON s.ClassID = c.ClassID
                WHERE e.StudentID = ?
            """, (student_id,))

        rows = cursor.fetchall()
        if not rows:
            conn.close()
            return jsonify({'success': True, 'data': {'subjects': [], 'overallPercent': 0.0, 'letter': ''}})

        subject_results = []
        total_weighted = 0.0
        total_credits = 0.0

        # load thresholds
        try:
            ensure_thresholds_table(cursor)
            cursor.execute("SELECT Letter, MinPercent FROM GradeThresholds ORDER BY MinPercent DESC")
            thr_rows = cursor.fetchall()
            thresholds = [(r[0], float(r[1])) for r in thr_rows]
        except Exception:
            thresholds = []

        for r in rows:
            subject_id = r[0]
            subject_name = r[1]
            credits = float(r[2] or 0)

            # load components
            cursor.execute("SELECT ComponentID, MaxMarks, WeightPercent FROM GradeComponents WHERE SubjectID = ?", (subject_id,))
            comps = cursor.fetchall()
            if not comps:
                # apply defaults if necessary
                settings = get_institution_settings(cursor)
                ensure_default_components_for_subject(cursor, subject_id, settings.get('institutionType'))
                conn.commit()
                cursor.execute("SELECT ComponentID, MaxMarks, WeightPercent FROM GradeComponents WHERE SubjectID = ?", (subject_id,))
                comps = cursor.fetchall()

            total_score = 0.0
            total_weight = 0.0
            for comp in comps:
                comp_id = comp[0]
                maxm = float(comp[1] or 0)
                weight = float(comp[2] or 0)
                cursor.execute("SELECT MarksObtained FROM StudentMarks WHERE StudentID = ? AND SubjectID = ? AND ComponentID = ?", (student_id, subject_id, comp_id))
                mrow = cursor.fetchone()
                marks = float(mrow[0]) if mrow and mrow[0] is not None else None
                if marks is not None and maxm > 0 and weight:
                    try:
                        total_score += (marks / maxm) * weight
                        total_weight += weight
                    except Exception:
                        pass

            percent = (total_score / total_weight * 100.0) if total_weight > 0 else 0.0

            subject_results.append({'subjectId': subject_id, 'subjectName': subject_name, 'credits': credits, 'percent': round(percent,2)})

            if by_credits:
                total_weighted += percent * credits
                total_credits += credits
            else:
                total_weighted += percent
                total_credits += 1.0

        overall_percent = (total_weighted / total_credits) if total_credits > 0 else 0.0

        # compute letter
        letter = ''
        if thresholds:
            for lt, mp in thresholds:
                if overall_percent >= mp:
                    letter = lt
                    break

        conn.close()
        return jsonify({'success': True, 'data': {'subjects': subject_results, 'overallPercent': round(overall_percent,2), 'letter': letter}})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/student/available-subjects')
def get_available_subjects():
    if 'user_type' not in session or session['user_type'] != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT ClassID FROM Students WHERE StudentID = ?", (session['user_id'],))
    result = cursor.fetchone()
    
    if not result or not result[0]:
        conn.close()
        return jsonify({'success': False, 'message': 'Not assigned to class. Contact admin.'})
    
    class_id = result[0]
    
    cursor.execute("""
        SELECT s.SubjectID, s.SubjectName, s.SubjectCode, s.Credits, 
               s.SubjectType, f.FirstName + ' ' + f.LastName as Faculty
        FROM Subjects s
        LEFT JOIN Faculty f ON s.FacultyID = f.FacultyID
        WHERE s.ClassID = ? 
        AND s.SubjectID NOT IN (SELECT SubjectID FROM Enrollments WHERE StudentID = ?)
    """, (class_id, session['user_id']))
    
    subjects = cursor.fetchall()
    conn.close()
    
    result = []
    for s in subjects:
        result.append({
            'id': s[0], 'name': s[1], 'code': s[2], 'credits': s[3],
            'type': s[4], 'faculty': s[5] or 'Not Assigned'
        })
    
    return jsonify({'success': True, 'data': result})


@app.route('/api/student/fees')
def get_student_fees():
    if 'user_type' not in session or session['user_type'] != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    conn = DatabaseConfig.get_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'})

    cursor = conn.cursor()
    ensure_fee_tables(cursor)

    try:
        cursor.execute("SELECT ClassID FROM Students WHERE StudentID = ?", (session['user_id'],))
        student_row = cursor.fetchone()
        class_id = student_row[0] if student_row else None

        if not class_id:
            return jsonify({'success': True, 'data': []})

        cursor.execute("""
            SELECT FeeStructureID, FeeName, Amount, FeeType, Frequency, DueDate
            FROM FeeStructures
            WHERE ClassID = ? OR ClassID IS NULL
            ORDER BY FeeStructureID
        """, (class_id,))

        fee_rows = cursor.fetchall()
        result = []

        for fee in fee_rows:
            fee_id, fee_name, amount, fee_type, frequency, due_date = fee
            cursor.execute("""
                SELECT COALESCE(SUM(AmountPaid), 0)
                FROM FeePayments
                WHERE StudentID = ? AND FeeStructureID = ?
            """, (session['user_id'], fee_id))
            paid_row = cursor.fetchone()
            amount_paid = float(paid_row[0] or 0)
            total_amount = float(amount or 0)
            amount_due = max(total_amount - amount_paid, 0)

            if amount_due <= 0 and total_amount > 0:
                status = 'Paid'
            elif amount_paid > 0:
                status = 'Partial'
            elif due_date and due_date < date.today():
                status = 'Overdue'
            else:
                status = 'Pending'

            result.append({
                'id': fee_id,
                'name': fee_name,
                'type': fee_type or 'Other',
                'totalAmount': total_amount,
                'amountPaid': amount_paid,
                'amountDue': amount_due,
                'dueDate': format_date(due_date) or 'N/A',
                'frequency': frequency or 'N/A',
                'status': status
            })

        return jsonify({'success': True, 'data': result})
    except Exception:
        return jsonify({'success': True, 'data': []})
    finally:
        conn.close()


@app.route('/api/student/fee-payments')
def get_student_fee_payments():
    if 'user_type' not in session or session['user_type'] != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    conn = DatabaseConfig.get_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'})

    cursor = conn.cursor()
    ensure_fee_tables(cursor)

    try:
        cursor.execute("""
            SELECT fp.PaymentID, fs.FeeName, fp.AmountPaid, fp.PaymentDate, fp.PaymentMethod,
                   fp.ReceiptNumber, fp.TransactionID
            FROM FeePayments fp
            LEFT JOIN FeeStructures fs ON fp.FeeStructureID = fs.FeeStructureID
            WHERE fp.StudentID = ?
            ORDER BY fp.PaymentDate DESC, fp.PaymentID DESC
        """, (session['user_id'],))

        payments = cursor.fetchall()
        result = []

        for payment in payments:
            result.append({
                'id': payment[0],
                'feeName': payment[1] or 'Fee Payment',
                'amount': float(payment[2] or 0),
                'date': format_date(payment[3]) or 'N/A',
                'method': payment[4] or 'N/A',
                'receipt': payment[5] or payment[6] or f'REC-{payment[0]}',
                'status': 'Recorded'
            })

        return jsonify({'success': True, 'data': result})
    except Exception:
        return jsonify({'success': True, 'data': []})
    finally:
        conn.close()

@app.route('/api/student/enroll', methods=['POST'])
def enroll_subject():
    if 'user_type' not in session or session['user_type'] != 'student':
        return jsonify({'success': False})
    
    subject_id = request.json.get('subjectId')
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO Enrollments (StudentID, SubjectID, EnrollmentDate) VALUES (?, ?, ?)",
                      (session['user_id'], subject_id, date.today()))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Enrolled successfully!'})
    except:
        conn.close()
        return jsonify({'success': False, 'message': 'Enrollment failed'})

@app.route('/api/student/unenroll', methods=['POST'])
def unenroll_subject():
    if 'user_type' not in session or session['user_type'] != 'student':
        return jsonify({'success': False})
    
    subject_id = request.json.get('subjectId')
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM Enrollments WHERE StudentID = ? AND SubjectID = ?",
                      (session['user_id'], subject_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Dropped successfully!'})
    except:
        conn.close()
        return jsonify({'success': False, 'message': 'Drop failed'})

@app.route('/api/faculty/courses')
def get_faculty_courses():
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return jsonify({'success': False})
    
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.SubjectID, s.SubjectName, s.SubjectCode, s.Credits, 
               c.ClassName, s.SubjectType
        FROM Subjects s
        LEFT JOIN Classes c ON s.ClassID = c.ClassID
        WHERE s.FacultyID = ?
    """, (session['user_id'],))
    
    courses = cursor.fetchall()
    conn.close()
    
    result = []
    for c in courses:
        result.append({
            'id': c[0], 'name': c[1], 'code': c[2], 'credits': c[3],
            'className': c[4] or 'N/A', 'type': c[5] or 'N/A'
        })
    
    return jsonify({'success': True, 'data': result})

@app.route('/api/faculty/course/<int:course_id>/students')
def get_course_students(course_id):
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return jsonify({'success': False})
    
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.StudentID, s.FirstName, s.LastName, s.Email, c.ClassName
        FROM Students s
        JOIN Enrollments e ON s.StudentID = e.StudentID
        LEFT JOIN Classes c ON s.ClassID = c.ClassID
        WHERE e.SubjectID = ?
    """, (course_id,))
    
    students = cursor.fetchall()
    conn.close()
    
    result = []
    for s in students:
        result.append({
            'id': s[0], 'name': f"{s[1]} {s[2]}", 'email': s[3], 'class': s[4] or 'N/A'
        })
    
    return jsonify({'success': True, 'data': result})


@app.route('/api/faculty/course/<int:course_id>/grades')
def get_course_grades(course_id):
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return jsonify({'success': False})

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.StudentID, s.FirstName, s.LastName, s.Email, e.Grade, c.ClassName
        FROM Enrollments e
        JOIN Students s ON e.StudentID = s.StudentID
        LEFT JOIN Classes c ON s.ClassID = c.ClassID
        WHERE e.SubjectID = ?
        ORDER BY s.LastName, s.FirstName
    """, (course_id,))

    rows = cursor.fetchall()

    # check lock state
    locked = False
    try:
        cursor.execute("SELECT IsLocked FROM GradeLocks WHERE SubjectID = ?", (course_id,))
        lock_row = cursor.fetchone()
        if lock_row and lock_row[0]:
            locked = True
    except Exception:
        locked = False

    conn.close()

    result = []
    for r in rows:
        result.append({
            'id': r[0], 'name': f"{r[1]} {r[2]}", 'email': r[3], 'grade': r[4] or 'Pending', 'class': r[5] or 'N/A'
        })

    return jsonify({'success': True, 'data': result, 'locked': locked})


@app.route('/api/faculty/course/<int:course_id>/marks')
def get_course_marks(course_id):
    if 'user_type' not in session or session['user_type'] not in ('faculty', 'admin'):
        return jsonify({'success': False})

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_marks_tables(cursor)

    # load components for subject
    cursor.execute("SELECT ComponentID, Name, MaxMarks, WeightPercent FROM GradeComponents WHERE SubjectID = ? ORDER BY ComponentID", (course_id,))
    comps = cursor.fetchall()

    # if no components, create default grading rubric by institution type
    if not comps:
        settings = get_institution_settings(cursor)
        ensure_default_components_for_subject(cursor, course_id, settings.get('institutionType'))
        conn.commit()
        cursor.execute("SELECT ComponentID, Name, MaxMarks, WeightPercent FROM GradeComponents WHERE SubjectID = ? ORDER BY ComponentID", (course_id,))
        comps = cursor.fetchall()

    components = []
    for c in comps:
        components.append({'id': c[0], 'name': c[1], 'maxMarks': float(c[2]), 'weight': float(c[3])})

    # load students
    cursor.execute("SELECT s.StudentID, s.FirstName, s.LastName, s.Email, c.ClassName FROM Enrollments e JOIN Students s ON e.StudentID = s.StudentID LEFT JOIN Classes c ON s.ClassID = c.ClassID WHERE e.SubjectID = ? ORDER BY s.LastName, s.FirstName", (course_id,))
    students = cursor.fetchall()

    data_students = []
    for s in students:
        sid = s[0]
        marks_map = {}
        total_score = 0.0
        total_weight = 0.0

        for comp in components:
            comp_id = comp['id']
            # fetch mark
            cursor.execute("SELECT MarksObtained FROM StudentMarks WHERE StudentID = ? AND SubjectID = ? AND ComponentID = ?", (sid, course_id, comp_id))
            mrow = cursor.fetchone()
            marks = float(mrow[0]) if mrow and mrow[0] is not None else None

            marks_map[comp_id] = marks
            if marks is not None and comp['maxMarks'] and comp['weight']:
                try:
                    total_score += (float(marks) / float(comp['maxMarks'])) * comp['weight']
                    total_weight += comp['weight']
                except Exception:
                    pass

        data_students.append({
            'id': sid,
            'name': f"{s[1]} {s[2]}",
            'email': s[3],
            'class': s[4] or 'N/A',
            'marks': marks_map,
            'totalScore': round(total_score, 2),
            'totalWeight': round(total_weight, 2)
        })

    # load thresholds
    try:
        ensure_thresholds_table(cursor)
        cursor.execute("SELECT Letter, MinPercent FROM GradeThresholds ORDER BY MinPercent DESC")
        thr_rows = cursor.fetchall()
        thresholds = [(r[0], float(r[1])) for r in thr_rows]
    except Exception:
        thresholds = []

    # compute letter grades
    for ds in data_students:
        letter = None
        if thresholds and ds['totalWeight'] > 0:
            pct = ds['totalScore'] / ds['totalWeight'] * 100.0 if ds['totalWeight'] > 0 else 0.0
            for lt, mp in thresholds:
                if pct >= mp:
                    letter = lt
                    break
        ds['letter'] = letter or ''

    conn.close()
    return jsonify({'success': True, 'components': components, 'students': data_students, 'thresholds': thresholds})


@app.route('/api/faculty/course/<int:course_id>/marks', methods=['POST'])
def post_course_marks(course_id):
    if 'user_type' not in session or session['user_type'] not in ('faculty', 'admin'):
        return jsonify({'success': False})

    data = request.json or {}
    marks = data.get('marks', [])
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_marks_tables(cursor)
    ensure_thresholds_table(cursor)

    try:
        touched_students = set()

        for rec in marks:
            student_id = rec.get('studentId')
            comp_id = rec.get('componentId')
            val = rec.get('marks')
            if student_id is None or comp_id is None or val is None:
                continue
            touched_students.add(int(student_id))
            # upsert
            cursor.execute("SELECT MarkID FROM StudentMarks WHERE StudentID = ? AND SubjectID = ? AND ComponentID = ?", (student_id, course_id, comp_id))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE StudentMarks SET MarksObtained = ? WHERE MarkID = ?", (val, existing[0]))
            else:
                cursor.execute("INSERT INTO StudentMarks (StudentID, SubjectID, ComponentID, MarksObtained) VALUES (?, ?, ?, ?)", (student_id, course_id, comp_id, val))

        for sid in touched_students:
            recompute_and_store_letter_grade(cursor, course_id, sid)

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Marks saved and grades computed'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/faculty/course/<int:course_id>/components', methods=['GET', 'POST'])
def manage_components(course_id):
    if 'user_type' not in session or session['user_type'] not in ('faculty', 'admin'):
        return jsonify({'success': False})

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_marks_tables(cursor)

    if request.method == 'GET':
        cursor.execute("SELECT ComponentID, Name, MaxMarks, WeightPercent FROM GradeComponents WHERE SubjectID = ? ORDER BY ComponentID", (course_id,))
        rows = cursor.fetchall()
        conn.close()
        comps = [{'id': r[0], 'name': r[1], 'maxMarks': float(r[2]), 'weight': float(r[3])} for r in rows]
        return jsonify({'success': True, 'components': comps})

    # POST: replace components
    data = request.json or {}
    comps = data.get('components', [])
    try:
        cursor.execute("DELETE FROM GradeComponents WHERE SubjectID = ?", (course_id,))
        for c in comps:
            cursor.execute("INSERT INTO GradeComponents (SubjectID, Name, MaxMarks, WeightPercent) VALUES (?, ?, ?, ?)", (course_id, c.get('name'), c.get('maxMarks') or 100, c.get('weight') or 0))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Components updated'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/config/grade-thresholds', methods=['GET', 'POST'])
def grade_thresholds():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_thresholds_table(cursor)
    if request.method == 'GET':
        cursor.execute("SELECT ThresholdID, Letter, MinPercent FROM GradeThresholds ORDER BY MinPercent DESC")
        rows = cursor.fetchall()
        if not rows:
            settings = get_institution_settings(cursor)
            defaults = get_institution_grading_preset(settings.get('institutionType')).get('thresholds', [])
            for letter, min_pct in defaults:
                cursor.execute("INSERT INTO GradeThresholds (Letter, MinPercent) VALUES (?, ?)", (letter, min_pct))
            conn.commit()
            cursor.execute("SELECT ThresholdID, Letter, MinPercent FROM GradeThresholds ORDER BY MinPercent DESC")
            rows = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'thresholds': [{'id': r[0], 'letter': r[1], 'minPercent': float(r[2])} for r in rows]})

    data = request.json or {}
    thr = data.get('thresholds', [])
    try:
        cursor.execute("DELETE FROM GradeThresholds")
        for t in thr:
            cursor.execute("INSERT INTO GradeThresholds (Letter, MinPercent) VALUES (?, ?)", (t.get('letter'), t.get('minPercent')))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Thresholds updated'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/config/institution', methods=['GET', 'POST'])
def institution_config():
    if 'user_type' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()

    try:
        if request.method == 'GET':
            settings = get_institution_settings(cursor)
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'data': settings})

        if session.get('user_type') != 'admin':
            conn.close()
            return jsonify({'success': False, 'message': 'Admin only'}), 403

        payload = request.json or {}
        institution_name = (payload.get('institutionName') or 'School Management System').strip()
        institution_type = (payload.get('institutionType') or 'School').strip().title()
        if institution_type not in ('School', 'College', 'University'):
            institution_type = 'School'

        settings = get_institution_settings(cursor)
        cursor.execute(
            "UPDATE InstitutionSettings SET InstitutionName = ?, InstitutionType = ?, UpdatedAt = ? WHERE SettingID = ?",
            (institution_name, institution_type, datetime.now(), settings['id'])
        )
        apply_institution_grading_criteria(cursor, institution_type)
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Institution settings updated'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/config/grading-criteria', methods=['GET', 'POST'])
def grading_criteria_config():
    if 'user_type' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()

    try:
        settings = get_institution_settings(cursor)
        institution_type = settings.get('institutionType') or 'School'

        if request.method == 'GET':
            preset = get_institution_grading_preset(institution_type)
            formula = "Weighted % = (Mids/max)*w + (Quiz/max)*w + (Assignment/max)*w + (Final/max)*w + (Lab/max)*w"
            return jsonify({
                'success': True,
                'institutionType': institution_type,
                'formula': formula,
                'components': preset.get('components', []),
                'thresholds': [{'letter': t[0], 'minPercent': float(t[1])} for t in preset.get('thresholds', [])]
            })

        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        requested_type = (request.json or {}).get('institutionType') or institution_type
        apply_institution_grading_criteria(cursor, requested_type)
        conn.commit()
        return jsonify({'success': True, 'message': f'Applied {requested_type} grading criteria to all subjects'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()


@app.route('/api/faculty/course/<int:course_id>/resources', methods=['GET', 'POST'])
def faculty_course_resources(course_id):
    if 'user_type' not in session or session['user_type'] not in ('faculty', 'admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_resource_tables(cursor)
    ensure_submission_tables(cursor)

    try:
        if session.get('user_type') == 'faculty':
            cursor.execute("SELECT SubjectID FROM Subjects WHERE SubjectID = ? AND FacultyID = ?", (course_id, session.get('user_id')))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'This course is not assigned to you'}), 403

        if request.method == 'GET':
            cursor.execute("""
                SELECT cr.ResourceID, cr.Title, cr.ResourceType, cr.Description, cr.DueDate, cr.MaxMarks, cr.FileName, cr.FileUrl, cr.UploadedAt,
                       (SELECT COUNT(*) FROM CourseSubmissions cs WHERE cs.ResourceID = cr.ResourceID) AS SubmissionCount
                FROM CourseResources cr
                WHERE cr.SubjectID = ?
                ORDER BY cr.UploadedAt DESC, cr.ResourceID DESC
            """, (course_id,))
            rows = cursor.fetchall()
            conn.close()

            resources = []
            for r in rows:
                resources.append({
                    'id': r[0],
                    'title': r[1],
                    'resourceType': r[2],
                    'description': r[3] or '',
                    'dueDate': format_date(r[4]),
                    'maxMarks': float(r[5]) if r[5] is not None else None,
                    'fileName': r[6],
                    'fileUrl': r[7],
                    'uploadedAt': format_date(r[8]),
                    'submissionCount': int(r[9] or 0)
                })
            return jsonify({'success': True, 'data': resources})

        file = request.files.get('file')
        title = (request.form.get('title') or '').strip()
        resource_type = (request.form.get('resourceType') or 'Assignment').strip().title()
        description = (request.form.get('description') or '').strip()
        due_date = (request.form.get('dueDate') or '').strip() or None
        max_marks_raw = (request.form.get('maxMarks') or '').strip()

        if not file or not file.filename:
            conn.close()
            return jsonify({'success': False, 'message': 'Please attach a file'}), 400
        if not title:
            conn.close()
            return jsonify({'success': False, 'message': 'Title is required'}), 400
        if resource_type not in ('Assignment', 'Quiz'):
            resource_type = 'Assignment'
        if not allowed_resource_file(file.filename):
            conn.close()
            return jsonify({'success': False, 'message': 'Unsupported file type'}), 400

        safe_name = secure_filename(file.filename)
        stored_name = f"{course_id}_{session.get('user_id')}_{uuid.uuid4().hex}_{safe_name}"
        file_path = os.path.join(RESOURCE_UPLOAD_DIR, stored_name)
        file.save(file_path)
        file_url = f"{RESOURCE_URL_BASE}/{stored_name}"
        max_marks = float(max_marks_raw) if max_marks_raw else None

        cursor.execute("""
            INSERT INTO CourseResources (SubjectID, FacultyID, Title, ResourceType, Description, DueDate, MaxMarks, FileName, FileUrl, UploadedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            course_id,
            session.get('user_id'),
            title,
            resource_type,
            description,
            due_date,
            max_marks,
            safe_name,
            file_url,
            datetime.now()
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'{resource_type} uploaded successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/student/resources')
def student_resources():
    if 'user_type' not in session or session['user_type'] != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_resource_tables(cursor)
    ensure_submission_tables(cursor)

    try:
        cursor.execute("""
            SELECT cr.ResourceID, cr.Title, cr.ResourceType, cr.Description, cr.DueDate, cr.MaxMarks,
                   cr.FileName, cr.FileUrl, cr.UploadedAt, s.SubjectName, s.SubjectCode,
                   f.FirstName + ' ' + f.LastName,
                   cs.SubmissionID, cs.FileName, cs.FileUrl, cs.SubmittedAt, cs.Grade, cs.Feedback, cs.Status
            FROM CourseResources cr
            JOIN Subjects s ON cr.SubjectID = s.SubjectID
            JOIN Enrollments e ON e.SubjectID = cr.SubjectID
            LEFT JOIN Faculty f ON cr.FacultyID = f.FacultyID
            LEFT JOIN CourseSubmissions cs ON cs.ResourceID = cr.ResourceID AND cs.StudentID = e.StudentID
            WHERE e.StudentID = ?
            ORDER BY cr.DueDate ASC, cr.UploadedAt DESC, cr.ResourceID DESC
        """, (session.get('user_id'),))
        rows = cursor.fetchall()
        conn.close()

        data = []
        for r in rows:
            data.append({
                'id': r[0],
                'title': r[1],
                'resourceType': r[2],
                'description': r[3] or '',
                'dueDate': format_date(r[4]),
                'maxMarks': float(r[5]) if r[5] is not None else None,
                'fileName': r[6],
                'fileUrl': r[7],
                'uploadedAt': format_date(r[8]),
                'subjectName': r[9],
                'subjectCode': r[10],
                'faculty': r[11] or 'N/A',
                'submissionId': r[12],
                'submissionFileName': r[13],
                'submissionFileUrl': r[14],
                'submittedAt': format_date(r[15]),
                'grade': float(r[16]) if r[16] is not None else None,
                'feedback': r[17] or '',
                'submissionStatus': r[18] or 'Pending'
            })

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/student/resource/<int:resource_id>/submit', methods=['POST'])
def submit_student_resource(resource_id):
    if 'user_type' not in session or session['user_type'] != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_resource_tables(cursor)
    ensure_submission_tables(cursor)

    try:
        cursor.execute("""
            SELECT cr.ResourceID
            FROM CourseResources cr
            JOIN Enrollments e ON e.SubjectID = cr.SubjectID
            WHERE cr.ResourceID = ? AND e.StudentID = ?
        """, (resource_id, session.get('user_id')))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Resource not available for this student'}), 403

        file = request.files.get('file')
        answer_text = (request.form.get('answerText') or '').strip()
        if not file or not file.filename:
            conn.close()
            return jsonify({'success': False, 'message': 'Please attach your answer file'}), 400
        if not allowed_submission_file(file.filename):
            conn.close()
            return jsonify({'success': False, 'message': 'Unsupported file type'}), 400

        safe_name = secure_filename(file.filename)
        stored_name = f"{resource_id}_{session.get('user_id')}_{uuid.uuid4().hex}_{safe_name}"
        file_path = os.path.join(SUBMISSION_UPLOAD_DIR, stored_name)
        file.save(file_path)
        file_url = f"{SUBMISSION_URL_BASE}/{stored_name}"

        cursor.execute("SELECT SubmissionID, FileUrl FROM CourseSubmissions WHERE ResourceID = ? AND StudentID = ?", (resource_id, session.get('user_id')))
        existing = cursor.fetchone()
        if existing:
            old_path = uploaded_file_path_from_url(existing[1])
            if old_path and os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass
            cursor.execute("""
                UPDATE CourseSubmissions
                SET AnswerText = ?, FileName = ?, FileUrl = ?, SubmittedAt = ?, Status = ?, Grade = NULL, Feedback = NULL, GradedAt = NULL
                WHERE SubmissionID = ?
            """, (answer_text, safe_name, file_url, datetime.now(), 'Resubmitted', existing[0]))
        else:
            cursor.execute("""
                INSERT INTO CourseSubmissions (ResourceID, StudentID, AnswerText, FileName, FileUrl, SubmittedAt, Status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (resource_id, session.get('user_id'), answer_text, safe_name, file_url, datetime.now(), 'Submitted'))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Submission uploaded successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/faculty/course/<int:course_id>/submissions')
def faculty_course_submissions(course_id):
    if 'user_type' not in session or session['user_type'] not in ('faculty', 'admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_submission_tables(cursor)

    try:
        if session.get('user_type') == 'faculty':
            cursor.execute("SELECT SubjectID FROM Subjects WHERE SubjectID = ? AND FacultyID = ?", (course_id, session.get('user_id')))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'This course is not assigned to you'}), 403

        cursor.execute("""
            SELECT cs.SubmissionID, cs.ResourceID, cr.Title, cr.ResourceType,
                   s.StudentID, s.FirstName, s.LastName,
                   cs.FileName, cs.FileUrl, cs.SubmittedAt, cs.Grade, cs.Feedback, cs.Status,
                   cr.MaxMarks, cr.DueDate
            FROM CourseSubmissions cs
            JOIN CourseResources cr ON cs.ResourceID = cr.ResourceID
            JOIN Students s ON cs.StudentID = s.StudentID
            WHERE cr.SubjectID = ?
            ORDER BY cs.SubmittedAt DESC, cs.SubmissionID DESC
        """, (course_id,))
        rows = cursor.fetchall()
        conn.close()

        data = []
        for r in rows:
            data.append({
                'submissionId': r[0],
                'resourceId': r[1],
                'resourceTitle': r[2],
                'resourceType': r[3],
                'studentId': r[4],
                'studentName': f"{r[5]} {r[6]}",
                'fileName': r[7],
                'fileUrl': r[8],
                'submittedAt': format_date(r[9]),
                'grade': float(r[10]) if r[10] is not None else None,
                'feedback': r[11] or '',
                'status': r[12] or 'Submitted',
                'maxMarks': float(r[13]) if r[13] is not None else None,
                'dueDate': format_date(r[14])
            })
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/faculty/submission/<int:submission_id>/grade', methods=['POST'])
def faculty_grade_submission(submission_id):
    if 'user_type' not in session or session['user_type'] not in ('faculty', 'admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    payload = request.json or {}
    grade = payload.get('grade')
    feedback = (payload.get('feedback') or '').strip()
    status = (payload.get('status') or 'Graded').strip()

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_submission_tables(cursor)

    try:
        cursor.execute("""
            SELECT cs.SubmissionID
            FROM CourseSubmissions cs
            JOIN CourseResources cr ON cs.ResourceID = cr.ResourceID
            WHERE cs.SubmissionID = ?
              AND (? = 'admin' OR cr.FacultyID = ?)
        """, (submission_id, session.get('user_type'), session.get('user_id')))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Submission not found'}), 404

        cursor.execute(
            "UPDATE CourseSubmissions SET Grade = ?, Feedback = ?, Status = ?, GradedAt = ? WHERE SubmissionID = ?",
            (grade, feedback, status, datetime.now(), submission_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Submission graded successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/faculty/resource/<int:resource_id>', methods=['PUT', 'DELETE'])
def faculty_manage_resource(resource_id):
    if 'user_type' not in session or session['user_type'] not in ('faculty', 'admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_resource_tables(cursor)
    ensure_submission_tables(cursor)

    try:
        cursor.execute("""
            SELECT ResourceID, FileUrl
            FROM CourseResources
            WHERE ResourceID = ?
              AND (? = 'admin' OR FacultyID = ?)
        """, (resource_id, session.get('user_type'), session.get('user_id')))
        resource_row = cursor.fetchone()
        if not resource_row:
            conn.close()
            return jsonify({'success': False, 'message': 'Resource not found'}), 404

        if request.method == 'PUT':
            payload = request.json or {}
            title = (payload.get('title') or '').strip()
            resource_type = (payload.get('resourceType') or 'Assignment').strip().title()
            description = (payload.get('description') or '').strip()
            due_date = (payload.get('dueDate') or '').strip() or None
            max_marks = payload.get('maxMarks')

            if not title:
                conn.close()
                return jsonify({'success': False, 'message': 'Title is required'}), 400
            if resource_type not in ('Assignment', 'Quiz'):
                resource_type = 'Assignment'

            cursor.execute("""
                UPDATE CourseResources
                SET Title = ?, ResourceType = ?, Description = ?, DueDate = ?, MaxMarks = ?
                WHERE ResourceID = ?
            """, (title, resource_type, description, due_date, max_marks, resource_id))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Resource updated successfully'})

        cursor.execute("SELECT FileUrl FROM CourseSubmissions WHERE ResourceID = ?", (resource_id,))
        sub_files = cursor.fetchall()
        for sf in sub_files:
            sub_path = uploaded_file_path_from_url(sf[0])
            if sub_path and os.path.exists(sub_path):
                try:
                    os.remove(sub_path)
                except Exception:
                    pass

        cursor.execute("DELETE FROM CourseSubmissions WHERE ResourceID = ?", (resource_id,))
        cursor.execute("DELETE FROM CourseResources WHERE ResourceID = ?", (resource_id,))

        main_path = uploaded_file_path_from_url(resource_row[1])
        if main_path and os.path.exists(main_path):
            try:
                os.remove(main_path)
            except Exception:
                pass

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Resource deleted successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/upcoming-deadlines')
def upcoming_deadlines():
    if 'user_type' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    limit = request.args.get('limit', default=8, type=int)
    if limit <= 0:
        limit = 8
    if limit > 25:
        limit = 25

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_resource_tables(cursor)
    ensure_submission_tables(cursor)

    try:
        if session.get('user_type') == 'student':
            cursor.execute("""
                SELECT TOP (?) cr.ResourceID, cr.Title, cr.ResourceType, cr.DueDate,
                       s.SubjectName, s.SubjectCode,
                       cs.Status, cs.SubmittedAt
                FROM CourseResources cr
                JOIN Enrollments e ON e.SubjectID = cr.SubjectID
                JOIN Subjects s ON s.SubjectID = cr.SubjectID
                LEFT JOIN CourseSubmissions cs ON cs.ResourceID = cr.ResourceID AND cs.StudentID = e.StudentID
                WHERE e.StudentID = ?
                  AND cr.DueDate IS NOT NULL
                  AND cr.DueDate >= ?
                ORDER BY cr.DueDate ASC, cr.ResourceID ASC
            """, (limit, session.get('user_id'), date.today()))
            rows = cursor.fetchall()
            conn.close()

            data = []
            for r in rows:
                data.append({
                    'resourceId': r[0],
                    'title': r[1],
                    'resourceType': r[2],
                    'dueDate': format_date(r[3]),
                    'subjectName': r[4],
                    'subjectCode': r[5],
                    'status': r[6] or 'Pending',
                    'submittedAt': format_date(r[7])
                })
            return jsonify({'success': True, 'data': data})

        if session.get('user_type') == 'faculty':
            cursor.execute("""
                SELECT TOP (?) cr.ResourceID, cr.Title, cr.ResourceType, cr.DueDate,
                       s.SubjectName, s.SubjectCode,
                       (SELECT COUNT(*) FROM CourseSubmissions cs WHERE cs.ResourceID = cr.ResourceID) AS SubmissionCount
                FROM CourseResources cr
                JOIN Subjects s ON s.SubjectID = cr.SubjectID
                WHERE cr.FacultyID = ?
                  AND cr.DueDate IS NOT NULL
                  AND cr.DueDate >= ?
                ORDER BY cr.DueDate ASC, cr.ResourceID ASC
            """, (limit, session.get('user_id'), date.today()))
            rows = cursor.fetchall()
            conn.close()

            data = []
            for r in rows:
                data.append({
                    'resourceId': r[0],
                    'title': r[1],
                    'resourceType': r[2],
                    'dueDate': format_date(r[3]),
                    'subjectName': r[4],
                    'subjectCode': r[5],
                    'submissionCount': int(r[6] or 0)
                })
            return jsonify({'success': True, 'data': data})

        conn.close()
        return jsonify({'success': True, 'data': []})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/admin/student/<int:student_id>/credentials', methods=['POST'])
def update_student_credentials(student_id):
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    
    try:
        email = data.get('email')
        password = data.get('password')
        firstName = data.get('firstName')
        lastName = data.get('lastName')
        
        # Check if email already exists for another student
        if email:
            cursor.execute("SELECT StudentID FROM Students WHERE Email = ? AND StudentID != ?", (email, student_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Email already exists for another student'}), 400
        
        # Build update query
        if password:
            cursor.execute("UPDATE Students SET FirstName = ?, LastName = ?, Email = ?, Password = ? WHERE StudentID = ?",
                          (firstName, lastName, email, password, student_id))
        else:
            cursor.execute("UPDATE Students SET FirstName = ?, LastName = ?, Email = ? WHERE StudentID = ?",
                          (firstName, lastName, email, student_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Student credentials updated'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/admin/faculty/<int:faculty_id>/credentials', methods=['POST'])
def update_faculty_credentials(faculty_id):
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    
    try:
        email = data.get('email')
        password = data.get('password')
        firstName = data.get('firstName')
        lastName = data.get('lastName')
        
        # Check if email already exists for another faculty
        if email:
            cursor.execute("SELECT FacultyID FROM Faculty WHERE Email = ? AND FacultyID != ?", (email, faculty_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Email already exists for another faculty'}), 400
        
        # Build update query
        if password:
            cursor.execute("UPDATE Faculty SET FirstName = ?, LastName = ?, Email = ?, Password = ? WHERE FacultyID = ?",
                          (firstName, lastName, email, password, faculty_id))
        else:
            cursor.execute("UPDATE Faculty SET FirstName = ?, LastName = ?, Email = ? WHERE FacultyID = ?",
                          (firstName, lastName, email, faculty_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Faculty credentials updated'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/faculty/course/<int:course_id>/report')
def course_report(course_id):
    fmt = request.args.get('format', 'csv').lower()
    if 'user_type' not in session or session['user_type'] not in ('faculty', 'admin'):
        return jsonify({'success': False}), 403

    # reuse marks endpoint logic
    with DatabaseConfig.get_connection() as conn:
        cursor = conn.cursor()
        # fetch marks data
        cursor.execute("SELECT ComponentID, Name, MaxMarks FROM GradeComponents WHERE SubjectID = ? ORDER BY ComponentID", (course_id,))
        comps = cursor.fetchall()
        cursor.execute("SELECT s.StudentID, s.FirstName, s.LastName FROM Enrollments e JOIN Students s ON e.StudentID = s.StudentID WHERE e.SubjectID = ? ORDER BY s.LastName, s.FirstName", (course_id,))
        students = cursor.fetchall()

        # build CSV
        headers = ['Student'] + [f"{c[1]}({c[2]})" for c in comps] + ['Total', 'Letter']
        rows = [headers]
        for s in students:
            sid = s[0]
            row = [f"{s[1]} {s[2]}"]
            total = 0.0
            for c in comps:
                cursor.execute("SELECT MarksObtained FROM StudentMarks WHERE StudentID = ? AND SubjectID = ? AND ComponentID = ?", (sid, course_id, c[0]))
                m = cursor.fetchone()
                val = m[0] if m and m[0] is not None else ''
                row.append(str(val))
            # calculate total & letter via marks endpoint
            # call internal function? reuse simple approach: skip accurate weighting here and leave total blank
            row.append('')
            row.append('')
            rows.append(row)

    csv = '\n'.join([','.join(['"' + str(x).replace('"','""') + '"' for x in r]) for r in rows])

    if fmt == 'pdf' and pdf_available:
        try:
            from io import BytesIO
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            table = Table(rows)
            table.setStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black)])
            doc.build([table])
            pdf = buffer.getvalue()
            buffer.close()
            return (pdf, 200, {'Content-Type': 'application/pdf', 'Content-Disposition': f'attachment; filename=grades_{course_id}.pdf'})
        except Exception:
            # if PDF generation fails, fall back to CSV below
            pass

    return (csv, 200, {'Content-Type': 'text/csv', 'Content-Disposition': f'attachment; filename=grades_{course_id}.csv'})


@app.route('/api/faculty/course/<int:course_id>/lock', methods=['POST'])
def lock_course_grades(course_id):
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return jsonify({'success': False})

    data = request.json or {}
    lock_flag = bool(data.get('lock'))

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_grade_tables(cursor)

    try:
        cursor.execute("SELECT SubjectID FROM GradeLocks WHERE SubjectID = ?", (course_id,))
        exists = cursor.fetchone()
        if exists:
            cursor.execute("UPDATE GradeLocks SET IsLocked = ?, LockedByFacultyID = ?, LockedAt = ? WHERE SubjectID = ?",
                          (1 if lock_flag else 0, session.get('user_id') if lock_flag else None, datetime.now() if lock_flag else None, course_id))
        else:
            cursor.execute("INSERT INTO GradeLocks (SubjectID, IsLocked, LockedByFacultyID, LockedAt) VALUES (?, ?, ?, ?)",
                          (course_id, 1 if lock_flag else 0, session.get('user_id') if lock_flag else None, datetime.now() if lock_flag else None))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'locked': lock_flag})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/faculty/attendance', methods=['POST'])
def mark_attendance():
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return jsonify({'success': False})
    
    data = request.json
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    
    try:
        for record in data['attendance']:
            cursor.execute("INSERT INTO Attendance (StudentID, SubjectID, Date, Status) VALUES (?, ?, ?, ?)",
                          (record['studentId'], data['courseId'], date.today(), record['status']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Attendance marked!'})
    except:
        conn.close()
        return jsonify({'success': False, 'message': 'Failed'})

@app.route('/api/faculty/grades', methods=['POST'])
def update_grades():
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return jsonify({'success': False})
    
    data = request.json
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_grade_tables(cursor)

    try:
        # Check if grades are locked for this subject
        cursor.execute("SELECT IsLocked FROM GradeLocks WHERE SubjectID = ?", (data['courseId'],))
        lock_row = cursor.fetchone()
        if lock_row and lock_row[0]:
            conn.close()
            return jsonify({'success': False, 'message': 'Grades are locked for this course'}), 400

        for record in data.get('grades', []):
            # fetch old grade
            cursor.execute("SELECT Grade FROM Enrollments WHERE StudentID = ? AND SubjectID = ?",
                          (record['studentId'], data['courseId']))
            existing = cursor.fetchone()
            old_grade = existing[0] if existing else None

            new_grade = record.get('grade')
            # insert history if changed
            if str(old_grade) != str(new_grade):
                cursor.execute("INSERT INTO GradeHistory (StudentID, SubjectID, OldGrade, NewGrade, ChangedByFacultyID, ChangedAt) VALUES (?, ?, ?, ?, ?, ?)",
                              (record['studentId'], data['courseId'], old_grade, new_grade, session.get('user_id'), datetime.now()))

            cursor.execute("UPDATE Enrollments SET Grade = ? WHERE StudentID = ? AND SubjectID = ?",
                          (new_grade, record['studentId'], data['courseId']))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Grades updated!'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/stats')
def get_stats():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False})
    
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM Students")
    students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Faculty")
    faculty = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Classes")
    classes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Subjects")
    subjects = cursor.fetchone()[0]

    total_fees = 0.0
    collected_fees = 0.0

    if table_exists(cursor, 'FeeStructures'):
        try:
            cursor.execute("SELECT COALESCE(SUM(Amount), 0) FROM FeeStructures")
            total_fees = float(cursor.fetchone()[0] or 0)
        except Exception:
            total_fees = 0.0

    if table_exists(cursor, 'FeePayments'):
        try:
            cursor.execute("SELECT COALESCE(SUM(AmountPaid), 0) FROM FeePayments")
            collected_fees = float(cursor.fetchone()[0] or 0)
        except Exception:
            collected_fees = 0.0
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'students': students,
            'faculty': faculty,
            'classes': classes,
            'subjects': subjects,
            'totalFees': total_fees,
            'collectedFees': collected_fees
        }
    })

@app.route('/api/admin/classes')
def get_all_classes():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False})
    
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.ClassID, c.ClassName, c.ClassType, c.Section, c.RoomNumber, c.Capacity,
               (SELECT COUNT(*) FROM Students WHERE ClassID = c.ClassID) as StudentCount,
               (SELECT COUNT(*) FROM Subjects WHERE ClassID = c.ClassID) as SubjectCount
        FROM Classes c ORDER BY c.ClassID
    """)
    
    classes = cursor.fetchall()
    conn.close()
    
    result = []
    for c in classes:
        result.append({
            'id': c[0], 'name': c[1], 'type': c[2], 'section': c[3], 'room': c[4],
            'capacity': c[5], 'studentCount': c[6], 'subjectCount': c[7]
        })
    
    return jsonify({'success': True, 'data': result})

@app.route('/api/admin/classes', methods=['POST'])
def add_class():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False})
    
    data = request.json
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO Classes (ClassName, ClassType, Section, Capacity, RoomNumber, AcademicYear) VALUES (?, ?, ?, ?, ?, ?)",
                      (data['name'], data['type'], data.get('section'), data.get('capacity'), data.get('room'), data.get('year')))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Class added!'})
    except:
        conn.close()
        return jsonify({'success': False, 'message': 'Failed'})

@app.route('/api/admin/students')
def get_all_students():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False})
    
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.StudentID, s.FirstName, s.LastName, s.Email, c.ClassName
        FROM Students s
        LEFT JOIN Classes c ON s.ClassID = c.ClassID
        ORDER BY s.StudentID
    """)
    
    students = cursor.fetchall()
    conn.close()
    
    result = []
    for s in students:
        result.append({
            'id': s[0], 'firstName': s[1], 'lastName': s[2], 'email': s[3], 'class': s[4] or 'Not Assigned'
        })
    
    return jsonify({'success': True, 'data': result})

@app.route('/api/admin/students', methods=['POST'])
def add_student():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False})
    
    data = request.json
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO Students (FirstName, LastName, Email, Password, PhoneNumber, Address, ClassID) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (data['firstName'], data['lastName'], data['email'], data['password'], data.get('phone'), data.get('address'), data.get('classId')))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Student added!'})
    except:
        conn.close()
        return jsonify({'success': False, 'message': 'Failed'})

@app.route('/api/admin/faculty')
def get_all_faculty():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False})
    
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT FacultyID, FirstName, LastName, Email, Department FROM Faculty ORDER BY FacultyID")
    
    faculty = cursor.fetchall()
    conn.close()
    
    result = []
    for f in faculty:
        result.append({'id': f[0], 'firstName': f[1], 'lastName': f[2], 'email': f[3], 'department': f[4]})
    
    return jsonify({'success': True, 'data': result})

@app.route('/api/admin/faculty', methods=['POST'])
def add_faculty():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False})
    
    data = request.json
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO Faculty (FirstName, LastName, Email, Password, PhoneNumber, Department, Qualification) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (data['firstName'], data['lastName'], data['email'], data['password'], data.get('phone'), data.get('department'), data.get('qualification')))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Faculty added!'})
    except:
        conn.close()
        return jsonify({'success': False, 'message': 'Failed'})

@app.route('/api/admin/subjects')
def get_all_subjects():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False})
    
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.SubjectID, s.SubjectName, s.SubjectCode, c.ClassName, 
               f.FirstName + ' ' + f.LastName as Faculty, s.Credits, s.SubjectType
        FROM Subjects s
        LEFT JOIN Classes c ON s.ClassID = c.ClassID
        LEFT JOIN Faculty f ON s.FacultyID = f.FacultyID
        ORDER BY s.SubjectID
    """)
    
    subjects = cursor.fetchall()
    conn.close()
    
    result = []
    for s in subjects:
        result.append({
            'id': s[0], 'name': s[1], 'code': s[2], 'class': s[3] or 'N/A',
            'faculty': s[4] or 'Not Assigned', 'credits': s[5], 'type': s[6]
        })
    
    return jsonify({'success': True, 'data': result})


@app.route('/api/admin/fee-structures')
def get_fee_structures():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False})

    conn = DatabaseConfig.get_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'})

    cursor = conn.cursor()
    ensure_fee_tables(cursor)

    try:
        cursor.execute("""
            SELECT fs.FeeStructureID, c.ClassName, fs.FeeName, fs.Amount, fs.FeeType, fs.Frequency, fs.DueDate
            FROM FeeStructures fs
            LEFT JOIN Classes c ON fs.ClassID = c.ClassID
            ORDER BY fs.FeeStructureID
        """)
        fees = cursor.fetchall()

        result = []
        for fee in fees:
            result.append({
                'id': fee[0],
                'className': fee[1] or 'N/A',
                'feeName': fee[2],
                'amount': float(fee[3] or 0),
                'type': fee[4] or 'Other',
                'frequency': fee[5] or 'N/A',
                'dueDate': format_date(fee[6])
            })

        return jsonify({'success': True, 'data': result})
    except Exception:
        return jsonify({'success': True, 'data': []})
    finally:
        conn.close()


@app.route('/api/admin/fee-structures', methods=['POST'])
def add_fee_structure():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False})

    data = request.json or {}
    conn = DatabaseConfig.get_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'})

    cursor = conn.cursor()
    ensure_fee_tables(cursor)

    try:
        cursor.execute("""
            INSERT INTO FeeStructures (ClassID, FeeName, Amount, FeeType, Frequency, DueDate, AcademicYear)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('classId'),
            data.get('feeName'),
            data.get('amount'),
            data.get('feeType'),
            data.get('frequency'),
            data.get('dueDate') or None,
            data.get('year')
        ))
        conn.commit()
        return jsonify({'success': True, 'message': 'Fee structure added!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()


@app.route('/api/admin/fee-payments', methods=['POST'])
def add_fee_payment():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False})

    data = request.json or {}
    conn = DatabaseConfig.get_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'})

    cursor = conn.cursor()
    ensure_fee_tables(cursor)

    try:
        payment_date = data.get('date') or date.today()
        cursor.execute("""
            INSERT INTO FeePayments (StudentID, FeeStructureID, AmountPaid, PaymentDate, PaymentMethod, TransactionID, Remarks, ReceiptNumber)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('studentId'),
            data.get('feeStructureId'),
            data.get('amount'),
            payment_date,
            data.get('method'),
            data.get('transactionId'),
            data.get('remarks'),
            None
        ))
        cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
        payment_id_row = cursor.fetchone()
        payment_id = payment_id_row[0] if payment_id_row else None
        receipt_number = f'REC-{payment_id}' if payment_id else f'REC-{date.today().strftime("%Y%m%d")}'
        if payment_id:
            cursor.execute("UPDATE FeePayments SET ReceiptNumber = ? WHERE PaymentID = ?", (receipt_number, payment_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Payment recorded!', 'receiptNumber': receipt_number})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/api/admin/subjects', methods=['POST'])
def add_subject():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False})
    
    data = request.json
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO Subjects (SubjectName, SubjectCode, ClassID, FacultyID, Credits, SubjectType) VALUES (?, ?, ?, ?, ?, ?)",
                      (data['name'], data['code'], data['classId'], data.get('facultyId'), data['credits'], data['type']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Subject added!'})
    except:
        conn.close()
        return jsonify({'success': False, 'message': 'Failed'})


@app.route('/api/announcements')
def get_announcements():
    if 'user_type' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_announcements_table(cursor)

    try:
        user_id = session.get('user_id')
        user_type = session.get('user_type')
        limit = request.args.get('limit', 10, type=int)

        if user_type == 'admin':
            cursor.execute("""
                SELECT TOP ? ca.AnnouncementID, ca.Title, ca.Content, ca.CreatedAt, ca.Priority,
                       s.SubjectName, f.FirstName, f.LastName
                FROM ClassAnnouncements ca
                JOIN Subjects s ON ca.SubjectID = s.SubjectID
                JOIN Faculty f ON ca.FacultyID = f.FacultyID
                ORDER BY ca.CreatedAt DESC
            """, (limit,))
        elif user_type == 'faculty':
            cursor.execute("""
                SELECT TOP ? ca.AnnouncementID, ca.Title, ca.Content, ca.CreatedAt, ca.Priority,
                       s.SubjectName, f.FirstName, f.LastName
                FROM ClassAnnouncements ca
                JOIN Subjects s ON ca.SubjectID = s.SubjectID
                JOIN Faculty f ON ca.FacultyID = f.FacultyID
                WHERE ca.FacultyID = ?
                ORDER BY ca.CreatedAt DESC
            """, (limit, user_id))
        else:  # student
            cursor.execute("""
                SELECT TOP ? ca.AnnouncementID, ca.Title, ca.Content, ca.CreatedAt, ca.Priority,
                       s.SubjectName, f.FirstName, f.LastName
                FROM ClassAnnouncements ca
                JOIN Subjects s ON ca.SubjectID = s.SubjectID
                JOIN Faculty f ON ca.FacultyID = f.FacultyID
                JOIN Enrollments e ON s.SubjectID = e.SubjectID
                WHERE e.StudentID = ?
                ORDER BY ca.CreatedAt DESC
            """, (limit, user_id))

        rows = cursor.fetchall()
        conn.close()

        data = [{
            'id': r[0],
            'title': r[1],
            'content': r[2],
            'createdAt': format_date(r[3]),
            'priority': r[4],
            'subjectName': r[5],
            'facultyName': f"{r[6]} {r[7]}"
        } for r in rows]
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/faculty/announcements', methods=['POST'])
def create_announcement():
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.json or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    subject_id = data.get('subjectId')
    priority = (data.get('priority') or 'Normal').strip()

    if not title or not content or not subject_id:
        return jsonify({'success': False, 'message': 'Title, content, and subject required'})

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_announcements_table(cursor)

    try:
        cursor.execute(
            "INSERT INTO ClassAnnouncements (SubjectID, FacultyID, Title, Content, Priority, CreatedAt) VALUES (?, ?, ?, ?, ?, ?)",
            (subject_id, session.get('user_id'), title, content, priority, datetime.now())
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Announcement posted!'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/faculty/announcements/<int:announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()
    ensure_announcements_table(cursor)

    try:
        cursor.execute("DELETE FROM ClassAnnouncements WHERE AnnouncementID = ? AND FacultyID = ?",
                      (announcement_id, session.get('user_id')))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Announcement deleted!'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    if 'user_type' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    user_type = session.get('user_type')
    user_id = session.get('user_id')
    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()

    try:
        stats = {}
        if user_type == 'admin':
            cursor.execute("SELECT COUNT(*) FROM Students")
            stats['totalStudents'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM Faculty")
            stats['totalFaculty'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM Classes")
            stats['totalClasses'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM Subjects")
            stats['totalSubjects'] = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(CAST(AmountPaid AS FLOAT)) FROM FeePayments WHERE CAST(PaymentDate AS DATE) >= DATEADD(MONTH, -1, CAST(GETDATE() AS DATE))")
            result = cursor.fetchone()
            stats['feesCollectedThisMonth'] = float(result[0]) if result[0] else 0

        elif user_type == 'faculty':
            cursor.execute("SELECT COUNT(*) FROM Subjects WHERE FacultyID = ?", (user_id,))
            stats['totalCourses'] = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(DISTINCT e.StudentID)
                FROM Enrollments e
                JOIN Subjects s ON e.SubjectID = s.SubjectID
                WHERE s.FacultyID = ?
            """, (user_id,))
            stats['totalStudents'] = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(*) FROM CourseSubmissions cs
                JOIN CourseResources cr ON cs.ResourceID = cr.ResourceID
                WHERE cr.FacultyID = ? AND cs.Status = 'Pending'
            """, (user_id,))
            stats['pendingSubmissionsToGrade'] = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(*) FROM Attendance
                WHERE FacultyID = ? AND CAST(AttendanceDate AS DATE) = CAST(GETDATE() AS DATE)
            """, (user_id,))
            stats['attendanceMarkedToday'] = cursor.fetchone()[0]

        else:  # student
            cursor.execute("""
                SELECT COUNT(*) FROM Enrollments WHERE StudentID = ?
            """, (user_id,))
            stats['totalCourses'] = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(*) FROM CourseSubmissions cs
                WHERE cs.StudentID = ? AND cs.Status = 'Pending'
            """, (user_id,))
            stats['pendingSubmissions'] = cursor.fetchone()[0]
            cursor.execute("""
                SELECT SUM(CAST(Amount AS FLOAT)) FROM FeePayments
                WHERE StudentID = ?
            """, (user_id,))
            result = cursor.fetchone()
            stats['totalFeesPaid'] = float(result[0]) if result[0] else 0
            cursor.execute("""
                SELECT AVG(CAST(Grade AS FLOAT)) FROM StudentMarks WHERE StudentID = ?
            """, (user_id,))
            result = cursor.fetchone()
            stats['averageGrade'] = float(result[0]) if result[0] else 0

        conn.close()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/students/search')
def search_students():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    query = request.args.get('q', '').strip()
    class_id = request.args.get('classId', type=int)
    limit = request.args.get('limit', 50, type=int)

    conn = DatabaseConfig.get_connection()
    cursor = conn.cursor()

    try:
        sql = "SELECT TOP ? StudentID, FirstName, LastName, Email, ClassID, RollNo FROM Students WHERE 1=1"
        params = [limit]
        if query:
            sql += " AND (FirstName LIKE ? OR LastName LIKE ? OR Email LIKE ? OR RollNo LIKE ?)"
            q = f"%{query}%"
            params.extend([q, q, q, q])
        if class_id:
            sql += " AND ClassID = ?"
            params.append(class_id)
        sql += " ORDER BY FirstName"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        data = [{'id': r[0], 'name': f"{r[1]} {r[2]}", 'email': r[3], 'classId': r[4], 'rollNo': r[5]} for r in rows]
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    app.run(debug=True, port=5000)
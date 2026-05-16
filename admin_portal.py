# admin_portal.py
# Admin portal module

from config import DatabaseConfig
import os
from datetime import date

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def admin_login():
    """Handle admin login"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "ADMIN LOGIN")
    print("=" * 50)
    
    username = input("\nEnter Username: ")
    password = input("Enter Password: ")
    
    conn = DatabaseConfig.get_connection()
    if not conn:
        print("Database connection failed!")
        input("\nPress Enter to continue...")
        return
    
    cursor = conn.cursor()
    cursor.execute("SELECT AdminID, FullName FROM Admins WHERE Username = ? AND Password = ?", (username, password))
    admin = cursor.fetchone()
    
    if admin:
        admin_id, full_name = admin
        print(f"\nWelcome, {full_name}!")
        input("\nPress Enter to continue...")
        admin_dashboard(admin_id, full_name, conn)
    else:
        print("\nInvalid credentials!")
        input("\nPress Enter to continue...")
    
    conn.close()

def admin_dashboard(admin_id, full_name, conn):
    """Admin dashboard with options"""
    while True:
        clear_screen()
        print("=" * 50)
        print(f" ADMIN DASHBOARD - {full_name}")
        print("=" * 50)
        print("\n1. Student Management")
        print("2. Faculty Management")
        print("3. Course Management")
        print("4. Enrollment Management")
        print("5. View Reports")
        print("6. Logout")
        print("\n" + "=" * 50)
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == '1':
            student_management(conn)
        elif choice == '2':
            faculty_management(conn)
        elif choice == '3':
            course_management(conn)
        elif choice == '4':
            enrollment_management(conn)
        elif choice == '5':
            view_reports(conn)
        elif choice == '6':
            print("\nLogging out...")
            break
        else:
            print("\nInvalid choice!")
            input("\nPress Enter to continue...")

def student_management(conn):
    """Student management submenu"""
    while True:
        clear_screen()
        print("=" * 50)
        print(" " * 13 + "STUDENT MANAGEMENT")
        print("=" * 50)
        print("\n1. Add New Student")
        print("2. View All Students")
        print("3. Update Student")
        print("4. Delete Student")
        print("5. Back to Main Menu")
        print("\n" + "=" * 50)
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            add_student(conn)
        elif choice == '2':
            view_all_students(conn)
        elif choice == '3':
            update_student(conn)
        elif choice == '4':
            delete_student(conn)
        elif choice == '5':
            break
        else:
            print("\nInvalid choice!")
            input("\nPress Enter to continue...")

def add_student(conn):
    """Add new student"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "ADD NEW STUDENT")
    print("=" * 50)
    
    first_name = input("\nFirst Name: ")
    last_name = input("Last Name: ")
    email = input("Email: ")
    password = input("Password: ")
    dob = input("Date of Birth (YYYY-MM-DD): ")
    phone = input("Phone Number: ")
    address = input("Address: ")
    class_id = input("Class ID: ")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Students (FirstName, LastName, Email, Password, 
                                DateOfBirth, PhoneNumber, Address, ClassID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, password, dob, phone, address, class_id))
        conn.commit()
        print("\n✓ Student added successfully!")
    except Exception as e:
        print(f"\nError: {e}")
    
    input("\nPress Enter to continue...")

def view_all_students(conn):
    """View all students"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "ALL STUDENTS")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.StudentID, s.FirstName, s.LastName, s.Email, c.ClassName, s.EnrollmentDate
        FROM Students s
        LEFT JOIN Classes c ON s.ClassID = c.ClassID
        ORDER BY StudentID
    """)
    
    students = cursor.fetchall()
    
    if students:
        print(f"\n{'ID':<5} {'Name':<30} {'Email':<30} {'Class':<10} {'Enrolled':<12}")
        print("-" * 87)
        for student in students:
            name = f"{student[1]} {student[2]}"
            print(f"{student[0]:<5} {name:<30} {student[3]:<30} {student[4] or 'N/A':<10} {str(student[5]):<12}")
    else:
        print("\nNo students found.")
    
    input("\nPress Enter to continue...")

def update_student(conn):
    """Update student information"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "UPDATE STUDENT")
    print("=" * 50)
    
    student_id = input("\nEnter Student ID: ")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.StudentID, s.FirstName, s.LastName, s.Email, s.Password, s.DateOfBirth,
               s.PhoneNumber, s.Address, s.ClassID, c.ClassName
        FROM Students s
        LEFT JOIN Classes c ON s.ClassID = c.ClassID
        WHERE s.StudentID = ?
    """, (student_id,))
    student = cursor.fetchone()
    
    if not student:
        print("\nStudent not found!")
        input("\nPress Enter to continue...")
        return
    
    print(f"\nCurrent Details:")
    print(f"Name: {student[1]} {student[2]}")
    print(f"Email: {student[3]}")
    print(f"Phone: {student[6]}")
    print(f"Class: {student[9] or 'N/A'}")
    
    print("\nEnter new details (press Enter to keep current value):")
    first_name = input(f"First Name [{student[1]}]: ") or student[1]
    last_name = input(f"Last Name [{student[2]}]: ") or student[2]
    phone = input(f"Phone [{student[6]}]: ") or student[6]
    address = input(f"Address [{student[7]}]: ") or student[7]
    class_id = input(f"Class ID [{student[8]}]: ") or student[8]
    
    try:
        cursor.execute("""
            UPDATE Students 
            SET FirstName = ?, LastName = ?, PhoneNumber = ?, Address = ?, ClassID = ?
            WHERE StudentID = ?
        """, (first_name, last_name, phone, address, class_id, student_id))
        conn.commit()
        print("\n✓ Student updated successfully!")
    except Exception as e:
        print(f"\nError: {e}")
    
    input("\nPress Enter to continue...")

def delete_student(conn):
    """Delete student"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "DELETE STUDENT")
    print("=" * 50)
    
    student_id = input("\nEnter Student ID to delete: ")
    
    cursor = conn.cursor()
    cursor.execute("SELECT FirstName, LastName FROM Students WHERE StudentID = ?", (student_id,))
    student = cursor.fetchone()
    
    if not student:
        print("\nStudent not found!")
        input("\nPress Enter to continue...")
        return
    
    print(f"\nStudent: {student[0]} {student[1]}")
    confirm = input("Are you sure you want to delete? (yes/no): ").lower()
    
    if confirm == 'yes':
        try:
            cursor.execute("DELETE FROM Students WHERE StudentID = ?", (student_id,))
            conn.commit()
            print("\n✓ Student deleted successfully!")
        except Exception as e:
            print(f"\nError: {e}")
    else:
        print("\nDeletion cancelled.")
    
    input("\nPress Enter to continue...")

def faculty_management(conn):
    """Faculty management submenu"""
    while True:
        clear_screen()
        print("=" * 50)
        print(" " * 13 + "FACULTY MANAGEMENT")
        print("=" * 50)
        print("\n1. Add New Faculty")
        print("2. View All Faculty")
        print("3. Update Faculty")
        print("4. Delete Faculty")
        print("5. Back to Main Menu")
        print("\n" + "=" * 50)
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            add_faculty(conn)
        elif choice == '2':
            view_all_faculty(conn)
        elif choice == '3':
            update_faculty(conn)
        elif choice == '4':
            delete_faculty(conn)
        elif choice == '5':
            break
        else:
            print("\nInvalid choice!")
            input("\nPress Enter to continue...")

def add_faculty(conn):
    """Add new faculty"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "ADD NEW FACULTY")
    print("=" * 50)
    
    first_name = input("\nFirst Name: ")
    last_name = input("Last Name: ")
    email = input("Email: ")
    password = input("Password: ")
    phone = input("Phone Number: ")
    department = input("Department: ")
    qualification = input("Qualification: ")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Faculty (FirstName, LastName, Email, Password, 
                               PhoneNumber, Department, Qualification)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, password, phone, department, qualification))
        conn.commit()
        print("\n✓ Faculty added successfully!")
    except Exception as e:
        print(f"\nError: {e}")
    
    input("\nPress Enter to continue...")

def view_all_faculty(conn):
    """View all faculty"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "ALL FACULTY")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT FacultyID, FirstName, LastName, Email, Department, JoiningDate
        FROM Faculty
        ORDER BY FacultyID
    """)
    
    faculty = cursor.fetchall()
    
    if faculty:
        print(f"\n{'ID':<5} {'Name':<30} {'Email':<30} {'Department':<15} {'Joined':<12}")
        print("-" * 92)
        for f in faculty:
            name = f"Prof. {f[1]} {f[2]}"
            print(f"{f[0]:<5} {name:<30} {f[3]:<30} {f[4]:<15} {str(f[5]):<12}")
    else:
        print("\nNo faculty found.")
    
    input("\nPress Enter to continue...")

def update_faculty(conn):
    """Update faculty information"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "UPDATE FACULTY")
    print("=" * 50)
    
    faculty_id = input("\nEnter Faculty ID: ")
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Faculty WHERE FacultyID = ?", (faculty_id,))
    faculty = cursor.fetchone()
    
    if not faculty:
        print("\nFaculty not found!")
        input("\nPress Enter to continue...")
        return
    
    print(f"\nCurrent Details:")
    print(f"Name: Prof. {faculty[1]} {faculty[2]}")
    print(f"Email: {faculty[3]}")
    print(f"Department: {faculty[6]}")
    
    print("\nEnter new details (press Enter to keep current value):")
    phone = input(f"Phone [{faculty[5]}]: ") or faculty[5]
    department = input(f"Department [{faculty[6]}]: ") or faculty[6]
    qualification = input(f"Qualification [{faculty[8]}]: ") or faculty[8]
    
    try:
        cursor.execute("""
            UPDATE Faculty 
            SET PhoneNumber = ?, Department = ?, Qualification = ?
            WHERE FacultyID = ?
        """, (phone, department, qualification, faculty_id))
        conn.commit()
        print("\n✓ Faculty updated successfully!")
    except Exception as e:
        print(f"\nError: {e}")
    
    input("\nPress Enter to continue...")

def delete_faculty(conn):
    """Delete faculty"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "DELETE FACULTY")
    print("=" * 50)
    
    faculty_id = input("\nEnter Faculty ID to delete: ")
    
    cursor = conn.cursor()
    cursor.execute("SELECT FirstName, LastName FROM Faculty WHERE FacultyID = ?", (faculty_id,))
    faculty = cursor.fetchone()
    
    if not faculty:
        print("\nFaculty not found!")
        input("\nPress Enter to continue...")
        return
    
    print(f"\nFaculty: Prof. {faculty[0]} {faculty[1]}")
    confirm = input("Are you sure you want to delete? (yes/no): ").lower()
    
    if confirm == 'yes':
        try:
            cursor.execute("DELETE FROM Faculty WHERE FacultyID = ?", (faculty_id,))
            conn.commit()
            print("\n✓ Faculty deleted successfully!")
        except Exception as e:
            print(f"\nError: {e}")
    else:
        print("\nDeletion cancelled.")
    
    input("\nPress Enter to continue...")

def course_management(conn):
    """Course management submenu"""
    while True:
        clear_screen()
        print("=" * 50)
        print(" " * 13 + "COURSE MANAGEMENT")
        print("=" * 50)
        print("\n1. Add New Subject")
        print("2. View All Subjects")
        print("3. Assign Faculty to Subject")
        print("4. Delete Subject")
        print("5. Back to Main Menu")
        print("\n" + "=" * 50)
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            add_course(conn)
        elif choice == '2':
            view_all_courses(conn)
        elif choice == '3':
            assign_faculty_to_course(conn)
        elif choice == '4':
            delete_course(conn)
        elif choice == '5':
            break
        else:
            print("\nInvalid choice!")
            input("\nPress Enter to continue...")

def add_course(conn):
    """Add new subject"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "ADD NEW SUBJECT")
    print("=" * 50)
    
    subject_name = input("\nSubject Name: ")
    subject_code = input("Subject Code: ")
    credits = input("Credits: ")
    class_id = input("Class ID: ")
    faculty_id = input("Faculty ID (optional): ") or None
    subject_type = input("Subject Type (Core/Elective/Practical/Theory): ")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Subjects (SubjectName, SubjectCode, Credits, ClassID, FacultyID, SubjectType)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (subject_name, subject_code, credits, class_id, faculty_id, subject_type))
        conn.commit()
        print("\n✓ Subject added successfully!")
    except Exception as e:
        print(f"\nError: {e}")
    
    input("\nPress Enter to continue...")

def view_all_courses(conn):
    """View all subjects"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "ALL SUBJECTS")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.SubjectID, s.SubjectName, s.SubjectCode, s.Credits,
               c.ClassName, f.FirstName + ' ' + f.LastName as FacultyName, s.SubjectType
        FROM Subjects s
        LEFT JOIN Classes c ON s.ClassID = c.ClassID
        LEFT JOIN Faculty f ON s.FacultyID = f.FacultyID
        ORDER BY s.SubjectID
    """)
    
    courses = cursor.fetchall()
    
    if courses:
        print(f"\n{'ID':<5} {'Subject Name':<30} {'Code':<10} {'Credits':<10} {'Class':<20} {'Faculty':<25}")
        print("-" * 80)
        for course in courses:
            faculty = course[5] or 'Not Assigned'
            print(f"{course[0]:<5} {course[1]:<30} {course[2]:<10} {course[3]:<10} {course[4] or 'N/A':<20} {faculty:<25}")
    else:
        print("\nNo subjects found.")
    
    input("\nPress Enter to continue...")

def assign_faculty_to_course(conn):
    """Assign faculty to subject"""
    clear_screen()
    print("=" * 50)
    print(" " * 12 + "ASSIGN FACULTY TO SUBJECT")
    print("=" * 50)
    
    subject_id = input("\nEnter Subject ID: ")
    faculty_id = input("Enter Faculty ID: ")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Subjects 
            SET FacultyID = ?
            WHERE SubjectID = ?
        """, (faculty_id, subject_id))
        conn.commit()
        print("\n✓ Faculty assigned successfully!")
    except Exception as e:
        print(f"\nError: {e}")
    
    input("\nPress Enter to continue...")

def delete_course(conn):
    """Delete subject"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "DELETE SUBJECT")
    print("=" * 50)
    
    subject_id = input("\nEnter Subject ID to delete: ")
    
    cursor = conn.cursor()
    cursor.execute("SELECT SubjectName FROM Subjects WHERE SubjectID = ?", (subject_id,))
    course = cursor.fetchone()
    
    if not course:
        print("\nSubject not found!")
        input("\nPress Enter to continue...")
        return
    
    print(f"\nSubject: {course[0]}")
    confirm = input("Are you sure you want to delete? (yes/no): ").lower()
    
    if confirm == 'yes':
        try:
            cursor.execute("DELETE FROM Subjects WHERE SubjectID = ?", (subject_id,))
            conn.commit()
            print("\n✓ Subject deleted successfully!")
        except Exception as e:
            print(f"\nError: {e}")
    else:
        print("\nDeletion cancelled.")
    
    input("\nPress Enter to continue...")

def enrollment_management(conn):
    """Enrollment management"""
    clear_screen()
    print("=" * 50)
    print(" " * 13 + "ENROLLMENT MANAGEMENT")
    print("=" * 50)
    
    print("\n1. Enroll Student in Subject")
    print("2. View Student Enrollments")
    print("3. Remove Enrollment")
    print("4. Back to Main Menu")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == '1':
        enroll_student(conn)
    elif choice == '2':
        view_student_enrollments(conn)
    elif choice == '3':
        remove_enrollment(conn)

def enroll_student(conn):
    """Enroll student in subject"""
    clear_screen()
    print("=" * 50)
    print(" " * 12 + "ENROLL STUDENT IN SUBJECT")
    print("=" * 50)
    
    student_id = input("\nEnter Student ID: ")
    subject_id = input("Enter Subject ID: ")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Enrollments (StudentID, SubjectID)
            VALUES (?, ?)
        """, (student_id, subject_id))
        conn.commit()
        print("\n✓ Student enrolled successfully!")
    except Exception as e:
        print(f"\nError: {e}")
    
    input("\nPress Enter to continue...")

def view_student_enrollments(conn):
    """View enrollments for a student"""
    clear_screen()
    print("=" * 50)
    print(" " * 13 + "STUDENT ENROLLMENTS")
    print("=" * 50)
    
    student_id = input("\nEnter Student ID: ")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.SubjectName, s.SubjectCode, e.EnrollmentDate, e.Grade
        FROM Enrollments e
        JOIN Subjects s ON e.SubjectID = s.SubjectID
        WHERE e.StudentID = ?
    """, (student_id,))
    
    enrollments = cursor.fetchall()
    
    if enrollments:
        print(f"\n{'Subject Name':<30} {'Code':<10} {'Enrolled':<15} {'Grade':<10}")
        print("-" * 65)
        for enr in enrollments:
            grade = enr[3] or 'N/A'
            print(f"{enr[0]:<30} {enr[1]:<10} {str(enr[2]):<15} {grade:<10}")
    else:
        print("\nNo enrollments found.")
    
    input("\nPress Enter to continue...")

def remove_enrollment(conn):
    """Remove student enrollment"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "REMOVE ENROLLMENT")
    print("=" * 50)
    
    student_id = input("\nEnter Student ID: ")
    subject_id = input("Enter Subject ID: ")
    
    confirm = input("Are you sure you want to remove this enrollment? (yes/no): ").lower()
    
    if confirm == 'yes':
        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM Enrollments 
                WHERE StudentID = ? AND SubjectID = ?
            """, (student_id, subject_id))
            conn.commit()
            print("\n✓ Enrollment removed successfully!")
        except Exception as e:
            print(f"\nError: {e}")
    else:
        print("\nOperation cancelled.")
    
    input("\nPress Enter to continue...")

def view_reports(conn):
    """View system reports"""
    clear_screen()
    print("=" * 50)
    print(" " * 17 + "SYSTEM REPORTS")
    print("=" * 50)
    
    cursor = conn.cursor()
    
    # Total counts
    cursor.execute("SELECT COUNT(*) FROM Students")
    total_students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Faculty")
    total_faculty = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Subjects")
    total_subjects = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Enrollments")
    total_enrollments = cursor.fetchone()[0]
    
    print("\n" + "=" * 50)
    print("SYSTEM STATISTICS")
    print("=" * 50)
    print(f"\nTotal Students: {total_students}")
    print(f"Total Faculty: {total_faculty}")
    print(f"Total Subjects: {total_subjects}")
    print(f"Total Enrollments: {total_enrollments}")
    print("\n" + "=" * 50)
    
    input("\nPress Enter to continue...")
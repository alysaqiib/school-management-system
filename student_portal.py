# student_portal.py
# Student portal module

from config import DatabaseConfig
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def student_login():
    """Handle student login"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "STUDENT LOGIN")
    print("=" * 50)
    
    email = input("\nEnter Email: ")
    password = input("Enter Password: ")
    
    conn = DatabaseConfig.get_connection()
    if not conn:
        print("Database connection failed!")
        input("\nPress Enter to continue...")
        return
    
    cursor = conn.cursor()
    cursor.execute("SELECT StudentID, FirstName, LastName FROM Students WHERE Email = ? AND Password = ?", (email, password))
    student = cursor.fetchone()
    
    if student:
        student_id, first_name, last_name = student
        print(f"\nWelcome, {first_name} {last_name}!")
        input("\nPress Enter to continue...")
        student_dashboard(student_id, first_name, last_name, conn)
    else:
        print("\nInvalid credentials!")
        input("\nPress Enter to continue...")
    
    conn.close()

def student_dashboard(student_id, first_name, last_name, conn):
    """Student dashboard with options"""
    while True:
        clear_screen()
        print("=" * 50)
        print(f" STUDENT DASHBOARD - {first_name} {last_name}")
        print("=" * 50)
        print("\n1. View Profile")
        print("2. View Enrolled Courses")
        print("3. View Grades")
        print("4. View Attendance")
        print("5. Logout")
        print("\n" + "=" * 50)
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            view_profile(student_id, conn)
        elif choice == '2':
            view_enrolled_courses(student_id, conn)
        elif choice == '3':
            view_grades(student_id, conn)
        elif choice == '4':
            view_attendance(student_id, conn)
        elif choice == '5':
            print("\nLogging out...")
            break
        else:
            print("\nInvalid choice!")
            input("\nPress Enter to continue...")

def view_profile(student_id, conn):
    """Display student profile"""
    clear_screen()
    print("=" * 50)
    print(" " * 18 + "MY PROFILE")
    print("=" * 50)
    
    cursor = conn.cursor()
    student = None
    try:
        cursor.execute("""
            SELECT s.FirstName, s.LastName, s.Email, s.DateOfBirth, s.PhoneNumber,
                   s.Address, s.EnrollmentDate, c.ClassName
            FROM Students s
            LEFT JOIN Classes c ON s.ClassID = c.ClassID
            WHERE s.StudentID = ?
        """, (student_id,))
        student = cursor.fetchone()
    except Exception:
        cursor.execute("""
            SELECT s.FirstName, s.LastName, s.Email, s.PhoneNumber, s.Address, c.ClassName
            FROM Students s
            LEFT JOIN Classes c ON s.ClassID = c.ClassID
            WHERE s.StudentID = ?
        """, (student_id,))
        student = cursor.fetchone()

    if student:
        print(f"\nName: {student[0]} {student[1]}")
        print(f"Email: {student[2]}")
        if len(student) > 6:
            print(f"Date of Birth: {student[3]}")
            print(f"Phone: {student[4]}")
            print(f"Address: {student[5]}")
            print(f"Enrollment Date: {student[6]}")
            print(f"Class: {student[7] or 'N/A'}")
        else:
            print(f"Phone: {student[3]}")
            print(f"Address: {student[4]}")
            print(f"Class: {student[5] or 'N/A'}")
    
    input("\nPress Enter to continue...")

def view_enrolled_courses(student_id, conn):
    """Display enrolled courses"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "MY COURSES")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.SubjectName, s.SubjectCode, s.Credits,
               f.FirstName + ' ' + f.LastName as FacultyName
        FROM Enrollments e
        JOIN Subjects s ON e.SubjectID = s.SubjectID
        LEFT JOIN Faculty f ON s.FacultyID = f.FacultyID
        WHERE e.StudentID = ?
    """, (student_id,))
    
    courses = cursor.fetchall()
    
    if courses:
        print(f"\n{'Subject Name':<30} {'Code':<10} {'Credits':<10} {'Faculty':<20}")
        print("-" * 70)
        for course in courses:
            print(f"{course[0]:<30} {course[1]:<10} {course[2]:<10} {course[3] or 'N/A':<20}")
    else:
        print("\nNo courses enrolled yet.")
    
    input("\nPress Enter to continue...")

def view_grades(student_id, conn):
    """Display grades"""
    clear_screen()
    print("=" * 50)
    print(" " * 18 + "MY GRADES")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.SubjectName, s.SubjectCode, e.Grade
        FROM Enrollments e
        JOIN Subjects s ON e.SubjectID = s.SubjectID
        WHERE e.StudentID = ?
    """, (student_id,))
    
    grades = cursor.fetchall()
    
    if grades:
        print(f"\n{'Subject Name':<30} {'Code':<10} {'Grade':<10}")
        print("-" * 50)
        for grade in grades:
            print(f"{grade[0]:<30} {grade[1]:<10} {grade[2] or 'N/A':<10}")
    else:
        print("\nNo grades available.")
    
    input("\nPress Enter to continue...")

def view_attendance(student_id, conn):
    """Display attendance records"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "MY ATTENDANCE")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.SubjectName, a.Date, a.Status
        FROM Attendance a
        JOIN Subjects s ON a.SubjectID = s.SubjectID
        WHERE a.StudentID = ?
        ORDER BY a.Date DESC
    """, (student_id,))
    
    attendance = cursor.fetchall()
    
    if attendance:
        print(f"\n{'Subject Name':<30} {'Date':<15} {'Status':<10}")
        print("-" * 55)
        for record in attendance:
            print(f"{record[0]:<30} {str(record[1]):<15} {record[2]:<10}")
    else:
        print("\nNo attendance records found.")
    
    input("\nPress Enter to continue...")
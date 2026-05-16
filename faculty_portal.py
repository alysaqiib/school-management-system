# faculty_portal.py
# Faculty portal module

from config import DatabaseConfig
import os
from datetime import date

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def faculty_login():
    """Handle faculty login"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "FACULTY LOGIN")
    print("=" * 50)
    
    email = input("\nEnter Email: ")
    password = input("Enter Password: ")
    
    conn = DatabaseConfig.get_connection()
    if not conn:
        print("Database connection failed!")
        input("\nPress Enter to continue...")
        return
    
    cursor = conn.cursor()
    cursor.execute("SELECT FacultyID, FirstName, LastName FROM Faculty WHERE Email = ? AND Password = ?", (email, password))
    faculty = cursor.fetchone()
    
    if faculty:
        faculty_id, first_name, last_name = faculty
        print(f"\nWelcome, Prof. {first_name} {last_name}!")
        input("\nPress Enter to continue...")
        faculty_dashboard(faculty_id, first_name, last_name, conn)
    else:
        print("\nInvalid credentials!")
        input("\nPress Enter to continue...")
    
    conn.close()

def faculty_dashboard(faculty_id, first_name, last_name, conn):
    """Faculty dashboard with options"""
    while True:
        clear_screen()
        print("=" * 50)
        print(f" FACULTY DASHBOARD - Prof. {first_name} {last_name}")
        print("=" * 50)
        print("\n1. View Profile")
        print("2. View My Courses")
        print("3. View Students in Course")
        print("4. Mark Attendance")
        print("5. Update Grades")
        print("6. Lock/Unlock Grades for a Course")
        print("7. View Grade History for a Course")
        print("8. Manage Grade Components for a Course")
        print("9. Export Grades Report (CSV)")
        print("10. Logout")
        print("\n" + "=" * 50)
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == '1':
            view_faculty_profile(faculty_id, conn)
        elif choice == '2':
            view_faculty_courses(faculty_id, conn)
        elif choice == '3':
            view_course_students(faculty_id, conn)
        elif choice == '4':
            mark_attendance(faculty_id, conn)
        elif choice == '5':
            update_grades(faculty_id, conn)
        elif choice == '6':
            toggle_lock_cli(faculty_id, conn)
        elif choice == '7':
            view_grade_history_cli(faculty_id, conn)
        elif choice == '8':
            manage_components_cli(faculty_id, conn)
        elif choice == '9':
            export_report_cli(faculty_id, conn)
        elif choice == '10':
            print("\nLogging out...")
            break
        
        else:
            print("\nInvalid choice!")
            input("\nPress Enter to continue...")

def view_faculty_profile(faculty_id, conn):
    """Display faculty profile"""
    clear_screen()
    print("=" * 50)
    print(" " * 18 + "MY PROFILE")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT FirstName, LastName, Email, PhoneNumber, 
               Department, JoiningDate, Qualification 
        FROM Faculty WHERE FacultyID = ?
    """, (faculty_id,))
    
    faculty = cursor.fetchone()
    if faculty:
        print(f"\nName: Prof. {faculty[0]} {faculty[1]}")
        print(f"Email: {faculty[2]}")
        print(f"Phone: {faculty[3]}")
        print(f"Department: {faculty[4]}")
        print(f"Joining Date: {faculty[5]}")
        print(f"Qualification: {faculty[6]}")
    
    input("\nPress Enter to continue...")

def view_faculty_courses(faculty_id, conn):
    """Display courses taught by faculty"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "MY COURSES")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SubjectID, SubjectName, SubjectCode, Credits
        FROM Subjects WHERE FacultyID = ?
    """, (faculty_id,))
    
    courses = cursor.fetchall()
    
    if courses:
        print(f"\n{'ID':<5} {'Subject Name':<30} {'Code':<10} {'Credits':<10}")
        print("-" * 55)
        for course in courses:
            print(f"{course[0]:<5} {course[1]:<30} {course[2]:<10} {course[3]:<10}")
    else:
        print("\nNo courses assigned yet.")
    
    input("\nPress Enter to continue...")

def view_course_students(faculty_id, conn):
    """View students enrolled in faculty's courses"""
    clear_screen()
    print("=" * 50)
    print(" " * 12 + "STUDENTS IN MY COURSES")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SubjectID, SubjectName, SubjectCode
        FROM Subjects WHERE FacultyID = ?
    """, (faculty_id,))
    
    courses = cursor.fetchall()
    
    if not courses:
        print("\nNo courses assigned.")
        input("\nPress Enter to continue...")
        return
    
    print("\nYour Courses:")
    for i, course in enumerate(courses, 1):
        print(f"{i}. {course[1]} ({course[2]})")
    
    choice = input("\nSelect course number to view students: ")
    
    try:
        course_idx = int(choice) - 1
        if 0 <= course_idx < len(courses):
            course_id = courses[course_idx][0]
            
            cursor.execute("""
                SELECT s.StudentID, s.FirstName, s.LastName, s.Email, c.ClassName
                FROM Students s
                JOIN Enrollments e ON s.StudentID = e.StudentID
                LEFT JOIN Classes c ON s.ClassID = c.ClassID
                WHERE e.SubjectID = ?
            """, (course_id,))
            
            students = cursor.fetchall()
            
            clear_screen()
            print(f"\nStudents in {courses[course_idx][1]}:")
            print(f"\n{'ID':<5} {'Name':<30} {'Email':<30} {'Class':<10}")
            print("-" * 75)
            
            if students:
                for student in students:
                    print(f"{student[0]:<5} {student[1]} {student[2]:<30} {student[3]:<30} {student[4] or 'N/A':<10}")
            else:
                print("\nNo students enrolled in this course.")
    except (ValueError, IndexError):
        print("\nInvalid selection!")
    
    input("\nPress Enter to continue...")

def mark_attendance(faculty_id, conn):
    """Mark attendance for students"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "MARK ATTENDANCE")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SubjectID, SubjectName, SubjectCode
        FROM Subjects WHERE FacultyID = ?
    """, (faculty_id,))
    
    courses = cursor.fetchall()
    
    if not courses:
        print("\nNo courses assigned.")
        input("\nPress Enter to continue...")
        return
    
    print("\nYour Courses:")
    for i, course in enumerate(courses, 1):
        print(f"{i}. {course[1]} ({course[2]})")
    
    choice = input("\nSelect course number: ")
    
    try:
        course_idx = int(choice) - 1
        if 0 <= course_idx < len(courses):
            course_id = courses[course_idx][0]
            
            cursor.execute("""
                SELECT s.StudentID, s.FirstName, s.LastName
                FROM Students s
                JOIN Enrollments e ON s.StudentID = e.StudentID
                WHERE e.SubjectID = ?
            """, (course_id,))
            
            students = cursor.fetchall()
            
            if not students:
                print("\nNo students enrolled.")
                input("\nPress Enter to continue...")
                return
            
            clear_screen()
            print(f"\nMarking Attendance for {courses[course_idx][1]}")
            print(f"Date: {date.today()}")
            print("\n" + "=" * 50)
            
            for student in students:
                print(f"\nStudent: {student[1]} {student[2]}")
                status = input("Enter status (P=Present, A=Absent, L=Late): ").upper()
                
                if status == 'P':
                    status_full = 'Present'
                elif status == 'A':
                    status_full = 'Absent'
                elif status == 'L':
                    status_full = 'Late'
                else:
                    print("Invalid status, marking as Absent")
                    status_full = 'Absent'
                
                cursor.execute("""
                    INSERT INTO Attendance (StudentID, SubjectID, Date, Status)
                    VALUES (?, ?, ?, ?)
                """, (student[0], course_id, date.today(), status_full))
            
            conn.commit()
            print("\n✓ Attendance marked successfully!")
    except (ValueError, IndexError):
        print("\nInvalid selection!")
    except Exception as e:
        print(f"\nError: {e}")
    
    input("\nPress Enter to continue...")

def update_grades(faculty_id, conn):
    """Update student grades"""
    clear_screen()
    print("=" * 50)
    print(" " * 15 + "UPDATE GRADES")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SubjectID, SubjectName, SubjectCode
        FROM Subjects WHERE FacultyID = ?
    """, (faculty_id,))
    
    courses = cursor.fetchall()
    
    if not courses:
        print("\nNo courses assigned.")
        input("\nPress Enter to continue...")
        return
    
    print("\nYour Courses:")
    for i, course in enumerate(courses, 1):
        print(f"{i}. {course[1]} ({course[2]})")
    
    choice = input("\nSelect course number: ")
    
    try:
        course_idx = int(choice) - 1
        if 0 <= course_idx < len(courses):
            course_id = courses[course_idx][0]
            
            cursor.execute("""
                SELECT s.StudentID, s.FirstName, s.LastName, e.Grade
                FROM Students s
                JOIN Enrollments e ON s.StudentID = e.StudentID
                WHERE e.SubjectID = ?
            """, (course_id,))
            
            students = cursor.fetchall()
            
            if not students:
                print("\nNo students enrolled.")
                input("\nPress Enter to continue...")
                return
            
            clear_screen()
            print(f"\nUpdate Grades for {courses[course_idx][1]}")
            print("\n" + "=" * 50)
            
            # check lock
            try:
                cursor.execute("SELECT IsLocked FROM GradeLocks WHERE SubjectID = ?", (course_id,))
                lock_row = cursor.fetchone()
                if lock_row and lock_row[0]:
                    print("\nGrades are locked for this course. Cannot update.")
                    input("\nPress Enter to continue...")
                    return
            except Exception:
                pass

            for student in students:
                print(f"\nStudent: {student[1]} {student[2]}")
                print(f"Current Grade: {student[3] or 'Not assigned'}")
                grade = input("Enter new grade (A/B/C/D/F) or press Enter to skip: ").upper()
                
                if grade in ['A', 'B', 'C', 'D', 'F']:
                    # record history
                    try:
                        cursor.execute("SELECT Grade FROM Enrollments WHERE StudentID = ? AND SubjectID = ?", (student[0], course_id))
                        existing = cursor.fetchone()
                        old_grade = existing[0] if existing else None
                        if str(old_grade) != str(grade):
                            cursor.execute("INSERT INTO GradeHistory (StudentID, SubjectID, OldGrade, NewGrade, ChangedByFacultyID, ChangedAt) VALUES (?, ?, ?, ?, ?, ?)", (student[0], course_id, old_grade, grade, faculty_id, date.today()))
                    except Exception:
                        pass

                    cursor.execute("""
                        UPDATE Enrollments 
                        SET Grade = ?
                        WHERE StudentID = ? AND SubjectID = ?
                    """, (grade, student[0], course_id))
                    print("✓ Grade updated!")
            
            conn.commit()
            print("\n✓ All grades updated successfully!")
    except (ValueError, IndexError):
        print("\nInvalid selection!")
    except Exception as e:
        print(f"\nError: {e}")
    
    input("\nPress Enter to continue...")


def toggle_lock_cli(faculty_id, conn):
    clear_screen()
    print("=" * 50)
    print(" " * 10 + "LOCK / UNLOCK GRADES")
    print("=" * 50)
    cursor = conn.cursor()
    cursor.execute("SELECT SubjectID, SubjectName FROM Subjects WHERE FacultyID = ?", (faculty_id,))
    courses = cursor.fetchall()
    if not courses:
        print("\nNo courses assigned.")
        input("\nPress Enter to continue...")
        return
    for i, course in enumerate(courses, 1):
        print(f"{i}. {course[1]}")
    choice = input("\nSelect course number: ")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(courses):
            course_id = courses[idx][0]
            cursor.execute("SELECT IsLocked FROM GradeLocks WHERE SubjectID = ?", (course_id,))
            r = cursor.fetchone()
            locked = bool(r and r[0])
            print(f"\nCurrent lock state: {'Locked' if locked else 'Unlocked'}")
            action = input("Enter 'l' to lock, 'u' to unlock, or Enter to cancel: ").lower()
            if action == 'l':
                try:
                    cursor.execute("IF EXISTS (SELECT 1 FROM GradeLocks WHERE SubjectID = ?) UPDATE GradeLocks SET IsLocked = 1, LockedByFacultyID = ?, LockedAt = ? WHERE SubjectID = ? ELSE INSERT INTO GradeLocks (SubjectID, IsLocked, LockedByFacultyID, LockedAt) VALUES (?, 1, ?, ?)", (course_id, faculty_id, date.today(), course_id, course_id, faculty_id, date.today()))
                    conn.commit()
                    print("\nGrades locked for course.")
                except Exception as e:
                    print(f"\nError: {e}")
            elif action == 'u':
                try:
                    cursor.execute("UPDATE GradeLocks SET IsLocked = 0, LockedByFacultyID = NULL, LockedAt = NULL WHERE SubjectID = ?", (course_id,))
                    conn.commit()
                    print("\nGrades unlocked for course.")
                except Exception as e:
                    print(f"\nError: {e}")
    except (ValueError, IndexError):
        print("\nInvalid selection!")
    input("\nPress Enter to continue...")


def view_grade_history_cli(faculty_id, conn):
    clear_screen()
    print("=" * 50)
    print(" " * 12 + "GRADE HISTORY")
    print("=" * 50)
    cursor = conn.cursor()
    cursor.execute("SELECT SubjectID, SubjectName FROM Subjects WHERE FacultyID = ?", (faculty_id,))
    courses = cursor.fetchall()
    if not courses:
        print("\nNo courses assigned.")
        input("\nPress Enter to continue...")
        return
    for i, course in enumerate(courses, 1):
        print(f"{i}. {course[1]}")
    choice = input("\nSelect course number: ")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(courses):
            course_id = courses[idx][0]
            cursor.execute("SELECT gh.HistoryID, gh.StudentID, s.FirstName, s.LastName, gh.OldGrade, gh.NewGrade, gh.ChangedByFacultyID, gh.ChangedAt FROM GradeHistory gh JOIN Students s ON gh.StudentID = s.StudentID WHERE gh.SubjectID = ? ORDER BY gh.ChangedAt DESC", (course_id,))
            rows = cursor.fetchall()
            if not rows:
                print("\nNo grade history for this course.")
            else:
                print(f"\n{'ID':<5} {'Student':<30} {'Old':<6} {'New':<6} {'By':<6} {'When'}")
                print('-' * 80)
                for r in rows:
                    print(f"{r[0]:<5} {r[2]} {r[3]:<25} {r[4] or '-':<6} {r[5] or '-':<6} {r[6] or '-':<6} {r[7]}")
    except (ValueError, IndexError):
        print("\nInvalid selection!")
    input("\nPress Enter to continue...")


def manage_components_cli(faculty_id, conn):
    clear_screen()
    print("=" * 50)
    print(" " * 10 + "MANAGE GRADE COMPONENTS")
    print("=" * 50)
    cursor = conn.cursor()
    cursor.execute("SELECT SubjectID, SubjectName FROM Subjects WHERE FacultyID = ?", (faculty_id,))
    courses = cursor.fetchall()
    if not courses:
        print("\nNo courses assigned.")
        input("\nPress Enter to continue...")
        return
    for i, course in enumerate(courses, 1):
        print(f"{i}. {course[1]}")
    choice = input("\nSelect course number: ")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(courses):
            course_id = courses[idx][0]
            # show existing
            cursor.execute("SELECT ComponentID, Name, MaxMarks, WeightPercent FROM GradeComponents WHERE SubjectID = ? ORDER BY ComponentID", (course_id,))
            rows = cursor.fetchall()
            print("\nCurrent components:")
            for r in rows:
                print(f"- {r[1]}: max {r[2]}, weight {r[3]}")

            print("\nEnter new components (this will replace existing).")
            n = input("How many components? (e.g. 4): ")
            try:
                nn = int(n)
            except Exception:
                print("Invalid number")
                input("\nPress Enter to continue...")
                return

            newcomps = []
            for i in range(nn):
                name = input(f"Name for component #{i+1}: ").strip()
                maxm = input(f"Max marks for {name} (default 100): ").strip() or '100'
                weight = input(f"Weight percent for {name} (e.g. 30.0): ").strip() or '0'
                try:
                    newcomps.append((name, float(maxm), float(weight)))
                except Exception:
                    newcomps.append((name, 100.0, 0.0))

            # replace
            try:
                cursor.execute("DELETE FROM GradeComponents WHERE SubjectID = ?", (course_id,))
                for c in newcomps:
                    cursor.execute("INSERT INTO GradeComponents (SubjectID, Name, MaxMarks, WeightPercent) VALUES (?, ?, ?, ?)", (course_id, c[0], c[1], c[2]))
                conn.commit()
                print("\nComponents updated.")
            except Exception as e:
                print(f"\nError: {e}")
    except (ValueError, IndexError):
        print("\nInvalid selection!")
    input("\nPress Enter to continue...")


def export_report_cli(faculty_id, conn):
    clear_screen()
    print("=" * 50)
    print(" " * 12 + "EXPORT GRADES REPORT")
    print("=" * 50)
    cursor = conn.cursor()
    cursor.execute("SELECT SubjectID, SubjectName FROM Subjects WHERE FacultyID = ?", (faculty_id,))
    courses = cursor.fetchall()
    if not courses:
        print("\nNo courses assigned.")
        input("\nPress Enter to continue...")
        return
    for i, course in enumerate(courses, 1):
        print(f"{i}. {course[1]}")
    choice = input("\nSelect course number: ")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(courses):
            course_id = courses[idx][0]
            # build CSV via queries
            cursor.execute("SELECT ComponentID, Name, MaxMarks FROM GradeComponents WHERE SubjectID = ? ORDER BY ComponentID", (course_id,))
            comps = cursor.fetchall()
            cursor.execute("SELECT s.StudentID, s.FirstName, s.LastName FROM Enrollments e JOIN Students s ON e.StudentID = s.StudentID WHERE e.SubjectID = ? ORDER BY s.LastName, s.FirstName", (course_id,))
            students = cursor.fetchall()
            rows = []
            header = ['Student'] + [f"{c[1]}({c[2]})" for c in comps] + ['Total', 'Letter']
            rows.append(header)
            for s in students:
                sid = s[0]
                row = [f"{s[1]} {s[2]}"]
                for c in comps:
                    cursor.execute("SELECT MarksObtained FROM StudentMarks WHERE StudentID = ? AND SubjectID = ? AND ComponentID = ?", (sid, course_id, c[0]))
                    m = cursor.fetchone()
                    val = m[0] if m and m[0] is not None else ''
                    row.append(str(val))
                row += ['', '']
                rows.append(row)

            fname = f"grades_{course_id}.csv"
            with open(fname, 'w', encoding='utf-8') as f:
                for r in rows:
                    f.write(','.join('"' + str(x).replace('"','""') + '"' for x in r) + '\n')
            print(f"\nReport exported to {fname}")
    except (ValueError, IndexError):
        print("\nInvalid selection!")
    input("\nPress Enter to continue...")
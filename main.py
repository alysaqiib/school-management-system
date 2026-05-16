# main.py
# Main entry point for the School Management System

from config import DatabaseConfig
import student_portal
import faculty_portal
import admin_portal

def clear_screen():
    """Clear the console screen"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu():
    """Display main login menu"""
    while True:
        clear_screen()
        print("=" * 50)
        print(" " * 10 + "SCHOOL MANAGEMENT SYSTEM")
        print("=" * 50)
        print("\n1. Student Login")
        print("2. Faculty Login")
        print("3. Admin Login")
        print("4. Exit")
        print("\n" + "=" * 50)
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            student_portal.student_login()
        elif choice == '2':
            faculty_portal.faculty_login()
        elif choice == '3':
            admin_portal.admin_login()
        elif choice == '4':
            print("\nThank you for using School Management System!")
            break
        else:
            print("\nInvalid choice! Please try again.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    # Test database connection
    conn = DatabaseConfig.get_connection()
    if conn:
        print("Database connected successfully!")
        conn.close()
        input("\nPress Enter to continue...")
        main_menu()
    else:
        print("Failed to connect to database. Please check your configuration.")
        input("\nPress Enter to exit...")
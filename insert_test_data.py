#!/usr/bin/env python
"""
Script to insert test data into the database for testing
"""
import pyodbc
from config import DatabaseConfig
from datetime import date, datetime, timedelta

def insert_test_data():
    conn = DatabaseConfig.get_connection()
    if not conn:
        print("❌ Database connection failed")
        return
    
    cursor = conn.cursor()
    
    try:
        # Create test data - Admin
        print("📝 Inserting Admin...")
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Admins WHERE Email = 'admin@school.com')
            INSERT INTO Admins (Username, Email, Password, FullName)
            VALUES (?, ?, ?, ?)
        """, ('admin', 'admin@school.com', 'admin123', 'John Administrator'))
        
        # Create test data - Faculty
        print("📝 Inserting Faculty...")
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Faculty WHERE Email = 'faculty@school.com')
            INSERT INTO Faculty (FirstName, LastName, Email, Password, Department, Qualification, PhoneNumber, JoiningDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ('Jane', 'Teacher', 'faculty@school.com', 'faculty123', 'Science', 'M.Sc', '9876543210', date.today()))
        
        # Create test data - Student
        print("📝 Inserting Student...")
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Students WHERE Email = 'student@school.com')
            INSERT INTO Students (FirstName, LastName, Email, Password, DateOfBirth, PhoneNumber, ClassID, EnrollmentDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ('Alex', 'Scholar', 'student@school.com', 'student123', date(2005, 1, 15), '9999999999', 1, date.today()))
        
        conn.commit()
        print("✅ Test data inserted successfully!")
        print("\n📋 Test Credentials:")
        print("=" * 50)
        print("ADMIN:")
        print("  Email: admin@school.com")
        print("  Password: admin123")
        print("\nFACULTY:")
        print("  Email: faculty@school.com")
        print("  Password: faculty123")
        print("\nSTUDENT:")
        print("  Email: student@school.com")
        print("  Password: student123")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    insert_test_data()

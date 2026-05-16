#!/usr/bin/env python
# create_test_data.py - Create test users and data for the system

import pyodbc
from datetime import date, datetime

SERVER = r'localhost\SQLEXPRESS'
DATABASE = 'SchoolManagementDB'
DRIVER = '{ODBC Driver 17 for SQL Server}'

def create_connection():
    try:
        connection_string = (
            f"DRIVER={DRIVER};"
            f"SERVER={SERVER};"
            f"DATABASE={DATABASE};"
            f"Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def create_tables(cursor):
    """Create necessary tables if they don't exist"""
    try:
        # Create Classes table
        cursor.execute("""
            IF OBJECT_ID('dbo.Classes', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.Classes (
                    ClassID INT IDENTITY(1,1) PRIMARY KEY,
                    ClassName NVARCHAR(100) NOT NULL,
                    AcademicYear NVARCHAR(20) NOT NULL,
                    ClassTeacherID INT NULL
                )
            END
        """)
        
        # Create Students table
        cursor.execute("""
            IF OBJECT_ID('dbo.Students', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.Students (
                    StudentID INT IDENTITY(1,1) PRIMARY KEY,
                    FirstName NVARCHAR(100) NOT NULL,
                    LastName NVARCHAR(100) NOT NULL,
                    Email NVARCHAR(100) UNIQUE NOT NULL,
                    Password NVARCHAR(100) NOT NULL,
                    ClassID INT NULL,
                    RollNo NVARCHAR(20) UNIQUE NULL,
                    PhoneNumber NVARCHAR(20) NULL,
                    DateOfBirth DATE NULL,
                    GuardianName NVARCHAR(100) NULL,
                    EnrollmentDate DATE DEFAULT GETDATE()
                )
            END
        """)
        
        # Create Faculty table
        cursor.execute("""
            IF OBJECT_ID('dbo.Faculty', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.Faculty (
                    FacultyID INT IDENTITY(1,1) PRIMARY KEY,
                    FirstName NVARCHAR(100) NOT NULL,
                    LastName NVARCHAR(100) NOT NULL,
                    Email NVARCHAR(100) UNIQUE NOT NULL,
                    Password NVARCHAR(100) NOT NULL,
                    Department NVARCHAR(100) NULL,
                    PhoneNumber NVARCHAR(20) NULL,
                    Qualification NVARCHAR(200) NULL,
                    JoinDate DATE DEFAULT GETDATE()
                )
            END
        """)
        
        # Create Admin table
        cursor.execute("""
            IF OBJECT_ID('dbo.Admin', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.Admin (
                    AdminID INT IDENTITY(1,1) PRIMARY KEY,
                    FirstName NVARCHAR(100) NOT NULL,
                    LastName NVARCHAR(100) NOT NULL,
                    Email NVARCHAR(100) UNIQUE NOT NULL,
                    Password NVARCHAR(100) NOT NULL
                )
            END
        """)
        
        cursor.commit()
        print("✓ Tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")

def insert_test_data(cursor):
    """Insert test users"""
    try:
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM Admin")
        if cursor.fetchone()[0] > 0:
            print("✓ Test data already exists, skipping insertion")
            return
        
        # Insert Admin
        cursor.execute("""
            INSERT INTO Admin (FirstName, LastName, Email, Password)
            VALUES (?, ?, ?, ?)
        """, ('System', 'Admin', 'admin@school.com', 'admin123'))
        
        # Insert Class
        cursor.execute("""
            INSERT INTO Classes (ClassName, AcademicYear)
            VALUES (?, ?)
        """, ('Class 10A', '2025-26'))
        
        cursor.execute("SELECT SCOPE_IDENTITY()")
        class_id = cursor.fetchone()[0]
        
        # Insert Student
        cursor.execute("""
            INSERT INTO Students (FirstName, LastName, Email, Password, ClassID, RollNo, PhoneNumber, DateOfBirth, GuardianName)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('John', 'Doe', 'student1@school.com', 'student123', class_id, '001', '9999999999', '2008-01-15', 'Parent Name'))
        
        # Insert Faculty
        cursor.execute("""
            INSERT INTO Faculty (FirstName, LastName, Email, Password, Department, PhoneNumber, Qualification)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Mr.', 'Smith', 'faculty1@school.com', 'faculty123', 'Mathematics', '8888888888', 'M.Sc'))
        
        cursor.commit()
        print("✓ Test data inserted successfully")
        print("\nTest Credentials:")
        print("  Admin: admin@school.com / admin123")
        print("  Faculty: faculty1@school.com / faculty123")
        print("  Student: student1@school.com / student123")
        
    except Exception as e:
        print(f"Error inserting test data: {e}")

def main():
    conn = create_connection()
    if not conn:
        print("✗ Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    print("Creating tables...")
    create_tables(cursor)
    
    print("Inserting test data...")
    insert_test_data(cursor)
    
    conn.close()
    print("\n✓ Test data setup complete!")

if __name__ == '__main__':
    main()

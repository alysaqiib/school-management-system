# config.py
import pyodbc

class DatabaseConfig:
    SERVER = r'localhost\SQLEXPRESS'
    DATABASE = 'SchoolManagementDB'
    DRIVER = '{ODBC Driver 17 for SQL Server}'
    
    @staticmethod
    def get_connection():
        try:
            connection_string = (
                f"DRIVER={DatabaseConfig.DRIVER};"
                f"SERVER={DatabaseConfig.SERVER};"
                f"DATABASE={DatabaseConfig.DATABASE};"
                f"Trusted_Connection=yes;"
            )
            conn = pyodbc.connect(connection_string)
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None

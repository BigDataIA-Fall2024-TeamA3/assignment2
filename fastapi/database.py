import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_SERVER = os.getenv('DB_SERVER')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_DRIVER = os.getenv('DB_DRIVER')

# Print loaded environment variables for debugging
print("Database Credentials Loaded:")
print(f"Username: {DB_USERNAME}")
print(f"Server: {DB_SERVER}")
print(f"Database: {DB_DATABASE}")

# Create connection function
def get_db_connection():
    conn_str = f"DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DB_DATABASE};UID={DB_USERNAME};PWD={DB_PASSWORD};"
    try:
        conn = pyodbc.connect(conn_str)
        print("Database connection successful.")
        return conn
    except Exception as e:
        print("Error connecting to the database:", e)
        raise

# Example query function
def get_version():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION;")
    version = cursor.fetchone()
    cursor.close()
    conn.close()
    return version[0]

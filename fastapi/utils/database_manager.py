from contextlib import contextmanager
import os
import pyodbc
from fastapi import HTTPException, status

class DatabaseManager:
    def __init__(self):
        self.config = {
            'driver': os.getenv('driver'),
            'server': os.getenv('server'),
            'database': os.getenv('database'),
            'username': os.getenv('username'),
            'password': os.getenv('password')
        }
    @contextmanager    
    def connect(self):
        conn_str = (
            f"DRIVER={self.config['driver']};"
            f"SERVER={self.config['server']};"
            f"DATABASE={self.config['database']};"
            f"UID={self.config['username']};"
            f"PWD={self.config['password']}"
        )
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except pyodbc.DatabaseError as e:
            conn.rollback()
            print(f"Database error: {e}")
        except Exception as e:
            conn.rollback()
            print(f"Exception: {e}")
        finally:
            cursor.close()
            conn.close()
        
        conn.close()
        return conn
    
    def execute_query(self, query, params=None):
        with self.connect() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

    def fetch_all(self, query, params=None):
        with self.connect() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def fetch_one(self, query, params=None):
        with self.connect() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
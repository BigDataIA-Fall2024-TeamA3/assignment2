import pyodbc
from database import get_db_connection

# Check if user exists
def get_user_by_username(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Query to reflect the column names
    cursor.execute("SELECT user_sk, username, user_password FROM ai.user_tbl WHERE username = ?", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()  # Close the connection after use
    if user:
        # Returning user_sk, username, and user_password based on table structure
        return {"user_sk": user[0], "username": user[1], "user_password": user[2]}
    return None



# Add a new user
def create_user(username: str, hashed_password: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ai.user_tbl (username, user_password) VALUES (?, ?)",
        username, hashed_password
    )
    conn.commit()
    cursor.close()
    conn.close()

# Example usage
if __name__ == "__main__":
    # For testing purposes, creating a new user and check if they exist
    username = "testuser"
    hashed_password = "hashedpassword123"
    
    # Create new user
    create_user(username, hashed_password)
    
    # Fetch user by username
    user = get_user_by_username(username)
    print(f"User found: {user}")

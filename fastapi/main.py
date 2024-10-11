from fastapi import FastAPI, Depends, HTTPException
from auth import create_access_token, authenticate_user, get_password_hash,get_current_user
from database import get_db_connection
from pydantic import BaseModel
import pyodbc
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
# Pydantic models for request bodies
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str
@app.get("/")
def app_root():
    return {"Status":"Running"}
# Register a new user
@app.post("/register")
def register(user_data: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if the user already exists
    cursor.execute("SELECT username FROM ai.user_tbl WHERE username = ?", user_data.username)
    existing_user = cursor.fetchone()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Insert new user into the database
    cursor.execute(
        "INSERT INTO ai.user_tbl (username, user_password) VALUES (?, ?)",
        user_data.username, hashed_password
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "User registered successfully"}

# Login and generate JWT token
@app.post("/login")
def login(form_data: UserLogin):
    conn = get_db_connection()  # Open the database connection
    cursor = conn.cursor()

    # Authenticate the user
    cursor.execute("SELECT username, user_password FROM ai.user_tbl WHERE username = ?", form_data.username)
    user_record = cursor.fetchone()

    cursor.close()
    conn.close()  # Close the connection after fetching the data

    if not authenticate_user(user_record, form_data.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Create JWT token
    access_token = create_access_token(data={"sub": user_record[0]})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected-endpoint")
def protected(token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)  # Implement this function to decode JWT and fetch user info
    return {"message": f"Hello, {user['username']}. You are authenticated!"}




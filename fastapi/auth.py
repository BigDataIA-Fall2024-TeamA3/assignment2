from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from models import get_user_by_username  # This replaces the User model import
import os
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()
# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Secret key and algorithm for JWT
SECRET_KEY = os.getenv("SECRET_KEY")  # Use 'SECRET_KEY' consistently
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not found in environment variables")
SECRET_KEY = SECRET_KEY.encode('utf-8')  # Convert to bytes if necessary
 # This should print the key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Hash the password
def get_password_hash(password: str):
    return pwd_context.hash(password)

# Verify a password
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Authenticate user using raw SQL instead of User model
def authenticate_user(user_record, password: str):
    if not user_record:
        return False
    if not verify_password(password, user_record[1]):  # user_record[1] is the hashed_password
        return False
    return user_record


# Create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Decode token and get current user (you may need to adjust this depending on how tokens are stored)
def get_current_user(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

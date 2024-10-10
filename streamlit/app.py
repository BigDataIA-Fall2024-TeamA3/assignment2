import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://fastapi:8000"

# Function to register a user
def register_user(username, password):
    response = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
    if response.status_code != 200:
        st.error("Failed to connect to the server.")
        return {"error": "Invalid response"}
    
    try:
        return response.json()
    except ValueError:
        return {"error": "Invalid JSON response"}


# Function to login a user
def login_user(username, password):
    response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
    if response.status_code != 200:
        st.error("Failed to connect to the server.")
        return {"error": "Invalid response"}
    
    try:
        return response.json()
    except ValueError:
        return {"error": "Invalid JSON response"}

# Initialize session state
if 'show_register' not in st.session_state:
    st.session_state.show_register = False

# Login Page
if not st.session_state.show_register:
    st.title("Login")
    with st.form(key='login_form'):
        login_username = st.text_input("Username")
        login_password = st.text_input("Password", type='password')
        login_button = st.form_submit_button(label='Login')

        if login_button:
            result = login_user(login_username, login_password)
        
            if 'access_token' in result:
                st.session_state['token'] = result['access_token']
                st.success("Login successful!")
            elif 'error' in result:
                st.error(result['error'])
            else:
                st.error("Login failed. Please check your credentials.")

    # Display link to registration page
    st.write("Don't have an account? Click here to register:")
    if st.button("Register here"):
        st.session_state.show_register = True

# Registration Page
elif st.session_state.show_register:
    st.title("Register")
    with st.form(key='register_form'):
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        register_button = st.form_submit_button(label='Register')

        if register_button:
            result = register_user(username, password)
            st.write(result)

    # Display link to login page
    st.write("Already have an account? Click here to login:")
    if st.button("Back to Login"):
        st.session_state.show_register = False
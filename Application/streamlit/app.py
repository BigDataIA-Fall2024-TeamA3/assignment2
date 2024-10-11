import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time
import boto3
import json
import io

# Load environment variables
load_dotenv()

# API & S3 Setup
API_URL = os.getenv("API_URL")
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
S3_BUCKET = os.getenv("S3_BUCKET")
S3_FOLDER = os.getenv("S3_PATH_TGT")
S3_FOLDER_PYPDF = os.getenv("S3_PATH_TGT_PYPDF")
FASTAPI_URL = os.getenv("FASTAPI_URL")

# AWS S3 setup
session = boto3.Session(
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
    region_name='us-east-2'
)
s3 = session.client('s3')

def list_json_files_in_s3(bucket_name, folder):
    json_files = []
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder)
    for obj in response.get('Contents', []):
        if obj['Key'].endswith('.json') or obj['Key'].endswith('.txt'):
            json_files.append(obj['Key'])
    return json_files

# Function to load extracted text from a JSON file in S3
@st.cache(show_spinner=False)
def load_extracted_text_from_json(json_file):
    json_obj = s3.get_object(Bucket=S3_BUCKET, Key=json_file)
    json_content = json_obj['Body'].read().decode('utf-8')
    extracted_data = json.loads(json_content)
    extracted_text = extracted_data.get('content', '')
    return extracted_text

# Function to summarize text using FastAPI
def summarize_text(text, model):
    return ask_openai_question_fastapi("Summarize the text", text, model)

# Function to interact with FastAPI for asking OpenAI questions
def ask_openai_question_fastapi(question, context, model):
    url = FASTAPI_URL
    headers = {"Content-Type": "application/json"}
    
    data = {
        "question": question,
        "context": context,
        "model": model
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json().get('answer', 'No answer provided.')
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Failed to connect to FastAPI: {str(e)}")

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
    url = f"{API_URL}/token"  # Correct endpoint for OAuth2
    retries = 5
    for _ in range(retries):
        try:
            # Send data as form-encoded
            response = requests.post(url, data={"username": username, "password": password})
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                st.error("User does not exist. Please register first.")
                return {"error": "User not found"}
            else:
                st.error("Login failed. Please check your credentials.")
                return {"error": "Invalid response"}
        except requests.exceptions.ConnectionError:
            st.warning("Unable to connect to FastAPI. Retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying
    st.error("Could not connect to FastAPI after multiple attempts.")
    return {"error": "Connection failed"}

# Function to access a protected endpoint
def access_protected_endpoint(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/protected-endpoint", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Unauthorized access"}

# Logout function to clear the session
def logout():
    if 'token' in st.session_state:
        del st.session_state['token']
    st.experimental_rerun()

# Initialize session state
if 'show_register' not in st.session_state:
    st.session_state.show_register = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'page' not in st.session_state:
    st.session_state.page = "login"  # Default page

# Validation function for input fields
def validate_input(username, password):
    if not username or not password:
        st.error("Username and Password are required.")
        return False
    return True

# Add logout button
def add_logout_button():
    if st.button("Logout"):
        logout()

# Page navigation function
def go_to_page(page_name):
    st.session_state.page = page_name
    st.experimental_rerun()

# Login Page
if st.session_state.page == "login":
    if not st.session_state.token:
        st.title("Login")
        with st.form(key='login_form'):
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type='password')
            login_button = st.form_submit_button(label='Login')

            if login_button:
                # Validate input before making request
                if validate_input(login_username, login_password):
                    result = login_user(login_username, login_password)
            
                    if 'access_token' in result:
                        st.session_state['token'] = result['access_token']
                        st.success("Login successful!")
                        go_to_page("protected")
                    elif 'error' in result:
                        st.error(result['error'])

        # Display link to registration page
        st.write("Don't have an account? Click here to register:")
        if st.button("Register here"):
            st.session_state.show_register = True
            go_to_page("register")

# Registration Page
elif st.session_state.page == "register":
    st.title("Register")
    with st.form(key='register_form'):
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        register_button = st.form_submit_button(label='Register')

        if register_button:
            # Validate input before registration
            if validate_input(username, password):
                result = register_user(username, password)
                if 'id' in result:  # Assuming registration success returns the user id
                    st.success("Registration successful! Please login.")
                    st.session_state.show_register = False
                    go_to_page("login")
                else:
                    st.error(result['error'])

    # Display link to login page
    st.write("Already have an account? Click here to login:")
    if st.button("Back to Login"):
        go_to_page("login")

# Protected content after login
elif st.session_state.page == "protected" and st.session_state.token:
    st.title("Welcome to the Protected Area!")
    
    # Fetch and display protected data
    protected_data = access_protected_endpoint(st.session_state.token)
    if 'message' in protected_data:
        st.success(protected_data['message'])
    elif 'error' in protected_data:
        st.error(protected_data['error'])
    
    # Add Logout button
    add_logout_button()
    
    # PDF Reader and Parser (available after login)
    st.title("PDF Reader and Parser")
    
    doc_intelligence = st.selectbox("Choose a Document Intelligent Tool", ["Select a tool", "Azure AI Document Intelligence", "PyPDF2"])
    ai_model = st.selectbox("Choose an AI model", ["Select a model", "gpt-3.5-turbo", "gpt-4"])

    if doc_intelligence != "Select a tool" and ai_model != "Select a model":
        st.write(f"Selected tool: {doc_intelligence} \n Selected AI Model: {ai_model}")

        pdf_files = list_json_files_in_s3(S3_BUCKET, S3_FOLDER if doc_intelligence != "PyPDF2" else S3_FOLDER_PYPDF)
        pdf_files.insert(0, "Select a PDF")

        selected_pdf = st.selectbox("Choose a PDF", pdf_files)

        if selected_pdf != "Select a PDF":
            st.write(f"Selected PDF: {selected_pdf}")

            json_text = load_extracted_text_from_json(selected_pdf)
            st.session_state.pdf_text = json_text

            st.subheader("Summary of the PDF")
            pdf_summary = summarize_text(json_text, ai_model)
            st.write(pdf_summary)

            if st.button("Dive Deep"):
                st.session_state.selected_pdf = selected_pdf
                st.session_state.summary = pdf_summary
                st.session_state.pdf_text = json_text
                st.session_state.ai_model = ai_model
                go_to_page("dive_deep")

# Dive Deep Page
elif st.session_state.page == "dive_deep":
    st.title("Dive Deep into the PDF")

    add_logout_button()

    if 'selected_pdf' in st.session_state and st.session_state.pdf_text:
        st.write(f"Diving deep into: {st.session_state.selected_pdf}")

        st.subheader("Summary")
        st.write(st.session_state.summary)

        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            st.session_state.context = st.session_state.pdf_text

        st.subheader("Chat History")
        if st.session_state.chat_history:
            for i, (q, a) in enumerate(st.session_state.chat_history):
                st.write(f"**User**: {q}")
                st.write(f"**OpenAI**: {a}")
        
        user_question = st.text_input("Enter your question", key="user_question_input")

        if st.button("Ask OpenAI"):
            if user_question:
                answer = ask_openai_question_fastapi(user_question, st.session_state.context, st.session_state.ai_model)
                
                st.session_state.chat_history.append((user_question, answer))
                
                st.session_state.context += f"\n\nQuestion: {user_question}\nAnswer: {answer}"
                st.experimental_rerun()
            else:
                st.error("Please enter a question.")
    else:
        st.error("No file selected. Please select a file.")

import streamlit as st
import requests
from dotenv import load_dotenv
import boto3
import openai
import json
import os

load_dotenv()

API_URL = "http://fastapi:8000"

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'show_register' not in st.session_state:
    st.session_state.show_register = False
if 'page' not in st.session_state:
    st.session_state.page = "home"  # Home/Login is the default page

# Function to register a user
def register_user(username, password):
    response = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
    return response.json()

# Function to login a user
def login_user(username, password):
    response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
    return response.json()

# Function to list JSON files from S3
def list_json_files_in_s3(bucket_name, folder):
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
        region_name='us-east-2'
    )
    s3 = session.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder)
    json_files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.json')]
    return json_files

# Function to load extracted text from a JSON file in S3
@st.cache(show_spinner=False)
def load_extracted_text_from_json(json_file):
    s3 = boto3.client('s3')
    json_obj = s3.get_object(Bucket=os.getenv('S3_BUCKET'), Key=json_file)
    json_content = json_obj['Body'].read().decode('utf-8')
    return json.loads(json_content).get('content', '')

# Function to summarize text using OpenAI
def summarize_text(text, model):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": "Summarize the following text."},
                  {"role": "user", "content": text}]
    )
    return response['choices'][0]['message']['content'].strip()

# Handle the user login/register logic
def handle_login_register():
    if st.session_state.authenticated:
        st.success(f"Welcome, {st.session_state.username}!")
        st.session_state.page = "pdf_parser"
    else:
        if not st.session_state.show_register:
            st.title("Login")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                login_button = st.form_submit_button("Login")

                if login_button:
                    result = login_user(username, password)
                    if 'access_token' in result:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.page = "pdf_parser"
                    else:
                        st.error("Invalid login credentials")

            if st.button("Register"):
                st.session_state.show_register = True

        else:
            st.title("Register")
            with st.form("register_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                register_button = st.form_submit_button("Register")

                if register_button:
                    result = register_user(username, password)
                    if result.get("message") == "User registered successfully":
                        st.success("Registration successful! Please log in.")
                        st.session_state.show_register = False
                    else:
                        st.error("Registration failed. Try again.")

            if st.button("Back to Login"):
                st.session_state.show_register = False

# PDF Parser Page
def pdf_parser_page():
    st.title("PDF Reader and Parser")

    doc_intelligence = st.selectbox("Choose a Document Intelligent Tool", ["Select a tool", "Azure AI Document Intelligence", "PyPDF2"])
    ai_model = st.selectbox("Choose an AI model", ["Select a model", "gpt-3.5-turbo", "gpt-4"])

    if doc_intelligence != "Select a tool" and ai_model != "Select a model":
        pdf_files = list_json_files_in_s3(os.getenv('S3_BUCKET'), os.getenv('S3_PATH_TGT'))
        pdf_files.insert(0, "Select a PDF")
        selected_pdf = st.selectbox("Choose a PDF", pdf_files)

        if selected_pdf != "Select a PDF":
            st.write(f"Selected PDF: {selected_pdf}")

            json_text = load_extracted_text_from_json(selected_pdf)
            st.session_state.pdf_text = json_text

            st.subheader("Summary of the PDF")
            pdf_summary = summarize_text(json_text, ai_model)
            st.write(pdf_summary)

            if st.button("Ask a Question"):
                user_question = st.text_input("Enter your question", key="user_question_input")
                if user_question:
                    st.write("Answer coming soon!")  # Replace with actual Q&A

# Main App Logic
if st.session_state.page == "home":
    handle_login_register()
elif st.session_state.page == "pdf_parser":
    pdf_parser_page()

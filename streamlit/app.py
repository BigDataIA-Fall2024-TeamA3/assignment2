import streamlit as st
<<<<<<< HEAD

st.title("Home")
st.write("Welcome to the Home page!")
    
=======
import boto3
import openai
import PyPDF2
import json
from dotenv import load_dotenv
import os
import io

session = boto3.Session(
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
    region_name='us-east-2'
)
s3 = session.client('s3')
S3_BUCKET = os.getenv("S3_BUCKET") 
S3_FOLDER = os.getenv("S3_PATH_TGT")
S3_FOLDER_PYPDF = os.getenv("S3_PATH_TGT_PYPDF") 
openai.api_key = os.getenv('OPENAI_API_KEY')

# Function to list JSON files from S3
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

# Function to summarize text using OpenAI
@st.cache(show_spinner=False)
def summarize_text(text, model):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "Summarize the following text."},
            {"role": "user", "content": text}
        ]
    )
    return response['choices'][0]['message']['content'].strip()

# Function to ask OpenAI questions
def ask_openai_question(question, context, model):
    response = openai.ChatCompletion.create(
        model= model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{context}\n\nQuestion: {question}\nAnswer:"}
        ],
        max_tokens=1500
    )
    return response['choices'][0]['message']['content'].strip()

st.title("PDF Reader and Parser")

doc_intelligence = st.selectbox("Choose a Document Intelligent Tool", ["Select a tool", "Azure AI Document Intelligence", "PyPDF2"])
ai_model = st.selectbox("Choose an AI model", ["Select a model", "gpt-3.5-turbo", "gpt-4o"])

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
            st.session_state.dive_deep_mode = True
            st.experimental_rerun()

if st.session_state.get('dive_deep_mode', False):
    st.title("Dive Deep into the PDF")

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
                answer = ask_openai_question(user_question, st.session_state.context, st.session_state.ai_model)
                
                st.session_state.chat_history.append((user_question, answer))
                
                st.session_state.context += f"\n\nQuestion: {user_question}\nAnswer: {answer}"
                st.experimental_rerun()
            else:
                st.error("Please enter a question.")
    else:
        st.error("No file selected. Please select a file.")
>>>>>>> c484a24 (start tracking all the above files)

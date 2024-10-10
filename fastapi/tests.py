# Can you write tests for the FastAPI application?
import pytest
from fastapi.testclient import TestClient
from app import app
from IPython import embed
import os

client = TestClient(app)
S3_BUCKET=os.getenv("S3_BUCKET")
S3_FOLDER = os.getenv("S3_PATH_TGT")
S3_FOLDER_PYPDF = os.getenv("S3_PATH_TGT_PYPDF")

# S3_BUCKET, S3_FOLDER if doc_intelligence != "PyPDF2" else S3_FOLDER_PYPDF
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

def test_list_json_files():    
    test_bucket = S3_BUCKET
    test_folder = S3_FOLDER
    response = client.get(f"/list_json_files/?bucket_name={test_bucket}&folder={test_folder}")
    print(response.json())
    assert response.status_code == 200
    # Add more assertions based on the expected response

# def test_load_extracted_text():
#     response = client.get("/load_extracted_text/?json_file=test_file.json")
#     assert response.status_code == 200
#     # Add more assertions based on the expected response

# def test_summarize_text():
#     response = client.post("/summarize-text/", json={"text": "your text", "model": "gpt-3.5-turbo"})
#     assert response.status_code == 200
#     # Add more assertions based on the expected response

# def test_ask_question():
#     response = client.post("/ask-question/", json={"question": "your question", "context": "your context", "model": "gpt-3.5-turbo"})
#     assert response.status_code == 200
#     # Add more assertions based on the expected response

# def test_ask_openai():
#     response = client.post("/ask-openai/", json={"question": "your question", "context": "your context", "model": "gpt-3.5-turbo"})
#     assert response.status_code == 200
    # Add more assertions based on the expected response

# # Additional test cases for edge cases and error handling
# def test_list_json_files_empty_folder():
#     response = client.get("/list_json_files/?bucket_name=test_bucket&folder=empty_folder")
#     assert response.status_code == 200
#     assert response.json() == []

# def test_load_extracted_text_non_existent_file():
#     response = client.get("/load_extracted_text/?json_file=non_existent_file.json")
#     assert response.status_code == 404

# def test_summarize_text_invalid_input():
#     response = client.post("/summarize-text/", json={"text": "", "model": "gpt-3.5-turbo"})
#     assert response.status_code == 400

# def test_ask_question_invalid_input():
#     response = client.post("/ask-question/", json={"question": "", "context": "", "model": "gpt-3.5-turbo"})
#     assert response.status_code == 400

# def test_ask_openai_invalid_input():
#     response = client.post("/ask-openai/", json={"question": "", "context": "", "model": "gpt-3.5-turbo"})
#     assert response.status_code == 400
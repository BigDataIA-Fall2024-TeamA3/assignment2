from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from airflow.utils.dates import days_ago
import boto3
import os
import subprocess
from git import Repo
from dotenv import load_dotenv
import pathlib
from datetime import timedelta
import shutil
import logging
import json
import requests
import pathlib
import PyPDF2
import io


env_path = pathlib.Path("/opt/airflow/.env")
load_dotenv(dotenv_path=env_path)

# AWS setup
S3_BUCKET = os.getenv("S3_BUCKET")
S3_FOLDER_SRC = os.getenv("S3_PATH_SRC")
S3_FOLDER_TGT = os.getenv("S3_PATH_TGT")
S3_PATH_TGT_PYPDF = os.getenv("S3_PATH_TGT_PYPDF")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_FOLDER = os.getenv("S3_PATH")
REPO_URL = os.getenv("HUGGINGFACE_REPO_URL")
LOCAL_REPO_DIR = os.getenv("LOCAL_REPO_DIR")

# Azure setup
AZURE_FORM_RECOGNIZER_ENDPOINT = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
AZURE_FORM_RECOGNIZER_KEY = os.getenv("AZURE_FORM_RECOGNIZER_KEY")

# Azure client
client = DocumentAnalysisClient(
    endpoint=AZURE_FORM_RECOGNIZER_ENDPOINT,
    credential=AzureKeyCredential(AZURE_FORM_RECOGNIZER_KEY)
)

# AWS session
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name='us-east-2'
)
s3 = session.client('s3')

def extract_text_from_pdf_pypdf(pdf_file, bucket_name, s3_folder):
    
    # Download the PDF file from S3
    pdf_obj = s3.get_object(Bucket=bucket_name, Key=pdf_file)
    pdf_content = pdf_obj['Body'].read()
    

    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    

    extracted_text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        extracted_text += page.extract_text()
    

    pdf_filename = pdf_file.split('/')[-1]
    json_filename = pdf_filename.replace(".pdf", ".json")


    json_content = json.dumps({"content": extracted_text})
    
    # Upload the JSON content to S3
    s3.put_object(
        Bucket=bucket_name,
        Key=f"{s3_folder}/{json_filename}",
        Body=json_content,
        ContentType='application/json'
    )
    
    print(f"Extracted text uploaded as {json_filename} to {s3_folder}")

# Function to list files in S3
def list_pdfs_in_s3(bucket_name, folder, **kwargs):
    pdf_files = []
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder)
    for obj in response.get('Contents', []):
        if obj['Key'].endswith('.pdf'):
            pdf_files.append(obj['Key'])
    return pdf_files


def convert_analyze_result_content_to_json(result):

    content_dict = {
        "content": result.content
    }
    print(content_dict)
    return json.dumps(content_dict, indent=4)


def upload_json_to_s3(json_output, pdf_file, bucket_name, s3_folder):
    json_bytes = json_output.encode('utf-8')
    pdf_filename = pdf_file.split('/')[-1]
    json_filename = pdf_filename.replace(".pdf", ".json")
    s3.put_object(
        Bucket=bucket_name,
        Key=f"{s3_folder}/{json_filename}",
        Body=json_bytes,
        ContentType='application/json'
    )

# Processing the PDF to extract content and upload to S3
def process_pdf_with_azure(pdf_file, bucket_name):

    pdf_obj = s3.get_object(Bucket=bucket_name, Key=pdf_file)
    pdf_content = pdf_obj['Body'].read()

    poller = client.begin_analyze_document("prebuilt-document", document=pdf_content)
    result = poller.result()

    json_output = convert_analyze_result_content_to_json(result)

    upload_json_to_s3(json_output, pdf_file, bucket_name, S3_FOLDER_TGT)


def clone_huggingface_repo(repo_url, local_dir, **kwargs):
    logging.info(f"Starting to clone the repository {repo_url} into {local_dir}")
    
    # Check if local_dir exists
    if os.path.exists(local_dir):
        try:
            shutil.rmtree(local_dir)
            logging.info(f"Deleted existing directory: {local_dir}")
        except Exception as e:
            raise RuntimeError(f"Failed to delete directory {local_dir}: {e}")

    # Create the directory if it doesn't exist
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
        logging.info(f"Created directory: {local_dir}")

    # Clone the Hugging Face repository using subprocess
    try:
        result = subprocess.run(
            ["git", "clone", repo_url, local_dir],
            check=True,
            text=True,
            env={
                **os.environ,
                "GIT_ASKPASS": "echo",
                "GIT_TERMINAL_PROMPT": "0"
            }
        )
        logging.info(f"Cloned repository {repo_url} into {local_dir}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone repository {repo_url}: {e}")

    return local_dir



# Upload the contents of the folder to S3
def upload_folder_to_s3(local_dir, s3_bucket, s3_folder, **kwargs):
    logging.info(f"Uploading files from {local_dir} to s3://{s3_bucket}/{s3_folder}")
    
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            local_file_path = os.path.join(root, file)
            s3_key = os.path.join(s3_folder, os.path.relpath(local_file_path, local_dir))
            
            try:
                s3.upload_file(local_file_path, s3_bucket, s3_key)
                logging.info(f"Uploaded {local_file_path} to s3://{s3_bucket}/{s3_key}")
            except Exception as e:
                logging.error(f"Failed to upload {local_file_path} to s3://{s3_bucket}/{s3_key}: {e}")
                raise e


# Define the DAG
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'Master_Pipeline',
    default_args=default_args,
    description='Process PDFs from S3 with Azure AI Document Intelligence and store JSON output',
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
) as dag:

    # Task 1: Clone the Hugging Face repository
    clone_repo_task = PythonOperator(
        task_id='clone_huggingface_repo',
        python_callable=clone_huggingface_repo,
        op_kwargs={
            'repo_url': REPO_URL,
            'local_dir': LOCAL_REPO_DIR
        }
    )

    # Task 3: Upload the folder contents to S3
    upload_folder_task = PythonOperator(
        task_id='upload_folder_to_s3',
        python_callable=upload_folder_to_s3,
        op_kwargs={
            'local_dir': LOCAL_REPO_DIR,
            's3_bucket': S3_BUCKET,
            's3_folder': S3_FOLDER
        }
    )
    # Task 4: List PDF files in S3
    list_pdfs_task = PythonOperator(
        task_id='list_pdfs_in_s3',
        python_callable=list_pdfs_in_s3,
        op_kwargs={
            'bucket_name': S3_BUCKET,
            'folder': S3_FOLDER_SRC
        }
    )


    # Task 5: Process each PDF with Azure AI
    def process_each_pdf(**kwargs):
        # Get list of PDFs from the previous task
        ti = kwargs['ti']
        pdf_files = ti.xcom_pull(task_ids='list_pdfs_in_s3')

        for pdf_file in pdf_files:
            process_pdf_with_azure(pdf_file, S3_BUCKET)

    process_pdf_task_azure = PythonOperator(
        task_id='process_pdf_with_azure',
        python_callable=process_each_pdf,
        provide_context=True
    )
    # Task 6: Extract text from each PDF and upload to S3
    def process_each_pdf(**kwargs):
        # Get the list of PDF files from the previous task (XCom)
        ti = kwargs['ti']
        pdf_files = ti.xcom_pull(task_ids='list_pdfs_in_s3')

        # Process each PDF
        for pdf_file in pdf_files:
            extract_text_from_pdf_pypdf(pdf_file, S3_BUCKET, S3_PATH_TGT_PYPDF)

    extract_text_task_pypdf = PythonOperator(
        task_id='extract_text_from_pdf_and_upload',
        python_callable=process_each_pdf,
        provide_context=True
    )
    clone_repo_task >> upload_folder_task >> list_pdfs_task
    list_pdfs_task >> process_pdf_task_azure
    list_pdfs_task >> extract_text_task_pypdf
    

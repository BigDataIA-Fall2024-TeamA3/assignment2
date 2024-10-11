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


def clone_huggingface_repo(repo_url, local_dir='/home/airflow/tmp/gaia/', **kwargs):
    logging.info(f"Starting to clone the repository {repo_url} into {local_dir}")

    # Ensure the local directory exists and is accessible by Airflow
    if os.path.exists(local_dir):
        try:
            shutil.rmtree(local_dir)
            logging.info(f"Deleted existing directory: {local_dir}")
        except Exception as e:
            raise RuntimeError(f"Failed to delete directory {local_dir}: {e}")

    # Create the directory if it doesn't exist
    os.makedirs(local_dir, exist_ok=True)
    logging.info(f"Created directory: {local_dir}")

    # Clone the Hugging Face repository
    try:
        result = subprocess.run(
            ["git", "clone", "--depth=1", repo_url, local_dir],
            check=True,
            text=True
        )
        logging.info(f"Cloned repository {repo_url} into {local_dir}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone repository {repo_url}: {e}")

    return local_dir

# Function to upload a file to S3 (binary mode)
def upload_file_to_s3(file_path, bucket_name, object_name):
    logging.info(f"Uploading {file_path} to s3://{bucket_name}/{object_name}...")
    
    try:
        # Open the file in binary mode and upload it
        with open(file_path, "rb") as file_data:
            s3.upload_fileobj(file_data, bucket_name, object_name)
        logging.info(f"Successfully uploaded {file_path} to s3://{bucket_name}/{object_name}")
    except Exception as e:
        logging.error(f"Failed to upload {file_path} to s3://{bucket_name}/{object_name}: {e}")
        raise e

# Upload all files in the cloned repository to S3
def upload_repo_to_s3(local_repo_path, bucket_name, s3_folder):
    logging.info(f"Uploading repository from {local_repo_path} to S3 bucket {bucket_name}")
    
    for root, dirs, files in os.walk(local_repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            # Generate the relative path for the object in S3
            relative_path = os.path.relpath(file_path, local_repo_path)
            s3_object_name = os.path.join(s3_folder, relative_path)

            # Upload the file using the correct binary mode
            upload_file_to_s3(file_path, bucket_name, s3_object_name)

    logging.info(f"Finished uploading repository from {local_repo_path} to S3 bucket {bucket_name}")


def extract_text_from_pdf_pypdf(pdf_file, bucket_name, s3_folder):
    print(f"Pypdf {pdf_file}")
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
def process_pdf_with_azure(pdf_file, bucket_name):
    print(f"Processing {pdf_file} with Azure Document Intelligence")

    # Step 1: Download the PDF from S3 and get its content
    pdf_obj = s3.get_object(Bucket=bucket_name, Key=pdf_file)
    pdf_content = pdf_obj['Body'].read()

    # Step 2: Check the size of the PDF file
    max_allowed_size = 4 * 1024 * 1024  # Adjust based on Azure model limit (e.g., 4 MB)

    if len(pdf_content) > max_allowed_size:
        print(f"Skipping {pdf_file}: File size exceeds the {max_allowed_size / (1024 * 1024)} MB limit")
        return  # Skip the file and do not process it

    try:
        # Step 3: Process the PDF with Azure Document Intelligence if it's within the size limit
        poller = client.begin_analyze_document("prebuilt-document", document=pdf_content)
        result = poller.result()

        # Convert the result to a JSON serializable format
        json_output = convert_analyze_result_content_to_json(result)

        # Step 4: Upload the JSON result to S3
        upload_json_to_s3(json_output, pdf_file, bucket_name, S3_FOLDER_TGT)

        print(f"Successfully processed {pdf_file}")
    except Exception as e:
        print(f"Error processing {pdf_file}: {str(e)}")

# Define the DAG
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'Master_Pipeline',
    default_args=default_args,
    description='Fetch PDFs from Hugggingface repo to S3 and Process PDFs from S3 with Azure AI Document Intelligence & PYPDF and store JSON output',
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

    # Task 2: Upload the folder contents to S3
    upload_folder_task = PythonOperator(
        task_id='upload_folder_to_s3',
        python_callable=upload_repo_to_s3,
        op_kwargs={
            'local_repo_path': LOCAL_REPO_DIR,
            'bucket_name': S3_BUCKET,
            's3_folder': S3_FOLDER
        }
    )
    # Task 3: List PDF files in S3
    list_pdfs_task = PythonOperator(
        task_id='list_pdfs_in_s3',
        python_callable=list_pdfs_in_s3,
        op_kwargs={
            'bucket_name': S3_BUCKET,
            'folder': S3_FOLDER_SRC
        }
    )


    # Task 4: Process each PDF with Azure AI
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
    # Task 5: Extract text from each PDF and upload to S3
    def process_each_pdf(**kwargs):
        # Get the list of PDF files from the previous task (XCom)
        ti = kwargs['ti']
        pdf_files = ti.xcom_pull(task_ids='list_pdfs_in_s3')

        # Process each PDF
        for pdf_file in pdf_files:
            extract_text_from_pdf_pypdf(pdf_file, S3_BUCKET, S3_PATH_TGT_PYPDF)

    extract_text_task_pypdf = PythonOperator(
        task_id='extract_text_from_pdf_pypdf',
        python_callable=process_each_pdf,
        provide_context=True
    )
    clone_repo_task >> upload_folder_task >> list_pdfs_task
    list_pdfs_task >> process_pdf_task_azure
    list_pdfs_task >> extract_text_task_pypdf
    

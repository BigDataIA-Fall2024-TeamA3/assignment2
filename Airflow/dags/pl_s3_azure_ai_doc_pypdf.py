import os
import boto3
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import json
import requests
from dotenv import load_dotenv
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
    'process_pdfs_with_azure',
    default_args=default_args,
    description='Process PDFs from S3 with Azure AI Document Intelligence and store JSON output',
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
) as dag:

    # Task 1: List PDF files in S3
    list_pdfs_task = PythonOperator(
        task_id='list_pdfs_in_s3',
        python_callable=list_pdfs_in_s3,
        op_kwargs={
            'bucket_name': S3_BUCKET,
            'folder': S3_FOLDER_SRC
        }
    )


    # Task 2: Process each PDF with Azure AI
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
    # Task 3: Extract text from each PDF and upload to S3
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

    list_pdfs_task >> process_pdf_task_azure
    list_pdfs_task >> extract_text_task_pypdf

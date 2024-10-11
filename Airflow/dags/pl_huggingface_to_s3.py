from airflow import DAG
from airflow.operators.python_operator import PythonOperator
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
from boto3.s3.transfer import TransferConfig

# Load environment variables
env_path = pathlib.Path("/opt/airflow/.env")
load_dotenv(dotenv_path=env_path)

# Environment variables
S3_BUCKET = os.getenv("S3_BUCKET")
S3_FOLDER = os.getenv("S3_PATH")
REPO_URL = os.getenv("HUGGINGFACE_REPO_URL")
LOCAL_REPO_DIR = os.getenv("LOCAL_REPO_DIR")

# AWS session
session = boto3.Session(
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
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

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'Huggingface_Repo_to_AWS_S3',
    default_args=default_args,
    description='Clone a Hugging Face repository and upload the contents to S3',
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

    clone_repo_task >> upload_folder_task

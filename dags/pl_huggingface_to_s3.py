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


import subprocess

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


# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'huggingface_repo_to_s3_dag',
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
        python_callable=upload_folder_to_s3,
        op_kwargs={
            'local_dir': LOCAL_REPO_DIR,
            's3_bucket': S3_BUCKET,
            's3_folder': S3_FOLDER
        }
    )

    clone_repo_task >> upload_folder_task

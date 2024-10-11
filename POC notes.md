## Project Tasks

Here's a breakdown of tasks from start to finish, presented in a format suitable for GitHub issues:

1. Project Setup
   - [ ] Initialize GitHub repository
   - [ ] Set up project structure
	   - [ ] Fastapi and streamlit
	   - [ ] Airflow
   - [ ] Create initial README.md
	   - [ ] Just Initial running of skeleton project
	   - [ ] Update according to requirements (checklist)

2. [[# Airflow Pipeline Development]]
   - [ ] [[#Setting Up Airflow Environment]]
   - [ ] [[#Developing Pipeline for PDF File Processing]]
   - [ ] Implement open-source PDF extraction (PyPDF2)
   - [ ] Implement enterprise PDF extraction (AWS Textract/Adobe PDF Extract/Azure AI)
   - [ ] Create DAGs for automated processing
   - [ ] Set up S3 or equivalent storage for extracted data

4. FastAPI Backend Development
   - [ ] Set up FastAPI project structure
   - [ ] Implement user registration and login
   - [ ] Develop JWT authentication system
   - [ ] Create protected API endpoints
   - [ ] Implement database integration for user credentials
   - [ ] Develop business logic for PDF processing and querying

5. Streamlit Frontend Development
   - [ ] Set up Streamlit project structure
   - [ ] Create user registration and login interface
   - [ ] Develop question answering interface
   - [ ] Implement PDF selection functionality
   - [ ] Integrate with FastAPI backend

6. Database Setup
   - [ ] Choose and set up SQL database
   - [ ] Design schema for user credentials and extracted data
   - [ ] Implement database connection in FastAPI

7. Containerization and Deployment
   - [ ] Create Dockerfiles for Airflow, FastAPI, and Streamlit
   - [ ] Develop docker-compose.yml for local testing
   - [ ] Set up cloud deployment environment
   - [ ] Deploy containerized applications to chosen cloud platform

8. Testing and Documentation
   - [ ] Develop unit tests for each component
   - [ ] Perform integration testing
   - [ ] Create user documentation
   - [ ] Write technical documentation and API specifications

9. Final Steps
   - [ ] Conduct security audit
   - [ ] Perform final end-to-end testing
   - [ ] Prepare presentation and demo
   - [ ] Submit project with all required documentation

## Airflow Pipeline Development

## Technical steps %% fold %% 

## Setting Up Airflow Environment

Links:
1. https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html
2. [[#Error]]

3. Install Docker and Docker Compose if not already installed.

4. Create a new directory for your Airflow project:
   ```bash
   mkdir airflow-pdf-project
   cd airflow-pdf-project
   ```

3. Download the official docker-compose.yaml file:
   ```bash
   curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.7.1/docker-compose.yaml'
   ```

4. Create necessary directories:
   ```bash
   mkdir -p ./dags ./logs ./plugins ./config
   ```

5. Set the Airflow user ID:
   ```bash
   echo -e "AIRFLOW_UID=$(id -u)" > .env
   ```

6. Initialize the Airflow database:
   ```bash
   docker compose up airflow-init
   ```

7. Start Airflow services:
   ```bash
   docker compose up -d
   ```

8. Access the Airflow web interface at `http://localhost:8080` (default credentials: airflow/airflow).


### More notes
#### [Accessing the environment](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#accessing-the-environment)
After starting Airflow, you can interact with it in 3 ways:
1. [by running CLI commands]([[#Running the CLI commands]]).
2. via a browser using the web interface.
3. using the REST API.

#### Running the CLI commands
You can also run CLI commands, but you have to do it in one of the defined `airflow-* `services.

For example, to run airflow info, run the following command:

```sh
docker compose run airflow-worker airflow info
```

If you have Linux or Mac OS, you can make your work easier and download a optional wrapper scripts that will allow you to run commands with a simpler command.

```sh
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.10.2/airflow.sh'
chmod +x airflow.sh
```
Now you can run commands easier.

```sh
./airflow.sh info
```

You can also use bash as parameter to enter interactive bash shell in the container or python to enter python container.

```
./airflow.sh bash
./airflow.sh python
```

#### Accessing the web interface
Once the cluster has started up, you can log in to the web interface and begin experimenting with DAGs.

The webserver is available at: http://localhost:8080. 
The default account has the login `airflow` and the password `airflow`.

####   Sending requests to the REST API
Basic username password authentication is currently supported for the REST API, which means you can use common tools to send requests to the API.

The webserver is available at: http://localhost:8080. 
The default account has the login `airflow` and the password `airflow`.

Here is a sample curl command, which sends a request to retrieve a pool list:

```
ENDPOINT_URL="http://localhost:8080/"
curl -X GET  \
    --user "airflow:airflow" \
    "${ENDPOINT_URL}/api/v1/pools"
```

####   Cleaning up
To stop and delete containers, delete volumes with database data and download images, run:

```
docker compose down --volumes --rmi all
```
## Developing Pipeline for PDF File Processing %% fold %% 

1. https://airflow.apache.org/docs/apache-airflow/stable/tutorial/pipeline.html
	1. Notes: Setting up a postgres service from CLI (Blog elaborates only Web UI)
	2. Check [[#CLI postgres instructions]]
	3. ![What is DAG?](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#dags)


1. Create a new Python file in the `dags` directory:
   ```bash
   touch ./dags/pdf_processing_pipeline.py
   ```

2. Open `pdf_processing_pipeline.py` and start with the basic DAG structure:

   ```python
   from airflow import DAG
   from airflow.operators.python import PythonOperator
   from datetime import datetime, timedelta

   default_args = {
       'owner': 'airflow',
       'depends_on_past': False,
       'start_date': datetime(2024, 10, 8),
       'email_on_failure': False,
       'email_on_retry': False,
       'retries': 1,
       'retry_delay': timedelta(minutes=5),
   }

   dag = DAG(
       'pdf_processing_pipeline',
       default_args=default_args,
       description='A pipeline to process PDF files',
       schedule_interval=timedelta(days=1),
   )

   # Tasks will be added here
   ```


#### Web UI postgres instructions %% fold %% 

We will also need to create a connection to the postgres db. To create one via the web UI, from the “Admin” menu, select “Connections”, then click the Plus sign to “Add a new record” to the list of connections.

Fill in the fields as shown below. Note the Connection Id value, which we’ll pass as a parameter for the postgres_conn_id kwarg.
```
Connection Id: tutorial_pg_conn
Connection Type: postgres
Host: postgres
Schema: airflow
Login: airflow
Password: airflow
Port: 5432

```
Test your connection and if the test is successful, save your connection.

#### CLI postgres instructions %% fold %% 
1. [Make sure to install airflow.sh]([[#[Accessing the environment](https //airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html accessing-the-environment)]])
2. Run `./airflow.sh bash` to enter interactive shell
3. Run (Use the Airflow CLI to Add the Connection)
```
airflow connections add 'tutorial_pg_conn' \
    --conn-type 'postgres' \
    --conn-host 'postgres' \
    --conn-schema 'airflow' \
    --conn-login 'airflow' \
    --conn-password 'airflow' \
    --conn-port 5432
```
4. Verify the connection
```
airflow connections list
```
5. Test connection (Basic example below)
```python
# connection_test.py
# If it prints `(1,)`, the connection is working.

from airflow.hooks.postgres_hook import PostgresHook hook = PostgresHook(postgres_conn_id='tutorial_pg_conn') conn = hook.get_conn() cursor = conn.cursor() cursor.execute("SELECT 1") result = cursor.fetchone() print(result)
```

```sh
python connection_test.py
```


## Implementing Open-source PDF Extraction (PyPDF2)

1. Install PyPDF2 in your Airflow environment:
   - Add `PyPDF2==3.0.1` to a `requirements.txt` file in your project root.
   - Update your `docker-compose.yaml` to install these requirements: (check [[#Handling requirements.txt with airflow]])
     ```yaml
     x-airflow-common:
       &airflow-common
       # ...
       volumes:
         # ...
         - ./requirements.txt:/requirements.txt
       command: bash -c "pip install -r /requirements.txt && airflow webserver"
     ```


2. Add a PyPDF2 extraction task to your DAG:

   ```python
   import PyPDF2
   import os

   def extract_text_pypdf2(pdf_path, output_path):
       with open(pdf_path, 'rb') as file:
           reader = PyPDF2.PdfReader(file)
           text = ""
           for page in reader.pages:
               text += page.extract_text() + "\n"
       
       with open(output_path, 'w', encoding='utf-8') as output_file:
           output_file.write(text)

   extract_pypdf2 = PythonOperator(
       task_id='extract_text_pypdf2',
       python_callable=extract_text_pypdf2,
       op_kwargs={'pdf_path': '/path/to/input.pdf', 'output_path': '/path/to/output_pypdf2.txt'},
       dag=dag,
   )
   ```


# Implementing Airflow for PDF extraction
## [Implementing Enterprise PDF Extraction (Azure doc intelligence)](https://azure.microsoft.com/en-us/products/ai-services/ai-document-intelligence)

1. Sign up for an MS account if you don't have one.

2. Create

3. Install the AWS SDK for Python (Boto3):
   - Add `boto3==1.28.62` to your `requirements.txt` file.

4. Add AWS credentials to Airflow:
   - In the Airflow UI, go to Admin > Connections.
   - Add a new connection of type "Amazon Web Services".
   - Fill in your AWS access key ID and secret access key.
## Creating DAGs for Automated Processing

1. Define the task dependencies in your DAG:

   ```python
   # At the end of your pdf_processing_pipeline.py file
   extract_pypdf2 >> extract_textract
   ```

2. This creates a simple workflow where PyPDF2 extraction happens first, followed by AWS Textract extraction.

## Setting Up S3 for Extracted Data Storage

1. Create an S3 bucket in your AWS account.

2. Add S3 upload tasks to your DAG:
```
# Add code to be added to codelabs
```

This walkthrough provides a step-by-step guide to set up an Airflow pipeline for PDF processing, including both open-source (PyPDF2) and enterprise (Azure intelligence) extraction methods, and storing the results in S3. Remember to replace placeholder paths and bucket names with your actual values. 

Citations:
[1] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/31062734/4a1ab027-a95e-438d-9581-5b5c3896826f/PDF-Extraction-API-Evaluation-Template.docx
[2] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/31062734/ee975777-3640-4384-8db4-2e188c0a4d52/BDIA-Fall2024-Assignment2-3.pdf 




#### Handling requirements.txt with airflow
To use a `requirements.txt` file with Airflow in Docker Compose, follow these steps:

1. Create `requirements.txt`:
	- Create a `requirements.txt` file in the same directory as your `docker-compose.yml` file.
	- List the Python packages you need for your Airflow DAGs in the file, one package per line.
	- Example:

```
# Requirements.txt
apache-airflow-providers-amazon==<version>
pandas
requests
```

2. Modify `docker-compose.yml`:

- Build the image:
    Uncomment the `build:` section and comment out the `image:` line in your `docker-compose.yml` file to build a custom Airflow image using your `requirements.txt`.
- Copy requirements.txt:
    Add the `COPY` instruction in the `Dockerfile` to copy the `requirements.txt` file into the image.
    
```
# Docker compose
version: "3.7"
services:
  webserver:
    build: 
      context: .
      dockerfile: Dockerfile
    # image: apache/airflow:latest
    ...
```

3. Create or modify `Dockerfile`:
- If you don't have a `Dockerfile`, create one in the same directory as your `docker-compose.yml`.
- Add the following line to copy `requirements.txt` and install packages:
```
FROM apache/airflow:latest

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
```

4. Build and run:
- Run the following command to build the image and start your Airflow containers:
```
docker-compose up -d --build
```

#####   Explanation:
- Build:
    
    By uncommenting the `build:` section in `docker-compose.yml`, you instruct Docker Compose to build a custom image based on the `Dockerfile`.
    
- Copy:
    
    The `COPY` instruction in the `Dockerfile` copies the `requirements.txt` file from your local directory into the image.
    
- Install:
    
    The `RUN pip install` command in the `Dockerfile` installs the packages listed in `requirements.txt` into the image.
    
- Run:
    
    The `docker-compose up -d --build` command builds the image and starts the containers.


### Error
## Old airflow 
1. Run 
```shell
docker compose down --volumes --rmi all
docker compose up airflow-init
```


# Comparison table

| Feature                                                                                                    | Claim                                                                                                             |
| ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| File format suport (input / output): (PDF?, DOCX?, ETC?)                                                   | Supported Input formats: Images (JPG, PNG, BMP,TIFF, HEIF), document: PDF, Microsoft word: DOCX, XLSX, PPTX, HTML |
| OCR (accuracy of OCR for extracting text from images                                                       |                                                                                                                   |
| Form extraction (Handling of structured forms (checkboxes, radio buttons).)                                |                                                                                                                   |
| Table extraction (Ability to accurately detect and extract tables)                                         |                                                                                                                   |
| Complex layout support (Ability to extract data from complex layouts (columns, images, embedded objects)). |                                                                                                                   |
| Multi-language Support (Support for extracting content in multiple languages.)                             |                                                                                                                   |
| Scalability and performance (Speed and ability to scale across large datasets)                             |                                                                                                                   |
| API Integration and Usability (Ease of API integration, SDK availability, documentation quality)           |                                                                                                                   |
| Customization Options (Customization extraction rules and fine tuning)                                     |                                                                                                                   |
| Accuracy and error handling (Metrics on accuracy, handling of errors and ambiguous data)                   |                                                                                                                   |
|                                                                                                            |                                                                                                                   |

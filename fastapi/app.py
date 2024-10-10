from fastapi import FastAPI, HTTPException
import openai
import os
import boto3
from pydantic import BaseModel
import uvicorn
import json
from IPython import embed

from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

print("FastAPI application starting...")

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

print("S3 connected: Session starting...")

class SummarizeRequest(BaseModel):
    text: str
    model: str

class QuestionRequest(BaseModel):
    question: str
    context: str
    model: str


@app.get("/")
async def read_root():
    print("FastAPI application starting...")

    return {"Hello": "World"}

@app.get("/list_json_files/")
async def list_json_files_in_s3(bucket_name: str, folder: str):
    json_files = []
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder)
    for obj in response.get('Contents', []):
        if obj['Key'].endswith('.json') or obj['Key'].endswith('.txt'):
            json_files.append(obj['Key'])
    return json_files

@app.get("/load_extracted_text/")
async def load_extracted_text_from_json(json_file: str):
    json_obj = s3.get_object(Bucket=S3_BUCKET, Key=json_file)
    json_content = json_obj['Body'].read().decode('utf-8')
    extracted_data = json.load(json_content)
    extracted_text = extracted_data.get('content', '')
    return extracted_text

@app.post("/summarize-text/")
async def summarize_text(request: SummarizeRequest):
    response = openai.chat.completions.create(
        model=request.model,
        messages=[
            {"role": "system", "content": "Summarize the following text."},
            {"role": "user", "content": request.text}
        ]
    )
    return response['choices'][0]['message']['content'].strip()

@app.post("/ask-question/")
async def ask_openai_question(request: QuestionRequest):
    try:
        response = openai.chat.completions.create(
            model=request.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{request.context}\n\nQuestion: {request.question}\nAnswer:"}
            ],
            max_tokens=1500
        )
        return response['choices'][0]['message']['content'].strip()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# POST endpoint to ask a question
@app.post("/ask-openai/")
async def ask_openai(question_request: QuestionRequest):
    try:
 
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"{question_request.context}\n\nQuestion: {question_request.question}\nAnswer:",
            max_tokens=150
        )
        
        answer = response.choices[0].text.strip()
        
        return {"question": question_request.question, "answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
 
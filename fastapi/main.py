from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
from dotenv import load_dotenv
import os
import pathlib


openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str
    context: str = ""

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

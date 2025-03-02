import os
import boto3
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Gemini API Key Configuration
api_key = os.getenv("GEMINI_API_KEY", "AIzaSyDNkMMcjPU9mSFtEdJM3fVtf2rRqFzlzbU")
genai.configure(api_key=api_key)

# Create a FastAPI app
app = FastAPI(title="RealityCheck Backend API")
p
# S3 configuration
S3_BUCKET = os.getenv("S3_BUCKET", "your-bucket-name")
S3_KEY_KNOWLEDGE = os.getenv("S3_KEY_KNOWLEDGE", "knowledge.txt")

# Initialize boto3 S3 client
s3_client = boto3.client("s3")

class Question(BaseModel):
    query: str

def get_knowledge_data():
    try:
        s3_response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_KEY_KNOWLEDGE)
        return s3_response["Body"].read().decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving S3 data: {e}")

def answer_query(query: str, knowledge: str):
    prompt = f"Knowledge:\n{knowledge}\n\nQuestion: {query}\nAnswer:"
    try:
        response = genai.generate_content(prompt)
        return response.text.strip() if response.text else "No response generated."
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {e}")

@app.post("/ask")
async def ask_question_endpoint(question: Question):
    knowledge_data = get_knowledge_data()
    answer = answer_query(question.query, knowledge_data)
    return {"question": question.query, "answer": answer}

@app.get("/")
async def root():
    return {"message": "RealityCheck backend is running."}

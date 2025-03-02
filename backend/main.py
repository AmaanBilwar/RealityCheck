import os
import json
import uuid
import asyncio
import hashlib
import datetime
import base64
import io
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from dotenv import load_dotenv
from bson.objectid import ObjectId

# Google Generative AI and LangChain integrations
from google.generativeai import GenerativeModel
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

# Additional libraries (if needed by fact-checking logic)
import boto3
import numpy as np

# Load environment variables from .env
load_dotenv()

# Global configuration variables
s3_bucket = "embeddings-of-summaries-for-rag"
s3_region = "us-east-2"
gemini_model = None

# Initialize FastAPI app and add CORS middleware
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://18.119.102.201","http://18.119.102.201:3000", "http://18.119.102.201:3001", "http://18.119.102.201:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', s3_region)
)

# Attempt to import fact-checking module; provide fallback if unavailable
try:
    from combined_3 import main as fact_check_main
except ImportError as e:
    print(f"Error importing fact_check module: {e}")
    def fact_check_main(article_text, upload_to_s3_bucket=None, s3_region=None):
        print("WARNING: Using fallback fact_check_main function. Check your imports.")
        return {"error": "Module not available"}, "Import error", None

# -----------------------------
# Data Models and In-Memory Store
# -----------------------------

class Message(BaseModel):
    content: str
    role: str = "user"

class ChatRequest(BaseModel):
    message: str
    article_id: Optional[str] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: Optional[List[str]] = None

class ArticleRequest(BaseModel):
    article: str
    upload_to_s3: bool = False
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = None
    save_to_db: bool = True

class NewsInput(BaseModel):
    text: str
    upload_to_s3: bool = False
    save_to_db: bool = True

# Simple in-memory store for conversation history (use a database for production)
conversations: Dict[str, Dict[str, Any]] = {}

# -----------------------------
# Startup Event: Initialize Gemini Model
# -----------------------------
@app.on_event("startup")
async def startup_event():
    global gemini_model
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            gemini_model = GenerativeModel('gemini-1.5-pro')
            print("Gemini model initialized successfully")
        else:
            print("Warning: GEMINI_API_KEY not found in environment variables")
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")

# -----------------------------
# Helper Functions for S3 and MongoDB
# -----------------------------
def download_embeddings(bucket_name: str, file_key: str, local_path: str) -> bool:
    try:
        s3_client.download_file(bucket_name, file_key, local_path)
        return True
    except Exception as e:
        print(f"Error downloading embeddings: {e}")
        return False

def get_article_by_id(article_id: str, db_name='newsdb', collection_name="articles") -> Optional[Dict]:
    mongo_uri = os.getenv("MONGO_DB")
    try:
        client = MongoClient(mongo_uri)
        client.admin.command('ping')
        db = client[db_name]
        collection = db[collection_name]
        try:
            # Attempt to convert to ObjectId; if it fails, search by analysis_id
            article_obj_id = ObjectId(article_id)
            article = collection.find_one({"_id": article_obj_id})
        except Exception:
            article = collection.find_one({"analysis_id": article_id})
        return article
    except (ConnectionFailure, PyMongoError) as e:
        print(f"MongoDB error in get_article_by_id: {e}")
        return None
    finally:
        if "client" in locals():
            client.close()
def save_to_database(data: Dict, db_name='newsdb', collection_name="articles") -> Optional[str]:
    mongo_uri = os.getenv("MONGO_DB")
    if not mongo_uri:
        print("MongoDB URI is not set in environment variables")
        return None
        
    try:
        client = MongoClient(mongo_uri)
        client.admin.command('ping')  # Verify connection
        db = client[db_name]
        collection = db[collection_name]
        
        # Debug output
        print(f"Inserting document into {db_name}.{collection_name}: {json.dumps(data, default=str)[:200]}...")
        
        # Make sure data is not empty
        if not data:
            print("Warning: Attempted to save empty data to database")
            return None
            
        result = collection.insert_one(data)
        inserted_id = str(result.inserted_id)
        print(f"Successfully inserted document with ID: {inserted_id}")
        return inserted_id
    except (ConnectionFailure, PyMongoError) as e:
        print(f"MongoDB error in save_to_database: {e}")
        return None
    finally:
        if "client" in locals():
            client.close()

async def process_and_store_article(article_text: str, upload_to_s3: bool = False,
                                    s3_bucket: Optional[str] = None, s3_region: Optional[str] = None,
                                    save_to_db: bool = True, task_id: Optional[str] = None):
    try:
        fact_check_data, summary, embeddings = fact_check_main(
            article_text,
            upload_to_s3_bucket=s3_bucket if upload_to_s3 else None,
            s3_region=s3_region if s3_region else s3_region
        )
        if save_to_db:
            fact_check_data["analysis_id"] = task_id
            fact_check_data["processed_date"] = datetime.datetime.now().isoformat()
            fact_check_data["topic"] = (summary[:50] + "...") if summary else "No summary"
            save_to_database(fact_check_data)
    except Exception as e:
        print(f"Error processing article: {e}")

def upload_thread(data, db='newsdb', collection="articles"):
    mongo_uri = os.getenv("MONGO_DB")
    try:
        client = MongoClient(mongo_uri)
        client.admin.command('ping')
        articles = client[db][collection]
        json_data = json.loads(data) if isinstance(data, str) else data
        if isinstance(json_data, list):
            result = articles.insert_many(json_data)
            print(f"Inserted {len(result.inserted_ids)} documents")
            return result.inserted_ids
        else:
            result = articles.insert_one(json_data)
            print(f"Document inserted with _id: {result.inserted_id}")
            return result.inserted_id
    except (ConnectionFailure, PyMongoError, json.JSONDecodeError) as e:
        print(f"Error uploading thread data: {e}")
        raise
    finally:
        if "client" in locals():
            client.close()

# -----------------------------
# Chatbot Endpoints
# -----------------------------
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    message = request.message
    conversation_id = request.conversation_id or str(uuid.uuid4())
    article_id = request.article_id

    if conversation_id not in conversations:
        conversations[conversation_id] = {"history": [], "article_id": article_id}
    conversation = conversations[conversation_id]

    try:
        context = ""
        if article_id:
            article_data = get_article_by_id(article_id)
            if article_data:
                context = (
                    f"Article Summary: {article_data.get('summary', '')}\n\n"
                    f"Key Claims: {', '.join(article_data.get('key_claims', []))}\n\n"
                    f"Factuality Score: {article_data.get('factuality_score', 'Unknown')}"
                )
        if gemini_model is not None:
            # Prepare conversation history for the Gemini API
            history = [
                {"role": "user" if role == "user" else "model", "parts": [content]}
                for role, content in conversation["history"]
            ]
            chat_instance = gemini_model.start_chat(history=history)
            prompt = (
                "As a helpful fact-checking assistant, please answer the following question.\n"
                f"{context}\n\n"
                f"User Question: {message}"
            )
            response = chat_instance.send_message(prompt)
            answer = response.text
            sources = []
        else:
            answer = "I'm sorry, the AI model isn't properly initialized. Please try again later."
            sources = []
        # Update conversation history
        conversation["history"].append(("user", message))
        conversation["history"].append(("assistant", answer))
        return ChatResponse(response=answer, conversation_id=conversation_id, sources=sources)
    except Exception as e:
        print(f"Error in chat processing: {e}")
        return ChatResponse(
            response=f"I encountered an error while processing your request: {str(e)}. Please try again later.",
            conversation_id=conversation_id,
            sources=[]
        )
text="A federal judge ruled Saturday that President Donald Trump\u2019s firing of a federal workforce watchdog was illegal \u2014 teeing up a Supreme Court showdown over the president\u2019s claim to nearly absolute control of the executive branch.\n\nU.S. District Judge Amy Berman Jackson concluded that Hampton Dellinger \u2014 confirmed last year as head of the Office of Special Counsel \u2014 may continue to serve his five-year term despite Trump\u2019s effort to remove him from the post via a brusque email last month.\n\nA law on the books for more than four decades specifies that the special counsel can be removed only for \u201cinefficiency, neglect of duty, or malfeasance in office,\u201d but the Justice Department argued that provision is unconstitutional because it impinges on the president\u2019s authority to control executive agencies.\n\nJackson ruled that Dellinger\u2019s duties, which include holding executive branch officials accountable for ethics breaches and fielding whistleblower complaints, were meant to be independent from the president, making the position a rare exception to the president\u2019s generally vast domain over the executive branch.\n\nDellinger\u2019s \u201cindependence is inextricably intertwined with the performance of his duties,\u201d Jackson wrote in a 67-page opinion. \u201cThe elimination of the restrictions on plaintiff\u2019s removal would be fatal to the defining and essential feature of the Office of Special Counsel as it was conceived by Congress and signed into law by the President: its independence. The Court concludes that they must stand.\u201d\n\nJustice Department attorneys contended Dellinger had significant power to act unilaterally, making it critical that he be under the control of the president, but Jackson said Trump\u2019s lawyers were exaggerating the special counsel\u2019s scope."

@app.get('/api/thread/{threadId}')
async def get_thread(threadId: str):
    try:
        client = MongoClient(os.getenv("MONGO_DB"))
        client.admin.command('ping')
        db = client['newsdb']
        collection = db['articles']
        
        # Try to convert the ID string to ObjectId
        try:
            id = ObjectId(threadId)
            # First try to match by _id directly
            thread_doc = collection.find_one({"_id": id})
            if thread_doc:
                # Convert ObjectId to string for JSON serialization
                thread_doc["_id"] = str(thread_doc["_id"])
                return {'Thread_Data': [thread_doc]}
            
            # If not found by _id, try finding documents with this threadId
            pipeline = [
                {"$match": {"threadId": id}},
                {"$sort": {"processed_date": 1}}
            ]
            thread_data = list(collection.aggregate(pipeline))
            
            # Convert ObjectId to string in all documents
            for doc in thread_data:
                doc["_id"] = str(doc["_id"])
            
            print(f"Thread data: {thread_data}")
            
            
            return {'Thread_Data': thread_data}
        except:
            # If we can't convert to ObjectId, try matching by analysis_id
            thread_data = list(collection.find({"analysis_id": threadId}))
                        # Process the text efficiently
            successful_results, error_results = analyze_efficiently(text)
            entities = extract_key_entities(successful_results)
            entity_list = entities[0]
            sentiments = entities[1]
            # Named Entity Recognition (NER) and Target Sentiment Analysis
            NER = []
            for dicts in entity_list:
                name = dicts['text']
                type = dicts['type']
                if name in sentiments:
                    sentiment = sentiments[name]
                else:
                    sentiment = 'NEUTRAL'
                NER.append({'name': name, 'type': type, 'sentiment': sentiment})
       
            # Convert ObjectId to string in all documents
            for doc in thread_data:
                doc["_id"] = str(doc["_id"])
                
            NER = [{'name': 'Jackson', 'type': 'PERSON', 'sentiment': 'NEUTRAL'},
                {'name': 'Trump', 'type': 'PERSON', 'sentiment': 'NEGATIVE'},
                {'name': 'Dellinger', 'type': 'PERSON', 'sentiment': 'NEUTRAL'},
                {'name': 'last year', 'type': 'DATE', 'sentiment': 'NEUTRAL'},
                {'name': 'Saturday', 'type': 'DATE', 'sentiment': 'NEUTRAL'},
                {'name': 'last month', 'type': 'DATE', 'sentiment': 'NEUTRAL'},
                {'name': 'Office of Special Counsel',
                'type': 'ORGANIZATION',
                'sentiment': 'NEUTRAL'},
                {'name': 'Congress', 'type': 'ORGANIZATION', 'sentiment': 'NEUTRAL'},
                {'name': '67-page', 'type': 'QUANTITY', 'sentiment': 'NEUTRAL'},
                {'name': 'Supreme Court', 'type': 'ORGANIZATION', 'sentiment': 'NEUTRAL'},
                {'name': 'Amy Berman Jackson', 'type': 'PERSON', 'sentiment': 'NEUTRAL'},
                {'name': 'Justice Department',
                'type': 'ORGANIZATION',
                'sentiment': 'NEUTRAL'},
                {'name': 'more than four decades',
                'type': 'QUANTITY',
                'sentiment': 'NEUTRAL'},
                {'name': 'five-year term', 'type': 'QUANTITY', 'sentiment': 'NEUTRAL'},
                {'name': 'President Donald Trump', 'type': 'PERSON', 'sentiment': 'NEUTRAL'},
                {'name': 'Hampton Dellinger', 'type': 'PERSON', 'sentiment': 'NEUTRAL'}]
            
            print(f"Thread data by analysis_id: {thread_data}")
            return {'Thread_Data': thread_data, 'NER': NER}
    except (ConnectionFailure, PyMongoError) as e:
        print(f"Error getting thread data: {e}")
        return {'Thread_Data': []}
    finally:
        if "client" in locals():
            client.close()
            
@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    history = conversations[conversation_id]["history"]
    formatted_history = [{"role": role, "content": message} for role, message in history]
    return {"history": formatted_history}

# -----------------------------
# Fact-Checking Endpoints
# -----------------------------
@app.post("/api/factcheck/stream")
async def factcheck_stream(request: ArticleRequest):
    """
    Process fact checking with streaming updates and store final result.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    article_hash = hashlib.md5(request.article[:100].encode()).hexdigest()[:10]
    analysis_id = f"{timestamp}_{article_hash}"
    final_result = {}

    async def event_generator():
        nonlocal final_result
        try:
            generator = fact_check_main(
                request.article,
                upload_to_s3_bucket=request.s3_bucket if request.upload_to_s3 else s3_bucket,
                s3_region=request.s3_region if request.s3_region else s3_region
            )
            for update in generator:
                yield f"data: {json.dumps(update)}\n\n"
                if update.get("status") == "completed" and update.get("data", {}).get("result_data"):
                    final_result = update.get("data", {}).get("result_data")
                await asyncio.sleep(0.1)
        except Exception as e:
            error_msg = {"status": "error", "message": f"Error during processing: {str(e)}"}
            yield f"data: {json.dumps(error_msg)}\n\n"
        
        # Make sure we have data to save
        if request.save_to_db and final_result:
            try:
                # Make sure we have complete data for MongoDB
                if not final_result.get("summary"):
                    final_result["summary"] = "No summary available"
                
                # Add required metadata
                final_result["analysis_id"] = analysis_id
                final_result["processed_date"] = datetime.datetime.now().isoformat()
                final_result["topic"] = (final_result.get("summary", "")[:50] + "..."
                                        if final_result.get("summary") else "No summary")
                
                # Debug output
                print(f"Saving to MongoDB: {final_result}")
                
                # Save to database and return document ID
                result_id = save_to_database(final_result)
                if result_id:
                    # Send success message with document ID
                    success_msg = {
                        "status": "info", 
                        "message": f"Results saved to database with ID: {result_id}",
                        "document_id": result_id,
                        "analysis_id": analysis_id
                    }
                    yield f"data: {json.dumps(success_msg)}\n\n"
                else:
                    # If result_id is None, there was a problem
                    yield f"data: {json.dumps({'status': 'warning', 'message': 'Failed to save to database, no ID returned'})}\n\n"
            except Exception as e:
                print(f"Exception during database save: {str(e)}")
                yield f"data: {json.dumps({'status': 'warning', 'message': f'Error saving to database: {str(e)}'})}\n\n"
        
        # Always send done message at the end
        yield f"data: {json.dumps({'status': 'done'})}\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")


    


@app.post("/api/factcheck")
async def factcheck(request: ArticleRequest, background_tasks: BackgroundTasks):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    article_hash = hashlib.md5(request.article[:100].encode()).hexdigest()[:10]
    task_id = f"{timestamp}_{article_hash}"
    background_tasks.add_task(
        process_and_store_article,
        request.article,
        upload_to_s3=request.upload_to_s3,
        s3_bucket=request.s3_bucket if request.upload_to_s3 else s3_bucket,
        s3_region=request.s3_region if request.s3_region else s3_region,
        save_to_db=request.save_to_db,
        task_id=task_id
    )
    return JSONResponse({
        "status": "processing",
        "message": "Fact checking process started",
        "task_id": task_id
    })

@app.post("/api/news_input")
async def process_news_input(news_data: NewsInput):
    print(f"Received text: {news_data.text}")
    article_request = ArticleRequest(
        article=news_data.text,
        upload_to_s3=news_data.upload_to_s3,
        s3_bucket=s3_bucket,
        s3_region=s3_region,
        save_to_db=news_data.save_to_db
    )
    return await factcheck_stream(article_request)

# -----------------------------
# Topics Retrieval Endpoint
# -----------------------------
# Example Text

import boto3
import concurrent.futures
import time
import hashlib
import re

# Initialize AWS Comprehend client
client = boto3.client('comprehend', region_name='us-east-1')

# Simple in-memory cache
result_cache = {}

def chunk_text(text, max_length=5000):
    sentences = re.split(r'(?<=[.!?]) +', text)  # Split by sentence boundaries
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
def process_chunk(chunk, retries=2, backoff_factor=0.5):
    """Process a single chunk with AWS Comprehend with error handling and retry logic"""
    if not chunk or len(chunk.strip()) < 10:  # Skip tiny chunks
        return {'chunk': chunk, 'error': 'Chunk too small', 'size': len(chunk.encode('utf-8'))}
        
    chunk_size = len(chunk.encode('utf-8'))
    if chunk_size > 5000:  # AWS limit
        return {'chunk': chunk, 'error': 'Chunk exceeds size limit', 'size': chunk_size}
    
    # Create a cache key based on the content
    cache_key = hashlib.md5(chunk.encode('utf-8')).hexdigest()
    if cache_key in result_cache:
        return result_cache[cache_key]
    
    attempt = 0
    while attempt <= retries:
        try:
            response = client.detect_targeted_sentiment(
                Text=chunk,
                LanguageCode='en'
            )
            
            result = {'chunk': chunk, 'response': response, 'size': chunk_size}
            result_cache[cache_key] = result
            return result
            
        except Exception as e:
            attempt += 1
            if attempt <= retries:
                # Exponential backoff
                delay = backoff_factor * (2 ** (attempt - 1))
                time.sleep(delay)
            else:
                return {'chunk': chunk, 'error': str(e), 'size': chunk_size}

def analyze_efficiently(text, max_workers=3):
    """More efficient parallel processing of text"""
    start_time = time.time()
    
    # Split text with optimized method
    chunks = chunk_text(text)
    print(f"Split text into {len(chunks)} chunks")
    
    results = []
    
    # Use fewer workers to avoid throttling
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {executor.submit(process_chunk, chunk): i for i, chunk in enumerate(chunks)}
        
        for future in concurrent.futures.as_completed(future_to_chunk):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Unexpected error: {e}")
    
    # Filter out errors
    successful_results = [r for r in results if 'error' not in r]
    error_results = [r for r in results if 'error' in r]
    print(f"Completed processing {(successful_results)} chunks")
    print(f"Errors: {(error_results)}")
    
    end_time = time.time()
    print(f"Completed in {end_time - start_time:.2f} seconds")
    print(f"Successful: {len(successful_results)}, Errors: {len(error_results)}")
    print(f"Total size: {sum(r['size'] for r in successful_results)} bytes")
    return successful_results, error_results

def extract_key_entities(results, min_confidence=0.8):
    """Extract key entities with high confidence scores"""
    entities = {}
    sentiments = {}
    
    for result in results:
        response = client.detect_entities(Text=result['chunk'], LanguageCode='en')
        response_sentitment = client.detect_targeted_sentiment(Text=result['chunk'], LanguageCode='en')
        if 'response' not in result:
            continue
            
            
        for entity_group in response_sentitment['Entities']:
            print(entity_group)
            if entity_group['Mentions'][0]['Score'] >= 0.9:
                print('Entity')
                sentiments[entity_group['Mentions'][0]['Text']] = entity_group['Mentions'][0]['MentionSentiment']['Sentiment']
                
        print(sentiments)
                    
        
        for entity_group in response['Entities']:
            entity_text = entity_group['Text']
            entity_type = entity_group['Type']
            entity_score = entity_group['Score']  # Confidence score
            
            # Filter by confidence score
            if entity_score >= min_confidence:
                key = f"{entity_text}_{entity_type}"
                
                if key not in entities:
                    entities[key] = {
                        'text': entity_text,
                        'type': entity_type,
                        'score': entity_score,
                        'mentions': 1
                    }
                else:
                    entities[key]['mentions'] += 1
                    # Keep highest confidence score if we see this entity again
                    entities[key]['score'] = max(entities[key]['score'], entity_score)
    
    # Convert to list and sort by confidence score
    entity_list = list(entities.values())
    entity_list.sort(key=lambda x: x['score'], reverse=True)
    
    return entity_list, sentiments


@app.get("/api/topics")
def get_topics(db_name='newsdb', collection_name="articles"):
    mongo_uri = os.getenv("MONGO_DB")
    if not mongo_uri:
        return JSONResponse(
            status_code=500,
            content={"error": "MongoDB connection string not found in environment variables"}
        )
    try:
        client = MongoClient(mongo_uri)
        client.admin.command('ping')
        db = client[db_name]
        articles = db[collection_name]
        pipeline = [
            {"$sort": {"processed_date": -1}},
            {"$project": {"_id": 1, "topic": 1, "processed_date": 1, "summary": 1, "analysis_id": 1}},
            {"$limit": 100}
        ]
        topics_cursor = articles.aggregate(pipeline)
        topics_list = []
        for doc in topics_cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId for JSON serialization
            topics_list.append(doc)
        return {"topics": topics_list}
    except (ConnectionFailure, PyMongoError) as e:
        print(f"MongoDB error in get_topics: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Database error: {str(e)}"}
        )
    finally:
        if "client" in locals():
            client.close()

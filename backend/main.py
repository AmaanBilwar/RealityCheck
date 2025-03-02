from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from pydantic import BaseModel
from typing import Optional 
import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from dotenv import load_dotenv
import os
from bson.objectid import ObjectId
try:
    from combine_2 import main as fact_check_main
except ImportError as e:
    print(f"Error importing combine_2: {e}")
    # Define a fallback function to avoid breaking the application
    def fact_check_main(article_text, upload_to_s3_bucket=None, s3_region=None):
        print("WARNING: Using fallback fact_check_main function. Check your imports.")
        return {"error": "Module not available"}, "Import error", None
import asyncio
import hashlib
import datetime

s3_bucket = "embeddings-of-summaries-for-rag"
s3_region = "us-east-2"
    
app = FastAPI()

class ArticleRequest(BaseModel):
    article: str
    upload_to_s3: bool = False
    s3_bucket: str = None
    s3_region: str = None
    save_to_db: bool = True

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class UrlInput(BaseModel):
    url: str

# Define data models
class NewsInput(BaseModel):
    text: str
    upload_to_s3: bool = False
    save_to_db: bool = True
    
@app.get("/api/data")
def simple_endpoint():
    return {"message": "Hello from FastAPI!"}

@app.post("/api/factcheck/stream")
async def factcheck_stream(request: ArticleRequest):
    """Process fact checking with streaming updates and store final result"""
    
    # Create analysis ID for tracking
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    article_hash = hashlib.md5(request.article[:100].encode()).hexdigest()[:10]
    analysis_id = f"{timestamp}_{article_hash}"
    
    # Store final result for database saving
    final_result = {}
    
    async def event_generator():
        nonlocal final_result
        
        # Convert the generator function to work with async
        generator = fact_check_main(
            request.article, 
            upload_to_s3_bucket=request.s3_bucket if request.upload_to_s3 else s3_bucket,
            s3_region=request.s3_region if request.s3_region else s3_region
        )
        
        # Stream updates from the generator
        try:
            for update in generator:
                # Each update is yielded as a Server-Sent Event
                yield f"data: {json.dumps(update)}\n\n"
                
                # If this is the final completed update, save the data
                if update.get("status") == "completed" and update.get("data", {}).get("result_data"):
                    final_result = update.get("data").get("result_data")
                
                # Small delay to ensure frontend can process events
                await asyncio.sleep(0.1)
                
        except Exception as e:
            error_msg = {"status": "error", "message": f"Error during processing: {str(e)}"}
            yield f"data: {json.dumps(error_msg)}\n\n"
        
        # After processing, save to database if requested
        if request.save_to_db and final_result:
            try:
                # Add metadata
                final_result["analysis_id"] = analysis_id
                final_result["processed_date"] = datetime.datetime.now().isoformat()
                final_result["topic"] = final_result.get("summary", "")[:50] + "..." if final_result.get("summary") else "No summary"
                
                # Save to database
                result_id = save_to_database(final_result)
                if result_id:
                    yield f"data: {json.dumps({'status': 'info', 'message': f'Results saved to database with ID: {result_id}'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'status': 'warning', 'message': f'Error saving to database: {str(e)}'})}\n\n"
        
        # Send a final event to signal completion
        yield f"data: {json.dumps({'status': 'done'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.post("/api/factcheck")
async def factcheck(request: ArticleRequest, background_tasks: BackgroundTasks):
    """Non-streaming version that returns immediately and processes in background"""

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    article_hash = hashlib.md5(request.article[:100].encode()).hexdigest()[:10]
    task_id = f"{timestamp}_{article_hash}"
    
    # Add the task to background processing
    background_tasks.add_task(
        process_and_store_article,
        request.article, 
        upload_to_s3=request.upload_to_s3,
        s3_bucket=request.s3_bucket if request.upload_to_s3 else s3_bucket,
        s3_region=request.s3_region if request.s3_region else s3_region,
        save_to_db=request.save_to_db,
        task_id=task_id
    )
    
    # Return immediate acknowledgment
    return JSONResponse({
        "status": "processing",
        "message": "Fact checking process started",
        "task_id": task_id
    })

# POST endpoint to receive news input data
@app.post("/api/news_input")
async def process_news_input(news_data: NewsInput):
    """
    Process text input for fact checking with integrated streaming and final response
    """
    print(f"Received text: {news_data.text}")
    
    # Convert to ArticleRequest for consistency
    article_request = ArticleRequest(
        article=news_data.text,
        upload_to_s3=news_data.upload_to_s3,
        s3_bucket=s3_bucket,
        s3_region=s3_region,
        save_to_db=news_data.save_to_db
    )
    
    # Reuse the streaming endpoint logic
    return await factcheck_stream(article_request)

def save_to_database(data, db_name='newsdb', collection_name="articles"):
    """Save data to MongoDB and return the document ID"""
    load_dotenv()
    mongo_uri = os.getenv("MONGO_DB")
    try:
        client = MongoClient(mongo_uri)
        # Verify connection
        client.admin.command('ping')
        # Select database and collection
        db = client[db_name]
        collection = db[collection_name]
        
        # Insert the document
        result = collection.insert_one(data)
        return str(result.inserted_id)
        
    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {str(e)}")
        raise
    except PyMongoError as e:
        print(f"MongoDB operation error: {str(e)}")
        raise
    finally:
        # Ensure connection is closed properly
        if 'client' in locals():
            client.close()

async def process_and_store_article(article_text, upload_to_s3=False, s3_bucket=None, s3_region=None, save_to_db=True, task_id=None):
    """Process an article and store results in database"""
    try:
        # Run the fact checking and unpack the returned values
        fact_check_data, summary, embeddings = fact_check_main(article_text, s3_bucket if upload_to_s3 else None, s3_region)
        
        if save_to_db:
            # Add metadata
            fact_check_data["analysis_id"] = task_id
            fact_check_data["processed_date"] = datetime.datetime.now().isoformat()
            fact_check_data["topic"] = summary[:50] + "..." if summary else "No summary"
            
            # Save to database
            save_to_database(fact_check_data)
            
    except Exception as e:
        print(f"Error processing article: {str(e)}")
        
def upload_thread(data, db='newsdb', collection="articles"):
    """Upload data to MongoDB database"""
    load_dotenv()
    mongo_uri = os.getenv("MONGO_DB")
    try:
        client = MongoClient(mongo_uri)
        # Verify connection
        client.admin.command('ping')
        # Select database and collection
        db = client[db]
        articles = db[collection]
        
        # Check if data is already parsed JSON or needs parsing
        if isinstance(data, str):
            json_data = json.loads(data)
        else:
            json_data = data  # Assume it's already a dict/list
            
        # Check if data is a list (for multiple documents)
        if isinstance(json_data, list):
            result = articles.insert_many(json_data)  # Use insert_many for arrays
            print(f"Inserted {len(result.inserted_ids)} documents")
            return result.inserted_ids
        else:
            result = articles.insert_one(json_data)  # Use insert_one for single docs
            print(f"Document inserted with _id: {result.inserted_id}")
            return result.inserted_id
            
    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {str(e)}")
        raise
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in data")
        raise
    except PyMongoError as e:
        print(f"MongoDB operation error: {str(e)}")
        raise
    finally:
        # Ensure connection is closed properly
        if 'client' in locals():
            client.close()
            
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
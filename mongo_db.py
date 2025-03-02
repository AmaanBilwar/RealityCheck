from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# MongoDB connection setup
mongo_uri = os.getenv("MONGO_DB")

try:
    # Create MongoDB connection
    client = MongoClient(mongo_uri)
    
    # Verify connection
    client.admin.command('ping')
    print("Connected to MongoDB Atlas")
    
    # Select database and collection
    db = client["newsdb"]
    articles = db["articles"]  # Changed collection name to be more descriptive
    
    # Load JSON data
    news_data_path = r'C:\Users\aniru\Desktop\Programming Languages Projects\RealityCheck\news_articles.json'
    
    # Use context manager for file handling
    with open(news_data_path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)  # Load the actual file content
        
        # Check if data is a list (for multiple documents)
        if isinstance(json_data, list):
            result = articles.insert_many(json_data)  # Use insert_many for arrays
            print(f"Inserted {len(result.inserted_ids)} documents")
        else:
            result = articles.insert_one(json_data)  # Use insert_one for single docs
            print(f"Document inserted with _id: {result.inserted_id}")
    
    # Create index before querying for better performance
    articles.create_index([("topic", "text")])  # Using text index for better search
    
    # Find documents by topic (using text search)
    query = {"$text": {"$search": "Trump Zelensky Oval Office"}}
    found_docs = articles.find(query).limit(5)
    
    print("\nFound documents:")
    for doc in found_docs:
        print(f"- {doc['topic']}")

except ConnectionFailure as e:
    print(f"MongoDB connection failed: {str(e)}")
except FileNotFoundError:
    print("Error: JSON file not found at specified path")
except json.JSONDecodeError:
    print("Error: Invalid JSON format in file")
except PyMongoError as e:
    print(f"MongoDB operation error: {str(e)}")
finally:
    # Ensure connection is closed properly
    if 'client' in locals():
        client.close()
        print("\nMongoDB connection closed")

from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from crewai import Agent, Task, LLM, Crew, Process

from pydantic import BaseModel
from dotenv import load_dotenv
import json
import re
import datetime
import subprocess
import time
import concurrent.futures
import boto3
from transformers import pipeline
from google import generativeai as genai
import os
import numpy as np
from typing import List, Dict, Any, Optional
import faiss
from sentence_transformers import SentenceTransformer
import uvicorn
from fastapi import FastAPI, HTTPException, Query

load_dotenv()

# Load environment variables
bedrock_client = boto3.client("bedrock-runtime")

serper_key = os.getenv("SERPER_DEV_KEY")
os.environ["SERPER_API_KEY"] = serper_key  # Ensure it's available globally

# Pydantic models for Article Fact Checking
class ArticleRequest(BaseModel):
    article: str

class NewsArticleSchema(BaseModel):
    title: str
    source: str
    date: str
    url: str
    snippet: str

class NewsOutputSchema(BaseModel):
    topic: str
    timestamp: str
    articles: list[NewsArticleSchema]

# Pydantic models for RAG API
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class Document(BaseModel):
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    score: Optional[float] = None

class QueryResponse(BaseModel):
    results: List[Document]
    query: str

# FastAPI app
app = FastAPI(title="Combined Fact Check and RAG API")

# Global variables for RAG
embeddings_dir = "embeddings-s3-bucket"
model = None
index = None
documents = {}

PROMPT = "Analyze the given article and extract complete, self-contained sentences or chunks that make factual claims, assertions, or statements requiring verification. Ensure that each extracted chunk has enough context to be meaningfully checked against external sources. Do not provide any explanations or summaries—only return the extracted statements that require fact-checking."

def call_ollama(prompt: str, model: str = "llama3.2:latest") -> str:
    command = ["ollama", "run", model]
    try:
        start_time = time.time()
        result = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
            timeout=60,
            encoding="utf-8"
        )
        end_time = time.time()
        print(f"✅ Ollama execution completed in {end_time - start_time:.2f} seconds")
        return result.stdout
    except subprocess.TimeoutExpired:
        print("⚠️ Ollama timed out! Try using a shorter input or a lighter model.")
        raise Exception("Ollama took too long to respond. Please try again with a shorter input or a lighter model.")
    except subprocess.CalledProcessError as e:
        print("❌ Ollama call error:", e.stderr)
        raise Exception(f"Ollama call error: {e.stderr}")

def extract_chunks(article_text: str) -> list:
    full_prompt = f"{PROMPT}\n\nArticle:\n{article_text}"
    response = call_ollama(full_prompt)
    
    chunks = []
    for line in response.splitlines():
        cleaned_line = line.strip()
        if cleaned_line:
            # Make sure it's not a numbering or bullet point alone
            if re.match(r'^[\d\.\-\*\•]+$', cleaned_line):
                continue
            # Remove numbering at the beginning if present
            cleaned_line = re.sub(r'^[\d\.\-\*\•]+\s*', '', cleaned_line)
            chunks.append(cleaned_line)
    
    return chunks

# Scraping and search functions
def scrape_article_content(url, attempt=1, max_attempts=3):
    """Scrape content from a URL with retry mechanism"""
    if not url or url == "None":
        return "No valid URL provided for scraping."
        
    try:
        print(f"Attempting to scrape: {url}")
        scraping_tool = ScrapeWebsiteTool(website_url=url)
        # Explicitly pass the URL to the tool
        result = scraping_tool.run()
        
        # If result is extremely short, it might be a failed scrape
        if len(result) < 100 and attempt < max_attempts:
            print(f"Short result from {url}, retrying ({attempt}/{max_attempts})")
            time.sleep(2)  # Wait before retry
            return scrape_article_content(url, attempt + 1, max_attempts)
        return result
    except Exception as e:
        if attempt < max_attempts:
            print(f"Error scraping {url}, retrying ({attempt}/{max_attempts}): {e}")
            time.sleep(2)  # Wait before retry
            return scrape_article_content(url, attempt + 1, max_attempts)
        print(f"Failed to scrape {url} after {max_attempts} attempts: {e}")
        return f"Failed to scrape content: {str(e)}"

def scrape_articles_parallel(articles, max_workers=5):
    """Scrape multiple articles in parallel"""
    updated_articles = []
    print(f"Scraping {len(articles)} articles with {max_workers} workers...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Prepare the futures
        future_to_article = {
            executor.submit(scrape_article_content, article["url"]): article 
            for article in articles
        }
        
        # Process as they complete
        for future in concurrent.futures.as_completed(future_to_article):
            article = future_to_article[future]
            try:
                content = future.result()
                # Create a new article with content
                article_with_content = article.copy()
                article_with_content["content"] = content
                updated_articles.append(article_with_content)
                print(f"Successfully scraped content for: {article['title'][:30]}...")
            except Exception as e:
                print(f"Exception scraping {article['url']}: {e}")
                # Keep the article but mark content as failed
                article_with_content = article.copy()
                article_with_content["content"] = "Failed to scrape content."
                updated_articles.append(article_with_content)
    
    return updated_articles

def extract_domain(url):
    match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    return match.group(1) if match else "Unknown Source"

def get_raw_news_results(topic, api_key):
    tool = SerperDevTool(
        name="DirectNewsSearch",
        parameters={'type': 'news', 'num': 10},
        api_key=api_key
    )
    # Use named parameter search_query
    results = tool.run(search_query=topic)
    
    # Format the raw results as backup JSON
    articles = []
    if isinstance(results, dict) and 'organic' in results:
        for item in results['organic']:
            articles.append({
                "title": item.get('title', 'No title'),
                "source": item.get('source', extract_domain(item.get('link', ''))),
                "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "url": item.get('link', ''),
                "snippet": item.get('snippet', 'No snippet available')
            })
    
    return {
        "topic": topic,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "articles": articles
    }

def search_for_topic(topic):
    """Function to search for a single topic and return results"""
    try:
        # Initialize LLM with strict temperature
        llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434", temperature=0.1)
        
        # Define Serper news search tool
        news_search_tool = SerperDevTool(
            name="SerperNewsSearch",
            description="Searches for news articles and returns titles, sources, dates, URLs, and snippets.",
            parameters={
                'type': 'news',
                'sort': 'date',
                'num': 5  # Reduced from 15 to 5 to make it faster per chunk
            },
            api_key=serper_key
        )
        
        # Define news link retrieval agent
        news_link_retriever = Agent(
            role="JSON Data Formatter",
            goal="Extract and format news data as valid JSON only, with no additional text.",
            backstory=(
                "You are a machine that only outputs valid JSON. You never explain or add commentary. "
                "You only return data in the exact JSON format specified."
            ),
            tools=[news_search_tool],
            verbose=False,
            memory=False,
            max_iter=3,
            llm=llm
        )
        
        # Task for retrieving news for a specific topic
        link_retrieval_task = Task(
            description=(
                "GET NEWS DATA AND FORMAT AS JSON: \n"
                f"1. Search for news about '{topic}' using SerperNewsSearch\n"
                "2. Format ALL results as valid JSON matching this EXACT structure:\n"
                "```json\n"
                "{{\n"
                '  "topic": "REPLACE_WITH_SEARCH_TOPIC",\n'
                '  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",\n'
                '  "articles": [\n'
                "    {{\n"
                '      "title": "Article Title",\n'
                '      "source": "Publication Name",\n'
                '      "date": "Publication Date",\n'
                '      "url": "https://full.url.com",\n'
                '      "snippet": "Brief description"\n'
                "    }}\n"
                "  ]\n"
                "}}\n"
                "```\n\n"
                "CRITICAL INSTRUCTIONS:\n"
                "- Return ONLY JSON, no other text\n"
                "- Do NOT include explanations before or after the JSON\n"
                "- Do NOT include code block markers (```) in your response\n"
                "- Include ALL articles found in the search\n"
                f"- The topic field should contain: {topic}\n"
                "- If dates are unavailable, use current date in ISO format"
            ),
            expected_output=(
                "ONLY RETURN VALID JSON WITH NO EXPLANATIONS OR COMMENTARY. "
                "DO NOT INCLUDE MARKDOWN FORMATTING. "
                "ONLY RETURN THE RAW JSON OBJECT."
            ),
            agent=news_link_retriever
        )
        
        # Create crew to execute the task
        news_links_crew = Crew(
            agents=[news_link_retriever],
            tasks=[link_retrieval_task],
            process=Process.sequential,
            verbose=False
        )
        
        # Execute search
        result_output = news_links_crew.kickoff(inputs={'topic': topic})
        
        # Extract raw content
        if hasattr(result_output, 'raw'):
            result = result_output.raw
        else:
            result = result_output
        
        # Process the result to extract JSON
        found_json = None
        
        if isinstance(result, dict):
            # Already a dict/JSON object
            found_json = result
        elif isinstance(result, str):
            # Clean the string of any explanatory text
            # Look for a JSON pattern
            json_pattern = r'(\{[\s\S]*?\})'
            matches = re.findall(json_pattern, result)
            
            if matches:
                for potential_json in sorted(matches, key=len, reverse=True):
                    try:
                        found_json = json.loads(potential_json)
                        # Basic validation
                        if isinstance(found_json, dict) and "articles" in found_json:
                            print("Successfully extracted JSON from response")
                            break
                    except:
                        continue
        
        # Use found JSON or fall back to backup
        if found_json:
            parsed_json = found_json
        else:
            print("Could not extract valid JSON. Using backup results.")
            # Get raw results directly from SerperDev as backup
            parsed_json = get_raw_news_results(topic, serper_key)
            
        return parsed_json
        
    except Exception as e:
        print(f"Error searching for '{topic}': {str(e)}")
        # Fall back to direct API call
        return get_raw_news_results(topic, serper_key)

def list_available_bedrock_models():
    """List all available Bedrock models to help identify which ones can be used"""
    try:
        bedrock = boto3.client('bedrock')
        models = bedrock.list_foundation_models()
        
        print("Available Bedrock Models:")
        for model in models['modelSummaries']:
            on_demand = "Yes" if model.get('inferenceTypesSupported', []) and 'ON_DEMAND' in model.get('inferenceTypesSupported', []) else "No"
            print(f"- {model['modelId']} (On-demand supported: {on_demand})")
        
        return models['modelSummaries']
    except Exception as e:
        print(f"Error listing models: {str(e)}")
        return []

def summarization(text, api_key=None):
    # Use provided API key or check environment variable
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Check if we have a valid API key
    if not GEMINI_API_KEY:
        print("API key not found. Please provide a valid Gemini API key.")
        return "API key not found"
    
    try:
        # Initialize the client
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Generate the summary
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=f'Summarize the following article:\n\n{text}'
        )
        return response.text
    except ValueError as e:
        print(f"API Client Error: {e}")
        return "Error: Could not initialize Gemini client. Check your API key."
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return f"Error: {str(e)}"

def generate_embeddings(text, model_provider="bedrock"):
    """
    Generate embeddings for the given text using the specified model provider.
    
    Parameters:
    text (str): The text to generate embeddings for
    model_provider (str): The model provider to use ('bedrock', 'huggingface', or 'ollama')
    
    Returns:
    list or dict: The embeddings generated from the text
    """
    if not text:
        print("Warning: Empty text provided for embeddings generation")
        return []
    
    # Truncate text if it's too long (most embedding models have token limits)
    max_chars = 8000
    if len(text) > max_chars:
        print(f"Text too long for embedding ({len(text)} chars). Truncating to {max_chars} chars.")
        text = text[:max_chars]
    
    if model_provider.lower() == "bedrock":
        try:
            # Amazon Bedrock embedding models
            response = bedrock_client.invoke_model(
                modelId="amazon.titan-embed-text-v1",  # You can change to other models like "cohere.embed-english-v3"
                body=json.dumps({
                    "inputText": text,
                    "embeddingConfig": {
                        "outputEmbeddingLength": 768  # Adjust based on the model used
                    }
                })
            )
            
            # Parse the response
            response_body = json.loads(response.get('body').read().decode('utf-8'))
            embeddings = response_body.get('embedding', [])
            
            print(f"Generated embeddings using Bedrock with dimension {len(embeddings)}")
            return embeddings
            
        except Exception as e:
            print(f"Error generating embeddings with Bedrock: {str(e)}")
            # Fall back to HuggingFace if Bedrock fails
            print("Falling back to HuggingFace for embeddings...")
            return generate_embeddings(text, "huggingface")
    
    elif model_provider.lower() == "huggingface":
        try:
            # Use a sentence-transformers model from HuggingFace
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            # Load model and tokenizer (all-MiniLM-L6-v2 is small and fast)
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
            
            # Tokenize and prepare inputs
            inputs = tokenizer(text, padding=True, truncation=True, return_tensors="pt", max_length=512)
            
            # Get embeddings
            with torch.no_grad():
                outputs = model(**inputs)
                # Use mean pooling for sentence embeddings
                embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
            
            print(f"Generated embeddings using HuggingFace with dimension {len(embeddings)}")
            return embeddings
            
        except Exception as e:
            print(f"Error generating embeddings with HuggingFace: {str(e)}")
            # Fall back to Ollama if HuggingFace fails
            print("Falling back to Ollama for embeddings...")
            return generate_embeddings(text, "ollama")
    
    elif model_provider.lower() == "ollama":
        try:
            # Use Ollama for embeddings (requires Ollama to be running)
            command = ["ollama", "embeddings", "llama3.2"]
            result = subprocess.run(
                command,
                input=text,
                text=True,
                capture_output=True,
                check=True,
                timeout=60,
                encoding="utf-8"
            )
            
            # Parse the JSON response
            embeddings = json.loads(result.stdout)
            print(f"Generated embeddings using Ollama with dimension {len(embeddings)}")
            return embeddings
            
        except Exception as e:
            print(f"Error generating embeddings with Ollama: {str(e)}")
            return []
    
    else:
        print(f"Unknown model provider: {model_provider}")
        return []


def upload_to_s3(data, bucket_name, file_key, region_name=None):
    """
    Upload data to an S3 bucket.
    
    Parameters:
    data (dict/list/str): The data to upload to S3
    bucket_name (str): Name of the S3 bucket
    file_key (str): The key (path) where the file will be stored in S3
    region_name (str, optional): AWS region name
    
    Returns:
    bool: True if upload successful, False otherwise
    """
    try:
        # Create S3 client with region if specified
        if region_name:
            s3_client = boto3.client('s3', region_name=region_name)
        else:
            s3_client = boto3.client('s3')
        
        # Convert data to JSON if it's a dict or list
        if isinstance(data, (dict, list)):
            data_to_upload = json.dumps(data, default=str)
        else:
            data_to_upload = str(data)
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=data_to_upload,
            ContentType='application/json'
        )
        
        print(f"Successfully uploaded to s3://{bucket_name}/{file_key}")
        return True
        
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        return False

def main(article_text, upload_to_s3_bucket=None, s3_region=None):
    """
    Main function for fact checking with streaming output.
    
    Parameters:
    article_text (str): The article text to fact check
    upload_to_s3_bucket (str, optional): S3 bucket name to upload results
    s3_region (str, optional): AWS region for S3 bucket
    
    Yields:
    dict: Progressive updates with processing status and data
    
    Returns:
    tuple: (fact_check_data, summary, embeddings) when complete
    """
    # Create a unique ID for this analysis (timestamp + hash of article)
    import hashlib
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    article_hash = hashlib.md5(article_text[:100].encode()).hexdigest()[:10]
    analysis_id = f"{timestamp}_{article_hash}"
    
    # Initialize the result structure
    result_data = {
        "analysis_id": analysis_id,
        "article": article_text,
        "verification_date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "processing",
        "fact_checks": []
    }
    
    # First progress update
    yield {"status": "starting", "message": "Starting fact check process", "analysis_id": analysis_id}
    
    # Add sentiment analysis for the original article using BERT pipeline
    yield {"status": "processing", "message": "Analyzing article sentiment...", "analysis_id": analysis_id}
    try:
        from transformers import pipeline
        import re

        # Tokenize text for length check
        tokenized_text = re.findall(r'\w+|[^\w\s]', article_text)
        
        # If text is too long, truncate it
        if len(tokenized_text) > 450:  # Using 450 for safety margin
            truncated_text = ' '.join(tokenized_text[:450])
            pipe = pipeline("text-classification", model="dhruvpal/fake-news-bert")
            result = pipe(truncated_text)
        else:
            pipe = pipeline("text-classification", model="dhruvpal/fake-news-bert")
            result = pipe(article_text)
            
        sentiment_result = {
            "score": result[0]["score"],
            "reasoning": result[0]["label"]
        }
        result_data["sentiment_analysis"] = sentiment_result
        yield {
            "status": "processing", 
            "message": f"Sentiment analysis complete: {result[0]['label']} ({result[0]['score']:.2f})", 
            "data": {"sentiment": sentiment_result},
            "analysis_id": analysis_id
        }
        
    except Exception as e:
        sentiment_result = {
            "score": 0.5,
            "reasoning": f"Failed to analyze sentiment: {str(e)}"
        }
        result_data["sentiment_analysis"] = sentiment_result
        yield {
            "status": "warning", 
            "message": f"Error analyzing sentiment: {str(e)}", 
            "analysis_id": analysis_id
        }
    
    # Step 1: Extract chunks from the article
    yield {"status": "processing", "message": "Extracting statements to verify...", "analysis_id": analysis_id}
    chunks = extract_chunks(article_text)
    yield {
        "status": "processing", 
        "message": f"Found {len(chunks)} statements to verify", 
        "data": {"chunks_count": len(chunks)},
        "analysis_id": analysis_id
    }
    
    # Step 2: For each chunk, search for news and add to results
    for i, chunk in enumerate(chunks):
        yield {
            "status": "processing", 
            "message": f"Verifying statement {i+1}/{len(chunks)}: {chunk[:50]}...", 
            "data": {"current_chunk": i+1, "total_chunks": len(chunks), "chunk_text": chunk[:50]},
            "analysis_id": analysis_id
        }
        
        # Search for news about this chunk
        search_result = search_for_topic(chunk)
        
        # Add articles with content
        if search_result and "articles" in search_result:
            yield {
                "status": "processing", 
                "message": f"Found {len(search_result['articles'])} articles for statement {i+1}", 
                "data": {"articles_found": len(search_result['articles'])},
                "analysis_id": analysis_id
            }
            
            # Only fetch content for the first 3 articles to keep things manageable
            limited_articles = search_result["articles"][:3]
            articles_with_content = scrape_articles_parallel(limited_articles, max_workers=3)
            
            # Add to results
            fact_check_entry = {
                "statement": chunk,
                "search_topic": search_result.get("topic", chunk),
                "articles": articles_with_content
            }
            
            result_data["fact_checks"].append(fact_check_entry)
            
            # Send update with the latest chunk's verification data
            yield {
                "status": "processing", 
                "message": f"Completed verification of statement {i+1}/{len(chunks)}", 
                "data": {"fact_check": fact_check_entry},
                "analysis_id": analysis_id
            }
        else:
            # Handle case where no articles were found
            fact_check_entry = {
                "statement": chunk,
                "search_topic": chunk,
                "articles": [],
                "error": "No articles found for this statement"
            }
            result_data["fact_checks"].append(fact_check_entry)
            
            yield {
                "status": "processing", 
                "message": f"No articles found for statement {i+1}/{len(chunks)}", 
                "data": {"fact_check": fact_check_entry},
                "analysis_id": analysis_id
            }
    
    # Generate summary
    yield {"status": "processing", "message": "Generating article summary...", "analysis_id": analysis_id}
    
    if not os.getenv('GEMINI_API_KEY'):
        yield {"status": "warning", "message": "No GEMINI_API_KEY found in environment", "analysis_id": analysis_id}
        if not api_key:
            yield {"status": "warning", "message": "Summarization skipped - no API key", "analysis_id": analysis_id}
            summary = "Summarization skipped due to missing API key."
            result_data["summary"] = summary
            
            # Save partial results without embeddings
            filename = save_results_to_file(result_data)
            yield {
                "status": "completed", 
                "message": f"Fact checking complete without summary. Results saved to {filename}", 
                "data": {"filename": filename, "result_data": result_data},
                "analysis_id": analysis_id
            }
            return result_data, summary, None
    else:
        api_key = os.getenv('GEMINI_API_KEY')
    
    # Generate summary using the article text
    summary = summarization(article_text, api_key)
    result_data["summary"] = summary
    
    yield {
        "status": "processing", 
        "message": "Summary generation complete", 
        "data": {"summary": summary},
        "analysis_id": analysis_id
    }
    
    # Generate embeddings for the summary
    yield {"status": "processing", "message": "Generating embeddings for the summary...", "analysis_id": analysis_id}
    embeddings = generate_embeddings(summary, "bedrock")
    result_data["summary_embeddings"] = embeddings
    
    if embeddings:
        yield {
            "status": "processing", 
            "message": f"Generated embeddings (dimension: {len(embeddings)})", 
            "data": {"embedding_dimension": len(embeddings)},
            "analysis_id": analysis_id
        }
    else:
        yield {"status": "warning", "message": "Could not generate embeddings", "analysis_id": analysis_id}
    
    # Save results to file
    filename = save_results_to_file(result_data)
    yield {
        "status": "processing", 
        "message": f"Results saved to {filename}", 
        "data": {"filename": filename},
        "analysis_id": analysis_id
    }
    
    # Upload to S3 if bucket name is provided
    if upload_to_s3_bucket:
        yield {
            "status": "processing", 
            "message": f"Uploading results to S3 bucket: {upload_to_s3_bucket}", 
            "analysis_id": analysis_id
        }
        
        # Upload complete result data
        results_key = f"fact_checks/{analysis_id}/complete_results.json"
        upload_success = upload_to_s3(result_data, upload_to_s3_bucket, results_key, s3_region)
        
        # Upload just the embeddings separately for easier access
        if embeddings:
            embeddings_key = f"embeddings/{analysis_id}.json"
            embeddings_data = {
                "analysis_id": analysis_id,
                "verification_date": result_data["verification_date"],
                "summary": summary,
                "embeddings": embeddings
            }
            upload_success = upload_to_s3(embeddings_data, upload_to_s3_bucket, embeddings_key, s3_region)
            
        yield {
            "status": "processing", 
            "message": "S3 upload complete", 
            "analysis_id": analysis_id
        }
    
    # Final update
    yield {
        "status": "completed", 
        "message": "Fact checking process complete", 
        "data": {"result_data": result_data},
        "analysis_id": analysis_id
    }
    
    return result_data, summary, embeddings

# Helper function to save results to file with unique name
def save_results_to_file(result_data):
    """Save results to a JSON file with a unique filename"""
    base_filename = "fact_check_results"
    extension = ".json"
    counter = 1
    filename = f"{base_filename}{extension}"
    
    while os.path.exists(filename):
        filename = f"{base_filename}_{counter}{extension}"
        counter += 1
        
    with open(filename, "w") as f:
        json.dump(result_data, f, indent=2)
    
    return filename

# Direct execution

# Default article text for testing
# prompt = input("Enter the article text to fact-check: ")
# ARTICLE_TEXT = prompt




# # Don't regenerate the summary - we already have it from the main function
# print("\n=== ARTICLE SUMMARY ===")
# print(summary)

# # Display information about the embeddings
# if embeddings:
#     print(f"\n=== EMBEDDING INFORMATION ===")
#     print(f"Generated embeddings with dimension: {len(embeddings)}")
#     print(f"First 5 values: {embeddings[:5]}")
# else:
#     print("\nNo embeddings were generated.")
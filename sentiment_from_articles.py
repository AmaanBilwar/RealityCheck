# Use a pipeline as a high-level helper

import boto3
import json
import sys 
from transformers import pipeline
import os

def analyze_article_with_bedrock(article_text):
    # Initialize the Bedrock client
    bedrock_client = boto3.client("bedrock-runtime")
    
    prompt = f'''
    Please analyze the following news article and determine if it's likely fake news or authentic.
    Rate it on a scale from 0 to 1, where 0 means completely fake and 1 means completely authentic.
    
    Article: {article_text}
    
    Provide your analysis in this JSON format:
    {{
        "score": [score between 0 and 1],
        "reasoning": [brief explanation of your rating]
    }}
    '''
    
    try: 
        response = bedrock_client.invoke_model(
            modelId="us.meta.llama3-2-3b-instruct-v1:0",
            body=json.dumps({
                "prompt": prompt,
                "max_gen_len": 512,
                "temperature": 0.1
            })
        )
        
        # Parse the response
        response_body = json.loads(response.get('body').read().decode('utf-8'))
        result = response_body.get('generation')
        
        # Extract the JSON part from the response
        try:
            # Try to find and extract JSON from the text response
            import re
            json_match = re.search(r'{.*}', result, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group(0))
                return result_json
            else:
                print("Warning: Could not extract JSON from LLM response.")
                return {"score": 0.5, "reasoning": "Could not analyze properly"}
        except Exception as e:
            print(f"Error parsing response: {str(e)}")
            return {"score": 0.5, "reasoning": "Error in analysis parsing"}
            
    except Exception as e:
        print(f"Error calling Bedrock: {str(e)}")
        return {"score": 0.5, "reasoning": "Error in analysis"}

def analyze_article_with_pipeline(article_text):
    # Use a pipeline as a high-level helper
    from transformers import pipeline

    pipe = pipeline("text-classification", model="dhruvpal/fake-news-bert")
    result = pipe(article_text)
    return result


def load_text_file(file_path):
    """Load article text from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error loading text file: {str(e)}")
        return None

def text_to_json(text):
    """Convert plain text into a JSON structure."""
    # Split text by double newlines to separate articles
    article_chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    
    # Create a structured JSON array
    articles = []
    
    for i, chunk in enumerate(article_chunks):
        article = {
            "id": i + 1,
            "text": chunk
        }
        articles.append(article)
    
    return articles

def save_json_file(articles, output_path):
    """Save the articles as a JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(articles, file, indent=2)
        print(f"JSON file created at {output_path}")
        return True
    except Exception as e:
        print(f"Error saving JSON file: {str(e)}")
        return False

def process_text_file(file_path):
    """Process a text file and convert it to JSON for analysis."""
    text = load_text_file(file_path)
    if not text:
        return None
    
    # Convert text to JSON structure
    articles = text_to_json(text)
    
    # Save JSON file (optional)
    json_path = os.path.splitext(file_path)[0] + ".json"
    save_json_file(articles, json_path)
    
    return articles

def main():
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "../message.txt"  # Default to text file
    
    # Check file extension
    _, file_extension = os.path.splitext(file_path)
    
    if file_extension.lower() == '.txt':
        print(f"Processing text file: {file_path}")
        article_data = process_text_file(file_path)
    else:
        print(f"Processing JSON file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                article_data = json.load(file)
        except Exception as e:
            print(f"Error loading JSON file: {str(e)}")
            article_data = None
    
    if not article_data:
        print("Could not load article data.")
        return
    
    # Adapt to the actual structure of the data
    if isinstance(article_data, dict):
        # If the data is a single object with articles as keys or values
        if "articles" in article_data:
            articles = article_data["articles"]
        else:
            # Maybe the entire object is a single article
            articles = [article_data]
    else:
        # If it's already a list
        articles = article_data
    
    # Process each article based on its structure
    for i, article in enumerate(articles):
        article_text = None
        
        # Try different possible formats
        if isinstance(article, dict):
            if "text" in article:
                article_text = article["text"]
            elif "content" in article:
                article_text = article["content"]
            elif "body" in article:
                article_text = article["body"]
            elif "article" in article:
                article_text = article["article"]
        elif isinstance(article, str):
            # Maybe the article is directly a string
            article_text = article
            
        if article_text:
            print(f"\nAnalyzing article {i+1}...")
            result = analyze_article_with_bedrock(article_text)
            
            print(f"Result: {'LIKELY TRUE' if result['score'] > 0.6 else 'LIKELY FAKE'}")
            print(f"Score: {result['score']}")
            print(f"Reasoning: {result['reasoning']}")
        else:
            print(f"Invalid article format at index {i}. Available keys: {list(article.keys()) if isinstance(article, dict) else 'Not a dict'}")

if __name__ == "__main__":
    main()
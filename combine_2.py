from crewai import Agent, Task, LLM, Crew, Process
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import re
import datetime
import subprocess
import time
import concurrent.futures
import boto3
from transformers import pipeline


# Load environment variables
load_dotenv()
serper_key = os.getenv("SERPER_DEV_KEY")
os.environ["SERPER_API_KEY"] = serper_key  # Ensure it's available globally

# Pydantic models
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

# ====== SENTIMENT ANALYSIS FUNCTIONS ======

# def analyze_article_with_bedrock(article_text):
#     # Initialize the Bedrock client
#     bedrock_client = boto3.client("bedrock-runtime")
    
#     prompt = f'''
#     Please analyze the following news article and determine if it's likely fake news or authentic.
#     Rate it on a scale from 0 to 1, where 0 means completely fake and 1 means completely authentic.
    
#     Article: {article_text}
    
#     Provide your analysis in this JSON format:
#     {{
#         "score": [score between 0 and 1],
#         "reasoning": [brief explanation of your rating]
#     }}
#     '''
    
#     try: 
#         response = bedrock_client.invoke_model(
#             modelId="us.meta.llama3-2-3b-instruct-v1:0",
#             body=json.dumps({
#                 "prompt": prompt,
#                 "max_gen_len": 512,
#                 "temperature": 0.1
#             })
#         )
        
#         # Parse the response
#         response_body = json.loads(response.get('body').read().decode('utf-8'))
#         result = response_body.get('generation')
        
#         # Extract the JSON part from the response
#         try:
#             # Try to find and extract JSON from the text response
#             import re
#             json_match = re.search(r'{.*}', result, re.DOTALL)
#             if json_match:
#                 result_json = json.loads(json_match.group(0))
#                 return result_json
#             else:
#                 print("Warning: Could not extract JSON from LLM response.")
#                 return {"score": 0.5, "reasoning": "Could not analyze properly"}
#         except Exception as e:
#             print(f"Error parsing response: {str(e)}")
#             return {"score": 0.5, "reasoning": "Error in analysis parsing"}
            
#     except Exception as e:
#         print(f"Error calling Bedrock: {str(e)}")
#         return {"score": 0.5, "reasoning": "Error in analysis"}


# def analyze_article_with_pipeline(article_text):
#     """
#     Analyze an article using a Hugging Face pipeline to determine if it's fake news.
#     Returns a standardized format with score and reasoning.
#     """
#     try:
#         # Use a pipeline as a high-level helper
#         pipe = pipeline("text-classification", model="dhruvpal/fake-news-bert")
        
#         # Check if article is too long for the model
#         max_length = 1600  # Most BERT models have this limit
#         if len(article_text.split()) > max_length:
#             # If too long, use only the first part of the article
#             words = article_text.split()
#             truncated_text = " ".join(words[:max_length])
#             print(f"Article truncated from {len(words)} to {max_length} words for BERT analysis")
#             raw_result = pipe(truncated_text)
#         else:
#             raw_result = pipe(article_text)
        
#         print(f"Raw pipeline result: {raw_result}")
        
#         # Process the result - extract label and score
#         if isinstance(raw_result, list) and len(raw_result) > 0:
#             result = raw_result[0]
#             label = result.get('label', '').upper()
#             confidence = result.get('score', 0.5)
            
#             # Convert to standardized output format
#             # Assuming the model uses labels like "REAL"/"FAKE" or "AUTHENTIC"/"FAKE"
#             if "REAL" in label or "AUTHENTIC" in label or "TRUE" in label:
#                 return {
#                     "score": confidence,
#                     "reasoning": f"Article appears authentic with {confidence:.2f} confidence"
#                 }
#             elif "FAKE" in label or "FALSE" in label:
#                 return {
#                     "score": 1.0 - confidence,
#                     "reasoning": f"Article appears to be fake news with {confidence:.2f} confidence"
#                 }
#             else:
#                 # Handle other labels
#                 return {
#                     "score": 0.5,
#                     "reasoning": f"Unclear classification: {label} with {confidence:.2f} confidence"
#                 }
#         else:
#             return {
#                 "score": 0.5,
#                 "reasoning": "Could not classify article"
#             }
#     except Exception as e:
#         print(f"Error in BERT pipeline: {str(e)}")
#         return {
#             "score": 0.5,
#             "reasoning": f"Error in BERT analysis: {str(e)}"
#         }

# Extract chunks function using Ollama
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
        llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434", temperature=0.0)
        
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
    

def main(article_text):
    # Add sentiment analysis for the original article using BERT pipeline
    print("Analyzing article sentiment with BERT pipeline...")
    try:
        from transformers import pipeline

        pipe = pipeline("text-classification", model="dhruvpal/fake-news-bert")
            
        result = pipe(article_text)
        sentiment_result = {
            "score": result[0]["score"],
            "reasoning": result[0]["label"]
        }
        print(f"Sentiment analysis result: {sentiment_result}")
        
    except Exception as e:
        print(f"Error analyzing sentiment with BERT pipeline: {str(e)}")
        sentiment_result = {
            "score": 0.5,
            "reasoning": "Failed to analyze sentiment"
        }
    
    # Step 1: Extract chunks from the article
    print("Extracting chunks from article...")
    chunks = extract_chunks(article_text)
    print(f"Found {len(chunks)} chunks to verify")
    
    # Prepare the result structure with sentiment analysis added
    result_data = {
        "article": article_text,
        "verification_date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sentiment_analysis": sentiment_result,  # Add sentiment analysis results
        "fact_checks": []
    }
    
    # Rest of the function remains the same...
    # Step 2: For each chunk, search for news and add to results
    for i, chunk in enumerate(chunks):
        print(f"\nProcessing chunk {i+1}/{len(chunks)}: {chunk[:50]}...")
        
        # Search for news about this chunk
        search_result = search_for_topic(chunk)
        
        # Add articles with content
        if search_result and "articles" in search_result:
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
        else:
            # Handle case where no articles were found
            result_data["fact_checks"].append({
                "statement": chunk,
                "search_topic": chunk,
                "articles": [],
                "error": "No articles found for this statement"
            })
    
    # Step 3: Save results to file
    filename = f"fact_check_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(result_data, f, indent=2)
    
    print(f"\nFact checking complete. Results saved to {filename}")
    
    # Return the data for further processing
    return result_data

# Example of how to use the result data variable for further processing
def analyze_fact_checking_results(fact_check_data):
    """
    Process the fact-checking results further
    """
    print("\n=== ANALYZING FACT CHECK RESULTS ===")
    
    # Count total statements checked
    total_statements = len(fact_check_data["fact_checks"])
    print(f"Total statements checked: {total_statements}")
    
    # Count statements with articles found
    statements_with_articles = sum(1 for check in fact_check_data["fact_checks"] if check.get("articles") and len(check.get("articles", [])) > 0)
    print(f"Statements with supporting articles found: {statements_with_articles} ({statements_with_articles/total_statements*100:.1f}%)")
    
    # Calculate average articles per statement
    total_articles = sum(len(check.get("articles", [])) for check in fact_check_data["fact_checks"])
    avg_articles = total_articles / total_statements if total_statements > 0 else 0
    print(f"Average articles found per statement: {avg_articles:.2f}")
    
    # Display sentiment analysis results
    if "sentiment_analysis" in fact_check_data:
        sentiment = fact_check_data["sentiment_analysis"]
        print(f"\nArticle Authenticity Score: {sentiment.get('score', 'N/A')}")
        print(f"Reasoning: {sentiment.get('reasoning', 'N/A')}")
    
    # Generate a summary report
    summary = {
        "total_statements": total_statements,
        "statements_with_articles": statements_with_articles,
        "statements_without_articles": total_statements - statements_with_articles,
        "total_articles_found": total_articles,
        "avg_articles_per_statement": avg_articles,
        "verification_date": fact_check_data["verification_date"],
        "article_authenticity": fact_check_data.get("sentiment_analysis", {}).get("score", "N/A")
    }
    
    # You could save this summary to a separate file
    summary_filename = f"fact_check_summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_filename, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary report saved to {summary_filename}")
    
    # Return the summary for further use
    return summary




# Direct execution
if __name__ == '__main__':
    # Default article text for testing
    prompt = input("Enter the article text to fact-check: ")
    ARTICLE_TEXT = prompt
    
    # Run the fact checking
    fact_check_data = main(ARTICLE_TEXT)
    
    # Further analyze the results
    summary = analyze_fact_checking_results(fact_check_data)
    
    # Example of using the fact check data to perform additional tasks
    print("\n=== DEMONSTRATION OF FURTHER PROCESSING ===")
    
    # Example 1: Find statements with the most sources
    if fact_check_data["fact_checks"]:
        most_sources = max(fact_check_data["fact_checks"], key=lambda x: len(x.get("articles", [])))
        print(f"\nStatement with most sources ({len(most_sources.get('articles', []))} articles):")
        print(f"  \"{most_sources['statement'][:100]}...\"")
    
    # Example 2: Create a knowledge graph (simplified example)
    print("\nCreating a simplified knowledge graph...")
    knowledge_graph = {
        "nodes": [],
        "edges": []
    }
    
    # Add the original article as a node
    knowledge_graph["nodes"].append({
        "id": "original_article",
        "type": "article",
        "label": "Original Article"
    })
    
    # Add sentiment analysis node
    knowledge_graph["nodes"].append({
        "id": "sentiment_analysis",
        "type": "analysis",
        "label": f"Sentiment Analysis (Score: {fact_check_data.get('sentiment_analysis', {}).get('score', 'N/A')})"
    })
    
    # Connect sentiment to original article
    knowledge_graph["edges"].append({
        "source": "original_article",
        "target": "sentiment_analysis",
        "label": "analyzed_by"
    })
    
    # Add each statement and connect to original article
    for i, check in enumerate(fact_check_data["fact_checks"]):
        statement_id = f"statement_{i}"
        knowledge_graph["nodes"].append({
            "id": statement_id,
            "type": "statement",
            "label": check["statement"][:50] + "..."
        })
        
        # Connect statement to original article
        knowledge_graph["edges"].append({
            "source": "original_article",
            "target": statement_id,
            "label": "contains"
        })
        
        # Add sources and connect to statements
        for j, article in enumerate(check.get("articles", [])):
            article_id = f"article_{i}_{j}"
            knowledge_graph["nodes"].append({
                "id": article_id,
                "type": "source",
                "label": article.get("title", "Unknown")[:50] + "..."
            })
            
            # Connect source to statement
            knowledge_graph["edges"].append({
                "source": statement_id,
                "target": article_id,
                "label": "supported_by" 
            })
    
    # Save knowledge graph to file
    graph_filename = f"knowledge_graph_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(graph_filename, "w") as f:
        json.dump(knowledge_graph, f, indent=2)
    
    print(f"Knowledge graph saved to {graph_filename}")
    print(f"Total nodes: {len(knowledge_graph['nodes'])}, Total edges: {len(knowledge_graph['edges'])}")



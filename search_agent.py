from crewai import Agent, Task, LLM, Crew, Process
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
import os
import json
import re
import datetime
from pydantic import BaseModel
load_dotenv()

# Pydantic Baseclass for JSON Schema
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


serper_key = os.getenv("SERPER_DEV_KEY")
os.environ["SERPER_API_KEY"] = serper_key  # Ensure it's available globally

# Initialize LLM with strict temperature
llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434", temperature=0.0)

# FIXED: Get raw search results directly as backup
def get_raw_news_results(topic, api_key):
    tool = SerperDevTool(
        name="DirectNewsSearch",
        parameters={'type': 'news', 'num': 10},
        api_key=api_key
    )
    # FIXED: Use named parameter search_query instead of positional argument
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

def extract_domain(url):
    match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    return match.group(1) if match else "Unknown Source"

# Define Serper news search tool
news_search_tool = SerperDevTool(
    name="SerperNewsSearch",
    description="Searches for news articles and returns titles, sources, dates, URLs, and snippets.",
    parameters={
        'type': 'news',
        'sort': 'date',
        'num': 15
    },
    api_key=serper_key
)

# Define news link retrieval agent with STRICT JSON output instructions
news_link_retriever = Agent(
    role="JSON Data Formatter",
    goal="Extract and format news data as valid JSON only, with no additional text.",
    backstory=(
        "You are a machine that only outputs valid JSON. You never explain or add commentary. "
        "You only return data in the exact JSON format specified."
    ),
    tools=[news_search_tool],
    verbose=True,
    memory=False,
    max_iter=3,
    llm=llm
)

# FIXED: Task description with proper escaping for JSON example
link_retrieval_task = Task(
    description=(
        "GET NEWS DATA AND FORMAT AS JSON: \n"
        "1. Search for news about {topic} using SerperNewsSearch\n"
        "2. Format ALL results as valid JSON matching this EXACT structure:\n"
        "```json\n"
        "{{\n"  # FIXED: Double curly braces to escape them
        '  "topic": "REPLACE_WITH_SEARCH_TOPIC",\n'
        '  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",\n'
        '  "articles": [\n'
        "    {{\n"  # FIXED: Double curly braces
        '      "title": "Article Title",\n'
        '      "source": "Publication Name",\n'
        '      "date": "Publication Date",\n'
        '      "url": "https://full.url.com",\n'
        '      "snippet": "Brief description"\n'
        "    }}\n"  # FIXED: Double curly braces
        "  ]\n"
        "}}\n"  # FIXED: Double curly braces
        "```\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "- Return ONLY JSON, no other text\n"
        "- Do NOT include explanations before or after the JSON\n"
        "- Do NOT include code block markers (```) in your response\n"
        "- Include ALL articles found in the search\n"
        "- The topic field should contain: {topic}\n"  # FIXED: No quotes
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
    verbose=True
)

# Execute with user-provided topic
search_topic = "Trump and Zelensky clash in the Oval Office"

try:
    result_output = news_links_crew.kickoff(inputs={'topic': search_topic})
    
    # Extract raw content
    if hasattr(result_output, 'raw'):
        result = result_output.raw
    else:
        result = result_output
    
    # First, find any JSON in the result
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
        parsed_json = get_raw_news_results(search_topic, serper_key)
        
    # Output the result
    result_json = json.dumps(parsed_json, indent=2)
    print("\nJSON Results:")
    print(result_json)
    
    # Save to file
    with open("news_articles.json", "w") as f:
        f.write(result_json)
    print("\nResults saved to news_articles.json")
    
except Exception as e:
    print(f"Error processing result: {str(e)}")
    # Fall back to direct API call
    backup_results = get_raw_news_results(search_topic, serper_key)
    result_json = json.dumps(backup_results, indent=2)
    
    # Save backup results to file
    with open("news_articles.json", "w") as f:
        f.write(result_json)
    print("Using backup results instead. Saved to news_articles.json")
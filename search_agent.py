from crewai import Agent, Task, LLM, Crew, Process
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
import os
import json
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
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

# Initialize LLM
llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")

# Define Serper news search tool
news_search_tool = SerperDevTool(
    name="News Search Engine",
    description="Retrieves the latest news articles, including source URLs, publication dates, and titles.",
    parameters={
        'type': 'news',
        'sort': 'date',
        'num': 15  # Ensure maximum coverage of relevant links
    },
    api_key=serper_key
)

# Define news link retrieval agent
news_link_retriever = Agent(
    role="News Link Retriever",
    goal="Extract accurate and working URLs for news articles related to a given topic.",
    backstory=(
        "A specialist in online news aggregation. Your role is to retrieve "
        "the latest and most relevant news articles and provide their direct URLs."
    ),
    tools=[news_search_tool],
    verbose=False,
    memory=False,
    max_iter=3,
    llm=llm
)

# Define task for link retrieval
link_retrieval_task = Task(
    description=(
        "Retrieve the latest news articles about {topic} using the News Search Engine. "
        "For each article, extract:\n"
        "1. Title of the article\n"
        "2. Source (publication name)\n"
        "3. Publication Date (if available)\n"
        "4. URL (full direct link to the article)\n"
        "5. Snippet or brief description (if available)\n\n"
        "Format the data as valid JSON. Include ALL search results with no filtering."
    ),
    expected_output=(
        "Strictly formatted JSON matching NewsOutputSchema structure. "
        "No markdown, only pure JSON."
    ),
    agent=news_link_retriever,
    output_json=NewsOutputSchema,  # Key structured output parameter
    constraints=[
        "No markdown formatting",
        "Strict ISO 8601 timestamps",
        "Valid URLs with HTTPS"
    ]
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
result = news_links_crew.kickoff(inputs={'topic': search_topic})

try:
    # Check the type of result first
    print(f"Result type: {type(result)}")
    
    # Handle different result types
    if isinstance(result, dict):
        # Already a dictionary object
        parsed_json = result
    elif isinstance(result, str):
        # String that might contain JSON
        # Try to extract JSON from markdown code blocks if present
        import re
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', result, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
        else:
            # If no code block markers, try to parse the whole string
            json_str = result
            
        # Clean string by removing any potential prefix/suffix text
        json_str = json_str.strip()
        
        # Try to find the beginning of JSON structure if there's prefix text
        if not json_str.startswith('{') and '{' in json_str:
            json_str = json_str[json_str.find('{'):]
            
        # Parse the JSON
        parsed_json = json.loads(json_str)
    else:
        # Handle other types by converting to string first
        parsed_json = json.loads(str(result))
    
    # Pretty print the JSON
    formatted_json = json.dumps(parsed_json, indent=2)
    print(f"\n\n### News Articles About: {search_topic} (JSON Format)\n")
    print(formatted_json)
    
    # Save to a file
    with open("news_articles.json", "w") as f:
        f.write(formatted_json)
    print("\nJSON output saved to news_articles.json")
    
except Exception as e:
    print("\nError processing result:", str(e))
    print("\nRaw output:")
    print(result)
    
    # Save the raw output for debugging
    with open("news_articles_raw.txt", "w") as f:
        f.write(str(result))
    print("\nRaw output saved to news_articles_raw.txt")
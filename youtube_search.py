from crewai_tools import YoutubeVideoSearchTool
from crewai import LLM
import os
from dotenv import load_dotenv
load_dotenv()

# Set up LLM
llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434", temperature=0.2)

tool = YoutubeVideoSearchTool(
    config=dict(
        llm=dict(
            provider="ollama", # or google, openai, anthropic, llama2, ...
            config=dict(
                model="llama2",
                # temperature=0.5,
                # top_p=1,
                # stream=true,
            ),
        ),
        embedder=dict(
            provider="google", # or openai, ollama, ...
            config=dict(
                model="models/embedding-001",
                task_type="retrieval_document",
                # title="Embeddings",
            ),
        ),
    )
)

# Test the tool
result = tool.run("What is the main topic of this video?")
print("\nTool Result:")
print(result)
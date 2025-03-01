from crewai_tools import YoutubeVideoSearchTool
from crewai import LLM
import os
import boto3
import json
from dotenv import load_dotenv
from typing import List


load_dotenv()

# Create custom Bedrock embedder - define our own base class
class BaseEmbedder:
    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError("Subclasses must implement this method")

class BedrockEmbedder(BaseEmbedder):
    def __init__(self, client, model_name):
        self.client = client
        self.model_name = model_name
        
    def embed_text(self, text: str) -> List[float]:
        response = self.client.invoke_model(
            body=json.dumps({"inputText": text}),
            modelId=self.model_name,
            accept="application/json",
            contentType="application/json"
        )
        response_body = json.loads(response.get('body').read())
        return response_body.get('embedding')

# Set up AWS client
try:
    bedrock_client = boto3.client("bedrock-runtime", 
                                region_name="us-east-1")
except Exception as e:
    print(f"Error initializing AWS Bedrock client: {e}")
    exit(1)

# Set up LLM
llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434", temperature=0.2)


# Configure the YouTube tool
tool = YoutubeVideoSearchTool(
    config=dict(
        llm=dict(
            provider="ollama",
            config=dict(
                model="llama3.2",
                base_url="http://localhost:11434",
                temperature=0.2
            )
        ),
        embedder=dict(
            provider="ollama",
            config=dict(
                model="all-minilm",
            )
        ) # Pass the embedder instance directly
    )
)

# Specify a YouTube video URL to analyze
video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Test the tool
try:
    result = tool.run(f"{video_url} - What is the main claim and factual information of this video?")
    print("\nTool Result:")
    print(result)
except Exception as e:
    print(f"Error running the tool: {e}")
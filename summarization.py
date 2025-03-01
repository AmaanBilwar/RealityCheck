import boto3
import json
import sys 
from transformers import pipeline
import os

def summarize_article_with_bedrock(article_content):
    # Initialize the Bedrock client
    bedrock_client = boto3.client("bedrock-runtime")
    
    prompt = f'''
    Please analyze the following news article and generate a summary that is brief and easy to understand for the user.

    Article: {article_content}
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
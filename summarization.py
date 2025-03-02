from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

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

def main():
    # Check if API key is in environment
    if not os.getenv('GEMINI_API_KEY'):
        print("No GEMINI_API_KEY found in environment variables.")
        if not api_key:
            print("No API key provided. Exiting.")
            return
    else:
        api_key = os.getenv('GEMINI_API_KEY')
        
    # Get the text to summarize
    text = input("Enter the text to summarize: ")
    
    # Generate and display the summary
    summary = summarization(text, api_key)
    print("\nSummary:", summary)


if __name__ == '__main__':
    main()
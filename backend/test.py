import requests

def test_api():
    # Test the root endpoint first
    root_url = "http://localhost:8000/"
    try:
        response = requests.get(root_url)
        print(f"Root endpoint status: {response.status_code}")
        print(f"Root response: {response.text}")
    except Exception as e:
        print(f"Error accessing root: {e}")
    
    # Test the /api/data endpoint
    data_url = "http://localhost:8000/api/data"
    try:
        response = requests.get(data_url)
        print(f"/api/data status: {response.status_code}")
        print(f"/api/data response: {response.text}")
    except Exception as e:
        print(f"Error accessing /api/data: {e}")
    
    # Try the news input endpoint
    news_url = "http://localhost:8000/api/news_input"
    payload = {"text": "This is a test message"}
    try:
        response = requests.post(news_url, json=payload)
        print(f"/api/news_input status: {response.status_code}")
        print(f"/api/news_input response: {response.text}")
    except Exception as e:
        print(f"Error accessing /api/news_input: {e}")

if __name__ == "__main__":
    test_api()
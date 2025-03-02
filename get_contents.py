import json


json_file = r'C:\Users\aniru\Desktop\Programming Languages Projects\RealityCheck\news_articles.json'

with open(json_file) as f:
    data = json.load(f)
    for article in data['articles']:
        print(article['url'])
        url = article['url']
    
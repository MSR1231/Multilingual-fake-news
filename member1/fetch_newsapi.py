"""
fetch_newsapi.py

Fetches English news articles from NewsAPI using the 'everything' endpoint.
Saves raw data to both JSON and CSV.
Requires 'config.yaml' in the main project folder with your NewsAPI key.
"""

import os
import requests
import json
import pandas as pd
import yaml

def fetch_news(queries, api_key, page_size=100):
    """Fetch articles from NewsAPI for each query."""
    all_articles = []
    base_url = 'https://newsapi.org/v2/everything'

    for term in queries:
        params = {
            'q': term,
            'language': 'en',  # English only
            'pageSize': page_size,
            'apiKey': api_key
        }

        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout:
            print(f"[!] Timeout while fetching '{term}'. Try again later.")
            continue
        except requests.exceptions.RequestException as e:
            print(f"[!] Request failed for '{term}': {e}")
            continue

        articles_list = data.get('articles', [])
        if not articles_list:
            print(f"[!] No articles found for '{term}'.")
            continue

        for article in articles_list:
            all_articles.append({
                'source': article.get('source', {}).get('name', ''),
                'title': article.get('title', '') or '',
                'description': article.get('description', '') or '',
                'content': article.get('content', '') or '',
                'url': article.get('url', '') or '',
                'publishedAt': article.get('publishedAt', ''),
                'query': term,
                'language': 'en'
            })

        print(f"[+] Fetched {len(articles_list)} articles for '{term}'.")

    return all_articles

def main():
    # Check if config.yaml exists
    if not os.path.exists("config.yaml"):
        print("[!] config.yaml not found. Please create it in the main project folder.")
        return

    # Load API key
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

    api_key = config.get('newsapi_key')
    if not api_key:
        print("[!] newsapi_key not found in config.yaml.")
        return

    # Queries to fetch (English only)
    queries = ["fake news", "misinformation", "politics", "technology", "health", "economy", "education", "weather"]

    # Ensure data folder exists
    os.makedirs("data/raw_api_data", exist_ok=True)

    # Fetch articles
    articles = fetch_news(queries, api_key)

    if articles:
        # Save CSV
        df = pd.DataFrame(articles)
        df.dropna(subset=['title', 'content'], inplace=True)
        csv_path = os.path.join('data', 'raw_api_data', 'newsapi_data.csv')
        df.to_csv(csv_path, index=False)
        print(f"[+] CSV saved to {csv_path} with {len(df)} articles.")

        # Save JSON
        json_path = os.path.join('data', 'raw_api_data', 'newsapi_data.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=4, ensure_ascii=False)
        print(f"[+] JSON saved to {json_path}")
    else:
        print("[!] No articles fetched from NewsAPI.")

if __name__ == "__main__":
    main()

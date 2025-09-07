"""
fetch_newsapi.py

Fetches articles from NewsAPI for given queries using the everything endpoint, and saves raw data to JSON + CSV.
Requires config.yaml to contain the API key.
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
            'language': 'en',
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

        if 'articles' not in data or not data['articles']:
            print(f"[!] No articles found for query '{term}'.")
            continue

        for article in data['articles']:
            all_articles.append({
                'source': article.get('source', {}).get('name', ''),
                'title': article.get('title', '') or '',
                'description': article.get('description', '') or '',
                'content': article.get('content', '') or '',
                'url': article.get('url', '') or '',
                'publishedAt': article.get('publishedAt', ''),
                'query': term
            })

    return all_articles, data

def main():
    # Ensure config.yaml exists
    if not os.path.exists("config.yaml"):
        print("[!] config.yaml not found. Please create it in the main project folder.")
        return

    # Load config.yaml
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

    api_key = config.get('newsapi_key')
    if not api_key:
        print("[!] newsapi_key not found in config.yaml.")
        return

    # Broader queries for better chance of results
    queries = ["fake news", "misinformation", "politics", "technology", "health"]

    # Ensure data folders exist
    os.makedirs("data/raw_api_data", exist_ok=True)

    articles, full_json = fetch_news(queries, api_key)

    # Save raw JSON
    json_path = os.path.join('data', 'raw_api_data', 'newsapi_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(full_json, f, indent=4)
    print(f"[+] Raw JSON saved to {json_path}")

    # Save to CSV
    if articles:
        df = pd.DataFrame(articles)
        df.dropna(subset=['title', 'content'], inplace=True)
        csv_path = os.path.join('data', 'raw_api_data', 'newsapi_data.csv')
        df.to_csv(csv_path, index=False)
        print(f"[+] CSV saved to {csv_path} with {len(df)} articles.")
    else:
        print("[!] No articles fetched from NewsAPI.")

if __name__ == "__main__":
    main()

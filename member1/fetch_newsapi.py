import os
import requests
import json
import pandas as pd
import yaml

def fetch_multilingual_news(queries_by_language, api_key, page_size=10):
    """Fetch articles from NewsAPI by language."""
    all_articles = []
    base_url = 'https://newsapi.org/v2/everything'

    for lang, queries in queries_by_language.items():
        for term in queries:
            params = {
                'q': term,
                'language': lang,
                'pageSize': page_size,
                'apiKey': api_key
            }

            try:
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                print(f"[!] Error fetching '{term}' in '{lang}': {e}")
                continue

            if 'articles' not in data or not data['articles']:
                print(f"[!] No articles found for '{term}' in '{lang}'")
                continue

            for article in data['articles']:
                all_articles.append({
                    'source': article.get('source', {}).get('name', ''),
                    'title': article.get('title', '') or '',
                    'description': article.get('description', '') or '',
                    'content': article.get('content', '') or '',
                    'url': article.get('url', '') or '',
                    'publishedAt': article.get('publishedAt', ''),
                    'language': lang,
                    'query': term
                })

    return all_articles

def main():
    # Load config.yaml
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

    api_key = config.get('newsapi_key')
    if not api_key:
        print("[!] newsapi_key not found in config.yaml.")
        return

    # Define multilingual queries
    queries_by_language = {
        'en': ["fake news", "politics", "technology"],
        'hi': ["फेक न्यूज़", "राजनीति", "प्रौद्योगिकी"],
        'te': ["చీలో న్యూస్", "రాజకీయాలు", "సాంకేతికత"]
    }

    os.makedirs("data/raw_api_data", exist_ok=True)

    articles = fetch_multilingual_news(queries_by_language, api_key)

    # Save to JSON
    json_path = 'data/raw_api_data/newsapi_multilang_data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)

    # Save to CSV
    if articles:
        df = pd.DataFrame(articles)
        df.dropna(subset=['title', 'content'], inplace=True)
        csv_path = 'data/raw_api_data/newsapi_multilang_data.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"[+] Saved {len(df)} articles to {csv_path}")
    else:
        print("[!] No articles fetched.")

if __name__ == "__main__":
    main()

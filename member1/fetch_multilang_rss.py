# fetch_multilang_rss.py
# Collects >=100 Hindi + Telugu news articles from Google News RSS

import os
import json
import time
import random
import html
import feedparser
import requests
import pandas as pd
from urllib.parse import quote_plus

OUTPUT_DIR = os.path.join("..", "data", "raw_api_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

LANG_CONFIG = {
    "hi": {
        "hl": "hi-IN", "gl": "IN", "ceid": "IN:hi",
        "queries": ["भारत", "राजनीति", "अर्थव्यवस्था", "टेक्नोलॉजी", "स्वास्थ्य", "मौसम", "मनोरंजन", "दिल्ली", "चुनाव"]
    },
    "te": {
        "hl": "te-IN", "gl": "IN", "ceid": "IN:te",
        "queries": ["తెలంగాణ", "రాజకీయాలు", "ఆరోగ్యం", "సాంకేతికత", "హైదరాబాద్", "ఎన్నికలు", "క్రీడలు", "వాతావరణం"]
    }
}

def parse_feed(url: str):
    fp = feedparser.parse(url, request_headers=HEADERS)
    if getattr(fp, "entries", None):
        return fp
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return feedparser.parse(r.content)
    except Exception:
        return fp

def normalize(txt):
    return html.unescape(str(txt)).strip() if txt else ""

def fetch_google_news(lang_key, cfg, target=100):
    hl, gl, ceid = cfg["hl"], cfg["gl"], cfg["ceid"]
    queries = cfg["queries"]

    results, seen = [], set()

    def add_entries(entries, source):
        nonlocal results
        for e in entries:
            link = normalize(e.get("link"))
            title = normalize(e.get("title"))
            if not title or (link and link in seen):
                continue
            results.append({
                "source": source,
                "title": title,
                "description": normalize(e.get("summary")),
                "url": link,
                "publishedAt": normalize(e.get("published", e.get("updated", ""))),
                "language": lang_key
            })
            if link:
                seen.add(link)
            if len(results) >= target:
                break

    # main feed
    fp = parse_feed(f"https://news.google.com/rss?hl={hl}&gl={gl}&ceid={ceid}")
    add_entries(fp.entries, "Google News Top")

    # queries
    for q in queries:
        if len(results) >= target:
            break
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={hl}&gl={gl}&ceid={ceid}"
        fp = parse_feed(url)
        add_entries(fp.entries, f"Google News: {q}")
        time.sleep(random.uniform(0.5, 1.0))

    return results

def main():
    all_articles = []
    per_lang = {}

    for lang, cfg in LANG_CONFIG.items():
        print(f"[+] Fetching {lang} news ...")
        articles = fetch_google_news(lang, cfg, target=100)
        per_lang[lang] = len(articles)
        all_articles.extend(articles)
        print(f"[✔] {lang}: {len(articles)} articles")

    # save
    json_path = os.path.join(OUTPUT_DIR, "rss_multilang_data.json")
    csv_path = os.path.join(OUTPUT_DIR, "rss_multilang_data.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)

    pd.DataFrame(all_articles).to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"[+] Saved JSON -> {json_path}")
    print(f"[+] Saved CSV  -> {csv_path} ({len(all_articles)} articles)")
    print(f"[=] Final counts: {per_lang}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Skincare Industry News Aggregator
Fetches latest headlines from a curated list of skincare/beauty B2B trade
publications (feeds.json) and builds a static index.html.

Runs daily via GitHub Actions at 10:30 IST (05:00 UTC).
"""
import json
import datetime
import html
import re
import time
import urllib.parse
import feedparser
import requests

FEEDS_FILE = "feeds.json"
OUTPUT_FILE = "index.html"
ARTICLES_PER_SOURCE = 6
DAYS_LOOKBACK = 10          # ignore anything older than this many days
TIMEOUT = 15
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SkincareNewsBot/1.0; +https://github.com/)"
}


def google_news_url(source):
    """Build a Google News RSS feed that searches a given site (or free query)."""
    if "site" in source:
        q = f'site:{source["site"]}'
    else:
        q = source["query"]
    q = urllib.parse.quote(q)
    return f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"


def clean_text(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(text).strip()


def fetch_source(source):
    url = source["url"] if source["type"] == "native" else google_news_url(source)
    articles = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=DAYS_LOOKBACK)

        for entry in feed.entries[: ARTICLES_PER_SOURCE * 3]:
            title = clean_text(entry.get("title", ""))
            link = entry.get("link", "")
            if not title or not link:
                continue

            published = None
            for key in ("published_parsed", "updated_parsed"):
                if entry.get(key):
                    published = datetime.datetime(*entry[key][:6])
                    break

            if published and published < cutoff:
                continue

            summary = clean_text(entry.get("summary", ""))[:220]

            # Google News titles often look like "Headline - Publisher"; trim publisher suffix
            if source["type"] == "google":
                title = re.sub(r"\s+-\s+[^-]+$", "", title)

            articles.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published": published,
                }
            )
            if len(articles) >= ARTICLES_PER_SOURCE:
                break

    except Exception as e:
        print(f"  [!] {source['name']}: {e}")

    return articles


def main():
    with open(FEEDS_FILE, "r") as f:
        sources = json.load(f)

    results = []
    for source in sources:
        print(f"Fetching: {source['name']}")
        articles = fetch_source(source)
        print(f"  -> {len(articles)} articles")
        results.append({"source": source["name"], "articles": articles})
        time.sleep(0.5)  # be polite

    build_html(results)


def build_html(results):
    now_utc = datetime.datetime.utcnow()
    now_ist = now_utc + datetime.timedelta(hours=5, minutes=30)
    timestamp = now_ist.strftime("%A, %d %B %Y — %I:%M %p IST")

    total_articles = sum(len(r["articles"]) for r in results)
    live_sources = sum(1 for r in results if r["articles"])

    cards = []
    for r in results:
        if not r["articles"]:
            continue
        items = ""
        for a in r["articles"]:
            date_str = a["published"].strftime("%d %b %Y") if a["published"] else ""
            items += f"""
            <li class="article">
              <a href="{html.escape(a['link'])}" target="_blank" rel="noopener noreferrer">{html.escape(a['title'])}</a>
              {f'<span class="date">{date_str}</span>' if date_str else ''}
              {f'<p class="summary">{html.escape(a["summary"])}</p>' if a['summary'] else ''}
            </li>"""
        cards.append(f"""
        <section class="source-card">
          <h2>{html.escape(r['source'])}</h2>
          <ul>{items}
          </ul>
        </section>""")

    cards_html = "\n".join(cards) if cards else "<p class='empty'>No articles fetched this run — check the Actions log.</p>"

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Skincare Industry Daily — {timestamp}</title>
<style>
  :root {{
    --bg: #faf7f3;
    --card-bg: #ffffff;
    --ink: #2b2320;
    --muted: #8a7d72;
    --accent: #b76e5b;
    --border: #eee2d8;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--ink);
    line-height: 1.5;
  }}
  header {{
    background: linear-gradient(135deg, #b76e5b, #d9a288);
    color: #fff;
    padding: 40px 24px 28px;
    text-align: center;
  }}
  header h1 {{
    margin: 0 0 6px;
    font-size: 1.9rem;
    letter-spacing: -0.5px;
  }}
  header p {{
    margin: 0;
    opacity: 0.92;
    font-size: 0.95rem;
  }}
  .stats {{
    max-width: 1100px;
    margin: -18px auto 0;
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
    padding: 0 16px;
  }}
  .stat-pill {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 8px 18px;
    font-size: 0.85rem;
    color: var(--muted);
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
  }}
  main {{
    max-width: 1100px;
    margin: 36px auto;
    padding: 0 16px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
  }}
  .source-card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px 22px 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
  }}
  .source-card h2 {{
    font-size: 1.05rem;
    margin: 0 0 12px;
    color: var(--accent);
    border-bottom: 2px solid var(--border);
    padding-bottom: 8px;
  }}
  .source-card ul {{
    list-style: none;
    margin: 0;
    padding: 0;
  }}
  .article {{
    padding: 10px 0 14px;
    border-bottom: 1px solid var(--border);
  }}
  .article:last-child {{ border-bottom: none; }}
  .article a {{
    color: var(--ink);
    text-decoration: none;
    font-weight: 600;
    font-size: 0.93rem;
  }}
  .article a:hover {{ color: var(--accent); text-decoration: underline; }}
  .date {{
    display: block;
    font-size: 0.72rem;
    color: var(--muted);
    margin-top: 3px;
  }}
  .summary {{
    font-size: 0.82rem;
    color: var(--muted);
    margin: 6px 0 0;
  }}
  .empty {{
    grid-column: 1 / -1;
    text-align: center;
    color: var(--muted);
  }}
  footer {{
    text-align: center;
    padding: 30px 16px 50px;
    color: var(--muted);
    font-size: 0.8rem;
  }}
</style>
</head>
<body>
<header>
  <h1>🧴 Skincare Industry Daily</h1>
  <p>Curated news for CEOs, category managers &amp; founders — updated {timestamp}</p>
</header>
<div class="stats">
  <div class="stat-pill">📰 {total_articles} articles</div>
  <div class="stat-pill">📡 {live_sources} active sources</div>
  <div class="stat-pill">🔄 Auto-updates daily, 10:30 AM IST</div>
</div>
<main>
{cards_html}
</main>
<footer>
  Built with GitHub Actions · Sources aggregated via RSS / Google News · Not affiliated with listed publications
</footer>
</body>
</html>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"\nWrote {OUTPUT_FILE} with {total_articles} articles from {live_sources} sources.")


if __name__ == "__main__":
    main()

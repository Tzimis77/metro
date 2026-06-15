"""
Thessaloniki Metro Scraper
Τρέχει σε GitHub Actions κάθε 30 λεπτά
Output: public/metro_status.json
"""
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def fetch(url, retries=3):
    for i in range(retries):
        try:
            r = SESSION.get(url, timeout=20)
            if r.status_code == 403:
                print(f"  403 on attempt {i+1}, waiting...")
                time.sleep(5 * (i + 1))
                continue
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"  Error attempt {i+1}: {e}")
            time.sleep(3)
    return None

def scrape_homepage():
    r = fetch("https://www.thessmetro.gr/")
    if not r:
        return "", False, {}

    soup = BeautifulSoup(r.text, "html.parser")

    announcement = ""
    is_disrupted = False
    keywords = ["εκτός επιβατικής", "διακοπή", "out of passenger service", "temporarily out"]
    for tag in soup.find_all(["p", "div", "span", "h2", "h3"]):
        txt = tag.get_text(" ", strip=True)
        if any(kw in txt.lower() for kw in keywords) and 30 < len(txt) < 600:
            announcement = txt
            is_disrupted = True
            break

    elevators = {}
    station_names = [
        "Νέος Σιδηροδρομικός Σταθμός", "Δημοκρατίας", "Βενιζέλου",
        "Αγίας Σοφίας", "Σιντριβάνι", "Πανεπιστήμιο",
        "Παπάφη", "Ευκλείδης", "Φλέμινγκ",
        "Ανάληψη", "25ης Μαρτίου", "Βούλγαρη", "Νέα Ελβετία"
    ]
    for li in soup.select("li"):
        txt = li.get_text(strip=True)
        classes = " ".join(li.get("class", []))
        img = li.find("img")
        img_src = ((img.get("src", "") or "") + (img.get("alt", "") or "")) if img else ""
        combined = classes + img_src
        for name in station_names:
            if name in txt:
                elevators[name] = "ektos" not in combined
                break

    return announcement, is_disrupted, elevators

def scrape_news():
    url = "https://www.thessmetro.gr/%ce%bd%ce%ad%ce%b1-%ce%b1%ce%bd%ce%b1%ce%ba%ce%bf%ce%b9%ce%bd%cf%8e%cf%83%ce%b5%ce%b9%cf%82/"
    r = fetch(url)
    if not r:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    news = []
    for article in soup.select("article")[:5]:
        title = article.find(["h2", "h3"])
        link = article.find("a")
        date = article.find("time")
        if title:
            news.append({
                "title": title.get_text(strip=True),
                "url": link["href"] if link and link.get("href") else "",
                "date": date.get("datetime", date.get_text(strip=True)) if date else ""
            })
    return news

def run():
    print(f"[{datetime.now().isoformat()}] Scraping thessmetro.gr...")

    announcement, is_disrupted, elevators = scrape_homepage()
    print(f"  status: disrupted={is_disrupted}, elevators={len(elevators)}")

    news = scrape_news()
    print(f"  news: {len(news)} articles")

    data = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "status": {
            "is_disrupted": is_disrupted,
            "announcement": announcement,
        },
        "elevators": elevators,
        "news": news,
        "stations": [
            {"id": 1,  "name": "Νέος Σιδηροδρομικός Σταθμός", "name_en": "New Railway Station"},
            {"id": 2,  "name": "Δημοκρατίας",                  "name_en": "Dimokratias"},
            {"id": 3,  "name": "Βενιζέλου",                    "name_en": "Venizelou"},
            {"id": 4,  "name": "Αγίας Σοφίας",                 "name_en": "Agias Sofias"},
            {"id": 5,  "name": "Σιντριβάνι",                   "name_en": "Sintrivani"},
            {"id": 6,  "name": "Πανεπιστήμιο",                 "name_en": "Panepistimio"},
            {"id": 7,  "name": "Παπάφη",                       "name_en": "Papafi"},
            {"id": 8,  "name": "Ευκλείδης",                    "name_en": "Efklidis"},
            {"id": 9,  "name": "Φλέμινγκ",                     "name_en": "Fleming"},
            {"id": 10, "name": "Ανάληψη",                      "name_en": "Analipsi"},
            {"id": 11, "name": "25ης Μαρτίου",                 "name_en": "25 Martiou"},
            {"id": 12, "name": "Βούλγαρη",                     "name_en": "Voulgarı"},
            {"id": 13, "name": "Νέα Ελβετία",                  "name_en": "Nea Elvetia"},
        ],
        "tickets": {
            "single_normal": 0.60,
            "single_reduced": 0.30,
            "daily_normal": 2.50,
            "bundle_11_normal": 5.80,
            "bundle_11_reduced": 2.90,
            "card_30d": {"normal": 16.00, "reduced": 8.00},
            "card_90d": {"normal": 45.00, "reduced": 22.50},
            "card_180d": {"normal": 85.00, "reduced": 42.50},
        },
        "schedule": {
            "weekday": {"first": "05:30", "last": "23:30"},
            "weekend": {"first": "06:00", "last": "23:30"},
            "frequency_min": 3.5,
            "end_to_end_min": 16
        }
    }

    import os
    os.makedirs("public", exist_ok=True)
    with open("public/metro_status.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved public/metro_status.json")
    return data

if __name__ == "__main__":
    run()

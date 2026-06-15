"""
Thessaloniki Metro Scraper
Τρέχει σε GitHub Actions κάθε 30 λεπτά
Output: public/metro_status.json
"""
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone

HEADERS = {"User-Agent": "Mozilla/5.0 (MetroThessApp/1.0 +https://github.com/YOUR_REPO)"}

def scrape_homepage():
    r = requests.get("https://www.thessmetro.gr/", headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # 1. Announcement / disruption
    announcement = ""
    is_disrupted = False
    for tag in soup.find_all(["p", "div", "span"]):
        txt = tag.get_text(" ", strip=True)
        if ("εκτός επιβατικής" in txt or "διακοπή" in txt) and 30 < len(txt) < 600:
            announcement = txt
            is_disrupted = True
            break

    # 2. Elevator status per station
    elevators = {}
    for li in soup.select("li"):
        txt = li.get_text(strip=True)
        classes = " ".join(li.get("class", []))
        img = li.find("img")
        img_src = (img.get("src", "") + img.get("alt", "")) if img else ""
        combined = classes + img_src

        station_names = [
            "Νέος Σιδηροδρομικός Σταθμός", "Δημοκρατίας", "Βενιζέλου",
            "Αγίας Σοφίας", "Σιντριβάνι", "Πανεπιστήμιο",
            "Παπάφη", "Ευκλείδης", "Φλέμινγκ",
            "Ανάληψη", "25ης Μαρτίου", "Βούλγαρη", "Νέα Ελβετία"
        ]
        for name in station_names:
            if name in txt:
                elevators[name] = "ektos" not in combined
                break

    return announcement, is_disrupted, elevators

def scrape_news():
    r = requests.get(
        "https://www.thessmetro.gr/%ce%bd%ce%ad%ce%b1-%ce%b1%ce%bd%ce%b1%ce%ba%ce%bf%ce%b9%ce%bd%cf%8e%cf%83%ce%b5%ce%b9%cf%82/",
        headers=HEADERS, timeout=15
    )
    soup = BeautifulSoup(r.text, "html.parser")
    news = []
    for article in soup.select("article")[:5]:
        title = article.find(["h2", "h3"])
        link = article.find("a")
        date = article.find("time")
        if title:
            news.append({
                "title": title.get_text(strip=True),
                "url": link["href"] if link else "",
                "date": date.get("datetime", date.get_text(strip=True)) if date else ""
            })
    return news

def run():
    print(f"[{datetime.now().isoformat()}] Scraping thessmetro.gr...")

    announcement, is_disrupted, elevators = scrape_homepage()
    news = scrape_news()

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

    print(f"✅ Done. is_disrupted={is_disrupted}, news={len(news)}, elevators={len(elevators)}")
    return data

if __name__ == "__main__":
    run()

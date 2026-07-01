"""Collecteur SADC Secretariat — appels d'offres régionaux Afrique australe.

robots.txt vérifié le 2026-06-30 : /procurement-opportunities non interdit.
Structure HTML validée : chaque AO = div.grid-item.
"""
import time
import requests
from bs4 import BeautifulSoup

BASE = "https://www.sadc.int"
LISTING = f"{BASE}/procurement-opportunities"
DELAI = 2.5
HEADERS = {"User-Agent": "LobsVeilleAO/1.0 (veille appels d'offres vétérinaires; contact: come.devalk@gmail.com)"}


def collecter(timeout=30):
    try:
        r = requests.get(LISTING, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        print(f"[SADC] erreur: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for item in soup.select("div.grid-item"):
        titre_tag = item.select_one("div.views-field-title a")
        if not titre_tag:
            continue
        titre = titre_tag.get_text(strip=True)
        href = titre_tag.get("href", "")
        lien = href if href.startswith("http") else f"{BASE}{href}"
        jour = item.select_one("div.views-field-field-closing-date.date-large")
        mois = item.select_one("div.views-field-field-closing-date-1.date-small")
        date_limite = ""
        if jour and mois:
            date_limite = f"{jour.get_text(strip=True)} {mois.get_text(strip=True)}"
        out.append({
            "source": "sadc",
            "ext_id": href,
            "pays": "",
            "organisme": "SADC Secretariat",
            "titre": titre[:300],
            "description": "",
            "type": "",
            "date_pub": "",
            "date_limite": date_limite,
            "financement": "SADC",
            "lien": lien,
            "texte_recherche": titre.lower(),
        })
        time.sleep(DELAI)
    return out

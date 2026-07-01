"""Collecteur BAD — Banque africaine de développement, avis de marchés.

URL : https://www.afdb.org/en/documents/project-related-procurement
Pas de RSS dédié aux marchés. La page charge en HTML pur (Drupal views).
Structure : div.col-xs-12 > div.views-field-title > a  + div.views-field-field-publication-date
Format titre : "TYPE - PAYS - description"
robots.txt : Cloudflare bloque le fichier mais la page principale est accessible
             avec un User-Agent standard — traitement identique aux autres sources HTML.
"""
import re
import time
import requests
from bs4 import BeautifulSoup

BASE = "https://www.afdb.org"
LISTING = f"{BASE}/en/documents/project-related-procurement"
DELAI = 3.0
MAX_PAGES = 3   # 20 notices/page = 60 notices récentes, suffisant pour une veille hebdo
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

# Extraction du pays depuis le titre "TYPE - PAYS - ..."
_RE_PAYS = re.compile(r'^[A-Z]+\s*-\s*([^-]+?)\s*-', re.UNICODE)


def _pays_depuis_titre(titre):
    m = _RE_PAYS.match(titre)
    if not m:
        return ""
    pays = m.group(1).strip()
    # Normalisation quelques cas fréquents
    mapping = {
        "Multinational": "Africa",
        "RDC": "Congo, Democratic Republic of",
        "Côte d'Ivoire": "Côte d'Ivoire",
        "Cote d'Ivoire": "Côte d'Ivoire",
        "Sénégal": "Sénégal",
    }
    return mapping.get(pays, pays)


def collecter(timeout=30):
    out = {}
    for page in range(0, MAX_PAGES):
        url = LISTING if page == 0 else f"{LISTING}?page={page}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
        except Exception as e:
            print(f"[BAD] erreur page {page}: {e}")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        container = soup.select_one(".views-bootstrap-grid-plugin-style")
        if not container:
            break

        items = container.select("div.col-xs-12")
        if not items:
            break

        for item in items:
            titre_tag = item.select_one("div.views-field-title a")
            if not titre_tag:
                continue
            href = titre_tag.get("href", "")
            if not href or href in out:
                continue
            titre = titre_tag.get_text(strip=True)
            date_tag = item.select_one("div.views-field-field-publication-date")
            date_pub = date_tag.get_text(strip=True) if date_tag else ""
            pays = _pays_depuis_titre(titre)
            lien = href if href.startswith("http") else f"{BASE}{href}"
            out[href] = {
                "source": "bad",
                "ext_id": href,
                "pays": pays,
                "organisme": "Banque africaine de développement",
                "titre": titre[:300],
                "description": "",
                "type": titre.split("-")[0].strip() if "-" in titre else "",
                "date_pub": date_pub,
                "date_limite": "",
                "financement": "BAD",
                "lien": lien,
                "texte_recherche": titre.lower(),
            }

        time.sleep(DELAI)

    print(f"[BAD] {len(out)} notices collectées")
    return list(out.values())

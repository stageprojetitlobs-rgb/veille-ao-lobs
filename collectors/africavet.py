"""Collecteur AfricaVET — appels d'offres vétérinaires Afrique.

robots.txt vérifié le 2026-06-30 : Crawl-delay: 10, aucun Disallow pertinent.
Structure : WordPress, category/jobs/markets-procurement/, articles h2 a + entry-meta.
"""
import re
import time
import requests
from bs4 import BeautifulSoup

BASE = "https://www.africavet.com"
LISTING = f"{BASE}/category/jobs/markets-procurement/"
DELAI = 10  # crawl-delay robots.txt
MAX_PAGES = 5
HEADERS = {"User-Agent": "LobsVeilleAO/1.0 (veille appels d'offres vétérinaires; contact: come.devalk@gmail.com)"}

# Tags WordPress → pays/région reconnus par filtre.py
_TAG_PAYS = {
    "djibouti": "Djibouti", "senegal": "Sénégal", "kenya": "Kenya",
    "nigeria": "Nigeria", "ghana": "Ghana", "cameroun": "Cameroun",
    "tchad": "Chad", "mali": "Mali", "niger": "Niger",
    "burkina": "Burkina Faso", "cote-d-ivoire": "Côte d'Ivoire",
    "ethiopie": "Ethiopia", "tanzanie": "Tanzania", "ouganda": "Uganda",
    "rwanda": "Rwanda", "afrique-du-sud": "South Africa",
    "zambie": "Zambia", "zimbabwe": "Zimbabwe", "angola": "Angola",
    "mozambique": "Mozambique", "madagascar": "Madagascar",
    "rdc": "Congo, Democratic Republic of",
    "afrique-de-l-ouest": "Western Africa", "ecowas": "Western Africa",
    "west-africa": "Western Africa", "afrique-australe": "Southern Africa",
    "sadc": "Southern Africa", "afrique-de-l-est": "Eastern Africa",
    "afrique-centrale": "Central Africa",
}

_MOIS = {
    "janvier": "01", "février": "02", "mars": "03", "avril": "04",
    "mai": "05", "juin": "06", "juillet": "07", "août": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12",
}

def _parse_date(txt):
    """'01 juin 2026' -> '2026-06-01'"""
    if not txt:
        return ""
    m = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", txt.strip())
    if not m:
        return txt.strip()
    j, mois, a = m.groups()
    return f"{a}-{_MOIS.get(mois.lower(), '??')}-{j.zfill(2)}"


def collecter(timeout=30):
    out = {}
    for page in range(1, MAX_PAGES + 1):
        url = LISTING if page == 1 else f"{LISTING}page/{page}/"
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 404:
                break
            r.raise_for_status()
        except Exception as e:
            print(f"[AfricaVET] erreur page {page}: {e}")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        articles = soup.select("article")
        if not articles:
            break

        for art in articles:
            titre_tag = art.select_one("h2 a, h1 a, h3 a")
            if not titre_tag:
                continue
            href = titre_tag.get("href", "")
            if not href or href in out:
                continue
            titre = titre_tag.get_text(strip=True)
            date_tag = art.select_one(".entry-meta, .post-meta, [class*='date']")
            date_pub = _parse_date(date_tag.get_text(strip=True) if date_tag else "")
            # pays : cherche dans les tags/catégories de l'article
            tags = [t.get_text(strip=True) for t in art.select("a[rel='tag'], .tag")]
            tag_slugs = [a["href"].rstrip("/").split("/")[-1]
                         for a in art.select("a[rel='tag']") if a.get("href")]
            pays = next((_TAG_PAYS[s] for s in tag_slugs if s in _TAG_PAYS), "Africa")
            desc = " ".join(tags[:5])
            out[href] = {
                "source": "africavet",
                "ext_id": href,
                "pays": pays,
                "organisme": "AfricaVET",
                "titre": titre[:300],
                "description": desc[:300],
                "type": "",
                "date_pub": date_pub,
                "date_limite": "",
                "financement": "",
                "lien": href,
                "texte_recherche": f"{titre} {desc}".lower(),
            }

        has_next = soup.select_one("a.next, a[rel='next'], .page-numbers.next")
        if not has_next:
            break
        time.sleep(DELAI)

    print(f"[AfricaVET] {len(out)} AO collectées")
    return list(out.values())

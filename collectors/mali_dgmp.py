"""Collecteur DGMP Mali — marchés publics électroniques.

URL : https://www.dgmp.gouv.ml/?q=node/71
robots.txt vérifié 2026-06-30 : Disallow uniquement /admin/, /search/, /user/*
La page charge 1800+ AO en HTML pur (tableau Drupal).
Structure : table tr avec 5 colonnes : Autorité | Service | Libellé | Date | PDF
"""
import re
import time
import requests
from bs4 import BeautifulSoup

BASE = "https://www.dgmp.gouv.ml"
LISTING = f"{BASE}/?q=node/71"
DELAI = 3.0
HEADERS = {"User-Agent": "LobsVeilleAO/1.0 (veille appels d'offres vétérinaires; contact: come.devalk@gmail.com)"}

_RE_DATE = re.compile(r'(\d{2})/(\d{2})/(\d{4})')


def _iso_date(txt):
    m = _RE_DATE.search(txt or "")
    if m:
        j, mo, a = m.groups()
        return f"{a}-{mo}-{j}"
    return txt or ""


def collecter(timeout=45):
    try:
        r = requests.get(LISTING, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        print(f"[Mali DGMP] erreur: {e}")
        return []

    soup = BeautifulSoup(r.content, "html.parser")
    rows = soup.select("table tr")
    out = {}

    for row in rows[1:]:  # skip header
        cells = row.select("td")
        if len(cells) < 4:
            continue
        autorite = cells[0].get_text(strip=True)
        service = cells[1].get_text(strip=True)
        titre = cells[2].get_text(strip=True)
        date_pub = _iso_date(cells[3].get_text(strip=True))

        # Lien PDF/DOCX dans la dernière cellule
        lien_tag = cells[-1].select_one("a")
        if lien_tag:
            href = lien_tag.get("href", "")
            lien = href if href.startswith("http") else f"{BASE}/{href.lstrip('./')}"
            ext_id = href  # URL du fichier = identifiant stable
        else:
            lien = LISTING
            ext_id = f"{autorite}|{titre}|{date_pub}"

        if not titre or ext_id in out:
            continue

        pays = "Mali"
        out[ext_id] = {
            "source": "mali_dgmp",
            "ext_id": ext_id,
            "pays": pays,
            "organisme": autorite,
            "titre": titre[:300],
            "description": service[:300],
            "type": "",
            "date_pub": date_pub,
            "date_limite": "",
            "financement": "Gouvernement malien",
            "lien": lien,
            "texte_recherche": f"{titre} {service} {autorite}".lower(),
        }

    print(f"[Mali DGMP] {len(out)} AO collectées")
    return list(out.values())

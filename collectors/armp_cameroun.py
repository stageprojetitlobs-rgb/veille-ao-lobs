"""Collecteur ARMP Cameroun — appels d'offres nationaux.

URL       : http://www.armp.cm/filtres?type=avis&val=1&page=N
robots.txt: Disallow: (vide) — tout autorisé
Stratégie : scan des 5 dernières pages (50 AOs les plus récents).
            On ne charge la fiche détail que si le MO/AC est lié à l'élevage,
            car le listing ne contient pas le titre.
"""
import re
import time
import requests
from bs4 import BeautifulSoup

BASE      = "http://www.armp.cm"
LISTING   = f"{BASE}/filtres?type=avis&val=1"
MAX_PAGES = 5
DELAI     = 2.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,*/*;q=0.8",
    "Accept-Language": "fr,en;q=0.8",
}

# Maîtres d'ouvrage à surveiller (sous-chaînes, insensibles à la casse)
_MO_CIBLES = [
    "minepia", "minader",
    "elevage", "élevage", "pêche", "peche",
    "industries animales", "betail", "bétail",
    "cheptel", "viva logone", "viva benoue", "viva bénué",
    "caisse de développement de l'elevage",
    "projet de developpement de l'elevage",
    "projet de developpement des chaines de valeur de l'elevage",
    "groupe d'initiative commune pour l'agriculture, l'elevage",
    "chambre d'agriculture, des pêches, de l'elevage",
]


def _mo_cible(mo: str) -> bool:
    m = mo.lower()
    return any(k in m for k in _MO_CIBLES)


def _extraire_blocs(soup):
    """Retourne la liste des blocs AO de la page listing."""
    return soup.find_all(
        "div",
        class_=lambda c: c and "row" in c and "mt-4" in c and "pr-3" in c,
    )


def _parse_bloc(bloc):
    """Extrait mo, dates et lien détail depuis un bloc de listing."""
    mo = date_pub = date_clo = detail_href = ""
    for row in bloc.find_all("div", class_="d-table-row"):
        cells = row.find_all("div", class_="d-table-cell")
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True)
        val   = cells[1].get_text(strip=True)
        if "MO/AC" in label:
            mo = val
        elif "Publié" in label:
            date_pub = val.split()[0] if val else ""  # "DD-MM-YYYY HH:MM:SS" → "DD-MM-YYYY"
        elif "clôture" in label:
            # La date de clôture peut être masquée (d-none) : prendre la 1re cell non-vide
            date_clo = val if val and val != "12:00:00" else ""
    for a in bloc.find_all("a", href=True):
        h = a["href"]
        if h.startswith("/details?type_publication=AO") or (
            h.startswith("http://www.armp.cm/details") and "type_publication=AO" in h
        ):
            detail_href = h
            break
    return mo, date_pub, date_clo, detail_href


def _charger_detail(url):
    """Charge la fiche AO et retourne (titre, organisme_complet, date_limite, financement)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"[ARMP-CM] erreur fiche {url}: {e}")
        return None
    soup = BeautifulSoup(r.text, "html.parser")

    titre = organisme = date_lim = financement = ""
    # L'organisme est dans un div seul avant le bloc "Avis d'Appel d'Offres"
    # Le titre est le premier <p> du bloc Objet
    main = soup.find("div", id="the_wrappper_new") or soup
    divs = main.find_all("div")
    for div in divs:
        txt = div.get_text(strip=True)
        if not organisme and re.search(r"MINIST[EÈ]RE|MINEPIA|MINADER|MAIRIE|CUD|COMMUNE", txt, re.IGNORECASE) and len(txt) < 200:
            children = [c for c in div.children if c.name]
            if not children:  # div feuille
                organisme = txt
        if "financement" in txt.lower() and len(txt) < 100:
            # "Source de financementBUDGET..." → extraire après "financement"
            m = re.search(r"financement\s*(.+)", txt, re.IGNORECASE)
            if m:
                financement = m.group(1).strip()[:60]

    # Titre : chercher la section Objet
    objet_div = None
    for div in divs:
        if re.search(r"1\.\s*Objet", div.get_text(strip=True)):
            objet_div = div
            break
    if objet_div:
        # Premier <p> de la section Objet
        p = objet_div.find("p")
        if p:
            titre = p.get_text(" ", strip=True)[:300]

    if not titre:
        # Fallback : bloc "Avis d'Appel d'Offres" → numéro + RELATIF À
        for div in divs:
            txt = div.get_text(" ", strip=True)
            if "AVIS D'APPEL D'OFFRES" in txt and "RELATIF" in txt and len(txt) < 600:
                titre = txt[:300]
                break

    return titre, organisme, date_lim, financement


def collecter(timeout=20):
    out = {}
    for page in range(1, MAX_PAGES + 1):
        url = LISTING if page == 1 else f"{LISTING}&page={page}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
        except Exception as e:
            print(f"[ARMP-CM] erreur page {page}: {e}")
            break

        soup  = BeautifulSoup(r.text, "html.parser")
        blocs = _extraire_blocs(soup)
        if not blocs:
            break

        for bloc in blocs:
            mo, date_pub, date_clo, detail_href = _parse_bloc(bloc)
            if not detail_href or not _mo_cible(mo):
                continue

            lien = detail_href if detail_href.startswith("http") else f"{BASE}{detail_href}"
            if lien in out:
                continue

            time.sleep(DELAI)
            result = _charger_detail(lien)
            if not result:
                continue
            titre, organisme, _, financement = result
            if not titre:
                continue

            # ext_id = id_publication
            m = re.search(r"id_publication=(\d+)", detail_href)
            ext_id = m.group(1) if m else detail_href

            out[lien] = {
                "source":          "armp_cameroun",
                "ext_id":          ext_id,
                "pays":            "Cameroon",
                "organisme":       organisme or mo,
                "titre":           titre,
                "description":     "",
                "type":            "Appel d'offres",
                "date_pub":        date_pub,
                "date_limite":     date_clo,
                "financement":     financement or "Budget national",
                "lien":            lien,
                "texte_recherche": titre.lower(),
            }

        time.sleep(DELAI)

    print(f"[ARMP-CM] {len(out)} AO élevage collectés")
    return list(out.values())

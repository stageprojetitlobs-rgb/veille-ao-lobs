"""Collecteur UFSA Mozambique — Unidade Funcional de Supervisão das Aquisições.

API AJAX publique : GET /query/Busca_concurso1.php?dado=&dt=
Retourne tous les concursos abertos en HTML (tableau).
robots.txt : pas de restriction sur /query/
"""
import re
import time
import requests
from bs4 import BeautifulSoup

BASE = "https://www.ufsa.gov.mz"
SEARCH_URL = f"{BASE}/query/Busca_concurso1.php"
DELAI = 2.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": f"{BASE}/concursos.php",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "text/html, */*",
}

# Mots-clés vétérinaires en portugais + anglais
KEYWORDS = [
    "veterinári", "veterinary",
    "animal", "pecuári", "gado", "bovino", "suino",
    "vacina", "vaccine",
    "antiparasit", "vermifugo", "antihelmintic",
    "medicamento veterinário", "sanidade animal",
    "ruminant", "avicul", "aves",
]


def _fetch_all():
    """Télécharge tous les concursos abertos (recherche vide = tout)."""
    r = requests.get(SEARCH_URL, params={"dado": "", "dt": ""},
                     headers=HEADERS, timeout=45)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def _parse_rows(soup):
    rows = soup.find_all("tr")
    notices = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue
        # Colonnes : [0] concurso+link, [1] objecto, [2] UGEA, [3] provincia, [4] lançamento, [5] abertura
        ref_cell = cells[0].get_text(" ", strip=True)
        obj_cell = cells[1].get_text(" ", strip=True)
        ugea = cells[2].get_text(" ", strip=True)[:150]
        provincia = cells[3].get_text(" ", strip=True) if len(cells) > 3 else ""
        lancamento = cells[4].get_text(" ", strip=True) if len(cells) > 4 else ""
        abertura = cells[5].get_text(" ", strip=True) if len(cells) > 5 else ""

        # Filtrer les lignes d'en-tête et les messages "N ITEM(NS) ENCONTRADO(S)"
        if not ref_cell or "ENCONTRADO" in ref_cell or "Concurso" in ref_cell:
            continue

        # Extraire la référence (ex: "CR41002141CC000 52026 Ver detalhes")
        ref_match = re.match(r"([A-Z0-9/\.\-_\s]+?)(?:\s+Ver detalhes)?$", ref_cell, re.IGNORECASE)
        ref = ref_match.group(1).strip() if ref_match else ref_cell[:60]

        # Lien de détail : souvent dans le <a>
        link_tag = cells[0].find("a")
        lien = link_tag["href"] if link_tag and link_tag.get("href") else ""
        if lien and not lien.startswith("http"):
            lien = f"{BASE}/{lien.lstrip('/')}"

        notices.append({
            "source":          "ufsa_mozambique",
            "ext_id":          ref,
            "pays":            "Mozambique",
            "organisme":       ugea,
            "titre":           obj_cell,
            "description":     "",
            "type":            "",
            "date_pub":        lancamento,
            "date_limite":     abertura,
            "financement":     "GOM",      # Government of Mozambique
            "lien":            lien or f"{BASE}/concursos.php",
            "texte_recherche": (obj_cell + " " + ugea).lower(),
        })
    return notices


def collecter():
    try:
        soup = _fetch_all()
    except Exception as e:
        print(f"[UFSA-MOZ] erreur réseau : {e}")
        return []

    notices = _parse_rows(soup)
    print(f"[UFSA-MOZ] {len(notices)} concursos abertos collectés")
    return notices

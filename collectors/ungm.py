"""Collecteur UNGM — UN Global Marketplace.

API  : POST https://www.ungm.org/Public/Notice/Search (AJAX, retourne HTML)
Detail: GET  https://www.ungm.org/Public/Notice/{id}
robots.txt: Disallow /UNUser/Documents/* uniquement — /Public/* autorisé
Agences couvertes : FAO, UNDP, UNICEF, WFP, WHO, UNOPS, IFAD, WB…
"""
import re
import time
import requests
from bs4 import BeautifulSoup

BASE        = "https://www.ungm.org"
SEARCH_URL  = f"{BASE}/Public/Notice/Search"
DELAI       = 2.5

HEADERS_GET  = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,*/*;q=0.8",
}
HEADERS_POST = {
    **HEADERS_GET,
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json; charset=UTF-8",
    "Referer": f"{BASE}/Public/Notice",
}

# Mots-clés à soumettre à l'API
KEYWORDS = [
    "veterinary vaccine",
    "veterinary drug",
    "animal health",
    "livestock vaccine",
    "antiparasitic",
    "vaccin vétérinaire",
    "PPR vaccine",
    "lumpy skin",
    "foot and mouth disease vaccine",
    "CBPP vaccine",
    "anthelmintic",
    "veterinary supplies",
    "Newcastle disease vaccine",
    # Kits et intrants élevage (attrapent "Livestock Toolkit", "veterinary kit", etc.)
    "veterinary kit",
    "animal health kit",
    "livestock inputs",
    "livestock medicine",
]


def _post_search(keyword, page=0, size=50):
    payload = {
        "PageIndex": page, "PageSize": size,
        "NoticeTASStatus": [], "Title": keyword,
        "DeadlineFrom": "", "DeadlineTo": "",
        "PublishedFrom": "", "PublishedTo": "",
        "SortField": "DatePublished", "SortOrder": "desc",
        "NoticeTypes": [], "Countries": [], "Agencies": [],
        "Categories": [], "IsSustainable": None,
    }
    r = requests.post(SEARCH_URL, headers=HEADERS_POST, json=payload, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def _parse_row(row):
    """Extrait titre, deadline, date_pub, pays depuis un row de listing."""
    notice_id = row.get("data-noticeid", "")
    cells = row.find_all("div", role="cell")

    title = ""
    deadline = ""
    date_pub = ""
    type_ao = ""
    ref = ""
    pays = ""

    title_el = row.find("span", class_="ungm-title")
    if title_el:
        title = title_el.get_text(strip=True)

    for cell in cells:
        data_desc = cell.get("data-description", "")
        txt = cell.get_text(" ", strip=True)
        cls = " ".join(cell.get("class", []))

        if data_desc == "Deadline" or "deadline" in cls:
            # "25-Sep-2025 14:00 (GMT 2.00) -278.84..."  → garder seulement la date
            m = re.match(r"(\d{2}-\w{3}-\d{4})", txt)
            deadline = m.group(1) if m else txt.split()[0] if txt else ""
        elif data_desc == "Reference":
            ref = txt
        elif not data_desc and txt:
            # Colonnes sans label : date_pub | type | pays (dans cet ordre approximatif)
            if re.match(r"\d{2}-\w{3}-\d{4}$", txt):
                date_pub = txt
            elif txt in ("Invitation to bid", "Request for proposal", "Expression of interest",
                         "Request for quotation", "Pre-qualification"):
                type_ao = txt
            elif len(txt) > 2 and not txt.startswith("Subscribe") and "UNGM" not in txt:
                pays = txt  # généralement le pays bénéficiaire

    lien = f"{BASE}/Public/Notice/{notice_id}"
    return notice_id, title, date_pub, deadline, pays, type_ao, ref, lien


def _charger_agence(notice_id):
    """Charge la fiche détail pour récupérer agence + pays si absent."""
    url = f"{BASE}/Public/Notice/{notice_id}"
    try:
        r = requests.get(url, headers=HEADERS_GET, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"[UNGM] erreur fiche {notice_id}: {e}")
        return "", ""
    soup = BeautifulSoup(r.text, "html.parser")
    txt = soup.get_text(" | ", strip=True)

    agence = ""
    pays = ""

    # Agence : la liste des agences UNGM est dans la nav → chercher juste après le titre
    for agency in ["FAO", "UNDP", "UNICEF", "WFP", "WHO", "UNOPS", "IFAD", "UNHCR",
                   "IAEA", "IOM", "ITC", "WB", "ILO", "UNFPA", "UNIDO"]:
        # L'agence apparaît souvent juste après le titre ou dans "Reference"
        if f" | {agency} | " in txt:
            agence = agency
            break

    # Pays bénéficiaire
    m = re.search(r"Beneficiary countr(?:y|ies) or territories?\s*:\s*\|\s*([^|]{2,60})\s*\|", txt)
    if m:
        pays = m.group(1).strip()

    return agence, pays


def collecter(timeout=20):
    out = {}

    for kw in KEYWORDS:
        try:
            soup = _post_search(kw)
        except Exception as e:
            print(f"[UNGM] erreur recherche '{kw}': {e}")
            time.sleep(DELAI)
            continue

        rows = soup.find_all("div", class_=lambda c: c and "dataRow" in c and "notice" in c)

        for row in rows:
            notice_id, title, date_pub, deadline, pays, type_ao, ref, lien = _parse_row(row)
            if not notice_id or notice_id in out:
                continue

            out[notice_id] = {
                "source":          "ungm",
                "ext_id":          notice_id,
                "pays":            pays,
                "organisme":       "",         # rempli par _charger_agence si besoin
                "titre":           title,
                "description":     "",
                "type":            type_ao,
                "date_pub":        date_pub,
                "date_limite":     deadline,
                "financement":     "UN",
                "lien":            lien,
                "texte_recherche": title.lower(),
                "_need_detail":    True,
            }

        time.sleep(DELAI)

    # Charger les fiches détail pour récupérer l'agence (seulement pour les nouvelles)
    for notice_id, rec in list(out.items()):
        if rec.pop("_need_detail", False):
            agence, pays_detail = _charger_agence(notice_id)
            if agence:
                rec["organisme"] = agence
                rec["financement"] = agence
            if pays_detail and not rec["pays"]:
                rec["pays"] = pays_detail
            # Enrichir texte_recherche avec agence + pays
            rec["texte_recherche"] = (rec["titre"] + " " + rec["pays"] + " " + agence).lower()
            time.sleep(DELAI)

    print(f"[UNGM] {len(out)} notices collectées")
    return list(out.values())

"""Collecteur NeST Tanzania — National e-Procurement System of Tanzania.

API : GraphQL sur https://nest.go.tz/gateway/nest-app/graphql (public, sans auth)
     endpoint découvert par interception réseau de l'Angular SPA.
Catégories couvertes : G (Goods) et NC (Non-Consultancy supplies)
robots.txt : pas de restriction sur /gateway/
"""
import time
import urllib.parse
import requests

BASE   = "https://nest.go.tz"
GQL_URL = f"{BASE}/gateway/nest-app/graphql"
DELAI  = 2.0

HEADERS = {
    "User-Agent":   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept":       "application/json",
    "Referer":      f"{BASE}/tenders/published-tenders",
    "Origin":       BASE,
}

_QUERY = """
query getPublishedEntityViewData($input: DataRequestInputInput, $withMetaData: Boolean) {
  items: getPublishedEntityViewData(input: $input, withMetaData: $withMetaData) {
    totalPages totalRecords currentPage hasNext
    rows: data {
      descriptionOfTheProcurement
      entityNumber
      entityType
      uuid: entityUuid
      invitationDate
      procurementCategoryAcronym: entityCategoryAcronym
      procuringEntityName
      submissionOrOpeningDate
      referenceNumber
    }
  }
}
"""


def _fetch_category(category, page_size=100):
    payload = {
        "query": _QUERY,
        "variables": {
            "input": {
                "page": 1,
                "pageSize": page_size,
                "fields": [{"fieldName": "invitationDate", "isSortable": True, "orderDirection": "DESC"}],
                "mustHaveFilters": [
                    {"fieldName": "entityStatus", "operation": "IN", "inValues": ["PUBLISHED"]},
                    {"fieldName": "entityCategoryAcronym", "operation": "EQ", "value1": category},
                ],
            }
        },
    }
    r = requests.post(GQL_URL, headers=HEADERS, json=payload, timeout=25)
    r.raise_for_status()
    d = r.json()
    items = d.get("data", {}).get("items", {})
    return items.get("rows", []), items.get("totalRecords", 0)


def _format_date(dt_str):
    """'2026-06-29T14:00' → '2026-06-29'"""
    if dt_str:
        return dt_str[:10]
    return ""


def collecter():
    out = {}

    for category in ["G", "NC"]:
        try:
            rows, total = _fetch_category(category)
        except Exception as e:
            print(f"[NeST-TZ] erreur catégorie {category}: {e}")
            time.sleep(DELAI)
            continue

        for row in rows:
            uuid = row.get("uuid", "") or row.get("entityNumber", "")
            if not uuid or uuid in out:
                continue
            ref = row.get("referenceNumber") or row.get("entityNumber") or uuid
            # NeST est une SPA Angular : l'ID du tender n'apparaît jamais dans l'URL,
            # il est passé en mémoire lors du clic depuis la liste. On ne peut donc pas
            # lier directement une page de détail — on pointe vers la liste pré-filtrée
            # sur entityNumber (referenceNumber inclut un suffixe de lot que la recherche
            # du site ne matche pas toujours).
            search_val = row.get("entityNumber") or ref
            lien = f"{BASE}/tenders/published-tenders?search={urllib.parse.quote(search_val)}"
            titre = row.get("descriptionOfTheProcurement", "")
            organisme = row.get("procuringEntityName", "")

            out[uuid] = {
                "source":          "nest_tanzania",
                "ext_id":          ref,
                "pays":            "Tanzania",
                "organisme":       organisme,
                "titre":           titre,
                "description":     "",
                "type":            row.get("entityType", ""),
                "date_pub":        _format_date(row.get("invitationDate", "")),
                "date_limite":     _format_date(row.get("submissionOrOpeningDate", "")),
                "financement":     "GOT",   # Government of Tanzania
                "lien":            lien,
                "texte_recherche": (titre + " " + organisme).lower(),
            }

        time.sleep(DELAI)

    print(f"[NeST-TZ] {len(out)} notices collectées")
    return list(out.values())

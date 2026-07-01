"""Collecteur API Banque Mondiale (notices de marchés).

Endpoint v2 : https://search.worldbank.org/api/v2/procnotices
On interroge par mots-clés vétérinaires (qterm), puis filtre.py filtre
côté client (zone + pertinence). srce=current => notices actives seulement.
"""
import re
import requests

API = "https://search.worldbank.org/api/v2/procnotices"
_HTML = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _clean(txt):
    if not txt:
        return ""
    return _WS.sub(" ", _HTML.sub(" ", txt)).strip()


def _lien(notice_id):
    return ("https://projects.worldbank.org/en/projects-operations/"
            f"procurement-detail/{notice_id}")


def collecter(mots_cles, rows=100, timeout=30):
    """Retourne une liste de notices normalisées (brutes, non filtrées)."""
    vues = {}
    for mot in mots_cles:
        params = {"format": "json", "qterm": mot, "rows": rows, "srce": "current"}
        try:
            r = requests.get(API, params=params, timeout=timeout)
            r.raise_for_status()
            data = r.json()
        except Exception as e:                      # noqa: BLE001
            print(f"[BM] erreur sur '{mot}': {e}")
            continue
        for n in data.get("procnotices", []):
            nid = n.get("id")
            if not nid or nid in vues:
                continue
            desc = _clean(n.get("bid_description") or n.get("notice_text"))
            titre = _clean(n.get("bid_description") or n.get("project_name"))
            vues[nid] = {
                "source": "banque_mondiale",
                "ext_id": nid,
                "pays": n.get("project_ctry_name", "") or "",
                "organisme": _clean(n.get("contact_organization")
                                    or n.get("project_name")),
                "titre": titre[:300],
                "description": desc[:600],
                "type": n.get("notice_type", "") or "",
                "date_pub": n.get("noticedate", "") or "",
                "date_limite": n.get("submission_deadline_date", "") or "",
                "financement": "Banque Mondiale",
                "lien": _lien(nid),
                # champ utilisé par le filtre :
                "texte_recherche": f"{n.get('project_name','')} {desc}".lower(),
            }
    return list(vues.values())

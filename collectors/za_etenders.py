"""Collecteur Afrique du Sud — National Treasury eTenders (API OCDS officielle).

API REST JSON, standard ouvert OCDS, licence libre (réutilisation commerciale OK).
Doc Swagger : https://ocds-api.etenders.gov.za/swagger/index.html

⚠️ Limite connue : ne couvre QUE les départements nationaux/provinciaux.
Ne couvre PAS les municipalités ni les entreprises publiques (Eskom, Transnet…),
qui ont leurs propres portails (hors périmètre pour l'instant).
"""
import datetime
import requests

API = "https://ocds-api.etenders.gov.za/api/OCDSReleases"


def _lien(release):
    return release.get("tender", {}).get("documents", [{}])[0].get("url", "") \
        if release.get("tender", {}).get("documents") else ""


def collecter(rows=100, timeout=30, jours=90):
    """Retourne les notices brutes (non filtrées), au format commun du pipeline."""
    today = datetime.date.today()
    date_from = (today - datetime.timedelta(days=jours)).strftime("%Y-%m-%d")
    date_to = today.strftime("%Y-%m-%d")
    params = {"pageSize": rows, "dateFrom": date_from, "dateTo": date_to}
    try:
        r = requests.get(API, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json()
    except Exception as e:                          # noqa: BLE001
        print(f"[ZA eTenders] erreur: {e}")
        return []

    out = []
    for rel in data.get("releases", data if isinstance(data, list) else []):
        tender = rel.get("tender", {}) or {}
        ext_id = rel.get("ocid") or tender.get("id") or rel.get("id")
        if not ext_id:
            continue
        titre = (tender.get("title") or "").strip()
        desc = (tender.get("description") or "").strip()
        buyer = (rel.get("buyer", {}) or {}).get("name", "")
        out.append({
            "source": "za_etenders",
            "ext_id": ext_id,
            "pays": "Afrique du Sud",
            "organisme": buyer,
            "titre": titre[:300],
            "description": desc[:600],
            "type": tender.get("mainProcurementCategory", "") or "",
            "date_pub": tender.get("tenderPeriod", {}).get("startDate", "") or "",
            "date_limite": tender.get("tenderPeriod", {}).get("endDate", "") or "",
            "financement": "Gouvernement sud-africain",
            "lien": _lien(rel) or f"https://www.etenders.gov.za/?ocid={ext_id}",
            "texte_recherche": f"{titre} {desc}".lower(),
        })
    return out

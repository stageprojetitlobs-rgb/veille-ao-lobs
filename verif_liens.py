"""Garde-fou anti-lien-mort.

Avant chaque envoi/affichage d'une AO nouvellement collectée, on vérifie que
son `lien` charge une vraie page (pas une redirection vers l'accueil du site,
symptôme observé sur NeST Tanzania : lien construit par pattern jamais
vérifié, qui redirigeait silencieusement vers la racine du domaine).

Heuristique : on suit les redirections, et si l'URL finale a un chemin vide
ou réduit à "/" alors que l'URL de départ avait un chemin plus profond,
on considère le lien suspect.
"""
import urllib.parse
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}


def lien_suspect(url, timeout=15):
    """Retourne (suspect: bool, raison: str)."""
    depart = urllib.parse.urlparse(url)
    if len(depart.path.strip("/")) == 0:
        return False, ""  # l'URL de départ est déjà une racine, rien à comparer
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    except Exception as e:
        return True, f"requête échouée : {e}"

    arrivee = urllib.parse.urlparse(r.url)
    if arrivee.netloc == depart.netloc and len(arrivee.path.strip("/")) == 0:
        return True, f"redirigé vers la racine du domaine ({r.url})"
    if r.status_code >= 400:
        return True, f"code HTTP {r.status_code}"
    return False, ""


def verifier(nouveaux):
    """Vérifie les liens d'une liste d'AO nouvelles, log les liens suspects."""
    for rec in nouveaux:
        url = rec.get("lien", "")
        if not url:
            continue
        suspect, raison = lien_suspect(url)
        if suspect:
            print(f"[LIEN SUSPECT] {rec.get('source')} / {rec.get('ext_id')} : {raison}")
            print(f"    -> {url}")

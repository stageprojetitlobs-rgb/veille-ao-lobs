"""Vérification complète des liens AVANT tout déploiement du dashboard.

Contrairement à `verif_liens.py` (qui ne vérifie que les AO nouvellement
collectées à chaque run), ce script scanne TOUTES les AO stockées dans
`ao.json` — utile avant de déployer le site publiquement, pour être sûr
qu'aucune AO déjà présente n'ait un lien mort (site changé depuis la
collecte, lien mal construit, etc.).

Usage : python3 verifier_avant_deploy.py
Code de sortie : 0 si tous les liens sont OK, 1 si au moins un est suspect
(utilisable comme étape bloquante dans un futur pipeline de déploiement).
"""
import json
import sys

import verif_liens

FICHIER_AO = "ao.json"


def main():
    with open(FICHIER_AO, encoding="utf-8") as f:
        ao_list = json.load(f)

    print(f"Vérification de {len(ao_list)} liens...")
    suspects = []
    for i, rec in enumerate(ao_list, 1):
        url = rec.get("lien", "")
        if not url:
            continue
        suspect, raison = verif_liens.lien_suspect(url)
        if suspect:
            suspects.append((rec, raison))
            print(f"[LIEN SUSPECT] {rec.get('source')} / {rec.get('ext_id')} : {raison}")
            print(f"    -> {url}")
        if i % 25 == 0:
            print(f"  ... {i}/{len(ao_list)}")

    print()
    if suspects:
        print(f"❌ {len(suspects)} lien(s) suspect(s) sur {len(ao_list)}. À corriger avant déploiement.")
        sys.exit(1)
    else:
        print(f"✅ Tous les liens ({len(ao_list)}) sont OK. Déploiement possible.")
        sys.exit(0)


if __name__ == "__main__":
    main()

# Veille AO vétérinaires — Lobs International Health

Détecte automatiquement les nouveaux appels d'offres de produits vétérinaires
(vaccins, antiparasitaires, médicaments) en Afrique, génère un dashboard HTML
et envoie un email des nouveautés.

## Fonctionnement
1. `main.py` interroge les 10 collecteurs (`collectors/`)
2. `filtre.py` élimine le bruit (services, infrastructure, hors-zone) et note la pertinence
3. Les notices déjà vues (`vus.json`) sont écartées — seules les nouvelles sont traitées
4. `dashboard.py` régénère `index.html` avec l'ensemble des AO connues (`ao.json`)
5. Un email récapitulatif est envoyé pour les nouveautés du run (si SMTP configuré)

Exécution automatique tous les jours à 20h00 UTC via **GitHub Actions**
(`.github/workflows/veille.yml`) — aucune dépendance à un Mac allumé. Le résultat
(`index.html`, `ao.json`, `vus.json`) est repoussé automatiquement dans le repo, et
publié publiquement via **GitHub Pages**.

## Arborescence
```
.
├── main.py              # orchestrateur (collecte → filtre → dashboard → email)
├── filtre.py            # zones cibles, mots-clés, scoring de pertinence
├── dashboard.py          # génère index.html à partir de ao.json
├── ao.json               # toutes les AO collectées (les plus récentes en premier)
├── vus.json              # hash des AO déjà traitées (dédoublonnage)
├── index.html             # dashboard publié (servi par GitHub Pages)
├── .env                  # config SMTP en local (jamais commité — voir .gitignore)
├── .github/workflows/veille.yml   # cron GitHub Actions (remplace le LaunchAgent macOS)
└── collectors/
    ├── worldbank.py       # API Banque Mondiale
    ├── za_etenders.py     # API OCDS — Afrique du Sud
    ├── sadc.py             # scraping — régional Afrique australe
    ├── africavet.py        # scraping — agrégateur vétérinaire Afrique
    ├── bad.py               # scraping — Banque Africaine de Développement
    ├── mali_dgmp.py          # scraping — Mali
    ├── armp_cameroun.py       # scraping — Cameroun
    ├── ungm.py                 # API AJAX — UN Global Marketplace (FAO, WFP, UNICEF...)
    ├── ufsa_mozambique.py       # API AJAX — Mozambique
    └── nest_tanzania.py          # API GraphQL — Tanzanie
```

## Lancer un run manuel
```
python3 main.py
```
Régénère `index.html` et `ao.json`, envoie l'email si des nouveautés sont trouvées.
En production (GitHub Actions), même commande, avec les secrets `.env` fournis via
les GitHub Secrets du repo (Settings → Secrets and variables → Actions).

## Configurer l'email (`.env` en local, GitHub Secrets en production)
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<ton adresse>
SMTP_PASS=<mot de passe d'application — PAS le mot de passe du compte>
MAIL_FROM=<= SMTP_USER en général>
MAIL_TO=<destinataire(s), séparés par des virgules>
```
Pour Gmail : myaccount.google.com/apppasswords (nécessite la 2FA activée).
Sans SMTP configuré, le run marche quand même : il met à jour le dashboard et saute l'email.

## Ajouter une source
Crée `collectors/ma_source.py` qui expose `collecter()` renvoyant une liste de dicts
avec les clés : `source`, `ext_id`, `pays`, `organisme`, `titre`, `description`, `type`,
`date_pub`, `date_limite`, `financement`, `lien`, `texte_recherche`.
Puis importe-le et concatène son résultat dans `main.py`. Le dédoublonnage par
`id_hash` (hash de `source|ext_id`) gère le reste automatiquement.

## Règles non négociables (voir CLAUDE.md)
- API/données officielles avant scraping
- Jamais de scraping des agrégateurs commerciaux payants (TendersOnTime, GlobalTenders, J360...)
- robots.txt + structure réelle vérifiés avant d'écrire un sélecteur HTML
- Zones cibles : Afrique Ouest / Est / Centrale / Australe (pas l'Australie)

## Vérifier les liens avant un déploiement
```
python3 verifier_avant_deploy.py
```
Scanne tous les liens de `ao.json` (pas seulement les nouveaux) et sort en erreur (code 1)
si un lien redirige vers l'accueil du site ou renvoie une erreur HTTP. À lancer avant
toute mise en ligne publique du dashboard.

## À surveiller
- Le cron GitHub Actions n'est pas garanti à la minute près (retard possible aux heures
  de forte charge GitHub) — sans impact pour une veille quotidienne. Vérifier l'onglet
  "Actions" du repo en cas de doute. `dernier_run.txt` évite un double run le même jour.
- Sources instables connues : UFSA Mozambique (timeouts serveur fréquents).

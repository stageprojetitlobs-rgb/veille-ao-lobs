# Veille AO vétérinaires — Lobs International Health

Détecte automatiquement les nouveaux appels d'offres de produits vétérinaires
(vaccins, antiparasitaires, médicaments) en Afrique, génère un dashboard HTML
et envoie un email des nouveautés.

## Fonctionnement
1. `main.py` interroge les 10 collecteurs (`collectors/`)
2. `filtre.py` élimine le bruit (services, infrastructure, hors-zone) et note la pertinence
3. Les notices déjà vues (`vus.json`) sont écartées — seules les nouvelles sont traitées
4. `dashboard.py` régénère `dashboard.html` avec l'ensemble des AO connues (`ao.json`)
5. Un email récapitulatif est envoyé pour les nouveautés du run (si SMTP configuré)

Exécution automatique tous les jours à 20h00 via un **LaunchAgent macOS**
(`~/Library/LaunchAgents/com.lobs.veille-ao.plist`) — logs dans `veille.log`.

## Arborescence
```
.
├── main.py              # orchestrateur (collecte → filtre → dashboard → email)
├── filtre.py            # zones cibles, mots-clés, scoring de pertinence
├── dashboard.py          # génère dashboard.html à partir de ao.json
├── ao.json               # toutes les AO collectées (les plus récentes en premier)
├── vus.json              # hash des AO déjà traitées (dédoublonnage)
├── veille.log            # sortie du dernier run automatique
├── .env                  # config SMTP (jamais commité — voir .gitignore)
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
Régénère `dashboard.html` et `ao.json`, envoie l'email si des nouveautés sont trouvées.

## Configurer l'email (`.env`)
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

## À surveiller
- Le LaunchAgent ne se déclenche que si le Mac est allumé et connecté à 20h00 — vérifier
  `veille.log` de temps en temps pour confirmer que les runs aboutissent.
- Sources instables connues : UFSA Mozambique (timeouts serveur fréquents).

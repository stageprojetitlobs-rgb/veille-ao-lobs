# CLAUDE.md — Pipeline de collecte des appels d'offres vétérinaires

## Mission
Collecter automatiquement les **appels d'offres de produits vétérinaires** (vaccins,
anti-infectieux, antiparasitaires, vitamines) publiés dans les zones cibles, les
dédoublonner, les scorer par pertinence, et les présenter dans un **dashboard HTML**
(`dashboard.html`) + un **email** de notification pour les nouveautés.

Société : Lobs International Health (génériques vétérinaires, marché export).

## Zones cibles (4 zones, 100% Afrique)
- Afrique de l'**Ouest** (CEDEAO/UEMOA : Sénégal, Côte d'Ivoire, Burkina, Mali, Niger, Nigeria, Ghana, Togo, Bénin…)
- Afrique de l'**Est** (Kenya, Tanzanie, Éthiopie, Ouganda, Rwanda, Burundi…)
- Afrique **Centrale** (Cameroun, Tchad, RCA, Congo, Gabon, RDC…)
- Afrique **Australe** (Afrique du Sud, Namibie, Botswana, Zambie, Zimbabwe, Mozambique, Angola, Lesotho, Eswatini, Malawi, Madagascar)

> ⚠️ PAS l'Australie (Océanie) — confusion corrigée en cours de projet, à ne pas reproduire.
> Hors périmètre confirmé : Europe de l'Est, Moyen-Orient, Chine, TED/Journal Officiel UE
> (100% pays UE, testé et écarté), IsDB/BOAD/DBSA (financent infrastructure, pas produits).

## Principes directeurs (NON négociables)
1. **API / données officielles AVANT scraping.** Si une source expose une API ou un
   export structuré, on l'utilise. On ne scrape jamais ce qu'on peut récupérer proprement.
2. **Jamais de scraping des agrégateurs commerciaux payants** (TendersOnTime, GlobalTenders,
   TendersInfo, Tender247, J360…) — exclus définitivement, même si redemandé. Leurs CGU
   l'interdisent et la donnée est derrière paywall.
3. **Respect des CGU et du `robots.txt`** de chaque source gratuite. Vérifier la structure
   HTML réelle AVANT d'écrire un sélecteur. Rate-limiting systématique entre requêtes.
4. **Rapport écrit après chaque phase, AVANT de passer à la suivante.** Arrêt et attente
   de validation entre chaque nouvelle source explorée — ne jamais enchaîner seul.

## Stack
- `requests` + `BeautifulSoup` — connecteurs API et scraping HTML
- `Playwright` — uniquement en phase d'exploration (interception réseau pour trouver
  l'API cachée derrière un portail JS) ; le collecteur final évite Playwright quand possible
- `hashlib` — dédoublonnage (`id_hash` = sha1(`source|ext_id`))
- Python 3, structure modulaire : un module par source dans `collectors/`

## Schéma de sortie (clés communes à tous les collecteurs)
Chaque `collecter()` renvoie une liste de dicts avec les clés :
`source`, `ext_id`, `pays`, `organisme`, `titre`, `description`, `type`,
`date_pub`, `date_limite`, `financement`, `lien`, `texte_recherche`.
`filtre.py` ajoute ensuite `zone`, `score`, `mots_cles` aux notices retenues.

## Filtre vétérinaire (`filtre.py`)
Deux passes : `EXCLUSION_ABSOLUE` (services, infrastructure, labo, formation… — élimine
avant tout scoring) puis `PRODUITS_TITRE` (le titre doit contenir un terme produit Lobs).
Le score final pondère les mots-clés trouvés + bonus si un terme d'ancrage animal/élevage
est présent (évite les faux positifs vaccins humains).

## Sources actives (10) — voir SOURCES.md pour le détail par source
worldbank, za_etenders, sadc, africavet, bad, mali_dgmp, armp_cameroun, ungm,
ufsa_mozambique, nest_tanzania.

## Sources explorées et écartées (ne pas retester sans raison nouvelle)
- **TED / Journal Officiel UE** : API publique fonctionnelle mais 100% pays UE/EEE, zéro AO africain.
- **SAM.gov (USAID)** : API publique fonctionnelle, mais USAID sous-traite l'achat à des
  implémenteurs (DAI, Chemonics…) qui n'achètent pas via SAM.gov — signal quasi nul en Afrique.
- **IsDB, BOAD, DBSA** : financent infrastructure, pas d'achat direct de produits vétérinaires.
- **Portails nationaux morts/inaccessibles testés** : Niger ARMP, Burkina ARCOP, Sénégal
  (marchespublics.sn, mercanet.sn), Kenya (tenders.go.ke, PPIP, PPOA — DNS mort), Éthiopie PPPA,
  Rwanda UMUCYO (DNS mort), Nigeria NOCOPO (contrats déjà attribués, pas d'AO ouverts),
  Uganda EGPU (AO présents mais aucun vétérinaire à date), ECOWAS, AU-IBAR, IFAD, DG ECHO/INTPA.

## Bugs connus corrigés
- Matching en sous-chaîne → corrigé avec regex à limites de mots (`\b...\b`) dans `filtre.py`.

## Points de vigilance opérationnelle
- Le run automatique passe par un **LaunchAgent macOS** (20h00 quotidien) — ne se déclenche
  que si la machine est allumée et connectée. Vérifier `veille.log` périodiquement.
- **UFSA Mozambique** : serveur instable, timeouts fréquents — normal, pas un bug du collecteur.
- `dashboard.html` et `ao.json` ne se mettent à jour qu'après un run réussi de `main.py` —
  toute modification de collecteur ne sera visible qu'au prochain run (auto ou manuel).

## À clarifier (en attente d'infos de Côme, ne pas deviner)
- GALVmed : confirmer s'il publie réellement des RFP exploitables ou simple veille.
- WOAH banques de vaccins (PPR/Rage) : acheteur direct identifié, format d'accès au
  portail jamais confirmé — à investiguer si prospection prioritaire dessus.

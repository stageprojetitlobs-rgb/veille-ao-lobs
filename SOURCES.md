# SOURCES.md — Qualification des sources

Statuts d'accès : `API` (officielle, structurée) · `API-AJAX` (endpoint interne non documenté,
trouvé par inspection réseau) · `SCRAPE` (HTML) · `EXCLU` (non conforme / hors périmètre).

---

## Sources actives — codées et branchées dans `main.py` (10)

| Source | Fichier | Accès | Couverture |
|---|---|---|---|
| **Banque Mondiale** | `worldbank.py` | `API` | Mondial, projets financés BM. `search.worldbank.org/api/v2/procnotices` (endpoint v2 obligatoire — le v1 ignore le filtre qterm). |
| **ZA eTenders** | `za_etenders.py` | `API` (OCDS) | Départements nationaux/provinciaux Afrique du Sud. `ocds-api.etenders.gov.za`. Ne couvre pas les municipalités ni entreprises publiques (Eskom, Transnet). |
| **SADC** | `sadc.py` | `SCRAPE` | Régional Afrique australe. `sadc.int/procurement-opportunities`. |
| **AfricaVET** | `africavet.py` | `SCRAPE` | Agrégateur vétérinaire Afrique (re-publication). Très haute pertinence (déjà filtré thématiquement à la source). |
| **BAD (AfDB)** | `bad.py` | `SCRAPE` | Projets financés Banque Africaine de Développement. |
| **Mali DGMP** | `mali_dgmp.py` | `SCRAPE` | Marchés publics Mali. |
| **ARMP Cameroun** | `armp_cameroun.py` | `SCRAPE` | Marchés publics Cameroun. |
| **UNGM** | `ungm.py` | `API-AJAX` | Agrège FAO, WFP, UNICEF, UNDP, WHO, UNOPS, IFAD… `ungm.org/Public/Notice/Search` (POST, retourne HTML). 17 mots-clés dont kits vétérinaires. **Rend FAO redondante** — ne pas scraper FAO séparément. |
| **UFSA Mozambique** | `ufsa_mozambique.py` | `API-AJAX` | Marchés publics Mozambique. `ufsa.gov.mz/query/Busca_concurso1.php`. ⚠️ Serveur instable, timeouts fréquents. |
| **NeST Tanzania** | `nest_tanzania.py` | `API` (GraphQL) | Marchés publics Tanzanie. `nest.go.tz/gateway/nest-app/graphql`, catégories Goods + Non-Consultancy. Endpoint public, pas d'auth requise. |

---

## Sources testées et écartées — ne pas retester sans fait nouveau

| Source | Raison de l'exclusion |
|---|---|
| **TED / Journal Officiel UE** | API publique fonctionnelle (`api.ted.europa.eu/v3/notices/search`), mais 100% des résultats sont des pays UE/EEE. Aucun AO africain — TED ne couvre pas la commande publique hors UE. |
| **SAM.gov (USAID)** | API publique fonctionnelle (`sam.gov/api/prod/sgs/v1/search`). USAID sous-traite l'achat aux implémenteurs de projet (DAI, Chemonics, ACDI/VOCA…) qui n'achètent pas via SAM.gov. Signal quasi nul en Afrique (résultats = ambassades US : construction, maintenance). |
| **IsDB, BOAD, DBSA** | Financent infrastructure, pas d'achat direct de produits vétérinaires. |
| **AU procurement / AU-IBAR** | Site Drupal cassé / aucun AO listé publiquement. |
| **ECOWAS** | Page procurement officielle sans AO listés. |
| **IFAD eProcurement** | 403/404 sur toutes les URLs testées. |
| **DG ECHO / INTPA (ex-DEVCO)** | Portail React sans API publique exploitable, 404/500 sur les endpoints testés. |
| **Niger ARMP** | Pages AO 404 même via Playwright (JS-rendu). |
| **Burkina ARCOP** | Catégorie "Appels d'offres" ne contient que 17 posts internes ARCOP, pas un marketplace national. |
| **Sénégal** (marchespublics.sn, mercanet.sn, asdea.sn) | DNS mort. |
| **Kenya** (tenders.go.ke, PPIP, PPOA) | DNS mort sur tous les domaines testés. |
| **Éthiopie PPPA** | DNS mort. |
| **Rwanda UMUCYO** | DNS mort. |
| **Nigeria NOCOPO** | Affiche uniquement des contrats déjà attribués (97 982 projets), pas d'AO ouverts consultables. |
| **Uganda EGPU** | Portail fonctionnel avec vraies données (20 notices testées), mais 0 AO vétérinaire à date — à resurveiller périodiquement si besoin, pas prioritaire. |
| **WOAH (site public)** | Page procurement ne montre que des décisions d'attribution passées, pas d'AO ouverts. |

---

## SIGNAL — Pas des AO à collecter, mais indicateurs à surveiller manuellement

| Source | Rôle |
|---|---|
| **OMSA/WAHIS** (foyers de maladies) | Anticipe où les campagnes de vaccination (et donc les AO) vont tomber. |
| **WOAH — Banques de vaccins PPR/Rage** | Acheteur direct confirmé (pas un simple signal), mais format d'accès au portail jamais confirmé. Les derniers appels couvraient 2022-2025 → un renouvellement est probablement dû. À investiguer si prospection prioritaire. |
| **GALVmed** | Financeur santé animale pays en développement, pas un portail d'AO classique. Statut RFP à clarifier. |

---

## EXCLU définitivement — Non conformes (paywall / CGU anti-scraping)

| Source | Raison |
|---|---|
| TendersOnTime, GlobalTenders, TendersInfo, Tender247, J360 | Agrégateurs commerciaux, données payantes, CGU interdisent le scraping. **Exclusion permanente**, même si redemandé. Utilisables manuellement uniquement, ou via pont email légitime (IMAP) si abonnement souscrit. |

---

## Doublons / pièges identifiés
- **FAO ⊂ UNGM** → ne pas collecter en double.
- **OMSA = OIE = WOAH** → une seule entité.
- **PRAPS = programme, pas portail** → ses marchés remontent via BM + AfricaVET.
- **Australie (Océanie) ≠ Afrique australe** → confusion déjà corrigée, zones cibles = 100% Afrique.

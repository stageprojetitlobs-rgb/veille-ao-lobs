"""Filtre vétérinaire + zones cibles (Afrique Ouest / Est / Centrale).

L'Australie n'est PAS couverte par la Banque Mondiale (pas un pays emprunteur)
=> elle viendra via une source dédiée (AusTender) plus tard.
"""
import re

ZONES = {
    "ouest": [
        # EN (Banque Mondiale)
        "Senegal", "Mali", "Niger", "Burkina Faso", "Cote d'Ivoire",
        "Côte d'Ivoire", "Ghana", "Nigeria", "Togo", "Benin", "Guinea",
        "Guinea-Bissau", "Liberia", "Sierra Leone", "Gambia, The",
        "Mauritania", "Western Africa",
        # FR (AfricaVET / Joffres)
        "Sénégal", "Bénin", "Guinée", "Guinée-Bissau", "Libéria", "Gambie",
        "Mauritanie", "Nigéria", "Afrique de l'Ouest",
    ],
    "est": [
        "Kenya", "Tanzania", "Ethiopia", "Uganda", "Rwanda", "Burundi",
        "South Sudan", "Sudan", "Somalia", "Eritrea", "Djibouti", "Eastern Africa",
        # FR
        "Tanzanie", "Éthiopie", "Ethiopie", "Ouganda", "Soudan du Sud",
        "Somalie", "Érythrée", "Erythree", "Afrique de l'Est",
    ],
    "centrale": [
        "Cameroon", "Chad", "Central African Republic", "Gabon",
        "Congo, Democratic Republic of", "Congo, Republic of",
        "Equatorial Guinea", "Central Africa",
        # FR
        "Cameroun", "Tchad", "République centrafricaine", "Centrafrique",
        "RDC", "République démocratique du Congo", "Congo",
        "Guinée équatoriale", "Afrique centrale",
    ],
    "australe": [
        # EN (Banque Mondiale)
        "South Africa", "Namibia", "Botswana", "Zambia", "Zimbabwe",
        "Mozambique", "Angola", "Lesotho", "Eswatini", "Malawi", "Madagascar",
        "Southern Africa",
        # FR
        "Afrique du Sud", "Namibie", "Botswana", "Zambie", "Zimbabwe",
        "Mozambique", "Angola", "Lesotho", "Eswatini", "Malawi", "Madagascar",
        "Afrique australe",
    ],
}
# libellés régionaux multi-pays (BM + agrégateurs)
GENERIQUES = {"Africa", "Western and Central Africa", "Eastern and Southern Africa",
              "Afrique", "Afrique de l'Ouest et centrale"}

_PAYS_ZONE = {p.lower(): z for z, pays in ZONES.items() for p in pays}

# Mots-clés de détection (FR + EN) — sert au scoring sur titre+description
MOTS_CLES = [
    "vaccin", "vaccination", "antiparasitaire", "vermifuge", "anthelminthique",
    "acaricide", "médicament vétérinaire", "produit vétérinaire", "santé animale",
    "vétérinaire", "peste des petits ruminants", "ppcb", "péripneumonie",
    "fièvre aphteuse", "newcastle", "rage", "brucellose", "dermatose nodulaire",
    "trypanosomose", "campagne de vaccination",
    "vaccine", "antiparasitic", "anthelmintic", "dewormer", "veterinary",
    "animal health", "ppr", "cbpp", "foot and mouth", "rabies", "brucellosis",
    "lumpy skin disease", "trypanosomiasis",
]

# Sous-ensemble envoyé à l'API en qterm (sans accents, termes porteurs)
MOTS_CLES_API = ["vaccine", "veterinary", "vaccin", "veterinaire", "antiparasitic",
                 "livestock vaccine", "PPR", "CBPP", "animal health",
                 "peste petits ruminants"]

# Ancrage "animal/élevage" : évite de remonter des vaccins HUMAINS
ANCRAGE = ["vétérinaire", "veterinary", "animal", "élevage", "elevage", "livestock",
           "cheptel", "bétail", "betail", "petits ruminants", "poultry", "volaille",
           "cattle", "bovin", "ruminant"]

# si le SEUL match est un de ces termes ambigus, exiger un ancrage animal
_AMBIGUS = {"vaccin", "vaccine", "vaccination", "rage", "rabies",
            "brucellose", "brucellosis"}

# Le titre doit contenir au moins un de ces termes : ce que Lobs vend
# (fourniture de médicaments/vaccins/antiparasitaires pour l'élevage)
PRODUITS_TITRE = [
    "vaccin", "vaccine",
    "antiparasitaire", "antiparasitic",
    "médicament vétérinaire", "veterinary drug", "veterinary medicine",
    "veterinary supplies", "veterinary inputs",
    "vermifuge", "anthelminthique", "anthelmintic", "dewormer",
    "acaricide", "ivermectin", "albendazole", "levamisole",
    "antibiotique vétérinaire", "antibiotic",
    "intrant vétérinaire", "produit vétérinaire",
    "livestock vaccine", "doses de vaccin",
    "drug", "drugs", "medicine", "medicines",
    # Kits et intrants élevage
    "veterinary kit", "animal health kit", "livestock kit", "livestock inputs",
    "livestock medicine",
]

# Exclusions ABSOLUES — hors périmètre même si "vaccin" apparaît dans le titre.
# Lobs vend des produits, pas des services ni de l'infrastructure.
EXCLUSION_ABSOLUE = [
    # Construction / travaux
    "travaux de", "construction de", "construction d'", "construction of",
    "réhabilitation", "rehabilitation", "renovation", "solarization",
    "building and installation", "establishment of cold chain",
    "cold chain facility", "cold chain equipment", "vaccine storage facility",
    "vaccine store", "vaccine production lab", "upgrading of existing vacc",
    # Consultance / études
    "recrutement", "consultant", "consulting firm", "consultancy",
    "bureau d'études", "cabinet d'études",
    "feasibility", "environmental safeguard", "design for the",
    "design for rehabilitation", "design for establishment",
    "supervision of the construction",
    # Formation / communication
    "formation des", "sensibilisation", "maquette d'information",
    "supports de campagne", "support de campagne",
    # Logistique non-produit
    "véhicule", "vehicle", "location de", "dédouanement",
    "solar panel", "solar power",
    # Diagnostic / labo (pas des médicaments)
    "réactifs", "reagent", "sérologique", "serologique",
    "sero-surveillance", "kits de diagnostic", "kits diagnostic",
    "biologie moléculaire", "pcr machine", "polymerase chain reaction",
    "laboratory equipment", "laboratory material",
    "equipment and material",  # "field equipment and laboratory material"
    # Infrastructure vétérinaire
    "postes vétérinaires", "secteurs vétérinaires",
    "veterinary clinic", "veterinary hospital", "veterinary laborator",
    "animal health clinic", "animal health post",
    "quarantine center", "quarantine centre", "livestock quarantine",
    "insémination artificielle", "artificial insemination",
    # Administratif / imprimés
    "carnets de vaccination", "carnet de vaccination",
    "masque de saisie", "élaboration d'un", "digitization",
    "enquête de base", "évaluation finale", "rapport de capitalisation",
    "étude architecturale",
    # Surveillance épidémiologique
    "post-vaccination sero", "sero-monitoring", "seromonitoring",
    "enquête sérologique",
    # Accessoires non-produits (seringues, porte-vaccins, matériel de terrain)
    "vaccine carrier", "vaccine expander", "inoculation material",
    "automatic syringe", "cold box",
    "field equipment", "scalpel",
    # Missions / protocoles
    "mission d'appui", "protocole d'accord",
    # Matériels imprimés / supports
    "supports de campagne de vaccination", "supports de camapgne",
    "production des supports", "kits aux agents",
    # Matériel de production de vaccins (pas achat de vaccins)
    "matériel pour la production de vaccin", "milieu de culture",
    "matériel complémentaire de la ferme",
    # Hiring an institution (pas un achat direct de produit)
    "hiring unops", "hiring iiam", "hiring the iiam",
]


def _titre_produit(titre):
    """Retourne True si le titre contient au moins un terme produit Lobs."""
    t = titre.lower()
    return any(p in t for p in PRODUITS_TITRE)


def _titre_exclu(titre):
    """Retourne True si le titre est hors périmètre (infra, service, conseil…)."""
    t = titre.lower()
    return any(e in t for e in EXCLUSION_ABSOLUE)


def zone_du_pays(pays):
    if not pays:
        return None
    p = pays.lower()
    if p in _PAYS_ZONE:
        return _PAYS_ZONE[p]
    if pays in GENERIQUES:
        return "régional"
    return None


def evaluer(record):
    """Retourne (pertinent: bool, score: int, mots_trouves: list)."""
    zone = zone_du_pays(record.get("pays", ""))
    if zone is None:
        return False, 0, []
    titre = record.get("titre", "")
    # Exclure services/infrastructure en priorité (absolu)
    if _titre_exclu(titre):
        return False, 0, []
    # Exiger au moins un terme produit dans le titre
    if not _titre_produit(titre):
        return False, 0, []
    texte = record.get("texte_recherche", "")
    trouves = [m for m in MOTS_CLES if re.search(r'\b' + re.escape(m) + r's?\b', texte, re.IGNORECASE)]
    if not trouves:
        return False, 0, []
    ancrage = any(re.search(r'\b' + re.escape(a) + r'\b', texte, re.IGNORECASE) for a in ANCRAGE)
    if not ancrage and set(trouves) <= _AMBIGUS:
        return False, 0, trouves
    score = min(100, len(trouves) * 20 + (20 if ancrage else 0))
    record["zone"] = zone
    return True, score, trouves

"""Surveillant AO vétérinaires — pipeline sans Excel."""
import os
import json
import hashlib
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from collectors import worldbank, za_etenders, sadc, africavet, bad, mali_dgmp, armp_cameroun, ungm, ufsa_mozambique, nest_tanzania
import filtre
import dashboard

FICHIER_VUS = "vus.json"
FICHIER_AO  = "ao.json"

def id_hash(rec):
    return hashlib.sha1(f"{rec['source']}|{rec['ext_id']}".encode()).hexdigest()[:16]

def charger_vus():
    if os.path.exists(FICHIER_VUS):
        with open(FICHIER_VUS, encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def sauver_vus(vus):
    with open(FICHIER_VUS, "w", encoding="utf-8") as f:
        json.dump(list(vus), f)

def charger_ao():
    if os.path.exists(FICHIER_AO):
        with open(FICHIER_AO, encoding="utf-8") as f:
            return json.load(f)
    return []

def sauver_ao(ao_list):
    with open(FICHIER_AO, "w", encoding="utf-8") as f:
        json.dump(ao_list, f, ensure_ascii=False, indent=2)

def envoyer_email(nouveaux):
    host = os.environ.get("SMTP_HOST")
    if not host:
        print("[mail] SMTP non configuré — configurez .env")
        return
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    pwd  = os.environ.get("SMTP_PASS")
    src  = os.environ.get("MAIL_FROM", user)
    dst  = os.environ.get("MAIL_TO", "")
    if not dst:
        print("[mail] MAIL_TO non configuré")
        return
    blocs = []
    for r in nouveaux:
        blocs.append(
            f'<tr>'
            f'<td style="padding:6px;border:1px solid #ccc">{r["date_pub"] or "—"}</td>'
            f'<td style="padding:6px;border:1px solid #ccc">{r["pays"]}</td>'
            f'<td style="padding:6px;border:1px solid #ccc">{r["titre"][:120]}</td>'
            f'<td style="padding:6px;border:1px solid #ccc">{r["date_limite"] or "Inconnu"}</td>'
            f'<td style="padding:6px;border:1px solid #ccc">{r["financement"]}</td>'
            f'<td style="padding:6px;border:1px solid #ccc"><a href="{r["lien"]}">Voir</a></td>'
            f'</tr>'
        )
    html = (
        f'<h2 style="color:#1F4E79">Veille AO vétérinaires — {len(nouveaux)} nouvelle(s)</h2>'
        f'<p>Date : {datetime.date.today()}</p>'
        '<table style="border-collapse:collapse;font-family:Arial;font-size:13px;width:100%">'
        '<tr style="background:#1F4E79;color:white">'
        '<th style="padding:8px;border:1px solid #ccc">Date pub.</th>'
        '<th style="padding:8px;border:1px solid #ccc">Pays</th>'
        '<th style="padding:8px;border:1px solid #ccc">Titre</th>'
        '<th style="padding:8px;border:1px solid #ccc">Échéance</th>'
        '<th style="padding:8px;border:1px solid #ccc">Financement</th>'
        '<th style="padding:8px;border:1px solid #ccc">Lien</th>'
        '</tr>'
        + "".join(blocs)
        + '</table><p style="color:#888;font-size:11px">Lobs Veille AO automatique.</p>'
    )
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Veille AO] {len(nouveaux)} nouvelle(s) — {datetime.date.today()}"
    msg["From"] = src
    msg["To"] = dst
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pwd)
            s.sendmail(src, [d.strip() for d in dst.split(",") if d.strip()], msg.as_string())
        print(f"[mail] envoyé à {dst}")
    except Exception as e:
        print(f"[mail] erreur : {e}")

def main():
    vus = charger_vus()
    ao_list = charger_ao()

    print("[collecte] Banque Mondiale...")
    brut = worldbank.collecter(filtre.MOTS_CLES_API)
    print("[collecte] ZA eTenders...")
    brut += za_etenders.collecter()
    print("[collecte] SADC...")
    brut += sadc.collecter()
    print("[collecte] AfricaVET...")
    brut += africavet.collecter()
    print("[collecte] BAD...")
    brut += bad.collecter()
    print("[collecte] Mali DGMP...")
    brut += mali_dgmp.collecter()
    print("[collecte] ARMP Cameroun...")
    brut += armp_cameroun.collecter()
    print("[collecte] UNGM (FAO, UNDP, WFP...)...")
    brut += ungm.collecter()
    print("[collecte] UFSA Mozambique...")
    brut += ufsa_mozambique.collecter()
    print("[collecte] NeST Tanzania...")
    brut += nest_tanzania.collecter()
    print(f"[collecte] {len(brut)} notices brutes au total")

    nouveaux = []
    now = datetime.datetime.now().isoformat(timespec="seconds")
    for rec in brut:
        ok, score, mots = filtre.evaluer(rec)
        if not ok:
            continue
        rec["id_hash"] = id_hash(rec)
        if rec["id_hash"] in vus:
            continue
        rec["score"] = score
        rec["mots_cles"] = mots
        rec["date_collecte"] = now
        nouveaux.append(rec)
        vus.add(rec["id_hash"])

    print(f"[filtre] {len(nouveaux)} nouvelle(s) AO pertinente(s)")

    if nouveaux:
        ao_list = nouveaux + ao_list  # les plus récentes en premier
        sauver_ao(ao_list)
        sauver_vus(vus)
        dashboard.generer(ao_list)
        envoyer_email(nouveaux)
    else:
        print("Rien de nouveau.")

if __name__ == "__main__":
    main()

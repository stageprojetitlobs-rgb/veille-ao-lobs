"""Générateur de dashboard HTML — appelé par main.py après chaque collecte."""
import datetime
import re

FICHIER_HTML = "index.html"

_MOIS_EN = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
            "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}

def _parse_date(val):
    if not val:
        return datetime.datetime.min
    s = str(val).strip()
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m:
        return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r'(\d{1,2})-([A-Za-z]{3})-(\d{4})', s)
    if m:
        mo = _MOIS_EN.get(m.group(2).lower(), 0)
        if mo:
            return datetime.datetime(int(m.group(3)), mo, int(m.group(1)))
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', s)
    if m:
        return datetime.datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return datetime.datetime.min

def generer(ao_list):
    if not ao_list:
        return

    rows = sorted(ao_list, key=lambda r: _parse_date(r.get("date_pub")), reverse=True)
    total = len(rows)
    sources = {}
    for r in rows:
        s = r.get("source", "?")
        sources[s] = sources.get(s, 0) + 1

    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    lignes_html = []
    for r in rows:
        lien  = r.get("lien") or "#"
        titre = r.get("titre") or ""
        mots  = r.get("mots_cles")
        if isinstance(mots, list):
            mots = ", ".join(mots)
        date_lim = r.get("date_limite") or ""
        date_lim_html = date_lim if date_lim else "<span style='color:#aaa;font-style:italic'>Inconnu</span>"
        lignes_html.append(f"""
        <tr style="border-bottom:1px solid #dee2e6">
          <td style="padding:10px 8px;white-space:nowrap">{r.get("date_pub") or "—"}</td>
          <td style="padding:10px 8px;white-space:nowrap">{date_lim_html}</td>
          <td style="padding:10px 8px"><b>{r.get("pays") or "—"}</b><br><small style="color:#6c757d">{r.get("zone") or ""}</small></td>
          <td style="padding:10px 8px;max-width:400px">
            <a href="{lien}" target="_blank" style="color:#0563C1;text-decoration:none;font-weight:500">{titre[:120]}</a>
            <br><small style="color:#6c757d">{r.get("organisme") or ""}</small>
          </td>
          <td style="padding:10px 8px"><small>{mots or ""}</small></td>
          <td style="padding:10px 8px"><span style="background:#e9ecef;padding:2px 6px;border-radius:4px;font-size:11px">{r.get("source") or ""}</span></td>
        </tr>""")

    sources_html = "".join(
        f'<span style="background:#1F4E79;color:#fff;padding:4px 12px;border-radius:20px;font-size:13px;margin:2px">{s} <b>({n})</b></span>'
        for s, n in sorted(sources.items(), key=lambda x: -x[1])
    )

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Veille AO Vétérinaires — Lobs</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f4f6f9; color: #333; }}
  .header {{ background: #fff; color: #1a1a1a; padding: 16px 32px; display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #e5e7eb; }}
  .header-left {{ display:flex; align-items:center; gap:14px; }}
  .header-left img {{ height: 40px; width: 40px; border-radius: 50%; object-fit: cover; }}
  .header h1 {{ font-size: 17px; font-weight: 700; color: #1a1a1a; }}
  .header small {{ font-size: 12px; color: #8a8f98; font-weight: 400; }}
  .header .badge {{ text-align:right; }}
  .header .badge .n {{ font-size:24px; font-weight:700; color:#1F4E79; }}
  .header .badge .l {{ font-size:12px; color:#8a8f98; }}
  .stats {{ display: flex; gap: 16px; padding: 20px 32px; flex-wrap: wrap; }}
  .stat {{ background: #fff; border-radius: 10px; padding: 16px 24px; box-shadow: 0 1px 4px rgba(0,0,0,.08); min-width: 140px; }}
  .stat .n {{ font-size: 32px; font-weight: 700; color: #1F4E79; }}
  .stat .l {{ font-size: 12px; color: #6c757d; margin-top: 2px; }}
  .sources {{ padding: 0 32px 16px; display:flex; flex-wrap:wrap; gap:6px; }}
  .filters {{ padding: 0 32px 12px; display:flex; gap:8px; flex-wrap:wrap; align-items:center; }}
  .filters input {{ padding: 8px 14px; border: 1px solid #ced4da; border-radius: 6px; font-size: 14px; width: 280px; }}
  .filters select {{ padding: 8px 12px; border: 1px solid #ced4da; border-radius: 6px; font-size: 14px; }}
  .table-wrap {{ padding: 0 32px 32px; overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.08); overflow: hidden; }}
  thead tr {{ background: #1F4E79; color: #fff; }}
  thead th {{ padding: 12px 8px; text-align: left; font-size: 13px; font-weight: 600; white-space: nowrap; }}
  tbody tr:hover {{ background: #f8f9fa; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <img src="logo.png" alt="Lobs">
    <div>
      <h1>Lobs</h1>
      <small>Veille AO Vétérinaires — mise à jour {now}</small>
    </div>
  </div>
  <div class="badge">
    <div class="n">{total}</div>
    <div class="l">AO totales</div>
  </div>
</div>

<div class="stats">
  <div class="stat"><div class="n">{total}</div><div class="l">Total AO</div></div>
  <div class="stat"><div class="n">{len(sources)}</div><div class="l">Sources actives</div></div>
</div>

<div class="sources">{sources_html}</div>

<div class="filters">
  <input type="text" id="search" placeholder="Filtrer par pays, titre, mots-clés..." oninput="filtrer()">
  <select id="sel-source" onchange="filtrer()">
    <option value="">Toutes les sources</option>
    {"".join(f'<option value="{s}">{s}</option>' for s in sorted(sources))}
  </select>
  <span id="count" style="color:#6c757d;font-size:13px"></span>
</div>

<div class="table-wrap">
<table id="table-ao">
  <thead>
    <tr>
      <th>Date pub.</th>
      <th>Échéance</th>
      <th>Pays / Zone</th>
      <th>Titre / Organisme</th>
      <th>Mots-clés</th>
      <th>Source</th>
    </tr>
  </thead>
  <tbody id="tbody">
    {"".join(lignes_html)}
  </tbody>
</table>
</div>

<script>
function filtrer() {{
  const q = document.getElementById('search').value.toLowerCase();
  const src = document.getElementById('sel-source').value;
  const rows = document.querySelectorAll('#tbody tr');
  let visible = 0;
  rows.forEach(r => {{
    const txt = r.textContent.toLowerCase();
    const ok = (!q || txt.includes(q)) && (!src || txt.includes(src));
    r.style.display = ok ? '' : 'none';
    if (ok) visible++;
  }});
  document.getElementById('count').textContent = visible + ' AO affichées';
}}
filtrer();
</script>
</body>
</html>"""

    with open(FICHIER_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[dashboard] {FICHIER_HTML} généré ({total} AO)")

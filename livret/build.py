#!/usr/bin/env python3
"""Génère livret/livret.html (livret famille) à partir des fichiers Markdown du dépôt.
Usage : python3 livret/build.py
"""
import html, json, os, re, subprocess, pathlib, datetime, sys, unicodedata, urllib.parse

ROOT_OUTILS = pathlib.Path(__file__).resolve().parent.parent / "outils"
sys.path.insert(0, str(ROOT_OUTILS))
from generer_voix import fichiers_scripts, nom_propre, nettoyer, VERSIONS, SCENE_RE, VERSION_RE, BLOC_RE  # même numérotation que la génération

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "livret" / "livret.html"

ROLES = {  # clé -> (libellé, variable de couleur)
    "NARRATEUR": ("Narrateur", "narr"), "ROMY": ("Romy", "romy"), "ALIX": ("Alix", "alix"),
    "ROMY ET ALIX": ("Romy et Alix", "romy"), "MATHÉO": ("Mathéo", "matheo"), "PAPIC": ("Papic", "papic"),
    "MAMILY": ("Mamily", "mamily"), "TATA BÊTISE": ("Tata Bêtise", "tata"), "PAILLETTE": ("Paillette", "paillette"),
    "GRUMO": ("Grumo", "grumo"), "TOUS": ("Tous", "narr"), "PÈRE NOËL": ("Père Noël", "papic"),
    "PIPOU": ("Pipou", "paillette"), "MAMAN DAUPHIN": ("Maman dauphin", "paillette"),
    "NOISETTE": ("Noisette", "grumo"), "LE CRABE": ("Le crabe", "tata"), "LE POISSON ROUGE": ("Le poisson rouge", "tata"),
}
FILTER = ["NARRATEUR", "PAPIC", "MAMILY", "TATA BÊTISE", "ROMY", "ALIX", "MATHÉO", "PAILLETTE", "GRUMO", "PÈRE NOËL"]
ROLE_RE = re.compile(r"^([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ' ]{3,}?)(\s*\([^)]*\))?\s*:\s(.*)$")
TAG_RE = re.compile(r"\[(×3|×compagnon|commun)\]")
OV = {  # balises OmniVoice -> libellé affiché dans le livret
    "laughter": "rire", "sigh": "soupir", "surprise-oh": "oh !", "surprise-ah": "ah !", "surprise-wa": "waouh !",
    "surprise-yo": "oh !", "dissatisfaction-hnn": "hmm…", "confirmation-en": "mm-hm", "question-en": "hein ?",
    "question-ah": "ah ?", "question-oh": "oh ?", "question-ei": "hein ?", "question-yi": "hein ?",
}
OV_RE = re.compile(r"\[(" + "|".join(map(re.escape, OV)) + r")\]\s?")

def index_audio():
    """{'H1-1-Romy_04_Paillette': [nom de fichier, ...]} pour toutes les prises présentes dans le Drive."""
    try:
        cfg = json.loads((ROOT_OUTILS / "voix.json").read_text(encoding="utf-8"))
        audio = pathlib.Path(os.environ.get("LIVRET_AUDIO") or cfg["drive_audio"]).expanduser()
    except Exception:
        return {}
    idx = {}
    dossiers = [*audio.glob("H* */1 – Prises"), *audio.glob("* Menus/1 – Prises")] if audio.is_dir() else []
    for d in sorted(dossiers):
        for f in sorted(d.iterdir()):
            m = re.match(r"^((?:H\d+-\d+[a-z]?(?:-[^_]+)?|Menu\d-[^_]+|Fin-[^_]+)_\d\d_[^_]+)_(.+)\.(wav|mp3|m4a)$", f.name)
            if m:
                idx.setdefault(m.group(1), []).append(f)
    return idx

AUDIO = index_audio()

def dossier_audio():
    try:
        cfg = json.loads((ROOT_OUTILS / "voix.json").read_text(encoding="utf-8"))
        a = pathlib.Path(os.environ.get("LIVRET_AUDIO") or cfg["drive_audio"]).expanduser()
        return a if a.is_dir() else None
    except Exception:
        return None

def index_montages():
    """Montages exportés (.wav/.mp3) et projets Audacity (.aup3/.aup4), par nom en minuscules."""
    mont, proj = {}, set()
    audio = dossier_audio()
    if not audio:
        return mont, proj
    for d in sorted(audio.glob("*/*")):
        nom = unicodedata.normalize("NFC", d.name)
        if not d.is_dir() or not re.match(r"^[23] – (Projets Audacity|Montés)", nom):
            continue
        for f in d.iterdir():
            cle = unicodedata.normalize("NFC", f.stem).lower()
            if f.suffix.lower() in (".wav", ".mp3", ".m4a"):
                # le MP3 Lunii (dossier « 3 – Montés ») passe devant le .wav de travail
                if cle not in mont or "Montés" in nom:
                    mont[cle] = f
            elif f.suffix.lower() in (".aup3", ".aup4", ".aup"):
                proj.add(cle)
    return mont, proj

MONTAGES, PROJETS = index_montages()

try:  # même découpage que la création des projets Audacity (segments et 3 parcours par histoire)
    from creer_projets_audacity import scenes as _scenes, plan_segments, plan_completes
    _STRUCT = _scenes(None)
    SEGMENTS = {}
    for nom, hid, _ in plan_segments(_STRUCT):
        SEGMENTS.setdefault(hid, []).append(nom)
    PARCOURS = {}
    for nom, hid, parcours in plan_completes(_STRUCT):
        PARCOURS.setdefault(hid, []).append((nom, [n for n, _ in parcours]))
except Exception as e:  # pragma: no cover
    print("(avancement du montage indisponible :", e, ")")
    SEGMENTS, PARCOURS = {}, {}
PARCOURS_NOMS = ["Romy", "Alix", "Les deux"]

def lien_drive(f):
    fid = drive_id(f)
    return (f"https://drive.google.com/file/d/{fid}/view" if fid
            else "https://drive.google.com/drive/search?q=" + urllib.parse.quote(unicodedata.normalize("NFC", f.stem)))

def etat_segment(nom):
    """('monte', fichier) | ('projet', None) | ('afaire', None)"""
    cle = unicodedata.normalize("NFC", nom).lower()
    if cle in MONTAGES:
        return "monte", MONTAGES[cle]
    return ("projet" if cle in PROJETS else "afaire"), None

def puce_segment(nom):
    etat, f = etat_segment(nom)
    if etat == "monte":
        return f'<a class="etat monte" href="{lien_drive(f)}" target="_blank" rel="noopener" title="Montage exporté : {html.escape(f.name)}">✓ monté ▶</a>'
    if etat == "projet":
        return '<span class="etat projet" title="Le projet Audacity existe, le montage n\'est pas encore exporté en .wav">◐ en montage</span>'
    return '<span class="etat afaire">○ à monter</span>'

def drive_id(f):
    """Identifiant Google Drive du fichier (attribut posé par Google Drive pour ordinateur), sinon None."""
    try:
        out = subprocess.run(["xattr", "-p", "com.google.drivefs.item-id#S", str(f)], capture_output=True, text=True)
        return out.stdout.strip() or None
    except Exception:
        return None

def audio_links(cle):
    files = AUDIO.get(cle, [])
    if not files:
        return ""
    liens = []
    for f in files:
        prise = f.stem[len(cle) + 1:]
        lab = prise.replace("omnivoice", "IA ").replace("prise", "voix ").replace("_OK", " ✓")
        url = lien_drive(f)
        ok = " ok" if prise.endswith("_OK") else ""
        liens.append(f'<a class="play{ok}" href="{url}" target="_blank" rel="noopener" title="{html.escape(f.name)}">▶ {html.escape(lab)}</a>')
    return '<span class="audio">' + "".join(liens) + "</span>"

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\{([A-Z_]+)\}", r'<mark class="todo">\1</mark>', t)
    t = OV_RE.sub(lambda m: f'<span class="ov" title="Balise OmniVoice : {m.group(1)}">{OV[m.group(1)]}</span> ', t)
    t = re.sub(r"\[([^\]]+)\]", r'<span class="sfx">\1</span>', t)
    return t

SFX_RE = re.compile(r"\[([^\]]+)\]")

def sfx_items(texte):
    """Bruitages (crochets en français) d'un texte, hors balises OmniVoice et étiquettes de scène."""
    return [("sfx", m.group(1)) for m in SFX_RE.finditer(texte)
            if m.group(1) not in OV and not TAG_RE.fullmatch(m.group(0))]

def rendre_section(sec):
    """Encadre chaque bloc avec le MP3 qu'il sert à monter, puis ajoute l'ordre de montage."""
    scene, blocs = sec["scene"], [b for b in sec["blocs"] if b["html"]]
    variantes = [b["var"] for b in blocs if b["kind"] == "variant"]
    cibles = [f"{scene}-{v}" for v in dict.fromkeys(variantes)] or [scene]
    html_out = [sec["head"]]
    for b in blocs:
        if b["kind"] == "variant":
            tag, cls = f"🎬 {scene}-{b['var']}.mp3", "bloc"
        elif variantes:
            tag, cls = "Commun → à recoller dans " + ", ".join(f"{c}.mp3" for c in cibles), "bloc commun"
        else:
            tag, cls = f"🎬 {scene}.mp3", "bloc"
        etat = puce_segment(f"{scene}-{b['var']}" if b["kind"] == "variant" else scene) if not (b["kind"] != "variant" and variantes) else ""
        html_out.append(f'<div class="{cls}"><span class="bloc-tag">{html.escape(tag)}{etat}</span>{"".join(b["html"])}</div>')
    recap = []
    for c in cibles:
        v = c[len(scene) + 1:] if c != scene else None
        items = [it for b in blocs if b["kind"] != "variant" or b["var"] == v for it in b["items"]]
        if not items:
            continue
        lis = []
        for it in items:
            if it[0] == "sfx":
                lis.append(f'<li class="r-sfx">🔔 Bruitage : {html.escape(it[1])}</li>')
            else:
                _, cle, qui, texte, son = it
                court = texte if len(texte) <= 60 else texte[:57].rsplit(" ", 1)[0] + "…"
                lis.append(f'<li><code>{html.escape(cle)}</code> <b>{html.escape(qui)}</b> {html.escape(court)}{son}</li>')
        recap.append(f'<p class="r-mp3"><b>{html.escape(c)}.mp3</b> {puce_segment(c)} <span>projet Audacity « {html.escape(c)} »</span></p><ol>{"".join(lis)}</ol>')
    if recap:
        n = len(recap)
        html_out.append(f'<details class="recap"><summary>🎬 Ordre de montage : {n} fichier{"s" if n > 1 else ""} MP3</summary>{"".join(recap)}</details>')
    return "".join(html_out)

def story(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    sid = path.stem.split("-")[0].lower()
    out, meta, title, narr = [], [], "", ""
    scene, variante, compteur, nb, nb_audio = None, None, {}, 0, 0
    sec = None  # section (### …) en cours : ses blocs sont encadrés à la fin

    def ajoute(h, items=()):
        if sec:
            sec["blocs"][-1]["html"].append(h)
            sec["blocs"][-1]["items"].extend(items)
        else:
            out.append(h)

    def nouveau_bloc(kind, var=None):
        sec["blocs"].append(dict(kind=kind, var=var, html=[], items=[]))

    for ln in lines:
        s = ln.strip()
        if not s or s == "---":
            continue
        if s.startswith("# "):
            title = s[2:]
        elif s.startswith("- ") and not out and not sec:
            if s.startswith("- Narrateur : "):
                narr = s[len("- Narrateur : "):].strip()
            meta.append(f"<li>{inline(s[2:])}</li>")
        elif s.startswith("Déroulé"):
            ajoute(f'<p class="flow">{inline(s)}</p>')
        elif s.startswith("### "):
            if sec:
                out.append(rendre_section(sec))
            m = SCENE_RE.match(s)
            scene, variante = (m.group(1) if m else None), None
            h = s[4:]
            m = TAG_RE.search(h)
            tag = ""
            if m:
                label = {"×3": "3 versions", "×compagnon": "1 par compagnon", "commun": "une fois"}[m.group(1)]
                tag = f'<span class="tag">{label}</span>'
                h = TAG_RE.sub("", h).strip()
            sec = dict(scene=scene or h, head=f"<h4>{inline(h)} {tag}</h4>", blocs=[])
            nouveau_bloc("main")
        elif sec and s.startswith("**") and s.endswith("**"):
            v = s[2:-2].strip()
            variante = VERSIONS.get(v.lower()) or nom_propre(v.upper())
            nouveau_bloc("variant", variante)
            ajoute(f'<p class="variant">{inline(s[2:-2])}</p>')
        elif sec and s.startswith("*(") and s.endswith(")*"):
            variante = "commun"
            nouveau_bloc("commun")
            ajoute(f'<p class="note">{inline(s[2:-2])}</p>')
        elif s.startswith("[") and s.endswith("]") and "]" not in s[1:-1]:
            ajoute(f'<p class="sfxline">{inline(s)}</p>', sfx_items(s))
        else:
            m = ROLE_RE.match(s)
            if m and m.group(1).strip() in ROLES:
                key = m.group(1).strip()
                label, color = ROLES[key]
                if key == "NARRATEUR" and narr:
                    label = f"Narrateur · {narr}"
                    color = {"Papic": "papic", "Mamily": "mamily"}.get(narr, color)
                son, items = "", []
                if scene and nettoyer(m.group(3)):
                    seg = scene + (f"-{variante}" if variante else "")
                    compteur[seg] = compteur.get(seg, 0) + 1
                    cle = f"{seg}_{compteur[seg]:02d}_{nom_propre(key)}"
                    son = audio_links(cle)
                    nb += 1
                    nb_audio += bool(son)
                    items.append(("ligne", cle, label, nettoyer(SFX_RE.sub("", m.group(3))), son))
                items += sfx_items(m.group(3))
                how = f' <em>{html.escape(m.group(2).strip())}</em>' if m.group(2) else ""
                ajoute(f'<div class="line" data-role="{key}" style="--rc:var(--{color})">'
                       f'<span class="who">{label}{how}</span><span class="say">{inline(m.group(3))}{son}</span></div>', items)
            else:
                ajoute(f"<p>{inline(s)}</p>")
    if sec:
        out.append(rendre_section(sec))
    num = "M" if sid.startswith("menu") else sid.upper()
    short = title.split("–", 1)[-1].strip()
    st = avancement(sid.upper(), nb, nb_audio)
    body = (f'<article class="story" id="{sid}" data-narr="{narr.upper()}"><header><p class="num">{num}</p><h2>{html.escape(short)}</h2>'
            f'<ul class="meta">{"".join(meta)}</ul>{st["bloc"]}</header>{"".join(out)}'
            f'<p class="top"><a href="#sommaire">Retour au sommaire</a></p></article>')
    return sid, num, short, body, st

def jauge(fait, total):
    pc = round(100 * fait / total) if total else 0
    cls = " fini" if total and fait >= total else ""
    return (f'<span class="jauge{cls}" role="img" aria-label="{fait} sur {total}"><span style="width:{pc}%"></span></span>'
            f'<span class="nb">{fait}/{total}</span>')

def avancement(hid, nb, nb_audio):
    """Voix, segments montés et histoires complètes d'une histoire (ou des menus)."""
    segs = SEGMENTS.get(hid, [])
    etats = [etat_segment(n)[0] for n in segs]
    montes = etats.count("monte")
    completes = []
    for k, (nom, parcours) in enumerate(PARCOURS.get(hid, [])):
        etat, f = etat_segment(nom)
        lab = PARCOURS_NOMS[k] if k < len(PARCOURS_NOMS) else str(k + 1)
        chemin = " → ".join(parcours)
        if etat == "monte":
            completes.append(f'<a class="complete ok" href="{lien_drive(f)}" target="_blank" rel="noopener" '
                             f'title="{html.escape(nom)} : {html.escape(chemin)}">▶ {lab}</a>')
        else:
            quoi = "projet créé, pas encore exporté" if etat == "projet" else "pas encore montée"
            completes.append(f'<span class="complete" title="{html.escape(nom)} ({quoi}) : {html.escape(chemin)}">'
                             f'{"◐" if etat == "projet" else "○"} {lab}</span>')
    nc = sum("ok" in c for c in completes)
    lignes = [f'<div class="av-l"><span class="av-k">Voix</span>{jauge(nb_audio, nb)}</div>']
    if segs:
        lignes.append(f'<div class="av-l"><span class="av-k">Montage</span>{jauge(montes, len(segs))}</div>')
    if completes:
        lignes.append(f'<div class="av-l"><span class="av-k">Histoire complète</span><span class="completes">{"".join(completes)}</span></div>')
    bloc = f'<div class="av">{"".join(lignes)}</div>' if nb else ""
    return dict(nb=nb, voix=nb_audio, segs=len(segs), montes=montes, nc=nc, ncomp=len(completes),
                completes="".join(completes), bloc=bloc)

def doc(path, anchor):
    try:  # bibliothèque Python « markdown » (installée par publier.sh), sinon pandoc
        import markdown
        texte = path.read_text(encoding="utf-8")
        # comme GitHub : une liste peut suivre un paragraphe sans ligne vide
        texte = re.sub(r"(?m)^(?![-*] |\d+\. |\s*$|\|)(.+)\n(?=[-*] |\d+\. )", r"\1\n\n", texte)
        texte = re.sub(r"(?m)^  ([-*] )", r"    \1", texte)  # sous-listes indentées de 2 espaces
        texte = re.sub(r"(?m)^([-*]) \[([ xX])\] ", lambda m: m.group(1) + (" ☑ " if m.group(2) != " " else " ☐ "), texte)
        frag = markdown.markdown(texte, extensions=["tables", "fenced_code", "sane_lists"])
        frag = re.sub(r"<(/?)h([1-5])\b", lambda m: f"<{m.group(1)}h{int(m.group(2)) + 1}", frag)
    except ImportError:
        frag = subprocess.run(["pandoc", "-f", "gfm", "-t", "html", "--shift-heading-level-by=1", str(path)],
                              capture_output=True, text=True, check=True).stdout
    frag = re.sub(r"<table>", '<div class="tablewrap"><table>', frag).replace("</table>", "</table></div>")
    return f'<section class="doc" id="{anchor}">{frag}<p class="top"><a href="#sommaire">Retour au sommaire</a></p></section>'

stories = [story(p) for p in fichiers_scripts()]
def etat_court(st):
    if st["ncomp"] and st["nc"] == st["ncomp"]:
        return "fini", "✓ Terminée"
    if st["montes"] or st["nc"]:
        return "encours", "◐ Montage en cours"
    if st["voix"]:
        return "voix", "◔ Voix en cours" if st["voix"] < st["nb"] else "◑ Voix prêtes"
    return "afaire", "○ À faire"

toc = "".join(f'<li><a href="#{sid}"><span class="n">{num}</span><span class="t">{html.escape(t)}'
              f'<span class="etat-h {etat_court(st)[0]}">{etat_court(st)[1]}</span></span></a></li>'
              for sid, num, t, _, st in stories)
rows = "".join(
    f'<tr><th scope="row"><a href="#{sid}">{num} · {html.escape(t)}</a></th>'
    f'<td>{jauge(st["voix"], st["nb"])}</td>'
    f'<td>{jauge(st["montes"], st["segs"]) if st["segs"] else "–"}</td>'
    f'<td><span class="completes">{st["completes"] or "–"}</span></td></tr>'
    for sid, num, t, _, st in stories)
tot = {k: sum(st[k] for *_, st in stories) for k in ("nb", "voix", "segs", "montes", "nc", "ncomp")}
suivi = (f'<section class="suivi" id="suivi"><h2 class="sec">Où en est-on ?</h2>'
         f'<p class="suivi-tot"><b>{tot["voix"]}/{tot["nb"]}</b> répliques en voix · <b>{tot["montes"]}/{tot["segs"]}</b> morceaux montés · '
         f'<b>{tot["nc"]}/{tot["ncomp"]}</b> histoires complètes écoutables</p>'
         f'<div class="tablewrap"><table class="av-table"><thead><tr><th>Histoire</th><th>Voix</th><th>Montage</th>'
         f'<th>Histoires complètes</th></tr></thead><tbody>{rows}</tbody></table></div>'
         f'<p class="legende">▶ = à écouter dans le Drive · ◐ = projet Audacity prêt, montage pas encore exporté · ○ = pas encore fait. '
         f'Chaque histoire existe en 3 parcours : Romy, Alix, les deux (le compagnon et le choix changent d\'un parcours à l\'autre ; '
         f'survole un bouton pour voir le chemin).</p></section>')
opts = ('<option value="NARRATEUR-PAPIC">Narrateur · Papic</option><option value="NARRATEUR-MAMILY">Narrateur · Mamily</option>'
        + "".join(f'<option value="{k}">{ROLES[k][0]}</option>' for k in FILTER if k != "NARRATEUR"))
today = datetime.date.today().strftime("%d/%m/%Y")
tpl = (ROOT / "livret" / "template.html").read_text(encoding="utf-8")
page = (tpl.replace("{{TOC}}", toc).replace("{{SUIVI}}", suivi).replace("{{OPTIONS}}", opts).replace("{{DATE}}", today)
        .replace("{{STORIES}}", "".join(b for *_, b, _ in stories))
        .replace("{{PERSONNAGES}}", doc(ROOT / "docs" / "02-personnages-et-voix.md", "personnages"))
        .replace("{{PLAN}}", doc(ROOT / "docs" / "01-plan-projet.md", "plan")))
OUT.write_text(page, encoding="utf-8")
# Version autonome pour GitHub Pages (page complète, non référencée par les moteurs de recherche)
SITE = ROOT / "livret" / "site"
SITE.mkdir(exist_ok=True)
head = ('<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
        '<meta name="robots" content="noindex, nofollow">')
(SITE / "index.html").write_text(head + page.replace("<div class=\"wrap\">", "</head><body><div class=\"wrap\">", 1) + "</body></html>", encoding="utf-8")
print(f"OK {OUT} ({len(page)//1024} Ko, {len(stories) - 1} histoires + menus) + {SITE / 'index.html'}")

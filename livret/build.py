#!/usr/bin/env python3
"""Génère livret/livret.html (livret famille) à partir des fichiers Markdown du dépôt.
Usage : python3 livret/build.py
"""
import html, re, subprocess, pathlib, datetime

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

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\{([A-Z_]+)\}", r'<mark class="todo">\1</mark>', t)
    t = OV_RE.sub(lambda m: f'<span class="ov" title="Balise OmniVoice : {m.group(1)}">{OV[m.group(1)]}</span> ', t)
    t = re.sub(r"\[([^\]]+)\]", r'<span class="sfx">\1</span>', t)
    return t

def story(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    sid = path.stem.split("-")[0].lower()
    out, meta, title = [], [], ""
    for ln in lines:
        s = ln.strip()
        if not s or s == "---":
            continue
        if s.startswith("# "):
            title = s[2:]
        elif s.startswith("- ") and not out:
            meta.append(f"<li>{inline(s[2:])}</li>")
        elif s.startswith("Déroulé"):
            out.append(f'<p class="flow">{inline(s)}</p>')
        elif s.startswith("### "):
            h = s[4:]
            m = TAG_RE.search(h)
            tag = ""
            if m:
                label = {"×3": "3 versions", "×compagnon": "1 par compagnon", "commun": "une fois"}[m.group(1)]
                tag = f'<span class="tag">{label}</span>'
                h = TAG_RE.sub("", h).strip()
            out.append(f"<h4>{inline(h)} {tag}</h4>")
        elif s.startswith("**") and s.endswith("**"):
            out.append(f'<p class="variant">{inline(s[2:-2])}</p>')
        elif s.startswith("*(") and s.endswith(")*"):
            out.append(f'<p class="note">{inline(s[2:-2])}</p>')
        elif s.startswith("[") and s.endswith("]") and "]" not in s[1:-1]:
            out.append(f'<p class="sfxline">{inline(s)}</p>')
        else:
            m = ROLE_RE.match(s)
            if m and m.group(1).strip() in ROLES:
                key = m.group(1).strip()
                label, color = ROLES[key]
                how = f' <em>{html.escape(m.group(2).strip())}</em>' if m.group(2) else ""
                out.append(f'<div class="line" data-role="{key}" style="--rc:var(--{color})">'
                           f'<span class="who">{label}{how}</span><span class="say">{inline(m.group(3))}</span></div>')
            else:
                out.append(f"<p>{inline(s)}</p>")
    num = sid.upper()
    short = title.split("–", 1)[-1].strip()
    body = (f'<article class="story" id="{sid}"><header><p class="num">{num}</p><h2>{html.escape(short)}</h2>'
            f'<ul class="meta">{"".join(meta)}</ul></header>{"".join(out)}'
            f'<p class="top"><a href="#sommaire">Retour au sommaire</a></p></article>')
    return sid, num, short, body

def doc(path, anchor):
    frag = subprocess.run(["pandoc", "-f", "gfm", "-t", "html", "--shift-heading-level-by=1", str(path)],
                          capture_output=True, text=True, check=True).stdout
    frag = re.sub(r"<table>", '<div class="tablewrap"><table>', frag).replace("</table>", "</table></div>")
    return f'<section class="doc" id="{anchor}">{frag}<p class="top"><a href="#sommaire">Retour au sommaire</a></p></section>'

stories = [story(p) for p in sorted((ROOT / "histoires").glob("H*.md"))]
toc = "".join(f'<li><a href="#{sid}"><span class="n">{num}</span>{html.escape(t)}</a></li>' for sid, num, t, _ in stories)
opts = "".join(f'<option value="{k}">{ROLES[k][0]}</option>' for k in FILTER)
today = datetime.date.today().strftime("%d/%m/%Y")
tpl = (ROOT / "livret" / "template.html").read_text(encoding="utf-8")
page = (tpl.replace("{{TOC}}", toc).replace("{{OPTIONS}}", opts).replace("{{DATE}}", today)
        .replace("{{STORIES}}", "".join(b for *_, b in stories))
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
print(f"OK {OUT} ({len(page)//1024} Ko, {len(stories)} histoires) + {SITE / 'index.html'}")

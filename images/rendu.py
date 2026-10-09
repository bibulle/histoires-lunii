#!/usr/bin/env python3
"""Fabrique toutes les images Lunii :
  svg/<code>.svg       le dessin vectoriel
  png/<code>.png       l'image pour STUdio : 320x240, fond noir, 16 couleurs au plus
  planche.png          toutes les images sur une page, pour relire
  vignette.png         la vignette du pack dans STUdio
Usage : python3 rendu.py     (il faut : pip install playwright pillow numpy ; playwright install chromium)
"""
import os
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
import dessins
import scenes

ICI = os.path.dirname(os.path.abspath(__file__))
IMAGES = dessins.IMAGES[:3] + scenes.SCENES[:1] + dessins.IMAGES[3:] + scenes.SCENES[1:]
ORDRE = ["Menu0-accueil", "Menu1-", "Menu2-", "Menu3-", "H", "Fin-"]
IMAGES.sort(key=lambda i: next(n for n, p in enumerate(ORDRE) if i[0].startswith(p)))


def seize_couleurs(grand, chemin, n=16, k=4):
    """La Lunii (format « fs ») n'affiche que 16 couleurs par image, et STUdio réduit
    lui-même les images trop riches avec un tramage qui salit tout. On livre donc des
    images déjà propres : le dessin est rendu k fois trop grand et sans lissage (que des
    aplats), puis chaque pixel final prend la couleur majoritaire de son carré k×k.
    S'il reste plus de n couleurs, les plus rares prennent la couleur la plus proche.
    Renvoie (nombre d'aplats du dessin, couleurs abandonnées)."""
    im = np.asarray(Image.open(grand).convert("RGB"))
    h, w = im.shape[0] // k, im.shape[1] // k
    code = (im[..., 0].astype(np.int32) << 16) | (im[..., 1].astype(np.int32) << 8) | im[..., 2]
    couleurs, idx = np.unique(code, return_inverse=True)
    idx = idx.reshape(code.shape)
    votes = np.stack([(idx == c).reshape(h, k, w, k).sum(axis=(1, 3)) for c in range(len(couleurs))])
    petit = votes.argmax(axis=0)
    surface = np.bincount(petit.ravel(), minlength=len(couleurs))
    rgb = np.stack([(couleurs >> 16) & 255, (couleurs >> 8) & 255, couleurs & 255], axis=1).astype(np.int32)
    presentes = [c for c in np.argsort(-surface) if surface[c] > 0]
    gardees, perdues = presentes[:n], presentes[n:]
    for c in perdues:
        d = ((rgb[gardees] - rgb[c]) ** 2).sum(axis=1)
        petit[petit == c] = gardees[int(d.argmin())]
    Image.fromarray(rgb[petit].astype(np.uint8), "RGB").save(chemin)
    return len(presentes), [("#%06X" % couleurs[c], int(surface[c])) for c in perdues]


def planche(chemin, images, colonnes=5, marge=14, legende=22):
    """Planche faite avec les vrais PNG (ce que verra la Lunii), à l'échelle 1."""
    from PIL import ImageDraw, ImageFont
    try:
        police = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except OSError:
        police = ImageFont.load_default()
    lignes = (len(images) + colonnes - 1) // colonnes
    out = Image.new("RGB", (marge + colonnes * (320 + marge), marge + lignes * (240 + legende + marge)), (21, 21, 28))
    d = ImageDraw.Draw(out)
    for i, (code, titre, _f) in enumerate(images):
        x = marge + (i % colonnes) * (320 + marge)
        y = marge + (i // colonnes) * (240 + legende + marge)
        out.paste(Image.open(os.path.join(ICI, "png", code + ".png")), (x, y))
        d.text((x + 2, y + 244), "%s  ·  %s" % (code, titre), fill=(200, 200, 214), font=police)
    out.save(chemin)


def vignette(chemin, code="Menu0-accueil", cote=300):
    """La vignette du pack dans la bibliothèque de STUdio : l'image d'accueil, au carré."""
    im = Image.open(os.path.join(ICI, "png", code + ".png")).convert("RGB")
    out = Image.new("RGB", (im.width, im.width), (0, 0, 0))
    out.paste(im, (0, (im.width - im.height) // 2))
    out.resize((cote, cote), Image.LANCZOS).save(chemin)


if __name__ == "__main__":
    for dossier in ("svg", "png"):
        os.makedirs(os.path.join(ICI, dossier), exist_ok=True)
    with sync_playwright() as p:
        nav = p.chromium.launch()
        page = nav.new_page(viewport={"width": 320, "height": 240}, device_scale_factor=4)
        for code, _titre, f in IMAGES:
            source = dessins.svg(f())
            with open(os.path.join(ICI, "svg", code + ".svg"), "w", encoding="utf-8") as fh:
                fh.write(source)
            page.set_content('<style>body{margin:0;background:#000}svg *{shape-rendering:crispEdges}</style>' + source)
            chemin = os.path.join(ICI, "png", code + ".png")
            page.screenshot(path=chemin)
            aplats, perdues = seize_couleurs(chemin, chemin)
            if perdues:
                print("%-20s %d aplats, abandonnés : %s" % (code, aplats, perdues))
        nav.close()
    planche(os.path.join(ICI, "planche.png"), IMAGES)
    vignette(os.path.join(ICI, "vignette.png"))
    print("%d images" % len(IMAGES))

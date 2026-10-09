#!/usr/bin/env python3
"""Images Lunii (320x240, fond noir) – planche d'essai.
Chaque fonction renvoie le contenu SVG d'une image ; `python3 dessins.py` écrit
les .svg dans svg/ (le rendu PNG est fait par rendu.py)."""
import math
import os

W, H = 320, 240

# Palette : aplats vifs sur fond noir (le noir = écran éteint derrière la coque)
BLANC = "#FFFFFF"
ROSE = "#FF7EB6"
ROSE_PALE = "#FFD3E8"
VIOLET = "#B58CFF"
TURQUOISE = "#4FD6D0"
JAUNE = "#FFD23F"
ORANGE = "#FF9A3C"
ROUGE = "#FF5A5A"
VERT = "#5FD068"
VERT_CLAIR = "#A6ECA0"
VERT_FONCE = "#2E9E4A"
BLEU = "#5AB0FF"
GRIS = "#C9CED6"
GRIS_FONCE = "#8C94A0"
PEAU = "#FFD2B0"
PEAU_OMBRE = "#F2B48E"
ENCRE = "#1B1B24"
BOUCHE = "#B8324B"


def etoile(cx, cy, r, couleur=JAUNE):
    """Petite étincelle à 4 branches."""
    k = r * 0.28
    pts = [(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
           (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)]
    return '<polygon points="%s" fill="%s"/>' % (
        " ".join("%.1f,%.1f" % p for p in pts), couleur)


def coeur(cx, cy, s, couleur=ROSE):
    return ('<path transform="translate(%g %g) scale(%g)" fill="%s" '
            'd="M0 6 C-11 -3 -6 -11 0 -5 C6 -11 11 -3 0 6Z"/>' % (cx, cy, s, couleur))


def bulle(cx, cy, r):
    return ('<circle cx="%g" cy="%g" r="%g" fill="#17395C" '
            'stroke="#BFE4FF" stroke-width="3.5"/>'
            '<path d="M%g %g a%g %g 0 0 1 %g %g" fill="none" stroke="#BFE4FF" '
            'stroke-width="3.5" stroke-linecap="round"/>'
            % (cx, cy, r, cx - r * .55, cy - r * .15, r * .5, r * .5, r * .4, -r * .45))


def oeil(cx, cy, r=9):
    return ('<circle cx="%g" cy="%g" r="%g" fill="%s"/>'
            '<circle cx="%g" cy="%g" r="%g" fill="#fff"/>'
            % (cx, cy, r, ENCRE, cx + r * .3, cy - r * .35, r * .33))


def joue(cx, cy, r=9, c="#FF9DB5"):
    return '<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (cx, cy, r, c)


def sourire(cx, cy, l=14, h=9, ep=4, c=ENCRE):
    return ('<path d="M%g %g q%g %g %g 0" fill="none" stroke="%s" stroke-width="%g" '
            'stroke-linecap="round"/>' % (cx - l, cy, l, h * 2, 2 * l, c, ep))


def couronne(cx, cy, l=26, h=22, c=JAUNE, gemme=ROSE, angle=0):
    """Couronne à 3 pointes, base centrée en (cx, cy)."""
    p = [(-l, 0), (-l, -h * .75), (-l / 2, -h * .3), (0, -h), (l / 2, -h * .3),
         (l, -h * .75), (l, 0)]
    pts = " ".join("%.1f,%.1f" % q for q in p)
    return ('<g transform="translate(%g %g) rotate(%g)">'
            '<polygon points="%s" fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>'
            '<circle cx="0" cy="%g" r="3.6" fill="%s"/>'
            '<circle cx="%g" cy="%g" r="2.6" fill="#fff"/><circle cx="%g" cy="%g" r="2.6" fill="#fff"/>'
            '</g>' % (cx, cy, angle, pts, c, c, -h * .32, gemme,
                      -l * .62, -h * .22, l * .62, -h * .22))


# ---------------------------------------------------------------- Paillette
def paillette(decor=True):
    s = []
    # crinière (derrière la tête)
    for cx, cy, r, c in [(98, 92, 30, ROSE), (88, 134, 27, VIOLET), (98, 174, 23, TURQUOISE),
                         (104, 208, 17, ROSE), (146, 64, 21, VIOLET), (176, 60, 17, TURQUOISE)]:
        s.append('<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (cx, cy, r, c))
    # oreilles
    s.append('<path d="M112 86 L104 44 L140 68Z" fill="#fff" stroke="#fff" stroke-width="6" stroke-linejoin="round"/>')
    s.append('<path d="M208 86 L216 44 L180 68Z" fill="#fff" stroke="#fff" stroke-width="6" stroke-linejoin="round"/>')
    s.append('<path d="M114 76 L110 55 L128 68Z" fill="%s"/>' % ROSE)
    s.append('<path d="M206 76 L210 55 L192 68Z" fill="%s"/>' % ROSE)
    # corne
    s.append('<path d="M160 12 L146 72 L174 72Z" fill="%s" stroke="%s" stroke-width="4" stroke-linejoin="round"/>' % (JAUNE, JAUNE))
    for y, dx in [(30, 4), (44, 7), (58, 10)]:
        s.append('<path d="M%g %g L%g %g" stroke="%s" stroke-width="3.5" stroke-linecap="round"/>'
                 % (160 - dx, y + 4, 160 + dx, y - 3, ORANGE))
    # tête + museau
    s.append('<ellipse cx="160" cy="124" rx="62" ry="58" fill="#fff"/>')
    s.append('<ellipse cx="160" cy="172" rx="40" ry="29" fill="%s"/>' % ROSE_PALE)
    s.append('<ellipse cx="147" cy="167" rx="3.2" ry="4.5" fill="#E77FB3"/>')
    s.append('<ellipse cx="173" cy="167" rx="3.2" ry="4.5" fill="#E77FB3"/>')
    s.append(sourire(160, 182, 12, 6, 3.5, "#C2578F"))
    # yeux, cils, joues
    for x, sens in [(132, -1), (188, 1)]:
        s.append(oeil(x, 120, 10.5))
        for dx, dy in [(11, -9), (14, -3)]:
            s.append('<path d="M%g %g l%g %g" stroke="%s" stroke-width="4" stroke-linecap="round"/>'
                     % (x + sens * 8, 120 + dy + 4, sens * (dx - 7), dy * .35 - 2, ENCRE))
    s.append(joue(110, 143, 9))
    s.append(joue(210, 143, 9))
    # mèche sur le front
    s.append('<path d="M150 70 C128 74 122 96 138 100 C150 94 160 82 168 70Z" fill="%s"/>' % ROSE)
    if not decor:
        return "".join(s)
    # paillettes
    for x, y, r, c in [(258, 52, 15, JAUNE), (286, 108, 9, BLANC), (256, 150, 11, ROSE),
                       (282, 196, 13, JAUNE), (40, 44, 11, JAUNE), (34, 196, 9, BLANC)]:
        s.append(etoile(x, y, r, c))
    return "".join(s)


# -------------------------------------------------------------------- Grumo
def grumo(decor=True):
    s = []
    # ailes
    s.append('<path d="M92 150 L30 104 L40 150 L22 158 L46 176 L34 196 L96 190Z" fill="%s"/>' % VERT_FONCE)
    s.append('<path d="M228 150 L290 104 L280 150 L298 158 L274 176 L286 196 L224 190Z" fill="%s"/>' % VERT_FONCE)
    # corps + ventre
    s.append('<ellipse cx="160" cy="200" rx="72" ry="58" fill="%s"/>' % VERT)
    s.append('<ellipse cx="160" cy="212" rx="44" ry="44" fill="#F3F0A8"/>')
    for y in (190, 206, 222):
        s.append('<path d="M%g %g q%g 7 %g 0" fill="none" stroke="#D9D277" stroke-width="4.5" stroke-linecap="round"/>'
                 % (160 - 30, y, 30, 60))
    # cornes et crête
    s.append('<path d="M112 56 L98 20 L134 42Z" fill="%s" stroke="%s" stroke-width="5" stroke-linejoin="round"/>' % (JAUNE, JAUNE))
    s.append('<path d="M208 56 L222 20 L186 42Z" fill="%s" stroke="%s" stroke-width="5" stroke-linejoin="round"/>' % (JAUNE, JAUNE))
    s.append('<path d="M146 38 L160 14 L174 38Z" fill="%s" stroke="%s" stroke-width="4" stroke-linejoin="round"/>' % (ORANGE, ORANGE))
    # tête
    s.append('<ellipse cx="160" cy="92" rx="72" ry="56" fill="%s"/>' % VERT)
    # yeux
    for x in (128, 192):
        s.append('<circle cx="%g" cy="72" r="16" fill="#fff"/>' % x)
        s.append('<circle cx="%g" cy="75" r="8" fill="%s"/>' % (x, ENCRE))
        s.append('<circle cx="%g" cy="72" r="2.8" fill="#fff"/>' % (x + 3))
    # museau, nez enrhumé
    s.append('<ellipse cx="160" cy="118" rx="54" ry="31" fill="%s"/>' % VERT_CLAIR)
    s.append('<ellipse cx="160" cy="105" rx="27" ry="12" fill="#FF8C8C"/>')
    s.append('<ellipse cx="149" cy="105" rx="5" ry="6" fill="%s"/>' % ENCRE)
    s.append('<ellipse cx="171" cy="105" rx="5" ry="6" fill="%s"/>' % ENCRE)
    s.append(sourire(160, 126, 24, 8, 4.5, VERT_FONCE))
    s.append('<path d="M172 135 l4 10 l7 -9Z" fill="#fff"/>')
    if not decor:
        return "".join(s)
    # bulles
    for x, y, r in [(258, 48, 19), (292, 92, 11), (50, 54, 14), (28, 96, 9)]:
        s.append(bulle(x, y, r))
    return "".join(s)


# -------------------------------------------------------------- Tata Bêtise
def tata_betise(decor=True):
    s = []
    CHEVEUX = "#6B4630"
    MECHES = "#8A5E42"
    s.append('<defs><pattern id="rayures" width="18" height="18" patternUnits="userSpaceOnUse" '
             'patternTransform="rotate(32)"><rect width="18" height="18" fill="#FFF1DC"/>'
             '<rect width="9" height="18" fill="#E2323F"/></pattern></defs>')
    # chignon en bataille (en haut à droite) + cheveux tirés en arrière
    s.append('<circle cx="208" cy="60" r="23" fill="%s"/>' % CHEVEUX)
    s.append('<path d="M222 42 q10 -12 20 -8 M228 58 q12 -4 18 6 M212 38 q2 -12 12 -16" fill="none" '
             'stroke="%s" stroke-width="4.5" stroke-linecap="round"/>' % CHEVEUX)
    s.append('<ellipse cx="160" cy="118" rx="59" ry="60" fill="%s"/>' % CHEVEUX)
    # cou + haut rayé rouge et blanc
    s.append('<rect x="142" y="176" width="36" height="34" fill="%s"/>' % PEAU_OMBRE)
    s.append('<path d="M88 240 C92 206 128 198 160 198 C192 198 228 206 232 240Z" fill="%s"/>' % PEAU)
    s.append('<path d="M112 240 L122 202 L140 199 Q160 226 180 199 L198 202 L208 240Z" fill="url(#rayures)"/>')
    # oreilles + perles
    s.append('<circle cx="105" cy="138" r="10" fill="%s"/>' % PEAU_OMBRE)
    s.append('<circle cx="215" cy="138" r="10" fill="%s"/>' % PEAU_OMBRE)
    s.append('<circle cx="103" cy="153" r="5.5" fill="#fff"/><circle cx="217" cy="153" r="5.5" fill="#fff"/>')
    # visage
    s.append('<ellipse cx="160" cy="132" rx="54" ry="58" fill="%s"/>' % PEAU)
    # racine des cheveux tirés + petites mèches folles
    s.append('<path d="M106 122 C104 86 130 70 160 70 C190 70 216 86 214 122 C206 100 188 88 160 88 '
             'C132 88 114 100 106 122Z" fill="%s"/>' % CHEVEUX)
    s.append('<path d="M110 112 q-8 10 -4 22 M210 112 q8 10 4 22" fill="none" stroke="%s" stroke-width="4" stroke-linecap="round"/>' % CHEVEUX)
    # casserole à l'envers sur la tête, de travers
    s.append('<g transform="translate(-22 4) rotate(-16 160 52)">'
             '<path d="M118 64 L128 20 L196 20 L206 64Z" fill="%s" stroke="%s" stroke-width="4" stroke-linejoin="round"/>'
             '<rect x="108" y="58" width="108" height="11" rx="5.5" fill="%s"/>'
             '<rect x="62" y="27" width="62" height="10" rx="5" fill="%s"/>'
             '<path d="M186 30 L190 52" stroke="#fff" stroke-width="4" stroke-linecap="round"/>'
             '</g>' % (GRIS, GRIS, GRIS_FONCE, GRIS_FONCE))
    # deux yeux bien ouverts, avec le trait d'eye-liner
    s.append(oeil(138, 124, 9))
    s.append(oeil(182, 124, 9))
    s.append('<path d="M191 120 l10 -7" fill="none" stroke="%s" stroke-width="4.5" stroke-linecap="round"/>' % ENCRE)
    s.append('<path d="M129 120 l-10 -7" fill="none" stroke="%s" stroke-width="4.5" stroke-linecap="round"/>' % ENCRE)
    s.append('<path d="M126 100 q12 -8 24 -2" fill="none" stroke="%s" stroke-width="4" stroke-linecap="round"/>' % CHEVEUX)
    s.append('<path d="M170 100 q12 -8 24 0" fill="none" stroke="%s" stroke-width="4" stroke-linecap="round"/>' % CHEVEUX)
    # grand rire
    s.append('<path d="M132 148 Q160 152 188 148 Q186 184 160 184 Q134 184 132 148Z" fill="%s"/>' % BOUCHE)
    s.append('<path d="M138 150 Q160 154 182 150 L181 158 Q160 162 139 158Z" fill="#fff"/>')
    s.append('<ellipse cx="160" cy="175" rx="15" ry="8" fill="#FF9DB5"/>')
    s.append(joue(116, 148, 10))
    s.append(joue(204, 148, 10))
    if not decor:
        return "".join(s)
    # éclaboussures et étoiles « oups »
    for x, y, r, c in [(34, 160, 8, TURQUOISE), (54, 204, 10, VIOLET), (284, 150, 9, ROSE),
                       (270, 200, 8, JAUNE)]:
        s.append('<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (x, y, r, c))
    s.append(etoile(36, 112, 11, JAUNE))
    s.append(etoile(282, 56, 12, JAUNE))
    return "".join(s)


# -------------------------------------------------------------------- Papic
def papic(decor=True):
    s = []
    CHEVEUX = "#F4F4F8"
    MONTURE = "#30303C"
    # polo blanc + salopette d'inventeur
    s.append('<path d="M84 240 C88 202 126 196 160 196 C194 196 232 202 236 240Z" fill="%s"/>' % BLANC)
    s.append('<rect x="122" y="218" width="76" height="22" fill="%s"/>' % BLEU)
    s.append('<rect x="114" y="198" width="13" height="42" fill="%s"/>' % BLEU)
    s.append('<rect x="193" y="198" width="13" height="42" fill="%s"/>' % BLEU)
    s.append('<circle cx="120.5" cy="224" r="4.5" fill="%s"/>' % JAUNE)
    s.append('<circle cx="199.5" cy="224" r="4.5" fill="%s"/>' % JAUNE)
    s.append('<rect x="143" y="176" width="34" height="28" fill="%s"/>' % PEAU_OMBRE)
    s.append('<path d="M138 194 L160 214 L182 194 L192 203 L170 226 L160 214 L150 226 L128 203Z" '
             'fill="#fff" stroke="#D5D9E2" stroke-width="2.5" stroke-linejoin="round"/>')
    # cheveux blancs ébouriffés (derrière le visage)
    for x, y, r in [(116, 76, 22), (140, 60, 22), (166, 54, 22), (192, 62, 22), (210, 82, 20),
                    (102, 102, 18), (220, 108, 17), (99, 124, 13), (222, 127, 12)]:
        s.append('<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (x, y, r, CHEVEUX))
    s.append('<path d="M128 44 q-4 -12 -14 -14 M156 34 q2 -12 12 -16 M186 42 q8 -10 18 -8" '
             'fill="none" stroke="%s" stroke-width="5" stroke-linecap="round"/>' % CHEVEUX)
    # oreilles + visage
    s.append('<circle cx="104" cy="136" r="11" fill="%s"/>' % PEAU_OMBRE)
    s.append('<circle cx="216" cy="136" r="11" fill="%s"/>' % PEAU_OMBRE)
    s.append('<ellipse cx="160" cy="126" rx="55" ry="60" fill="%s"/>' % PEAU)
    # mèche sur le haut du front (front dégagé) + rides
    s.append('<path d="M118 82 C132 60 176 56 200 78 C184 70 166 72 154 80 C142 74 130 76 118 82Z" fill="%s"/>' % CHEVEUX)
    # sourcils
    s.append('<path d="M120 100 q15 -9 30 -3" fill="none" stroke="%s" stroke-width="5" stroke-linecap="round"/>' % GRIS)
    s.append('<path d="M170 97 q15 -6 30 3" fill="none" stroke="%s" stroke-width="5" stroke-linecap="round"/>' % GRIS)
    # yeux + lunettes rectangulaires (barre du haut plus épaisse)
    s.append(oeil(136, 121, 6.5))
    s.append(oeil(184, 121, 6.5))
    for x in (116, 164):
        s.append('<rect x="%g" y="107" width="40" height="27" rx="7" fill="none" '
                 'stroke="%s" stroke-width="4"/>' % (x, GRIS_FONCE))
        s.append('<path d="M%g 108 L%g 108" stroke="%s" stroke-width="5.5" stroke-linecap="round"/>'
                 % (x + 3, x + 37, MONTURE))
    s.append('<path d="M156 112 L164 112 M116 111 L104 114 M204 111 L216 114" fill="none" '
             'stroke="%s" stroke-width="4.5" stroke-linecap="round"/>' % MONTURE)
    # nez, joues, grand sourire
    s.append('<ellipse cx="160" cy="142" rx="9" ry="8" fill="%s"/>' % PEAU_OMBRE)
    s.append(joue(122, 150, 10, "#FF9A8A"))
    s.append(joue(198, 150, 10, "#FF9A8A"))
    s.append('<path d="M136 154 Q160 161 184 154 Q182 180 160 180 Q138 180 136 154Z" fill="%s"/>' % BOUCHE)
    s.append('<path d="M141 156 Q160 162 179 156 L178 163 Q160 168 142 163Z" fill="#fff"/>')
    if not decor:
        return "".join(s)
    # clé plate (à droite) et engrenages (à gauche)
    s.append('<g transform="translate(266 130) rotate(24) scale(.88)">'
             '<rect x="-7" y="-46" width="14" height="96" rx="6" fill="%s"/>'
             '<path d="M-17 -64 a19 19 0 1 0 34 0 l-8 0 l0 16 l-18 0 l0 -16Z" fill="%s"/>'
             '<circle cx="0" cy="48" r="13" fill="%s"/><circle cx="0" cy="48" r="5.5" fill="#000"/>'
             '</g>' % (GRIS, GRIS, GRIS))
    dents = "".join('<rect x="-6" y="-31" width="12" height="14" rx="2" fill="%s" transform="rotate(%d)"/>'
                    % (JAUNE, a) for a in range(0, 360, 45))
    s.append('<g transform="translate(48 96) rotate(12)">%s<circle r="21" fill="%s"/>'
             '<circle r="8" fill="#000"/></g>' % (dents, JAUNE))
    dents2 = "".join('<rect x="-4" y="-20" width="8" height="9" rx="1.5" fill="%s" transform="rotate(%d)"/>'
                     % (ORANGE, a) for a in range(0, 360, 60))
    s.append('<g transform="translate(40 170)">%s<circle r="13" fill="%s"/><circle r="5" fill="#000"/></g>'
             % (dents2, ORANGE))
    s.append(etoile(286, 40, 9, JAUNE))
    return "".join(s)


# ------------------------------------------------------------------- Mamily
def mamily(decor=True):
    s = []
    CHEVEUX = "#E8CD8E"
    MECHES = "#CDAA62"
    # cheveux blonds mi-longs, pointes vers l'extérieur
    s.append('<path d="M160 46 C100 46 86 96 88 148 C88 172 84 186 70 194 C92 202 114 196 124 184 '
             'L196 184 C206 196 228 202 250 194 C236 186 232 172 232 148 C234 96 220 46 160 46Z" fill="%s"/>' % CHEVEUX)
    # robe
    s.append('<rect x="143" y="176" width="34" height="28" fill="%s"/>' % PEAU_OMBRE)
    s.append('<path d="M84 240 C88 204 126 198 160 198 C194 198 232 204 236 240Z" fill="%s"/>' % ROSE)
    s.append('<path d="M138 199 Q160 222 182 199" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/>')
    for x in (146, 160, 174):
        s.append('<circle cx="%g" cy="%g" r="4" fill="#fff"/>' % (x, 216 if x == 160 else 211))
    # visage
    s.append('<ellipse cx="160" cy="128" rx="52" ry="58" fill="%s"/>' % PEAU)
    # mèche sur le côté
    s.append('<path d="M108 114 C112 76 146 64 170 68 C196 70 210 90 212 114 '
             'C198 104 186 92 176 80 C162 98 134 110 108 114Z" fill="%s"/>' % CHEVEUX)
    # yeux rieurs, joues, grand sourire
    s.append('<path d="M126 126 q11 -12 22 0" fill="none" stroke="%s" stroke-width="4.5" stroke-linecap="round"/>' % ENCRE)
    s.append('<path d="M172 126 q11 -12 22 0" fill="none" stroke="%s" stroke-width="4.5" stroke-linecap="round"/>' % ENCRE)
    for x in (137, 183):
        s.append('<circle cx="%g" cy="125" r="18" fill="none" stroke="#E9B95C" stroke-width="4"/>' % x)
        s.append('<path d="M%g 123 a18 18 0 0 1 36 0" fill="none" stroke="#8A5A3A" stroke-width="5" stroke-linecap="round"/>' % (x - 18))
    s.append('<path d="M155 121 q5 -5 10 0" fill="none" stroke="#E9B95C" stroke-width="4" stroke-linecap="round"/>')
    s.append(joue(118, 152, 10))
    s.append(joue(202, 152, 10))
    s.append('<ellipse cx="160" cy="142" rx="6" ry="5" fill="%s"/>' % PEAU_OMBRE)
    s.append('<path d="M136 152 Q160 159 184 152 Q182 178 160 178 Q138 178 136 152Z" fill="%s"/>' % BOUCHE)
    s.append('<path d="M141 154 Q160 160 179 154 L178 161 Q160 166 142 161Z" fill="#fff"/>')
    # couronne de reine des câlins
    s.append(couronne(160, 58, 34, 34, JAUNE, ROSE))
    s.append(coeur(160, 44, 0.9, ROUGE))
    if not decor:
        return "".join(s)
    # cœurs (les câlins) et petit gâteau
    for x, y, k, c in [(48, 60, 2.4, ROSE), (40, 140, 1.8, ROUGE),
                       (274, 56, 2.0, ROUGE)]:
        s.append(coeur(x, y, k, c))
    s.append('<g transform="translate(288 190) scale(.86)">'
             '<path d="M-24 4 L-18 40 L18 40 L24 4Z" fill="%s"/>'
             '<path d="M-10 8 L-7 38 M0 8 L0 38 M10 8 L7 38" stroke="#fff" stroke-width="4" stroke-linecap="round"/>'
             '<path d="M-28 6 C-30 -12 -14 -22 0 -22 C14 -22 30 -12 28 6 C18 12 8 2 0 8 C-8 2 -18 12 -28 6Z" fill="#fff"/>'
             '<circle cx="0" cy="-26" r="7" fill="%s"/>'
             '</g>' % (VIOLET, ROUGE))
    return "".join(s)


# -------------------------------------------------------------- Princesses
def oeil_bleu(cx, cy, r=8):
    return ('<circle cx="%g" cy="%g" r="%g" fill="#4F9BE8"/>'
            '<circle cx="%g" cy="%g" r="%g" fill="%s"/>'
            '<circle cx="%g" cy="%g" r="%g" fill="#fff"/>'
            % (cx, cy, r, cx, cy, r * .58, ENCRE, cx + r * .35, cy - r * .38, r * .3))


VICHY = ('<defs><pattern id="vichy" width="20" height="20" patternUnits="userSpaceOnUse">'
         '<rect width="20" height="20" fill="#fff"/>'
         '<rect width="10" height="20" fill="#A9D4FF"/><rect width="20" height="10" fill="#A9D4FF"/>'
         '<rect width="10" height="10" fill="#5AB0FF"/></pattern></defs>')


def _princesse(cx, cy, k, cheveux, meches, robe, gemme, style, penche=0):
    """Une petite princesse. style = 'couettes' (Romy) ou 'libre' (Alix)."""
    g = ['<g transform="translate(%g %g) scale(%g)">' % (cx, cy, k), VICHY]
    if style == "couettes":
        # deux couettes qui tombent sur les épaules
        for sx in (-1, 1):
            g.append('<path transform="scale(%d 1)" d="M-42 -8 C-66 -6 -72 30 -64 58 C-56 52 -46 50 -38 54 '
                     'C-36 32 -38 10 -42 -8Z" fill="%s"/>' % (sx, cheveux))
        g.append('<path d="M0 -52 C-44 -52 -52 -14 -48 12 L48 12 C52 -14 44 -52 0 -52Z" fill="%s"/>' % cheveux)
    else:
        # cheveux libres, un peu fous, jusqu'aux épaules
        g.append('<path d="M0 -54 C-46 -54 -58 -16 -54 16 C-52 36 -58 46 -66 50 C-52 58 -38 54 -32 44 '
                 'L32 44 C38 54 52 58 66 50 C58 46 52 36 54 16 C58 -16 46 -54 0 -54Z" fill="%s"/>' % cheveux)
    # robe + cou
    g.append('<rect x="-12" y="40" width="24" height="18" fill="%s"/>' % PEAU_OMBRE)
    g.append('<path d="M-52 110 C-50 62 -24 54 0 54 C24 54 50 62 52 110Z" fill="%s"/>' % robe)
    g.append('<path d="M-16 55 Q0 70 16 55" fill="none" stroke="#fff" stroke-width="4.5" stroke-linecap="round"/>')
    # visage
    g.append('<ellipse cx="0" cy="4" rx="42" ry="44" fill="%s"/>' % PEAU)
    if style == "couettes":
        # raie au milieu
        for sx in (-1, 1):
            g.append('<path transform="scale(%d 1)" d="M0 -41 C-22 -41 -41 -28 -42 0 C-36 -18 -20 -28 0 -33Z" fill="%s"/>' % (sx, cheveux))
        # élastiques des couettes
        g.append('<circle cx="-43" cy="-4" r="6" fill="%s"/><circle cx="43" cy="-4" r="6" fill="%s"/>' % (ROSE, ROSE))
        # barrette nœud doré
        g.append('<g transform="translate(-22 -27) rotate(-18)"><path d="M0 0 L-10 -6 L-10 6Z M0 0 L10 -6 L10 6Z" '
                 'fill="%s" stroke="%s" stroke-width="2" stroke-linejoin="round"/><circle r="3" fill="#fff"/></g>' % (JAUNE, JAUNE))
    else:
        # mèche sur le côté
        g.append('<path d="M-42 -2 C-42 -34 -14 -44 8 -40 C28 -38 40 -24 42 -4 C32 -14 20 -22 12 -30 '
                 'C0 -14 -22 -4 -42 -2Z" fill="%s"/>' % cheveux)
    g.append(oeil_bleu(-16, 8, 8))
    g.append(oeil_bleu(16, 8, 8))
    g.append(joue(-28, 23, 8))
    g.append(joue(28, 23, 8))
    if style == "couettes":
        g.append(sourire(0, 24, 11, 6, 4, BOUCHE))
    else:
        g.append('<path d="M-15 21 Q0 25 15 21 Q13 40 0 40 Q-13 40 -15 21Z" fill="%s"/>' % BOUCHE)
        g.append('<path d="M-11 23 Q0 26 11 23 L10 28 Q0 31 -10 28Z" fill="#fff"/>')
    g.append(couronne(0, -46, 24, 24, JAUNE, gemme, penche))
    g.append("</g>")
    return "".join(g)


ROMY = ("#C49A62", "#A67E48", "url(#vichy)", BLEU, "couettes")   # robe à carreaux
ALIX = ("#EDCD82", "#D2AC58", ROSE, ROSE, "libre")               # robe rose


def romy():
    s = [_princesse(160, 120, 1.45, *ROMY)]
    for x, y, r, c in [(44, 50, 13, JAUNE), (276, 44, 10, BLANC), (290, 150, 12, JAUNE),
                       (30, 160, 9, BLANC)]:
        s.append(etoile(x, y, r, c))
    return "".join(s)


def alix():
    s = [_princesse(160, 120, 1.45, *ALIX, penche=10)]
    for x, y, r, c in [(40, 46, 12, JAUNE), (282, 40, 13, JAUNE), (292, 140, 9, BLANC),
                       (26, 150, 10, BLANC)]:
        s.append(etoile(x, y, r, c))
    return "".join(s)


def romy_et_alix():
    s = []
    s.append(_princesse(94, 112, 1.1, *ROMY))
    s.append(_princesse(236, 136, 0.92, *ALIX, penche=10))
    for x, y, r, c in [(168, 40, 12, JAUNE), (298, 44, 8, BLANC), (22, 34, 8, BLANC),
                       (304, 206, 8, JAUNE)]:
        s.append(etoile(x, y, r, c))
    return "".join(s)


IMAGES = [
    ("Menu1-Romy", "La Princesse Romy", romy),
    ("Menu1-Alix", "La Princesse Alix", alix),
    ("Menu1-Romy&Alix", "Les deux princesses", romy_et_alix),
    ("Menu3-Paillette", "Paillette, la licorne", paillette),
    ("Menu3-Grumo", "Grumo, le dragon", grumo),
    ("Menu3-TataBetise", "Tata Bêtise", tata_betise),
    ("Menu3-Papic", "Papic, le grand inventeur", papic),
    ("Menu3-Mamily", "Mamily, la reine des câlins", mamily),
]


def svg(contenu):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">'
            '<rect width="%d" height="%d" fill="#000"/>%s</svg>' % (W, H, W, H, W, H, contenu))

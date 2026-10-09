#!/usr/bin/env python3
"""Images Lunii – accueil, fin, titres des 9 histoires et images des 16 choix.
Les personnages viennent de dessins.py ; ici, les décors et les objets."""
import math
from dessins import (BLANC, ROSE, ROSE_PALE, VIOLET, TURQUOISE, JAUNE, ORANGE, ROUGE, VERT,
                     VERT_CLAIR, VERT_FONCE, BLEU, GRIS, GRIS_FONCE, ENCRE, BOUCHE,
                     etoile, coeur, bulle, oeil, joue, sourire,
                     paillette, grumo, tata_betise)

BLEU_FONCE = "#2F7FD6"
ROSE_FONCE = "#E8468F"
BRUN = "#C98A4B"
BRUN_FONCE = "#8A5A3A"
SABLE = "#EBCB8B"
SABLE_OMBRE = "#D2AC58"
BISCUIT = "#D9A066"
CIEL = "#BFE4FF"


# ------------------------------------------------------------------ outils
def R(x, y, w, h, c, rx=0, extra=""):
    return '<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" %s/>' % (x, y, w, h, rx, c, extra)


def C(cx, cy, r, c):
    return '<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (cx, cy, r, c)


def E(cx, cy, rx, ry, c, extra=""):
    return '<ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="%s" %s/>' % (cx, cy, rx, ry, c, extra)


def P(d, c, extra=""):
    return '<path d="%s" fill="%s" %s/>' % (d, c, extra)


def T(d, c, ep=5):
    """Trait (sans remplissage), bouts arrondis."""
    return ('<path d="%s" fill="none" stroke="%s" stroke-width="%g" stroke-linecap="round" '
            'stroke-linejoin="round"/>' % (d, c, ep))


def G(contenu, tr):
    return '<g transform="%s">%s</g>' % (tr, contenu)


def mini(perso, cx, cy, k):
    """Un personnage de dessins.py (sans décor), réduit, tête centrée en (cx, cy)."""
    return G(perso(decor=False), "translate(%g %g) scale(%g)" % (cx - 160 * k, cy - 125 * k, k))


def etoile5(cx, cy, r, c):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * .46
        pts.append("%.1f,%.1f" % (cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return ('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%g" stroke-linejoin="round"/>'
            % (" ".join(pts), c, c, max(3, r * .16)))


def engrenage(cx, cy, r, c, n=8):
    dents = "".join('<rect x="%g" y="%g" width="%g" height="%g" rx="2" fill="%s" transform="rotate(%g)"/>'
                    % (-r * .28, -r * 1.45, r * .56, r * .7, c, i * 360 / n) for i in range(n))
    return G(dents + C(0, 0, r, c) + C(0, 0, r * .38, "#000"), "translate(%g %g)" % (cx, cy))


def cle(cx, cy, rot, k=1, c=GRIS):
    return G(R(-7, -46, 14, 96, c, 6)
             + P("M-17 -64 a19 19 0 1 0 34 0 l-8 0 l0 16 l-18 0 l0 -16Z", c)
             + C(0, 48, 13, c) + C(0, 48, 5.5, "#000"),
             "translate(%g %g) rotate(%g) scale(%g)" % (cx, cy, rot, k))


def vagues(y, c, amp=12, pas=40, dec=0):
    d = "M-40 240 L-40 %g Q%g %g %g %g" % (y, -40 + dec + pas / 2, y - amp, -40 + dec + pas, y)
    x = -40 + dec + pas
    while x < 360:
        x += pas
        d += " T%g %g" % (x, y)
    return P(d + " L360 240Z", c)


def etoiles(liste):
    return "".join(etoile(x, y, r, c) for x, y, r, c in liste)


# ----------------------------------------------------------------- château
def _chateau():
    s = []
    s.append(E(160, 218, 140, 14, VERT))
    # tour rose (Romy) et tour bleue (Alix)
    s.append(R(60, 96, 56, 118, ROSE))
    s.append(P("M50 98 L88 40 L126 98Z", ROSE_FONCE))
    s.append(R(204, 96, 56, 118, BLEU))
    s.append(P("M194 98 L232 40 L270 98Z", BLEU_FONCE))
    # corps du château + donjon
    s.append(R(108, 128, 104, 86, BLANC))
    for x in (108, 137, 166, 195):
        s.append(R(x, 114, 17, 16, BLANC))
    s.append(R(138, 72, 44, 60, BLANC))
    s.append(P("M128 74 L160 22 L192 74Z", VIOLET))
    # drapeaux
    for x, y, c in [(88, 40, JAUNE), (232, 40, JAUNE), (160, 22, ROSE)]:
        s.append(T("M%g %g L%g %g" % (x, y, x, y - 20), GRIS, 3.5))
        s.append(P("M%g %g l16 6 l-16 6Z" % (x, y - 20), c))
    # porte et fenêtres
    s.append(P("M140 214 L140 176 a20 20 0 0 1 40 0 L180 214Z", JAUNE))
    s.append(C(172, 196, 3.5, BRUN_FONCE))
    for x in (88, 232):
        s.append(P("M%g 152 L%g 132 a9 9 0 0 1 18 0 L%g 152Z" % (x - 9, x - 9, x + 9), "#000"))
    s.append(C(160, 100, 9, "#000"))
    return "".join(s)


def accueil():
    return _chateau() + etoiles([(30, 44, 13, JAUNE), (290, 50, 13, JAUNE), (24, 130, 8, BLANC),
                                 (298, 136, 8, BLANC), (120, 30, 7, BLANC), (204, 26, 7, BLANC)])


def fin():
    s = []
    # livre ouvert
    s.append(P("M30 204 L30 122 Q98 102 160 124 Q222 102 290 122 L290 204 Q222 186 160 208 Q98 186 30 204Z", VIOLET))
    s.append(P("M42 190 L42 112 Q102 94 160 114 L160 196 Q102 176 42 190Z", BLANC))
    s.append(P("M278 190 L278 112 Q218 94 160 114 L160 196 Q218 176 278 190Z", BLANC))
    s.append(T("M160 116 L160 196", GRIS, 3.5))
    for y in (132, 150, 168):
        s.append(T("M62 %g Q102 %g 142 %g" % (y, y - 12, y - 2), GRIS, 4))
        s.append(T("M258 %g Q218 %g 178 %g" % (y, y - 12, y - 2), GRIS, 4))
    # une nouvelle étoile s'envole
    s.append(etoile5(160, 56, 34, JAUNE))
    s.append(etoiles([(92, 62, 13, ROSE), (228, 62, 13, TURQUOISE), (50, 96, 9, BLANC), (270, 96, 9, BLANC)]))
    return "".join(s)


# ------------------------------------------------------------------ titres
def titre_h1():
    """Paillette va à l'école : Paillette et son cartable."""
    s = [mini(paillette, 104, 126, .78)]
    # cartable
    s.append(T("M226 108 q0 -22 22 -22 q22 0 22 22", BRUN_FONCE, 7))
    s.append(R(204, 106, 88, 94, ROUGE, 14))
    s.append(P("M204 150 L204 120 Q204 106 218 106 L278 106 Q292 106 292 120 L292 150 Q248 168 204 150Z", "#D93B3B"))
    s.append(R(220, 142, 14, 24, JAUNE, 4))
    s.append(R(262, 142, 14, 24, JAUNE, 4))
    # crayon
    s.append(G(R(-8, -34, 16, 56, JAUNE) + P("M-8 22 L0 40 L8 22Z", "#FFD2B0") + P("M-3 33 L0 40 L3 33Z", ENCRE)
               + R(-8, -46, 16, 14, ROSE, 4), "translate(250 48) rotate(-62)"))
    return "".join(s)


def titre_h2():
    """Grumo ne sait pas voler : Grumo regarde l'oiseau et le nuage."""
    s = [mini(grumo, 122, 146, .78)]
    # nuage
    for x, y, r in [(226, 52, 18), (250, 42, 22), (276, 54, 17)]:
        s.append(C(x, y, r, BLANC))
    s.append(R(222, 52, 58, 18, BLANC, 9))
    # petit oiseau
    s.append(P("M250 128 l-26 -16 l10 22Z", BLEU_FONCE))
    s.append(E(266, 130, 22, 16, BLEU))
    s.append(P("M262 126 q-4 -30 22 -30 q-2 18 -6 30Z", BLEU_FONCE))
    s.append(P("M286 126 l16 4 l-16 6Z", ORANGE))
    s.append(C(278, 126, 3.5, ENCRE))
    return "".join(s)


def titre_h3():
    """La machine à bisous de Papic."""
    s = []
    s.append(engrenage(74, 92, 22, JAUNE))
    # tuyau d'où sortent les bisous
    s.append(T("M196 100 L196 66 Q196 46 220 46 L236 46", GRIS, 18))
    s.append(E(240, 46, 7, 15, GRIS_FONCE))
    s.append(coeur(274, 40, 2.2, ROSE))
    s.append(coeur(294, 86, 1.5, ROUGE))
    s.append(coeur(262, 92, 1.3, ROSE))
    # pieds et corps de la machine
    s.append(R(86, 200, 20, 18, GRIS_FONCE, 4))
    s.append(R(194, 200, 20, 18, GRIS_FONCE, 4))
    s.append(R(62, 96, 176, 110, TURQUOISE, 18))
    # cadran à cœur
    s.append(C(116, 144, 30, BLANC))
    s.append(coeur(116, 146, 2.3, ROUGE))
    # les deux boutons
    s.append(C(178, 130, 15, GRIS_FONCE))
    s.append(C(178, 127, 12, ROUGE))
    s.append(C(214, 130, 15, GRIS_FONCE))
    s.append(C(214, 127, 12, BLEU))
    # bouche de la machine
    s.append(R(160, 162, 62, 22, ENCRE, 11))
    s.append(T("M172 173 q19 9 38 0", ROSE, 4.5))
    # antenne
    s.append(T("M96 96 L88 62", GRIS, 5))
    s.append(C(88, 58, 9, ROUGE))
    return "".join(s)


def titre_h4():
    """Le gâteau magique de Mamily."""
    s = []
    s.append(E(160, 208, 112, 12, GRIS))
    # trois étages
    s.append(R(74, 150, 172, 56, ROSE_PALE, 10))
    s.append(P("M74 172 L74 160 Q74 150 84 150 L236 150 Q246 150 246 160 L246 172 "
               "Q232 186 218 172 Q204 186 190 172 Q176 186 162 172 Q148 186 134 172 Q120 186 106 172 Q90 186 74 172Z", ROSE))
    s.append(R(100, 104, 120, 50, BLANC, 10))
    s.append(P("M100 124 L100 114 Q100 104 110 104 L210 104 Q220 104 220 114 L220 124 "
               "Q205 138 190 124 Q175 138 160 124 Q145 138 130 124 Q115 138 100 124Z", VIOLET))
    s.append(R(128, 66, 64, 42, ROSE_PALE, 10))
    s.append(P("M128 84 L128 76 Q128 66 138 66 L182 66 Q192 66 192 76 L192 84 Q176 98 160 84 Q144 98 128 84Z", ROSE))
    for x in (96, 128, 160, 192, 224):
        s.append(C(x, 196, 5.5, ROUGE))
    # l'étoile magique
    s.append(etoile5(160, 40, 24, JAUNE))
    s.append(etoiles([(60, 70, 13, JAUNE), (262, 64, 13, JAUNE), (40, 138, 9, BLANC),
                      (284, 132, 9, BLANC), (92, 34, 7, TURQUOISE), (230, 30, 7, TURQUOISE)]))
    return "".join(s)


def titre_h5():
    """Tata Bêtise a mis le château à l'envers."""
    s = [G(_chateau(), "translate(104 108) rotate(180) scale(.74) translate(-160 -125)")]
    s.append(mini(tata_betise, 262, 178, .5))
    s.append(etoiles([(258, 40, 13, JAUNE), (298, 84, 8, BLANC), (212, 60, 8, BLANC)]))
    return "".join(s)


def _dauphin(c="#BFE4FF"):
    s = []
    s.append(P("M-64 30 L-98 18 L-86 42 L-96 64 L-58 46Z", c, 'stroke="%s" stroke-width="5" stroke-linejoin="round"' % c))
    s.append(P("M-10 -42 L-22 -76 L20 -40Z", c, 'stroke="%s" stroke-width="5" stroke-linejoin="round"' % c))
    s.append(P("M-70 34 C-52 -32 20 -64 74 -24 L96 -20 C94 -8 84 -2 72 0 C40 -6 0 6 -40 42Z", c))
    s.append(P("M72 0 C40 -6 0 6 -40 42 C4 34 48 24 72 0Z", BLANC))
    s.append(C(54, -22, 5, ENCRE))
    s.append(T("M70 -8 q10 0 18 -8", BLEU_FONCE, 3.5))
    s.append(P("M10 10 L-2 38 L28 16Z", c))
    return "".join(s)


def titre_h6():
    """Le grand plouf : Pipou le bébé dauphin saute dans les vagues."""
    s = []
    s.append(G(_dauphin(), "translate(158 96) rotate(-14)"))
    # éclaboussures
    for x, y, r in [(70, 150, 9), (52, 118, 6), (96, 128, 7), (250, 150, 9), (272, 118, 6), (226, 126, 7),
                    (40, 164, 5), (284, 162, 5)]:
        s.append(C(x, y, r, "#BFE4FF"))
    s.append(vagues(178, BLEU, 14, 40, 20))
    s.append(vagues(202, BLEU_FONCE, 12, 40, 0))
    return "".join(s)


def _renard():
    s = []
    for sx in (-1, 1):
        s.append(P("M%g -22 L%g -76 L%g -42Z" % (sx * 44, sx * 46, sx * 6), ORANGE,
                   'stroke="%s" stroke-width="6" stroke-linejoin="round"' % ORANGE))
        s.append(P("M%g -34 L%g -62 L%g -44Z" % (sx * 36, sx * 38, sx * 18), BRUN_FONCE))
    s.append(E(0, 0, 50, 42, ORANGE))
    s.append(P("M-48 8 C-40 40 -14 42 0 22 C14 42 40 40 48 8 C30 14 14 6 0 -6 C-14 6 -30 14 -48 8Z", BLANC))
    s.append(E(0, 20, 8, 6.5, ENCRE))
    s.append(C(-20, -8, 6, ENCRE))
    s.append(C(20, -8, 6, ENCRE))
    return "".join(s)


def _lapin():
    s = []
    for sx, a in ((-1, -12), (1, 12)):
        s.append(G(E(0, 0, 14, 42, BLANC) + E(0, 4, 6.5, 28, ROSE), "translate(%g -66) rotate(%g)" % (sx * 22, a)))
    s.append(E(0, 0, 46, 40, BLANC))
    s.append(C(-18, -6, 6, ENCRE))
    s.append(C(18, -6, 6, ENCRE))
    s.append(E(0, 10, 7, 5.5, ROSE))
    s.append(T("M0 15 L0 22 M-9 24 q9 8 18 0", GRIS_FONCE, 3.5))
    s.append(joue(-28, 12, 8))
    s.append(joue(28, 12, 8))
    return "".join(s)


def titre_h7():
    """Le doudou perdu : Doudou Renard et Doudou Lapin… où sont-ils ?"""
    s = [G(_renard(), "translate(88 156)"), G(_lapin(), "translate(232 164)")]
    s.append(T("M140 50 C140 22 184 22 184 50 C184 66 162 66 162 86", JAUNE, 12))
    s.append(C(162, 108, 8, JAUNE))
    return "".join(s)


def titre_h8():
    """Le traîneau du Père Noël est en panne."""
    s = []
    g = []
    # cadeaux
    g.append(R(134, 82, 40, 52, VERT, 4))
    g.append(R(150, 82, 8, 52, JAUNE))
    g.append(T("M154 82 q-14 -18 -20 -4 q10 8 20 4 q14 -18 20 -4 q-10 8 -20 4", JAUNE, 5))
    g.append(R(178, 96, 44, 38, VIOLET, 4))
    g.append(R(196, 96, 8, 38, BLANC))
    # traîneau
    g.append(P("M58 92 C54 150 80 166 118 166 L250 166 L250 112 L224 112 L224 134 L118 134 C106 134 100 120 100 92Z", ROUGE))
    g.append(T("M58 92 q22 -14 42 0", BLANC, 8))
    g.append(T("M112 166 L112 192 M228 166 L228 192", JAUNE, 7))
    g.append(T("M260 192 L84 192 C56 192 50 168 66 158", JAUNE, 8))
    s.append(G("".join(g), "rotate(7 160 150)"))
    # la clé de Papic et les flocons
    s.append(cle(276, 62, 30, .62))
    s.append(etoiles([(40, 44, 12, BLANC), (104, 34, 8, BLANC), (208, 40, 9, BLANC), (30, 138, 8, BLANC),
                      (292, 150, 9, BLANC)]))
    return "".join(s)


def titre_h9():
    """La promenade des étoiles : la lune qui dort."""
    s = []
    s.append(C(128, 112, 70, JAUNE))
    s.append(C(164, 92, 62, "#000"))
    s.append(T("M78 116 q9 8 18 0", BRUN_FONCE, 4.5))
    s.append(T("M92 146 q10 6 18 -2", BRUN_FONCE, 4))
    s.append(etoiles([(214, 60, 20, JAUNE), (268, 120, 14, BLANC), (212, 150, 11, JAUNE), (276, 44, 9, BLANC),
                      (50, 36, 9, BLANC), (36, 200, 8, BLANC), (256, 196, 9, JAUNE)]))
    return "".join(s)


# ------------------------------------------------------------------- choix
def h1_toboggan():
    s = []
    s.append(R(0, 212, 320, 8, VERT, 4))
    # tas de feuilles à l'arrivée
    for x, y, r, c in [(262, 200, 16, ORANGE), (288, 204, 13, JAUNE), (276, 190, 12, JAUNE), (246, 206, 11, ROUGE)]:
        s.append(C(x, y, r, c))
    # échelle
    s.append(T("M56 212 L80 62 M100 212 L112 62", JAUNE, 8))
    for i in range(5):
        y = 188 - i * 28
        s.append(T("M%g %g L%g %g" % (62 + i * 4.5, y, 102 + i * 2.2, y), JAUNE, 6))
    # plateforme et glissière
    s.append(R(74, 54, 58, 14, BLEU, 6))
    s.append(T("M126 68 C190 70 196 196 268 196", ROUGE, 26))
    s.append(T("M128 60 C196 62 204 186 262 188", "#FF8C8C", 6))
    return "".join(s)


def h1_bac_a_sable():
    s = []
    # seau et pelle
    s.append(T("M46 132 q22 -30 44 0", GRIS, 5))
    s.append(P("M42 130 L94 130 L86 178 L50 178Z", ROUGE))
    s.append(R(38, 126, 60, 10, "#D93B3B", 5))
    s.append(G(R(-5, -44, 10, 50, BLEU, 5) + P("M-17 4 L17 4 L17 26 Q0 44 -17 26Z", BLEU)
               + R(-13, -52, 26, 10, BLEU, 5), "translate(262 136) rotate(18)"))
    # château de sable à trois tours
    for x, y, h in [(110, 116, 66), (144, 92, 90), (178, 116, 66)]:
        s.append(R(x, y, 32, h, SABLE))
        for dx in (0, 12, 24):
            s.append(R(x + dx, y - 9, 8, 10, SABLE))
    s.append(P("M152 182 L152 160 a8 8 0 0 1 16 0 L168 182Z", SABLE_OMBRE))
    s.append(R(120, 136, 10, 14, SABLE_OMBRE, 5))
    s.append(R(190, 136, 10, 14, SABLE_OMBRE, 5))
    # la paillette de Paillette, tout en haut
    s.append(etoile(160, 58, 18, JAUNE))
    # tas de sable et cadre du bac
    s.append(P("M52 190 Q160 150 268 190Z", SABLE))
    s.append(R(30, 184, 260, 30, BRUN, 8))
    s.append(T("M46 199 L274 199", BRUN_FONCE, 3.5))
    return "".join(s)


def h2_colline():
    s = []
    s.append(C(46, 46, 22, JAUNE))
    s.append(mini(grumo, 160, 66, .42))
    s.append(P("M-10 244 Q160 -2 330 244Z", VERT))
    s.append(T("M150 236 Q110 200 160 176 Q204 156 164 134", VERT_CLAIR, 10))
    for x, y, c in [(84, 206, ROSE), (236, 208, JAUNE), (222, 172, BLANC), (104, 176, BLANC)]:
        s.append(C(x, y, 6.5, c))
    return "".join(s)


def h2_trampoline():
    s = []
    s.append(mini(grumo, 160, 84, .52))
    # traits de rebond
    s.append(T("M76 132 q-12 12 0 26 M244 132 q12 12 0 26", JAUNE, 6))
    # trampoline
    s.append(T("M70 194 L56 232 M250 194 L264 232 M160 206 L160 234", GRIS_FONCE, 8))
    s.append(E(160, 190, 116, 26, BLEU))
    s.append(E(160, 188, 92, 16, "#30303C"))
    s.append(T("M108 186 q52 12 104 0", GRIS_FONCE, 3.5))
    return "".join(s)


def _bouton(c, c_ombre):
    s = []
    s.append(E(160, 196, 118, 30, GRIS_FONCE))
    s.append(R(42, 176, 236, 20, GRIS_FONCE))
    s.append(E(160, 176, 118, 30, GRIS))
    s.append(E(160, 172, 86, 21, c_ombre))
    s.append(P("M74 172 L74 150 C74 34 246 34 246 150 L246 172 A86 21 0 0 1 74 172Z", c))
    s.append(T("M104 116 C108 86 132 68 156 66", BLANC, 9))
    return "".join(s)


def h3_bouton_rouge():
    return _bouton(ROUGE, "#C93A3A")


def h3_bouton_bleu():
    return _bouton(BLEU, BLEU_FONCE)


def h4_etoiles_en_sucre():
    s = []
    # la grande échelle de Papic
    s.append(T("M38 236 L88 16 M92 236 L134 16", BRUN, 9))
    for i in range(6):
        y = 212 - i * 36
        t = (236 - y) / 220.0
        s.append(T("M%g %g L%g %g" % (38 + 50 * t, y, 92 + 42 * t, y), BRUN, 7))
    # les étoiles en sucre
    s.append(etoile5(214, 70, 38, JAUNE))
    s.append(etoile5(268, 150, 24, ROSE))
    s.append(etoile5(184, 164, 22, BLANC))
    s.append(etoile5(238, 208, 15, TURQUOISE))
    s.append(etoile5(162, 34, 13, ROSE))
    return "".join(s)


def h4_fraise_geante():
    s = []
    s.append(P("M160 222 C92 190 66 126 88 90 C106 62 146 66 160 84 C174 66 214 62 232 90 C254 126 228 190 160 222Z", ROUGE))
    for x, y in [(120, 112), (160, 122), (200, 112), (104, 146), (140, 152), (180, 152), (216, 146),
                 (124, 180), (160, 186), (196, 180)]:
        s.append(E(x, y, 4.5, 6.5, JAUNE))
    # collerette de feuilles et queue
    s.append(T("M160 70 Q164 44 178 34", VERT_FONCE, 8))
    for a in (-70, -35, 0, 35, 70):
        s.append(G(P("M0 0 Q-13 -20 0 -44 Q13 -20 0 0Z", VERT), "translate(160 84) rotate(%g)" % a))
    s.append(etoiles([(52, 60, 12, JAUNE), (272, 60, 12, JAUNE), (40, 180, 8, BLANC), (284, 184, 8, BLANC)]))
    return "".join(s)


def h5_chambre():
    """La chambre : une banane sur l'oreiller !"""
    s = []
    # lit
    s.append(R(30, 78, 24, 138, BRUN, 10))
    s.append(R(270, 132, 20, 84, BRUN, 8))
    s.append(R(44, 156, 240, 38, BLANC, 8))
    s.append(E(100, 144, 44, 20, BLANC))
    s.append(G(P("M70 96 C98 126 140 118 160 90 C150 100 108 104 82 84Z", JAUNE,
                 'stroke="%s" stroke-width="9" stroke-linejoin="round"' % JAUNE)
               + T("M72 90 l-6 -8", BRUN_FONCE, 6), "translate(-18 42) rotate(-6 115 100)"))
    s.append(P("M140 150 Q140 136 154 136 L266 136 Q280 136 280 150 L280 196 L140 196Z", VIOLET))
    s.append(R(140, 136, 140, 16, ROSE, 8))
    s.append(etoiles([(180, 176, 9, JAUNE), (222, 170, 7, BLANC), (252, 182, 8, JAUNE)]))
    s.append(etoiles([(236, 60, 12, JAUNE), (286, 92, 8, BLANC)]))
    return "".join(s)


def h5_salle_de_bain():
    """La salle de bain : la brosse à dents dans le pot de confiture !"""
    s = []
    # brosse à dents
    s.append(G(R(-8, -118, 16, 124, TURQUOISE, 8) + R(8, -116, 18, 40, BLANC, 4)
               + T("M10 -104 L24 -104 M10 -92 L24 -92", GRIS, 2.5), "translate(176 110) rotate(28)"))
    # pot de confiture
    s.append(R(96, 104, 128, 112, "#D93B5A", 22))
    s.append(R(88, 90, 144, 24, GRIS, 10))
    s.append(R(120, 136, 80, 54, BLANC, 10))
    s.append(P("M160 182 C136 168 132 150 146 146 C154 144 158 150 160 154 C162 150 166 144 174 146 C188 150 184 168 160 182Z", ROUGE))
    s.append(P("M160 150 l-8 -8 l8 2 l0 -6 l0 6 l8 -2Z", VERT, 'stroke="%s" stroke-width="3" stroke-linejoin="round"' % VERT))
    s.append(T("M108 126 L108 190", "#FF8FA8", 6))
    # bulles de savon
    for x, y, r in [(54, 80, 14), (40, 150, 9), (270, 160, 13), (286, 100, 8)]:
        s.append(bulle(x, y, r))
    return "".join(s)


def _fond_marin():
    return R(0, 214, 320, 26, SABLE) + T("M-10 30 q20 -14 40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0", BLEU, 6)


def h6_rocher():
    s = [_fond_marin()]
    # crabe qui dépasse à droite
    g = []
    g.append(T("M-26 -6 L-50 -30 M26 -6 L50 -30", ROUGE, 7))
    g.append(P("M-50 -30 l-16 -14 a13 13 0 1 0 22 -4 l-6 12Z", ROUGE))
    g.append(P("M50 -30 l16 -14 a13 13 0 1 1 -22 -4 l6 12Z", ROUGE))
    g.append(T("M-30 12 L-48 26 M30 12 L48 26 M-22 20 L-34 38 M22 20 L34 38", ROUGE, 6))
    g.append(E(0, 0, 38, 26, ROUGE))
    g.append(T("M-12 -22 L-14 -40 M12 -22 L14 -40", ROUGE, 5))
    g.append(C(-14, -42, 8, BLANC) + C(14, -42, 8, BLANC) + C(-13, -42, 4, ENCRE) + C(15, -42, 4, ENCRE))
    g.append(T("M-12 6 q12 10 24 0", ENCRE, 4))
    s.append(G("".join(g), "translate(246 172) scale(.95)"))
    # grand rocher
    s.append(P("M22 216 C10 150 46 76 112 62 C170 50 210 94 216 150 C220 184 216 204 212 216Z", GRIS_FONCE))
    s.append(P("M64 124 C80 96 108 84 132 86 C108 96 88 112 80 136Z", GRIS))
    for x, y, r in [(276, 76, 13), (252, 108, 7), (296, 112, 6)]:
        s.append(bulle(x, y, r))
    return "".join(s)


def h6_algues():
    s = []
    s.append(T("M-10 30 q20 -14 40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0", BLEU, 6))
    # algues
    for x, h, c in [(40, 120, VERT_FONCE), (82, 160, VERT), (236, 150, VERT), (280, 110, VERT_FONCE), (124, 96, VERT_FONCE)]:
        d = "M%g 220" % x
        y, sens = 220, 1
        while y > 220 - h:
            d += " q%g -20 0 -40" % (sens * 22)
            y -= 40
            sens = -sens
        s.append(T(d, c, 15))
    s.append(R(0, 214, 320, 26, SABLE))
    # petit poisson rouge
    g = P("M-34 0 L-66 -26 L-58 0 L-66 26Z", ORANGE) + E(0, 0, 42, 28, ORANGE)
    g += P("M-6 -26 Q8 -48 26 -22Z", "#E8742A") + T("M-4 6 q10 10 4 22", "#E8742A", 5)
    g += C(20, -6, 8, BLANC) + C(22, -6, 4, ENCRE) + T("M28 12 q8 0 12 -6", ENCRE, 3.5)
    s.append(G(g, "translate(178 124)"))
    for x, y, r in [(244, 76, 11), (262, 46, 7), (226, 52, 5)]:
        s.append(bulle(x, y, r))
    return "".join(s)


def h7_sous_le_lit():
    s = []
    # lit vu de côté, haut sur pattes
    s.append(R(30, 28, 22, 186, BRUN, 10))
    s.append(R(270, 62, 20, 152, BRUN, 8))
    s.append(R(44, 70, 240, 30, BLANC, 8))
    s.append(E(96, 62, 40, 17, BLANC))
    s.append(P("M52 84 L278 84 L278 116 Q262 130 246 116 Q230 130 214 116 Q198 130 182 116 Q166 130 150 116 "
               "Q134 130 118 116 Q102 130 86 116 Q70 130 52 116Z", TURQUOISE))
    s.append(R(0, 212, 320, 8, BRUN_FONCE, 4))
    # dessous : une chaussette, un crayon rouge, un mouton de poussière
    g = R(-13, -38, 26, 46, BLANC, 6) + P("M-13 0 L13 0 L13 10 Q13 26 -4 26 L-30 26 Q-42 26 -42 14 Q-42 4 -30 4 L-13 4Z", BLANC)
    g += R(-13, -30, 26, 8, ROSE) + R(-13, -14, 26, 8, ROSE) + P("M-42 14 Q-42 4 -30 4 L-26 4 L-26 26 L-30 26 Q-42 26 -42 14Z", ROSE)
    s.append(G(g, "translate(116 180)"))
    s.append(G(R(-36, -7, 56, 14, ROUGE) + P("M20 -7 L38 0 L20 7Z", "#FFD2B0") + P("M31 -3 L38 0 L31 3Z", ENCRE)
               + R(-44, -7, 10, 14, GRIS, 3), "translate(196 198) rotate(-8)"))
    for x, y, r in [(244, 184, 12), (258, 192, 10), (234, 196, 9), (252, 178, 8)]:
        s.append(C(x, y, r, GRIS))
    s.append(C(242, 186, 3, ENCRE) + C(254, 186, 3, ENCRE))
    return "".join(s)


def h7_baignoire():
    s = []
    # robinet
    s.append(T("M262 116 L262 76 Q262 56 242 56 L232 56 L232 70", GRIS, 10))
    # mousse
    for x, y, r in [(84, 104, 18), (110, 96, 15), (220, 104, 16), (196, 98, 13), (60, 112, 12)]:
        s.append(C(x, y, r, CIEL))
    # canard en plastique
    s.append(E(150, 96, 34, 24, JAUNE))
    s.append(P("M178 94 l22 -14 l-6 22Z", JAUNE))
    s.append(C(128, 66, 21, JAUNE))
    s.append(P("M110 66 l-22 4 l20 10Z", ORANGE))
    s.append(C(124, 60, 4.5, ENCRE))
    s.append(P("M146 96 q16 -12 30 2 q-14 12 -30 -2Z", "#F2B622"))
    # baignoire
    s.append(T("M90 198 L80 224 M230 198 L240 224", JAUNE, 9))
    s.append(P("M48 124 L272 124 C272 178 250 202 212 202 L108 202 C70 202 48 178 48 124Z", BLANC))
    s.append(R(32, 110, 256, 20, GRIS, 10))
    s.append(T("M78 146 C80 168 90 180 106 184", GRIS, 5))
    for x, y, r in [(288, 60, 9), (36, 60, 12), (300, 96, 6)]:
        s.append(bulle(x, y, r))
    return "".join(s)


def _carotte():
    s = []
    for a in (-28, 0, 28):
        s.append(G(E(0, -20, 8, 22, VERT), "translate(0 -44) rotate(%g)" % a))
    s.append(P("M-19 -44 Q0 -58 19 -44 L5 54 Q0 62 -5 54Z", ORANGE))
    s.append(T("M-9 -20 l12 0 M0 4 l10 0 M-6 26 l8 0", "#E8742A", 4))
    return "".join(s)


def h8_carottes():
    s = []
    for x, y, a, k in [(92, 136, -24, 1.25), (160, 128, 0, 1.4), (228, 136, 24, 1.25)]:
        s.append(G(_carotte(), "translate(%g %g) rotate(%g) scale(%g)" % (x, y, a, k)))
    s.append(etoiles([(22, 116, 10, BLANC), (298, 116, 10, BLANC), (34, 204, 9, BLANC), (286, 204, 9, BLANC),
                      (160, 224, 7, BLANC)]))
    return "".join(s)


def h8_biscuits():
    s = []
    s.append(E(160, 196, 140, 26, GRIS))
    s.append(E(160, 192, 112, 16, BLANC))
    # biscuit étoile
    s.append(etoile5(86, 112, 44, BISCUIT))
    s.append(etoile5(86, 112, 22, BLANC))
    s.append(etoile5(86, 112, 15, BISCUIT))
    # bonhomme en pain d'épices
    g = T("M-34 -4 L34 -4 M-14 34 L-22 66 M14 34 L22 66", BISCUIT, 20) + R(-19, -14, 38, 58, BISCUIT, 14)
    g += C(0, -40, 24, BISCUIT) + C(-9, -44, 3.5, ENCRE) + C(9, -44, 3.5, ENCRE) + T("M-9 -32 q9 8 18 0", BLANC, 4)
    g += C(0, 2, 5, ROUGE) + C(0, 20, 5, ROUGE)
    g += T("M-40 -10 l0 12 M40 -10 l0 12 M-28 60 l12 4 M28 60 l-12 4", BLANC, 4)
    s.append(G(g, "translate(170 106) scale(.98)"))
    # biscuit rond au cœur
    s.append(C(254, 126, 38, BISCUIT))
    s.append(coeur(254, 130, 3.2, ROUGE))
    s.append(etoiles([(250, 44, 11, JAUNE), (36, 44, 9, BLANC)]))
    return "".join(s)


SCENES = [
    ("Menu0-accueil", "Accueil : le château des Princesses", accueil),
    ("Menu2-H1", "Paillette va à l'école", titre_h1),
    ("Menu2-H2", "Grumo ne sait pas voler", titre_h2),
    ("Menu2-H3", "La machine à bisous de Papic", titre_h3),
    ("Menu2-H4", "Le gâteau magique de Mamily", titre_h4),
    ("Menu2-H5", "Tata Bêtise a mis le château à l'envers", titre_h5),
    ("Menu2-H6", "Le grand plouf", titre_h6),
    ("Menu2-H7", "Le doudou perdu", titre_h7),
    ("Menu2-H8", "Le traîneau du Père Noël est en panne", titre_h8),
    ("Menu2-H9", "La promenade des étoiles", titre_h9),
    ("H1-5a", "H1 – Le toboggan", h1_toboggan),
    ("H1-5b", "H1 – Le bac à sable", h1_bac_a_sable),
    ("H2-5a", "H2 – La colline", h2_colline),
    ("H2-5b", "H2 – Le trampoline", h2_trampoline),
    ("H3-4a", "H3 – Le bouton rouge", h3_bouton_rouge),
    ("H3-4b", "H3 – Le bouton bleu", h3_bouton_bleu),
    ("H4-4a", "H4 – Les étoiles en sucre", h4_etoiles_en_sucre),
    ("H4-4b", "H4 – Les fraises géantes", h4_fraise_geante),
    ("H5-4a", "H5 – La chambre", h5_chambre),
    ("H5-4b", "H5 – La salle de bain", h5_salle_de_bain),
    ("H6-4a", "H6 – Le grand rocher", h6_rocher),
    ("H6-4b", "H6 – Les algues", h6_algues),
    ("H7-4a", "H7 – Sous le lit", h7_sous_le_lit),
    ("H7-4b", "H7 – Dans la baignoire", h7_baignoire),
    ("H8-4a", "H8 – Les carottes", h8_carottes),
    ("H8-4b", "H8 – Les biscuits de Mamily", h8_biscuits),
    ("Fin-autre-aventure", "Fin : encore une aventure ?", fin),
]

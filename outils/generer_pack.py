#!/usr/bin/env python3
"""Fabrique le pack Lunii « Les Aventures des Princesses » : une archive STUdio (.zip) avec le
graphe complet (story.json), les images et les sons.

Usage (depuis le dossier histoires-lunii) :
  sh outils/pack.sh             # fabrique pack/Les-Aventures-des-Princesses.zip
  sh outils/pack.sh --liste     # montre ce qui serait fait et ce qui manque, sans rien écrire
  sh outils/pack.sh --incomplet # fabrique quand même s'il manque des sons (remplacés par un silence)
  sh outils/pack.sh --wav       # garde les .wav tels quels (archive bien plus grosse)

Ce que le script lit :
  histoires/*.md           la structure : segments, variantes par princesse et par compagnon, choix
  Audacity/<segment>.wav   les montages exportés (H2-1-Romy.wav, H2-5a.wav, Menu3-Grumo.wav…)
  images/png/<code>.png    les images (voir images/README.md) et images/vignette.png

Le parcours dans la Lunii :
  Accueil → Menu 1 (qui part ?) → Menu 2 (quelle histoire ?) → Menu 3 (qui vient aussi ?)
  → l'histoire, segment après segment, avec son choix au milieu → « Encore une aventure ? »
  → retour au Menu 2, sur l'histoire suivante.          H9 (le dodo) : ni Menu 3, ni choix, ni fin.
  Bouton maison : depuis une histoire ou le Menu 3 on revient au Menu 2, du Menu 2 au Menu 1.

La Lunii n'a pas de mémoire : pour que la fin dise le bon prénom, chaque princesse a son propre
chemin dans le graphe (et chaque compagnon aussi, tant que son segment n'est pas passé). Les sons
et les images, eux, ne sont rangés qu'une fois dans l'archive.

Le choix dans l'histoire : après la question, la molette montre les deux images. Si un petit
montage « H1-5a-choix.wav » existe dans Audacity/ (ex. « Le toboggan ! »), il est joué à chaque
cran de molette ; sinon l'image s'affiche en silence. Le bouton OK lance la suite.

Les sons sont convertis en MP3 mono 44,1 kHz avec ffmpeg (gardés dans pack/mp3/ pour ne pas tout
refaire à chaque fois). Sans ffmpeg, les .wav sont mis tels quels : STUdio les convertit lui-même.
À la fin, le script rejoue tous les parcours dans le graphe et les compare aux scripts.
"""
import argparse, hashlib, json, pathlib, shutil, subprocess, sys, uuid, wave, zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from creer_projets_audacity import scenes, dossier_audacity, FILLES  # noqa: E402

DEPOT = pathlib.Path(__file__).resolve().parent.parent
IMAGES = DEPOT / "images" / "png"
VIGNETTE = DEPOT / "images" / "vignette.png"
SORTIE = DEPOT / "pack"
TITRE = "Les Aventures des Princesses"
DESCRIPTION = ("Neuf histoires dont Romy et Alix sont les héroïnes, avec Papic, Mamily, Tata Bêtise, "
               "Paillette la licorne et Grumo le dragon.")
VERSION = 1
ESPACE = uuid.UUID("6c756e69-6920-4c65-7320-5072696e6365")   # pour des identifiants stables d'une fois sur l'autre

# Réglages des boutons, par sorte d'écran
COUVERTURE = dict(wheel=True, ok=True, home=False, pause=False, autoplay=False)
QUESTION = dict(wheel=False, ok=False, home=False, pause=False, autoplay=True)
REPONSE = dict(wheel=True, ok=True, home=True, pause=False, autoplay=False)
HISTOIRE = dict(wheel=False, ok=False, home=True, pause=True, autoplay=True)


# ------------------------------------------------------------------ structure des histoires
def base_choix(sc):
    """« H2-5 » pour H2-5a / H2-5b, None si ce n'est pas une branche de choix."""
    return sc[:-1] if sc[-1].isalpha() and sc[-2].isdigit() else None


def lire_structure():
    """{hid: [étape]} où une étape est ("segment", scène, sorte) ou ("choix", [scène a, scène b]) ;
    sorte = "commun", "fille" (une version par princesse) ou "compagnon" ; et {hid: [compagnons]}."""
    histoires, compagnons = {}, {}
    for hid, liste in scenes(None).items():
        if not (hid.startswith("H") and hid[1:].isdigit()):
            continue
        etapes = []
        for sc, variantes, _lignes in liste:
            if base_choix(sc):
                if etapes and etapes[-1][0] == "choix" and base_choix(etapes[-1][1][0]) == base_choix(sc):
                    etapes[-1][1].append(sc)
                else:
                    etapes.append(("choix", [sc]))
            elif not variantes:
                etapes.append(("segment", sc, "commun"))
            elif set(variantes) <= set(FILLES):
                etapes.append(("segment", sc, "fille"))
            else:
                etapes.append(("segment", sc, "compagnon"))
                compagnons[hid] = list(variantes)
        histoires[hid] = etapes
    return dict(sorted(histoires.items(), key=lambda kv: int(kv[0][1:]))), compagnons


def son_de(etape, fille, compagnon):
    _, sc, sorte = etape
    return {"commun": sc, "fille": f"{sc}-{fille}", "compagnon": f"{sc}-{compagnon}"}[sorte]


# ------------------------------------------------------------------------------ le graphe
class Pack:
    def __init__(self):
        self.ecrans, self.aiguillages, self._seul = [], [], {}

    def ecran(self, nom, reglage, son=None, image=None, depart=False):
        e = dict(uuid=str(uuid.uuid5(ESPACE, "ecran " + nom)), type="stage", name=nom, squareOne=depart,
                 image=image, audio=son, okTransition=None, homeTransition=None, controlSettings=dict(reglage))
        self.ecrans.append(e)
        return e

    def aiguillage(self, nom, options=()):
        a = dict(id=str(uuid.uuid5(ESPACE, "aiguillage " + nom)), type="action", name=nom,
                 options=[o["uuid"] for o in options])
        self.aiguillages.append(a)
        return a

    def vers(self, cible, rang=0):
        """Transition vers un aiguillage (au rang donné) ou vers un écran seul."""
        if cible is None:
            return None
        if "uuid" in cible:  # un écran : il lui faut un aiguillage à une seule sortie
            if cible["uuid"] not in self._seul:
                self._seul[cible["uuid"]] = self.aiguillage("→ " + cible["name"], [cible])
            cible = self._seul[cible["uuid"]]
        return dict(actionNode=cible["id"], optionIndex=rang)


def construire(histoires, compagnons, etiquettes=()):
    """etiquettes : codes des choix qui ont un petit son « H1-5a-choix »."""
    p = Pack()
    hids = list(histoires)
    accueil = p.ecran("Accueil", COUVERTURE, "Menu0-accueil", "Menu0-accueil", depart=True)
    q1 = p.ecran("Menu1-question", QUESTION, "Menu1-question")
    menu1 = p.aiguillage("Menu 1 : qui part à l'aventure ?")
    accueil["okTransition"] = p.vers(q1)
    q1["okTransition"] = p.vers(menu1)

    for i, fille in enumerate(FILLES):
        o1 = p.ecran(f"Menu1-{fille}", REPONSE, f"Menu1-{fille}", f"Menu1-{fille}")
        menu1["options"].append(o1["uuid"])
        q2 = p.ecran(f"Menu2-question ({fille})", QUESTION, "Menu2-question")
        menu2 = p.aiguillage(f"Menu 2 : quelle histoire ? ({fille})")
        o1["okTransition"] = p.vers(q2)
        q2["okTransition"] = p.vers(menu2)

        for j, hid in enumerate(hids):
            etapes, memo = histoires[hid], {}
            retour = p.vers(menu2, j)
            o2 = p.ecran(f"Menu2-{hid} ({fille})", REPONSE, f"Menu2-{hid}", f"Menu2-{hid}")
            o2["homeTransition"] = p.vers(menu1, i)
            menu2["options"].append(o2["uuid"])
            a_un_choix = any(e[0] == "choix" for e in etapes)

            def suite(k, comp, fille=fille, hid=hid, j=j, etapes=etapes, memo=memo, retour=retour,
                      menu2=menu2, a_un_choix=a_un_choix):
                """Transition vers la suite de l'histoire à partir de l'étape k."""
                reste_comp = any(e[0] == "segment" and e[2] == "compagnon" for e in etapes[k:])
                cle = (k, comp if reste_comp else None)
                if cle in memo:
                    return memo[cle]
                qui = fille + (f", {comp}" if cle[1] else "")
                if k == len(etapes):
                    if not a_un_choix:          # H9 : l'histoire s'arrête simplement
                        res = None
                    else:
                        fin = p.ecran(f"Fin ({hid}, {fille})", HISTOIRE, "Fin-autre-aventure", "Fin-autre-aventure")
                        fin["okTransition"] = p.vers(menu2, (j + 1) % len(hids))
                        fin["homeTransition"] = retour
                        res = p.vers(fin)
                elif etapes[k][0] == "choix":
                    options = []
                    for sc in etapes[k][1]:
                        o = p.ecran(f"{sc} choix ({qui})", REPONSE, f"{sc}-choix" if sc in etiquettes else "silence", sc)
                        b = p.ecran(f"{sc} ({qui})", HISTOIRE, sc, sc)
                        o["okTransition"], o["homeTransition"] = p.vers(b), retour
                        b["okTransition"], b["homeTransition"] = suite(k + 1, comp), retour
                        options.append(o)
                    res = p.vers(p.aiguillage(f"Choix {base_choix(etapes[k][1][0])} ({qui})", options))
                else:
                    son = son_de(etapes[k], fille, comp)
                    e = p.ecran(f"{son} ({qui})", HISTOIRE, son)
                    e["okTransition"], e["homeTransition"] = suite(k + 1, comp), retour
                    res = p.vers(e)
                memo[cle] = res
                return res

            if hid in compagnons:
                q3 = p.ecran(f"Menu3-question ({hid}, {fille})", QUESTION, "Menu3-question")
                menu3 = p.aiguillage(f"Menu 3 : qui vient aussi ? ({hid}, {fille})")
                o2["okTransition"], q3["okTransition"] = p.vers(q3), p.vers(menu3)
                for comp in compagnons[hid]:
                    o3 = p.ecran(f"Menu3-{comp} ({hid}, {fille})", REPONSE, f"Menu3-{comp}", f"Menu3-{comp}")
                    o3["okTransition"], o3["homeTransition"] = suite(0, comp), retour
                    menu3["options"].append(o3["uuid"])
            else:
                o2["okTransition"] = suite(0, None)
    return p


def placer(p):
    """Une position par nœud, colonne par colonne depuis l'accueil (pour l'éditeur de STUdio)."""
    ecrans = {e["uuid"]: e for e in p.ecrans}
    aig = {a["id"]: a for a in p.aiguillages}
    prof, file = {p.ecrans[0]["uuid"]: 0}, [p.ecrans[0]["uuid"]]
    while file:
        n = file.pop(0)
        if n in ecrans:
            t = ecrans[n]["okTransition"]
            suivants = [t["actionNode"]] if t else []
        else:
            suivants = aig[n]["options"]
        for s in suivants:
            if s not in prof:
                prof[s] = prof[n] + 1
                file.append(s)
    rang = {}
    for n in list(ecrans.values()) + list(aig.values()):
        d = prof.get(n.get("uuid") or n["id"], 0)
        rang[d] = rang.get(d, 0) + 1
        n["position"] = dict(x=min(100 + d * 240, 32000), y=min(60 + (rang[d] - 1) * 110, 32000))


# -------------------------------------------------------------------------- vérification
def verifier(p, histoires, compagnons):
    """Rejoue chaque parcours dans le graphe et le compare au script. Renvoie [(nom, [sons])]."""
    ecrans = {e["uuid"]: e for e in p.ecrans}
    aig = {a["id"]: a for a in p.aiguillages}
    for e in p.ecrans:
        for t in (e["okTransition"], e["homeTransition"]):
            assert t is None or 0 <= t["optionIndex"] < len(aig[t["actionNode"]]["options"]), e["name"]
        assert e["controlSettings"]["autoplay"] or e["controlSettings"]["ok"], e["name"]
    assert len(ecrans) == len(p.ecrans) and len(aig) == len(p.aiguillages), "identifiants en double"
    for a in p.aiguillages:
        assert a["options"] and all(o in ecrans for o in a["options"]), a["name"]
    vus, file = set(), [p.ecrans[0]["uuid"]]
    while file:
        n = file.pop()
        if n in vus:
            continue
        vus.add(n)
        for t in (ecrans[n]["okTransition"], ecrans[n]["homeTransition"]):
            if t:
                file.extend(aig[t["actionNode"]]["options"])
    assert len(vus) == len(ecrans), "écrans inaccessibles : %d" % (len(ecrans) - len(vus))

    def aller(e, rang=0):
        t = e["okTransition"]
        return None if t is None else ecrans[aig[t["actionNode"]]["options"][rang if rang is not None else t["optionIndex"]]]

    hids, parcours = list(histoires), []
    menu1 = aller(aller(p.ecrans[0]), None)
    assert menu1["audio"] == "Menu1-" + FILLES[0]
    for i, fille in enumerate(FILLES):
        o1 = aller(aller(p.ecrans[0]), i)
        for j, hid in enumerate(hids):
            o2 = aller(aller(o1, None), j)
            assert o2["audio"] == f"Menu2-{hid}", o2["name"]
            etapes = histoires[hid]
            nb_choix = max([len(e[1]) for e in etapes if e[0] == "choix"] or [1])
            for c, comp in enumerate(compagnons.get(hid, [None])):
                for b in range(nb_choix):
                    attendu = []
                    for e in etapes:
                        attendu.append(e[1][b] if e[0] == "choix" else son_de(e, fille, comp))
                    e = aller(aller(o2, None), c) if comp else aller(o2, None)
                    if comp:
                        assert e["audio"] == f"Menu3-{comp}", e["name"]
                        e = aller(e, None)
                    joue = []
                    while e is not None and e["audio"] != "Fin-autre-aventure":
                        if e["controlSettings"]["wheel"]:      # l'écran du choix : on prend la branche b
                            t = e["homeTransition"]
                            assert aig[t["actionNode"]]["options"][t["optionIndex"]] == o2["uuid"]
                            freres = next(a["options"] for a in p.aiguillages if e["uuid"] in a["options"])
                            e = aller(ecrans[freres[b]], None)
                        joue.append(e["audio"])
                        e = aller(e, None)
                    nom = f"{hid} · {fille}" + (f" · {comp}" if comp else "") + (f" · {attendu[[x[0] for x in etapes].index('choix')]}" if nb_choix > 1 else "")
                    assert joue == attendu, f"{nom} : {joue} au lieu de {attendu}"
                    if nb_choix > 1:      # après la fin : retour au menu 2 de la même princesse, histoire suivante
                        assert e is not None and aller(e, None)["audio"] == f"Menu2-{hids[(j + 1) % len(hids)]}", nom
                        assert aller(e, None)["uuid"] in [o for a in p.aiguillages for o in a["options"] if o2["uuid"] in a["options"]]
                    else:
                        assert e is None, nom
                    parcours.append((nom, joue))
    return parcours


# ------------------------------------------------------------------------------ fichiers
def duree(f):
    with wave.open(str(f)) as w:
        return w.getnframes() / w.getframerate()


def ecrire_silence(cible, secondes=0.4):
    with wave.open(str(cible), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(44100)
        w.writeframes(b"\0\0" * int(44100 * secondes))


def en_mp3(wav, mp3):
    if mp3.exists() and mp3.stat().st_mtime >= wav.stat().st_mtime:
        return False
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-ac", "1", "-ar", "44100",
                    "-codec:a", "libmp3lame", "-b:a", "96k", "-map_metadata", "-1", "-id3v2_version", "0",
                    "-write_xing", "0", str(mp3)], check=True)
    return True


def hms(s):
    return "%d min %02d" % (s // 60, s % 60)


def main():
    ap = argparse.ArgumentParser(description="Fabrique le pack Lunii (archive STUdio).")
    ap.add_argument("--liste", action="store_true", help="montrer sans rien écrire")
    ap.add_argument("--incomplet", action="store_true", help="un silence à la place des sons qui manquent")
    ap.add_argument("--wav", action="store_true", help="garder les .wav (pas de conversion en MP3)")
    a = ap.parse_args()

    audacity = dossier_audacity()
    histoires, compagnons = lire_structure()
    codes_choix = [sc for et in histoires.values() for e in et if e[0] == "choix" for sc in e[1]]
    etiquettes = [sc for sc in codes_choix if (audacity / f"{sc}-choix.wav").exists()]
    p = construire(histoires, compagnons, etiquettes)
    placer(p)
    parcours = verifier(p, histoires, compagnons)

    sons = sorted({e["audio"] for e in p.ecrans if e["audio"]})
    images = sorted({e["image"] for e in p.ecrans if e["image"]})
    sons_absents = [s for s in sons if s != "silence" and not (audacity / f"{s}.wav").exists()]
    images_absentes = [i for i in images if not (IMAGES / f"{i}.png").exists()]

    print(f"{TITRE} : {len(histoires)} histoires, {len(parcours)} parcours vérifiés un par un")
    print(f"  graphe : {len(p.ecrans)} écrans, {len(p.aiguillages)} aiguillages")
    print(f"  {len(sons) - 1} sons, {len(images)} images")
    if not sons_absents:
        d = {s: duree(audacity / f"{s}.wav") for s in sons if s != "silence"}
        longueurs = sorted((sum(d[s] for s in joue), nom) for nom, joue in parcours)
        print(f"  durée d'une histoire : de {hms(longueurs[0][0])} ({longueurs[0][1]}) à {hms(longueurs[-1][0])} ({longueurs[-1][1]})")
        print(f"  tous les sons bout à bout : {hms(sum(d.values()))}")
    print("  choix dans les histoires : " + (f"{len(etiquettes)} avec leur petit son, " if etiquettes else "")
          + f"{len(codes_choix) - len(etiquettes)} en silence (image seule)")
    for nom, liste in (("sons", sons_absents), ("images", images_absentes)):
        if liste:
            print(f"  !! {nom} qui manquent ({len(liste)}) : " + ", ".join(liste))
    if a.liste:
        return
    if images_absentes or (sons_absents and not a.incomplet):
        sys.exit("Pack non fabriqué : il manque des fichiers" + (" (--incomplet pour le faire quand même)." if not images_absentes else "."))

    SORTIE.mkdir(exist_ok=True)
    (SORTIE / "mp3").mkdir(exist_ok=True)
    silence = SORTIE / "mp3" / "silence.wav"
    ecrire_silence(silence)
    mp3 = not a.wav and shutil.which("ffmpeg")
    if not a.wav and not mp3:
        print("  ffmpeg introuvable : les sons sont mis en .wav (STUdio les convertira).")
    fichiers, refaits = {}, 0          # nom dans le graphe -> fichier sur le disque
    for s in sons:
        source = silence if (s == "silence" or s in sons_absents) else audacity / f"{s}.wav"
        if mp3:
            cible = SORTIE / "mp3" / f"{s}.mp3"
            refaits += en_mp3(source, cible)
            source = cible
        fichiers[("audio", s)] = source
    for i in images:
        fichiers[("image", i)] = IMAGES / f"{i}.png"
    if mp3:
        print(f"  MP3 : {refaits} convertis, {len(sons) - refaits} déjà à jour")

    # Dans l'archive, chaque fichier porte l'empreinte de son contenu (comme le fait STUdio)
    noms, contenus = {}, {}
    for cle, f in fichiers.items():
        donnees = f.read_bytes()
        nom = hashlib.sha1(donnees).hexdigest() + f.suffix
        noms[cle], contenus[nom] = nom, donnees
    ecrans = []
    for e in p.ecrans:
        e = dict(e)
        e["audio"] = noms[("audio", e["audio"])] if e["audio"] else None
        e["image"] = noms[("image", e["image"])] if e["image"] else None
        ecrans.append(e)
    histoire = dict(format="v1", title=TITRE, version=VERSION, description=DESCRIPTION,
                    nightModeAvailable=False, stageNodes=ecrans, actionNodes=p.aiguillages)
    cible = SORTIE / (TITRE.replace(" ", "-") + ".zip")
    with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("story.json", json.dumps(histoire, ensure_ascii=False, indent=1))
        if VIGNETTE.exists():
            z.write(VIGNETTE, "thumbnail.png")
        for nom, donnees in sorted(contenus.items()):
            z.writestr("assets/" + nom, donnees, zipfile.ZIP_STORED if nom.endswith(".mp3") else zipfile.ZIP_DEFLATED)
    print(f"→ {cible.relative_to(DEPOT)} ({cible.stat().st_size / 1e6:.1f} Mo)")


if __name__ == "__main__":
    main()

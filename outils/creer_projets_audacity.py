#!/usr/bin/env python3
"""Crée les projets Audacity (.aup3) prêts à monter, à partir des prises OmniVoice.

Usage (depuis le dossier histoires-lunii, Audacity 3.7 ouvert, mod-script-pipe activé) :
  sh outils/projets-audacity.sh --liste            # voir ce qui sera créé, sans rien faire
  sh outils/projets-audacity.sh                    # tout créer (segments + histoires complètes)
  sh outils/projets-audacity.sh --histoire H2 H3   # seulement certaines histoires (ou Menus)
  sh outils/projets-audacity.sh --quoi completes   # seulement les histoires complètes (ou : segments)
  sh outils/projets-audacity.sh --histoire Menus --quoi completes   # le projet « Menus complet »

1) Un projet par segment et par variante : H2-1-Romy, H2-1-Alix, H2-1-Romy&Alix (avec leur début
   et fin communs), H2-2, H2-3-Mamily…  Dans chaque projet :
   - une piste par réplique, placées bout à bout dans l'ordre du script (les prises d'une même
     réplique, ex. …-Romy&Alix-Romy et …-Romy&Alix-Alix, sont superposées sur des pistes séparées) ;
   - une piste d'étiquettes « Script » avec le texte de chaque réplique ;
   - deux pistes vides « Bruitages » et « Musique ».

2) Trois histoires complètes par histoire (« H2 complete - 1/2/3 »), un parcours chacune :
   1 = Romy, 2 = Alix, 3 = les deux ; le compagnon et le choix changent d'un parcours à l'autre.
   Chaque segment du parcours est pris dans son montage « H2-1-Romy.wav » (dossier Projets) s'il
   existe, sinon dans les prises brutes. Une étiquette marque le début de chaque segment.

3) Pour les menus : un seul projet « Menus complet », tous les fichiers dans l'ordre du script
   (accueil → question → toutes les réponses → question suivante… → fin), 1 s de blanc entre deux
   fichiers, chacun pris dans son montage « Menu1-Romy.wav » s'il existe, sinon dans les prises.

Enregistré dans « 2 – Projets Audacity » de l'histoire (« 3 – Menus » pour les menus).

On NE TOUCHE JAMAIS à un projet existant : un projet est sauté s'il existe déjà en .aup3/.aup4
du même nom dans n'importe quel dossier « 2 – Projets Audacity » ou « 3 – Montés » du Drive
(un montage .wav/.mp3 seul n'empêche pas la création). Un projet auquel il manque une prise
(ex. réplique de Mathéo) n'est pas créé, mais il est signalé. Relancer ne crée que ce qui manque.
"""
import argparse, errno, json, os, pathlib, plistlib, re, select, subprocess, sys, time, unicodedata, wave

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from generer_voix import CONFIG, lire_histoires, dossier_prises  # noqa: E402

BLANC = 0.5        # silence entre deux répliques / deux segments (s)
BLANC_MENUS = 1.0  # entre deux fichiers de menu dans « Menus complet » (s)
MANQUE = 2.0       # place laissée pour une réplique sans prise (s)
EXTS_PROJET = {".aup3", ".aup4", ".aup"}
FILLES = ["Romy", "Alix", "Romy&Alix"]


def nfc(t):
    return unicodedata.normalize("NFC", t)


# ---------------------------------------------------------------- structure des histoires
def scene_de(segment):
    """H2-1-Romy&Alix -> H2-1 ; H2-5a -> H2-5a ; Menu1-Romy&Alix -> Menu1-Romy&Alix."""
    if segment.startswith("H"):
        return "-".join(segment.split("-")[:2])
    return segment


def variante_de(segment, scene):
    return segment[len(scene) + 1:] if len(segment) > len(scene) else None


def scenes(filtre):
    """{hid: [(scène, [variantes], [items])]} dans l'ordre du script."""
    par_scene = {}
    for it in lire_histoires(filtre):
        par_scene.setdefault((it["hid"], scene_de(it["segment"])), []).append(it)
    res = {}
    for (hid, sc), lignes in par_scene.items():
        variantes = []
        for it in lignes:
            v = variante_de(it["segment"], sc)
            if v and v != "commun" and v not in variantes:
                variantes.append(v)
        res.setdefault(hid, []).append((sc, variantes, lignes))
    return res


def lignes_variante(lignes, sc, v):
    """La variante avec le début et la fin communs, dans l'ordre du script."""
    return [it for it in lignes if variante_de(it["segment"], sc) in (None, "commun", v)]


def plan_segments(struct):
    """[(nom, hid, items)]"""
    projets = []
    for hid, liste in struct.items():
        for sc, variantes, lignes in liste:
            if not variantes:
                projets.append((sc, hid, lignes))
            for v in variantes:
                projets.append((f"{sc}-{v}", hid, lignes_variante(lignes, sc, v)))
    return projets


def plan_completes(struct):
    """[(nom, hid, [(nom_segment, items)])] : 3 parcours par histoire, 1 « Menus complet »."""
    projets = []
    for hid, liste in struct.items():
        if hid == "MENUS":  # tous les fichiers des menus bout à bout, dans l'ordre du script
            projets.append(("Menus complet", hid, [(sc, lignes) for sc, _, lignes in liste]))
            continue
        if not hid.startswith("H"):
            continue
        # Regroupe les choix (H2-5a / H2-5b) : même scène sans la lettre finale
        etapes = []  # [[(sc, variantes, lignes), …]] ; plusieurs éléments = un choix
        def base_choix(sc):  # « H2-5 » pour H2-5a / H2-5b, None si ce n'est pas un choix
            return sc[:-1] if sc[-1].isalpha() and sc[-2].isdigit() else None
        for sc, variantes, lignes in liste:
            if etapes and base_choix(sc) and base_choix(etapes[-1][0][0]) == base_choix(sc):
                etapes[-1].append((sc, variantes, lignes))
            else:
                etapes.append([(sc, variantes, lignes)])
        for k in range(3):
            parcours = []
            for options in etapes:
                sc, variantes, lignes = options[k % len(options)]
                if not variantes:
                    parcours.append((sc, lignes))
                    continue
                v = FILLES[k] if set(variantes) <= set(FILLES) and FILLES[k] in variantes \
                    else variantes[k % len(variantes)]
                parcours.append((f"{sc}-{v}", lignes_variante(lignes, sc, v)))
            projets.append((f"{hid} complete - {k + 1}", hid, parcours))
    return projets


# ---------------------------------------------------------------- fichiers
def projets_existants(audio):
    noms = {}
    for d in audio.rglob("*"):
        if d.is_dir() and nfc(d.name) in ("2 – Projets Audacity", "3 – Montés (MP3 Lunii)"):
            for f in d.iterdir():
                if f.suffix.lower() in EXTS_PROJET:
                    noms.setdefault(nfc(f.stem).lower(), []).append(f)
    return noms


def dossier_projets(audio, hid):
    return dossier_prises(audio, hid).parent / "2 – Projets Audacity"


def prises_de(dossier, it):
    """Tous les fichiers de la réplique : H2-1-Romy_02_*.wav (prises multiples, voix superposées)."""
    motif = nfc(f"{it['segment']}_{it['n']:02d}_")
    return sorted(f for f in dossier.iterdir() if f.suffix.lower() == ".wav" and nfc(f.name).startswith(motif))


def montage_de(dossier, nom):
    for f in dossier.iterdir():
        if f.suffix.lower() == ".wav" and nfc(f.stem).lower() == nfc(nom).lower():
            return f
    return None


def duree(f):
    with wave.open(str(f), "rb") as w:
        return w.getnframes() / float(w.getframerate())


# ---------------------------------------------------------------- frise : pistes + étiquettes
def frise_prises(lignes, dossier, t=0.0):
    """Place les prises bout à bout. -> (pistes [(fichier, début, nom)], étiquettes, fin)"""
    pistes, etiquettes = [], []
    for it in lignes:
        fichiers = prises_de(dossier, it)
        texte = f"{it['n']:02d} {it['qui']} : {it['texte']}"
        if not fichiers:
            etiquettes.append((t, t + MANQUE, "À ENREGISTRER — " + texte))
            t += MANQUE + BLANC
            continue
        etiquettes.append((t, t, texte))
        for f in fichiers:
            pistes.append((f, t, f.stem.replace("_omnivoice1", "")))
        t += max(duree(f) for f in fichiers) + BLANC
    return pistes, etiquettes, t


def frise_complete(parcours, dossier_pr, dossier_proj, entre=0.0):
    """entre : blanc ajouté entre deux segments, en plus de BLANC (menus : on entend chaque fichier)."""
    pistes, etiquettes, t, sources = [], [], 0.0, []
    for i, (nom, lignes) in enumerate(parcours):
        if i:
            t += entre
        m = montage_de(dossier_proj, nom)
        if m:
            etiquettes.append((t, t, f"▶ {nom} (montage)"))
            pistes.append((m, t, nom))
            t += duree(m) + BLANC
            sources.append(f"{nom}=montage")
        else:
            etiquettes.append((t, t, f"▶ {nom} (prises brutes)"))
            p, e, t = frise_prises(lignes, dossier_pr, t)
            pistes += p
            etiquettes += e
            sources.append(f"{nom}=prises")
    return pistes, etiquettes, sources


# ---------------------------------------------------------------- pilotage d'Audacity
AIDE_AUDACITY = ("  1. Ouvre Audacity 3.7 (pas la 4 : elle n'a pas encore le module de script)\n"
                 "  2. Préférences › Modules › mod-script-pipe : « Activé », puis quitte et relance Audacity\n"
                 "  3. Ferme les fenêtres de dialogue éventuelles, puis relance ce script\n"
                 "     (une seule fenêtre de projet ouverte : le script la réutilise)")


def audacity_ouverts():
    """Versions d'Audacity en cours d'exécution sur le Mac, ex. ['Audacity 4.0.1']."""
    try:
        ps = subprocess.run(["ps", "-axo", "comm="], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return []
    res = []
    for ln in ps.splitlines():
        m = re.match(r"^(.*?\.app)/Contents/MacOS/[^/]*$", ln.strip())
        if not m or "audacity" not in ln.lower():
            continue
        app = m.group(1)
        try:
            with open(f"{app}/Contents/Info.plist", "rb") as f:
                v = plistlib.load(f).get("CFBundleShortVersionString", "?")
        except Exception:
            v = "?"
        nom = f"Audacity {v} ({os.path.basename(app)})"
        if nom not in res:
            res.append(nom)
    return res


def pas_de_reponse(pourquoi):
    ouverts = audacity_ouverts()
    if not ouverts:
        etat = "Audacity n'est pas ouvert."
    elif not any(o.startswith("Audacity 3.") for o in ouverts):
        etat = f"Ouvert : {', '.join(ouverts)}. Il faut la 3.7 (la 4 ne se pilote pas encore par script)."
    else:
        etat = f"Ouvert : {', '.join(ouverts)}, mais le module de script ne répond pas."
    sys.exit(f"{pourquoi}\n{etat}\n{AIDE_AUDACITY}")


class Audacity:
    """Pilote Audacity par mod-script-pipe, sans jamais rester bloqué (plus besoin de Ctrl-C)."""
    DELAI = 120   # s max pour une commande (import d'un long fichier, enregistrement…)

    def __init__(self):
        uid = os.getuid()
        to, fr = f"/tmp/audacity_script_pipe.to.{uid}", f"/tmp/audacity_script_pipe.from.{uid}"
        if not (os.path.exists(to) and os.path.exists(fr)):
            pas_de_reponse("Audacity ne répond pas (module de script jamais lancé).")
        # Les tuyaux restent sur le disque après la fermeture d'Audacity : on vérifie que quelqu'un écoute
        try:
            self.w = os.open(to, os.O_WRONLY | os.O_NONBLOCK)
        except OSError as e:
            if e.errno == errno.ENXIO:
                pas_de_reponse("Audacity 3.7 n'écoute pas (fermé, ou module de script pas activé).")
            raise
        os.set_blocking(self.w, True)
        self.r = os.open(fr, os.O_RDONLY | os.O_NONBLOCK)
        self.buf = b""
        try:
            self("Message: Text=Papic", delai=10)
        except (TimeoutError, OSError):
            pas_de_reponse("Audacity ne répond pas au bout de 10 s (une fenêtre de dialogue ouverte ?).")

    def _ligne(self, fin):
        while b"\n" not in self.buf:
            reste = fin - time.monotonic()
            if reste <= 0:
                raise TimeoutError("pas de réponse d'Audacity")
            pret, _, _ = select.select([self.r], [], [], min(reste, 0.5))
            if pret:
                d = os.read(self.r, 65536)
                if d:
                    self.buf += d
                else:  # personne n'écrit (pas encore, ou Audacity fermé)
                    time.sleep(0.05)
        ln, self.buf = self.buf.split(b"\n", 1)
        return ln.decode("utf-8", "replace") + "\n"

    def __call__(self, cmd, delai=None):
        os.write(self.w, (cmd + "\n").encode("utf-8"))
        fin = time.monotonic() + (delai or self.DELAI)
        rep = []
        while True:
            ln = self._ligne(fin)
            if ln == "\n" and rep:
                break
            rep.append(ln)
        texte = "".join(rep)
        if "BatchCommand finished: Failed" in texte:
            raise RuntimeError(f"{cmd}\n{texte.strip()}")
        return texte


def q(t):
    return '"' + t.replace('"', "'") + '"'


def ecrire_projet(aud, pistes, etiquettes, cible):
    # Une seule fenêtre, vidée entre deux projets (ouvrir/fermer des fenêtres fait planter Audacity)
    aud("SelectAll:")
    aud("RemoveTracks:")
    n = 0
    for f, debut, nom in pistes:
        aud(f"Import2: Filename={q(str(f))}")
        aud(f"SelectTracks: Track={n} TrackCount=1 Mode=Set")
        aud(f"SetTrack: Name={q(nom)}")
        if debut > 0:
            aud(f"SetClip: At=0 Start={debut:.3f}")
        n += 1
    for type_, nom in (("NewMonoTrack:", "Bruitages"), ("NewStereoTrack:", "Musique"), ("NewLabelTrack:", "Script")):
        aud(type_)
        aud(f"SelectTracks: Track={n} TrackCount=1 Mode=Set")
        aud(f"SetTrack: Name={nom}")
        n += 1
    piste_etiq = n - 1
    for i, (debut, fin, txt) in enumerate(etiquettes):
        aud(f"SelectTime: Start={debut:.3f} End={fin:.3f}")
        aud(f"SelectTracks: Track={piste_etiq} TrackCount=1 Mode=Set")
        aud("AddLabel:")
        aud(f"SetLabel: Label={i} Text={q(txt)} Start={debut:.3f} End={fin:.3f}")
    aud("SelectNone:")
    aud("FitInWindow:")
    if cible.exists():  # ceinture et bretelles : jamais d'écrasement
        raise RuntimeError(f"{cible.name} existe déjà, pas enregistré")
    aud(f"SaveProject2: Filename={q(str(cible))} AddToHistory=0")
    time.sleep(0.3)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--histoire", nargs="*", help="ex. H2 H3 Menus (par défaut : tout)")
    ap.add_argument("--quoi", nargs="*", choices=["segments", "completes"], default=["segments", "completes"])
    ap.add_argument("--liste", action="store_true", help="afficher ce qui sera créé, sans rien faire")
    ap.add_argument("--audio", help="dossier « Audio (enregistrements) » (par défaut : celui de voix.json)")
    a = ap.parse_args()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    audio = pathlib.Path(a.audio or cfg["drive_audio"]).expanduser()
    if not audio.is_dir():
        sys.exit(f"Dossier Drive introuvable : {audio}")
    filtre = {h.upper() for h in a.histoire} if a.histoire else None
    struct = scenes(filtre)
    deja = projets_existants(audio)

    # (nom, hid, fabrique de la frise, description)
    candidats = []
    if "segments" in a.quoi:
        for nom, hid, lignes in plan_segments(struct):
            def fab(lignes=lignes, hid=hid):
                p, e, _ = frise_prises(lignes, dossier_prises(audio, hid))
                return p, e
            dp = dossier_prises(audio, hid)
            manq = [f"{it['n']:02d} {it['qui']}" for it in lignes if not prises_de(dp, it)]
            candidats.append((nom, hid, fab, f"{len(lignes)} répliques", manq))
    if "completes" in a.quoi:
        for nom, hid, parcours in plan_completes(struct):
            dp, dj = dossier_prises(audio, hid), dossier_projets(audio, hid)
            entre = BLANC_MENUS - BLANC if hid == "MENUS" else 0.0
            def fab(parcours=parcours, dp=dp, dj=dj, entre=entre):
                p, e, _ = frise_complete(parcours, dp, dj, entre)
                return p, e
            desc = " → ".join(n + ("" if montage_de(dj, n) else "*") for n, _ in parcours)
            manq = [f"{n} {it['n']:02d} {it['qui']}" for n, lignes in parcours if not montage_de(dj, n)
                    for it in lignes if not prises_de(dp, it)]
            candidats.append((nom, hid, fab, desc, manq))

    sautes = [c for c in candidats if nfc(c[0]).lower() in deja]
    incomplets = [c for c in candidats if nfc(c[0]).lower() not in deja and c[4]]
    a_faire = [c for c in candidats if nfc(c[0]).lower() not in deja and not c[4]]
    print(f"Projets déjà là (on n'y touche pas) : {len(sautes)}")
    for nom, *_ in sautes:
        print(f"  = {nom:<22} ({', '.join(sorted({f.name for f in deja[nfc(nom).lower()]}))})")
    if incomplets:
        print(f"PAS CRÉÉS, il manque des prises : {len(incomplets)}")
        for nom, _, _, _, manq in incomplets:
            print(f"  ! {nom:<22} manque : {', '.join(manq)}")
    print(f"À créer : {len(a_faire)}   (* = segment pas encore monté : prises brutes)")
    for nom, _, _, desc, _ in a_faire:
        print(f"  + {nom:<22} {desc}")
    if a.liste or not a_faire:
        return

    aud = Audacity()
    for i, (nom, hid, fab, *_) in enumerate(a_faire, 1):
        cible = dossier_projets(audio, hid) / f"{nom}.aup3"
        try:
            pistes, etiquettes = fab()
            ecrire_projet(aud, pistes, etiquettes, cible)
            print(f"[{i}/{len(a_faire)}] {cible.parent.parent.name}/{cible.name}", flush=True)
        except Exception as e:
            print(f"[{i}/{len(a_faire)}] ERREUR {nom} : {e}", flush=True)
            if isinstance(e, OSError):
                sys.exit("Audacity ne répond plus (planté, fermé ou fenêtre de dialogue ouverte ?). "
                         "Relance-le puis relance le script : il reprend où il en était.")
    print("Terminé. Ouvre les .aup3 dans Audacity 4 : il les convertit en .aup4 sans toucher l'original.")


if __name__ == "__main__":
    sys.exit(main())

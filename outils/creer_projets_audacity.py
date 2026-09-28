#!/usr/bin/env python3
"""Crée un projet Audacity (.aup3) par segment, prêt à monter, à partir des prises OmniVoice.

Usage (depuis le dossier histoires-lunii, Audacity 3.7 ouvert, mod-script-pipe activé) :
  sh outils/projets-audacity.sh --liste            # voir ce qui sera créé, sans rien faire
  sh outils/projets-audacity.sh                    # tout créer (histoires + menus)
  sh outils/projets-audacity.sh --histoire H2 H3   # seulement certaines histoires (ou Menus)

Un projet par segment et par variante : H2-1-Romy, H2-1-Alix, H2-1-Romy&Alix (avec leur début
et fin communs), H2-2, H2-3-Mamily…  Dans chaque projet :
  - une piste par réplique, placées bout à bout dans l'ordre du script (les prises d'une même
    réplique, ex. …-Romy&Alix-Romy et …-Romy&Alix-Alix, sont superposées sur des pistes séparées) ;
  - une piste d'étiquettes « Script » avec le texte de chaque réplique (et « À ENREGISTRER » pour
    une réplique sans prise, ex. Mathéo) ;
  - deux pistes vides « Bruitages » et « Musique ».
Enregistré dans « 2 – Projets Audacity » de l'histoire (« 3 – Menus » pour les menus).

On NE TOUCHE JAMAIS à l'existant : un segment est sauté s'il a déjà un projet (.aup3/.aup4)
ou un montage (.wav/.mp3) du même nom dans n'importe quel dossier « 2 – Projets Audacity »
ou « 3 – Montés » du Drive. Relancer le script ne crée que ce qui manque.
"""
import argparse, json, os, pathlib, sys, time, unicodedata, wave

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from generer_voix import CONFIG, lire_histoires, dossier_prises  # noqa: E402

BLANC = 0.5        # silence entre deux répliques (s)
MANQUE = 2.0       # place laissée pour une réplique sans prise (s)
EXTS_EXISTANT = {".aup3", ".aup4", ".aup", ".wav", ".mp3"}


def nfc(t):
    return unicodedata.normalize("NFC", t)


# ---------------------------------------------------------------- plan des projets
def plan_projets(filtre):
    """[(nom_projet, hid, [items dans l'ordre du script])]"""
    # segment = « H2-1 », « H2-1-commun », « H2-1-Romy », « Menu1-Romy&Alix »…
    par_scene = {}  # (hid, scène) -> [items dans l'ordre du script]
    for it in lire_histoires(filtre):
        par_scene.setdefault((it["hid"], scene_de(it["segment"])), []).append(it)

    projets = []
    for (hid, sc), lignes in par_scene.items():
        variantes = []
        for it in lignes:
            v = variante_de(it["segment"], sc)
            if v and v != "commun" and v not in variantes:
                variantes.append(v)
        if not variantes:
            projets.append((sc, hid, lignes))
        for v in variantes:  # chaque variante avec le début et la fin communs, dans l'ordre du script
            sel = [it for it in lignes if variante_de(it["segment"], sc) in (None, "commun", v)]
            projets.append((f"{sc}-{v}", hid, sel))
    return projets


def scene_de(segment):
    """H2-1-Romy&Alix -> H2-1 ; H2-5a -> H2-5a ; Menu1-Romy&Alix -> Menu1-Romy&Alix ; Fin-autre-aventure -> idem."""
    if segment.startswith("H"):
        parts = segment.split("-")
        return "-".join(parts[:2])
    return segment


def variante_de(segment, scene):
    return segment[len(scene) + 1:] if len(segment) > len(scene) else None


# ---------------------------------------------------------------- ce qui existe déjà
def existants(audio):
    noms = {}
    for d in audio.rglob("*"):
        if d.is_dir() and nfc(d.name) in ("2 – Projets Audacity", "3 – Montés (MP3 Lunii)"):
            for f in d.iterdir():
                if f.suffix.lower() in EXTS_EXISTANT:
                    noms.setdefault(nfc(f.stem).lower(), []).append(f)
    return noms


def dossier_projets(audio, hid):
    return dossier_prises(audio, hid).parent / "2 – Projets Audacity"


def prises_de(dossier, it):
    """Tous les fichiers de la réplique : H2-1-Romy_02_*.wav (prises multiples, voix superposées)."""
    motif = nfc(f"{it['segment']}_{it['n']:02d}_")
    return sorted(f for f in dossier.iterdir() if f.suffix.lower() == ".wav" and nfc(f.name).startswith(motif))


def duree(f):
    with wave.open(str(f), "rb") as w:
        return w.getnframes() / float(w.getframerate())


# ---------------------------------------------------------------- pilotage d'Audacity
class Audacity:
    def __init__(self):
        uid = os.getuid()
        to, fr = f"/tmp/audacity_script_pipe.to.{uid}", f"/tmp/audacity_script_pipe.from.{uid}"
        if not (os.path.exists(to) and os.path.exists(fr)):
            sys.exit("Audacity ne répond pas.\n"
                     "  1. Ouvre Audacity 3.7 (pas la 4 : elle n'a pas encore le module de script)\n"
                     "  2. Préférences › Modules › mod-script-pipe : « Activé », puis quitte et relance Audacity\n"
                     "  3. Relance ce script")
        # (Laisse une seule fenêtre de projet ouverte dans Audacity : le script la réutilise)
        self.to, self.fr = open(to, "w"), open(fr, "r")

    def __call__(self, cmd):
        self.to.write(cmd + "\n")
        self.to.flush()
        rep = []
        while True:
            ln = self.fr.readline()
            if ln == "\n" and rep:
                break
            rep.append(ln)
        texte = "".join(rep)
        if "BatchCommand finished: Failed" in texte:
            raise RuntimeError(f"{cmd}\n{texte.strip()}")
        return texte


def q(t):
    return '"' + t.replace('"', "'") + '"'


def creer(aud, nom, lignes, dossier_prises_hist, cible):
    # Une seule fenêtre, vidée entre deux projets (ouvrir/fermer des fenêtres fait planter Audacity)
    aud("SelectAll:")
    aud("RemoveTracks:")
    t, n_piste, etiquettes = 0.0, 0, []
    for it in lignes:
        fichiers = prises_de(dossier_prises_hist, it)
        texte = f"{it['n']:02d} {it['qui']} : {it['texte']}"
        if not fichiers:
            etiquettes.append((t, t + MANQUE, "À ENREGISTRER — " + texte))
            t += MANQUE + BLANC
            continue
        etiquettes.append((t, t, texte))
        longueur = 0.0
        for f in fichiers:
            aud(f"Import2: Filename={q(str(f))}")
            aud(f"SelectTracks: Track={n_piste} TrackCount=1 Mode=Set")
            aud(f"SetTrack: Name={q(f.stem.replace('_omnivoice1', ''))}")
            if t > 0:
                aud(f"SetClip: At=0 Start={t:.3f}")
            n_piste += 1
            longueur = max(longueur, duree(f))
        t += longueur + BLANC
    # Pistes de travail
    aud("NewMonoTrack:")
    aud(f"SelectTracks: Track={n_piste} TrackCount=1 Mode=Set")
    aud("SetTrack: Name=Bruitages")
    n_piste += 1
    aud("NewStereoTrack:")
    aud(f"SelectTracks: Track={n_piste} TrackCount=1 Mode=Set")
    aud("SetTrack: Name=Musique")
    n_piste += 1
    # Étiquettes avec le texte du script
    aud("NewLabelTrack:")
    aud(f"SelectTracks: Track={n_piste} TrackCount=1 Mode=Set")
    aud("SetTrack: Name=Script")
    for i, (debut, fin, txt) in enumerate(etiquettes):
        aud(f"SelectTime: Start={debut:.3f} End={fin:.3f}")
        aud(f"SelectTracks: Track={n_piste} TrackCount=1 Mode=Set")
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
    ap.add_argument("--liste", action="store_true", help="afficher ce qui sera créé, sans rien faire")
    ap.add_argument("--audio", help="dossier « Audio (enregistrements) » (par défaut : celui de voix.json)")
    a = ap.parse_args()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    audio = pathlib.Path(a.audio or cfg["drive_audio"]).expanduser()
    if not audio.is_dir():
        sys.exit(f"Dossier Drive introuvable : {audio}")
    filtre = {h.upper() for h in a.histoire} if a.histoire else None

    deja = existants(audio)
    a_faire, sautes = [], []
    for nom, hid, lignes in plan_projets(filtre):
        if nfc(nom).lower() in deja:
            sautes.append((nom, deja[nfc(nom).lower()]))
        else:
            a_faire.append((nom, hid, lignes))

    print(f"Déjà faits (on n'y touche pas) : {len(sautes)}")
    for nom, fs in sautes:
        print(f"  = {nom:<22} ({', '.join(sorted({f.name for f in fs}))})")
    print(f"À créer : {len(a_faire)}")
    for nom, hid, lignes in a_faire:
        dp = dossier_prises(audio, hid)
        manquantes = [it for it in lignes if not prises_de(dp, it)]
        note = f"  — {len(manquantes)} réplique(s) sans prise : " + ", ".join(
            f"{it['n']:02d} {it['qui']}" for it in manquantes) if manquantes else ""
        print(f"  + {nom:<22} {len(lignes)} répliques{note}")
    if a.liste or not a_faire:
        return

    aud = Audacity()
    for i, (nom, hid, lignes) in enumerate(a_faire, 1):
        cible = dossier_projets(audio, hid) / f"{nom}.aup3"
        try:
            creer(aud, nom, lignes, dossier_prises(audio, hid), cible)
            print(f"[{i}/{len(a_faire)}] {cible.parent.parent.name}/{cible.name}", flush=True)
        except Exception as e:
            print(f"[{i}/{len(a_faire)}] ERREUR {nom} : {e}", flush=True)
            if isinstance(e, (BrokenPipeError, OSError)):
                sys.exit("Audacity ne répond plus (planté ?). Relance-le puis relance le script : il reprend où il en était.")
    print("Terminé. Ouvre les .aup3 dans Audacity 4 : il les convertit en .aup4 sans toucher l'original.")


if __name__ == "__main__":
    sys.exit(main())

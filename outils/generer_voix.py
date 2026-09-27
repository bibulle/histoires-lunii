#!/usr/bin/env python3
"""Génère toutes les répliques des histoires avec OmniVoice, en batch (idéal la nuit).

Usage (depuis le dossier histoires-lunii) :
  sh outils/nuit.sh                          # tout générer, Mac éveillé, journal dans audio-genere/
  ~/omnivoice-env/bin/python outils/generer_voix.py --liste          # voir ce qui sera généré, sans rien générer
  ~/omnivoice-env/bin/python outils/generer_voix.py --histoire H1    # une seule histoire
  ~/omnivoice-env/bin/python outils/generer_voix.py --essais         # 3 essais de voix par personnage
  ~/omnivoice-env/bin/python outils/generer_voix.py --refaire        # régénérer même ce qui existe déjà

Rangement : audio-genere/H1-paillette-va-a-l-ecole/H1-1-Romy/H1-1-Romy_03_Paillette.wav
- une histoire par dossier, une scène (et sa version) par sous-dossier, fichiers numérotés dans l'ordre
- les voix se règlent dans outils/voix.json (description « instruct » ou clip de référence à cloner)
- un fichier déjà généré n'est pas refait : on peut relancer après une coupure
"""
import argparse, json, pathlib, re, sys, time, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "outils" / "voix.json"

OV_TAGS = ["laughter", "sigh", "surprise-oh", "surprise-ah", "surprise-wa", "surprise-yo",
           "dissatisfaction-hnn", "confirmation-en", "question-en", "question-ah", "question-oh",
           "question-ei", "question-yi"]
ROLE_RE = re.compile(r"^([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ' ]{3,}?)(\s*\([^)]*\))?\s*:\s(.*)$")
SCENE_RE = re.compile(r"^###\s+(H\d+-\d+[a-z]?)\b")
VERSION_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
BLOC_RE = re.compile(r"^\*\((.+?)\)\*\s*$")
NARR_META_RE = re.compile(r"^-\s*Narrateur\s*:\s*(\w+)", re.I)

CLONES = {}
VERSIONS = {"version romy": "Romy", "version alix": "Alix", "version les deux": "Romy&Alix"}


def nom_propre(role):
    """ROMY ET ALIX -> Romy&Alix, TATA BÊTISE -> Tata-Bêtise."""
    if role == "ROMY ET ALIX":
        return "Romy&Alix"
    return "-".join(w.capitalize() for w in role.lower().split())


def libelle_bloc(txt):
    t = unicodedata.normalize("NFD", txt.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    for mot, lib in (("debut", "debut-commun"), ("suite", "suite-commune"), ("fin", "fin-commune")):
        if t.startswith(mot):
            return lib
    return "commun"


def nettoyer(texte):
    """Garde les balises OmniVoice, retire guillemets et bruitages français."""
    t = texte.strip().strip("«»").strip()
    t = re.sub(r"\[([^\]]+)\]", lambda m: m.group(0) if m.group(1) in OV_TAGS else " ", t)
    t = t.replace("«", "").replace("»", "")
    return re.sub(r"\s+", " ", t).strip()


def lire_histoires(filtre=None):
    """Retourne une liste de répliques : dict(histoire, dossier, fichier, role, texte, voix)."""
    items = []
    for path in sorted((ROOT / "histoires").glob("H*.md")):
        hid = path.stem.split("-")[0]
        if filtre and hid.upper() not in filtre:
            continue
        narrateur, scene, version, bloc, compteur = "Papic", None, None, None, {}
        for ln in path.read_text(encoding="utf-8").splitlines():
            s = ln.strip()
            if m := NARR_META_RE.match(s):
                narrateur = m.group(1).capitalize()
            elif m := SCENE_RE.match(s):
                scene, version, bloc = m.group(1), None, None
            elif scene and (m := VERSION_RE.match(s)):
                v = m.group(1).strip()
                version, bloc = VERSIONS.get(v.lower(), v.replace(" ", "-")), None
            elif scene and (m := BLOC_RE.match(s)):
                bloc, version = libelle_bloc(m.group(1)), None
            elif scene and (m := ROLE_RE.match(s)):
                role, texte = m.group(1).strip(), nettoyer(m.group(3))
                if not texte:
                    continue
                dossier = scene + (f"-{version}" if version else f"-{bloc}" if bloc else "")
                compteur[dossier] = compteur.get(dossier, 0) + 1
                voix = f"NARRATEUR-{narrateur.upper()}" if role == "NARRATEUR" else role
                items.append(dict(histoire=path.stem, dossier=dossier, role=role, texte=texte, voix=voix,
                                  fichier=f"{dossier}_{compteur[dossier]:02d}_{nom_propre(role)}.wav"))
    return items


def charger_modele():
    import torch
    from omnivoice import OmniVoice
    if torch.backends.mps.is_available():
        device, dtype = "mps", torch.float32
    elif torch.cuda.is_available():
        device, dtype = "cuda:0", torch.float16
    else:
        device, dtype = "cpu", torch.float32
    print(f"Chargement du modèle sur {device}…", flush=True)
    model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=device, dtype=dtype)
    return model, torch


def generer(model, torch, texte, reglage, seed, sortie):
    import soundfile as sf
    torch.manual_seed(seed)
    kw = dict(text=texte, language="French")
    ref = reglage.get("reference")
    if ref and (ROOT / ref).exists():
        if ref not in CLONES:  # clip analysé une seule fois par voix
            CLONES[ref] = model.create_voice_clone_prompt(
                ref_audio=str(ROOT / ref), ref_text=reglage.get("reference_texte") or None)
        kw["voice_clone_prompt"] = CLONES[ref]
    elif reglage.get("instruct"):
        kw["instruct"] = reglage["instruct"]
    for cle, nom in (("vitesse", "speed"), ("etapes", "num_step"), ("guidance", "guidance_scale")):
        if cle in reglage:
            kw[nom] = reglage[cle]
    audio = model.generate(**kw)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(sortie), audio[0], getattr(model, "sampling_rate", 24000))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--histoire", nargs="*", help="ex. H1 H3 (par défaut : toutes)")
    ap.add_argument("--role", nargs="*", help="ex. PAILLETTE GRUMO (par défaut : tous)")
    ap.add_argument("--prises", type=int, default=None, help="nombre de prises par réplique (défaut : voix.json)")
    ap.add_argument("--sortie", default=None, help="dossier de sortie (défaut : audio-genere)")
    ap.add_argument("--liste", action="store_true", help="afficher sans générer")
    ap.add_argument("--essais", action="store_true", help="3 essais de voix par personnage, pour choisir")
    ap.add_argument("--refaire", action="store_true", help="régénérer les fichiers existants")
    a = ap.parse_args()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    voix = cfg["voix"]
    sortie = pathlib.Path(a.sortie or cfg.get("sortie", "audio-genere")).expanduser()
    if not sortie.is_absolute():
        sortie = ROOT / sortie
    prises = a.prises or cfg.get("prises", 1)
    filtre = {h.upper() for h in a.histoire} if a.histoire else None
    roles = {r.upper() for r in a.role} if a.role else None

    if a.essais:
        taches = []
        for nom, r in voix.items():
            if r.get("ignorer") or (roles and nom not in roles):
                continue
            for i in range(1, 4):
                taches.append((cfg["phrase_essai"].get(nom, cfg["phrase_essai"]["defaut"]), r, 1000 + i,
                               sortie / "_essais-voix" / f"{nom_propre(nom)}_essai{i}_seed{1000 + i}.wav", nom))
    else:
        taches = []
        for it in lire_histoires(filtre):
            r = voix.get(it["voix"]) or voix.get(it["role"])
            if r is None:
                print(f"  ! voix inconnue {it['voix']} ({it['fichier']}) : ajoute-la dans voix.json")
                continue
            if r.get("ignorer") or (roles and it["role"] not in roles):
                continue
            for p in range(1, prises + 1):
                f = it["fichier"] if prises == 1 else it["fichier"].replace(".wav", f"_prise{p}.wav")
                taches.append((it["texte"], r, r.get("seed", 1234) + p - 1,
                               sortie / it["histoire"] / it["dossier"] / f, it["voix"]))

    a_faire = [t for t in taches if a.refaire or not t[3].exists()]
    print(f"{len(taches)} fichiers prévus, {len(a_faire)} à générer → {sortie}")
    if a.liste:
        for texte, _, _, f, v in a_faire:
            print(f"{f.relative_to(sortie)}  [{v}]  {texte}")
        return
    if not a_faire:
        return

    model, torch = charger_modele()
    debut, erreurs = time.time(), 0
    for n, (texte, r, seed, f, v) in enumerate(a_faire, 1):
        t0 = time.time()
        try:
            generer(model, torch, texte, r, seed, f)
            ecoule = time.time() - debut
            reste = ecoule / n * (len(a_faire) - n)
            print(f"[{n}/{len(a_faire)}] {f.name}  ({time.time() - t0:.0f} s, reste ≈ {reste / 60:.0f} min)", flush=True)
        except Exception as e:  # une réplique ratée ne doit pas arrêter la nuit
            erreurs += 1
            print(f"[{n}/{len(a_faire)}] ERREUR {f.name} : {e}", flush=True)
    print(f"Terminé en {(time.time() - debut) / 60:.0f} min, {erreurs} erreur(s).")


if __name__ == "__main__":
    sys.exit(main())

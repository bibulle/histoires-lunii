#!/usr/bin/env python3
"""Génère les répliques des histoires avec OmniVoice, en clonant les voix de référence du Drive.

Usage (depuis le dossier histoires-lunii) :
  sh outils/nuit.sh                                   # tout générer (Mac éveillé, journal)
  ~/omnivoice-env/bin/python outils/generer_voix.py --liste        # voir ce qui sera fait, sans générer
  ~/omnivoice-env/bin/python outils/generer_voix.py --histoire H1  # une seule histoire
  ~/omnivoice-env/bin/python outils/generer_voix.py --essais       # une phrase test par voix de référence
  ~/omnivoice-env/bin/python outils/generer_voix.py --refaire      # régénérer même ce qui existe

Voix de référence : Drive « Audio (enregistrements)/4 - Sources », deux fichiers par voix,
  Personnage-Interprete.wav + Personnage-Interprete.txt (le texte exact prononcé).
  ex. Narrateur-Papic.wav/.txt (narrateur des histoires contées par Papic), Romy.wav/.txt
  Les anciennes versions (…-v1.wav) sont ignorées.

Sortie (nomenclature du Drive) : « Audio (enregistrements)/H1 – …/1 – Prises/ »
  H1-1-Romy_04_Paillette_omnivoice1.wav  = segment, n° de réplique dans le segment, qui parle, prise
  Les parties « début/fin commune » sont dans H1-6-commun_…
Un fichier déjà généré n'est pas refait : on peut relancer après une coupure,
ou après avoir ajouté une nouvelle voix dans Sources (seules les répliques manquantes sont faites).
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

VERSIONS = {"version romy": "Romy", "version alix": "Alix", "version les deux": "Romy&Alix"}
# Nom « qui parle » de la nomenclature du Drive
NOMS = {"ROMY ET ALIX": "Romy&Alix", "PÈRE NOËL": "PereNoel", "LE CRABE": "Crabe",
        "LE POISSON ROUGE": "PoissonRouge", "MAMAN DAUPHIN": "MamanDauphin"}
CLONES = {}


def sans_accents(t):
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def nom_propre(role):
    """TATA BÊTISE -> TataBetise, NARRATEUR-PAPIC -> Narrateur-Papic, MATHÉO -> Matheo."""
    if role in NOMS:
        return NOMS[role]
    return "-".join("".join(w.capitalize() for w in part.split())
                    for part in sans_accents(role).lower().split("-"))


def nettoyer(texte):
    """Garde les balises OmniVoice, retire guillemets et bruitages français."""
    t = re.sub(r"\[([^\]]+)\]", lambda m: m.group(0) if m.group(1) in OV_TAGS else " ", texte)
    t = t.replace("«", "").replace("»", "")
    return re.sub(r"\s+", " ", t).strip()


def lire_histoires(filtre=None):
    items = []
    for path in sorted((ROOT / "histoires").glob("H*.md")):
        hid = path.stem.split("-")[0].upper()
        if filtre and hid not in filtre:
            continue
        narrateur, scene, variante, compteur = "Papic", None, None, {}
        for ln in path.read_text(encoding="utf-8").splitlines():
            s = ln.strip()
            if m := NARR_META_RE.match(s):
                narrateur = m.group(1).capitalize()
            elif m := SCENE_RE.match(s):
                scene, variante = m.group(1), None
            elif scene and (m := VERSION_RE.match(s)):
                v = m.group(1).strip()
                variante = VERSIONS.get(v.lower()) or nom_propre(v.upper())
            elif scene and BLOC_RE.match(s):
                variante = "commun"
            elif scene and (m := ROLE_RE.match(s)):
                role, texte = m.group(1).strip(), nettoyer(m.group(3))
                if not texte:
                    continue
                segment = scene + (f"-{variante}" if variante else "")
                compteur[segment] = compteur.get(segment, 0) + 1
                voix = f"NARRATEUR-{narrateur.upper()}" if role == "NARRATEUR" else role
                items.append(dict(hid=hid, segment=segment, n=compteur[segment], role=role,
                                  qui=nom_propre(role), texte=texte, voix=voix))
    return items


def lire_texte(p):
    t = p.read_text(encoding="utf-8", errors="replace")
    if t.lstrip().startswith("{\\rtf"):  # texte enregistré en RTF par TextEdit
        t = re.sub(r"\\'[0-9a-f]{2}|\\[a-z]+-?\d* ?|[{}]", "", t)
    return " ".join(t.split())


def trouver_references(sources):
    """{'Narrateur-Papic': (wav, texte), 'Romy': (…)} — clé = nom du fichier sans extension."""
    refs = {}
    if not sources.is_dir():
        return refs
    for wav in sorted(sources.iterdir()):
        if wav.suffix.lower() not in (".wav", ".m4a", ".mp3") or re.search(r"-v\d+$", wav.stem):
            continue
        txt = wav.with_suffix(".txt")
        if txt.exists():
            refs[unicodedata.normalize("NFC", wav.stem)] = (wav, lire_texte(txt))
        else:
            print(f"  ! {wav.name} sans {txt.name} : échantillon ignoré (il faut le texte prononcé)")
    return refs


def reference_pour(voix, cfg, refs):
    """Cherche l'échantillon de la voix : nom exact, Personnage-Interprete, puis voix de secours."""
    for cle in [voix] + cfg.get("secours", {}).get(voix, []):
        nom = nom_propre(cle)
        if nom in refs:
            return nom, refs[nom]
        for stem, r in refs.items():  # Personnage-Interprete (ex. Grumo-Papic)
            if stem.startswith(nom + "-"):
                return stem, r
    return None, None


def dossier_prises(audio, hid):
    for d in sorted(audio.glob(f"{hid} *")):
        if d.is_dir():
            return d / "1 – Prises"
    return audio / "0 – À trier (dépôt)" / hid


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
    return OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=device, dtype=dtype), torch


def generer(model, torch, texte, ref, reglage, seed, sortie):
    import soundfile as sf
    torch.manual_seed(seed)
    kw = dict(text=texte, language="French")
    if ref:
        wav, ref_texte = ref
        if wav not in CLONES:  # échantillon analysé une seule fois
            CLONES[wav] = model.create_voice_clone_prompt(ref_audio=str(wav), ref_text=ref_texte)
        kw["voice_clone_prompt"] = CLONES[wav]
    elif reglage.get("instruct"):
        kw["instruct"] = reglage["instruct"]
    for cle, nom in (("vitesse", "speed"), ("etapes", "num_step"), ("guidance", "guidance_scale")):
        if cle in reglage:
            kw[nom] = reglage[cle]
    audio = model.generate(**kw)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    tmp = sortie.with_name(sortie.stem + ".part.wav")
    sf.write(str(tmp), audio[0], model.sampling_rate or 24000)
    tmp.rename(sortie)  # pas de fichier à moitié écrit dans le Drive


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--histoire", nargs="*", help="ex. H1 H3 (par défaut : toutes)")
    ap.add_argument("--role", nargs="*", help="ex. PAILLETTE GRUMO (par défaut : tous)")
    ap.add_argument("--prises", type=int, default=None, help="nombre de prises par réplique")
    ap.add_argument("--liste", action="store_true", help="afficher sans générer")
    ap.add_argument("--essais", action="store_true", help="une phrase test par voix de référence")
    ap.add_argument("--refaire", action="store_true", help="régénérer les fichiers existants")
    ap.add_argument("--sans-reference", choices=["ignorer", "instruct"], default=None,
                    help="voix sans échantillon : ne pas générer (défaut) ou voix décrite (maquette)")
    a = ap.parse_args()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    audio = pathlib.Path(cfg["drive_audio"]).expanduser()
    if not audio.is_dir():
        sys.exit(f"Dossier Drive introuvable : {audio}\n(vérifie Google Drive, ou 'drive_audio' dans outils/voix.json)")
    refs = trouver_references(audio / cfg.get("sources", "4 - Sources"))
    print("Voix de référence trouvées : " + (", ".join(refs) or "aucune"))
    sans_ref = a.sans_reference or cfg.get("sans_reference", "ignorer")
    prises = a.prises or cfg.get("prises", 1)
    filtre = {h.upper() for h in a.histoire} if a.histoire else None
    roles = {r.upper() for r in a.role} if a.role else None

    taches, manquantes = [], {}
    if a.essais:
        for stem, ref in refs.items():
            f = audio / "0 – À trier (dépôt)" / "essais-omnivoice" / f"Essai_{stem}_omnivoice1.wav"
            taches.append((cfg["phrase_essai"], ref, {}, 1234, f, stem))
    else:
        for it in lire_histoires(filtre):
            if roles and it["role"] not in roles:
                continue
            reglage = cfg["voix"].get(it["voix"], {})
            if reglage.get("ignorer"):
                continue
            nom_ref, ref = reference_pour(it["voix"], cfg, refs)
            if not ref:
                manquantes[nom_propre(it["voix"])] = manquantes.get(nom_propre(it["voix"]), 0) + 1
                if sans_ref == "ignorer" or not reglage.get("instruct"):
                    continue
            for p in range(1, prises + 1):
                nom = f"{it['segment']}_{it['n']:02d}_{it['qui']}_omnivoice{p}.wav"
                taches.append((it["texte"], ref, reglage, reglage.get("seed", 1234) + p - 1,
                               dossier_prises(audio, it["hid"]) / nom, nom_ref or f"{it['voix']} (décrite)"))

    if manquantes:
        print(f"Sans échantillon dans Sources ({'maquette voix décrite' if sans_ref == 'instruct' else 'non générées'}) : "
              + ", ".join(f"{k} ({v})" for k, v in sorted(manquantes.items())))
    a_faire = [t for t in taches if a.refaire or not t[4].exists()]
    print(f"{len(taches)} fichiers prévus, {len(a_faire)} à générer.")
    if a.liste:
        for texte, _, _, _, f, v in a_faire:
            print(f"{f.parent.parent.name}/{f.name}  [{v}]  {texte}")
        return
    if not a_faire:
        return

    model, torch = charger_modele()
    debut, erreurs = time.time(), 0
    for n, (texte, ref, reglage, seed, f, v) in enumerate(a_faire, 1):
        t0 = time.time()
        try:
            generer(model, torch, texte, ref, reglage, seed, f)
            reste = (time.time() - debut) / n * (len(a_faire) - n)
            print(f"[{n}/{len(a_faire)}] {f.name}  ({time.time() - t0:.0f} s, reste ≈ {reste / 60:.0f} min)", flush=True)
        except Exception as e:  # une réplique ratée ne doit pas arrêter la nuit
            erreurs += 1
            print(f"[{n}/{len(a_faire)}] ERREUR {f.name} : {e}", flush=True)
    print(f"Terminé en {(time.time() - debut) / 60:.0f} min, {erreurs} erreur(s).")


if __name__ == "__main__":
    sys.exit(main())

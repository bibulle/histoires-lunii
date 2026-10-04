#!/usr/bin/env python3
"""Génère les répliques des histoires avec OmniVoice, en clonant les voix de référence du Drive.

Usage (depuis le dossier histoires-lunii) :
  sh outils/nuit.sh                                   # tout générer (Mac éveillé, journal)
  ~/omnivoice-env/bin/python outils/generer_voix.py --liste        # voir ce qui sera fait, sans générer
  ~/omnivoice-env/bin/python outils/generer_voix.py --histoire H1  # une seule histoire
  ~/omnivoice-env/bin/python outils/generer_voix.py --histoire Menus   # les questions des menus
  sh outils/essais.sh --role ALIX --etapes 64 --guidance 1.5   # essai avec d autres réglages (fichier séparé)
  ~/omnivoice-env/bin/python outils/generer_voix.py --refaire      # régénérer même ce qui existe

Voix de référence : Drive « Audio (enregistrements)/4 - Sources », deux fichiers par voix,
  Personnage-Interprete.wav + Personnage-Interprete.txt (le texte exact prononcé).
  ex. Narrateur-Papic.wav/.txt (narrateur des histoires contées par Papic), Romy.wav/.txt
  Les anciennes versions (…-v1.wav) sont ignorées.

Sortie (nomenclature du Drive) : « Audio (enregistrements)/H1 – …/1 – Prises/ »
  H1-1-Romy_04_Paillette_omnivoice1.wav  = segment, n° de réplique dans le segment, qui parle, prise
  Les parties « début/fin commune » sont dans H1-6-commun_…
  Réplique à plusieurs voix (« ensemble » dans voix.json : ROMY ET ALIX, TOUS) : un fichier par voix,
  H1-6_03_Romy&Alix-Romy_omnivoice1.wav + H1-6_03_Romy&Alix-Alix_omnivoice1.wav, à superposer dans Audacity.
  TOUS = Papic, Mamily, Romy et Alix : H5-2_04_Tous-Papic_…, …_Tous-Mamily_…, …_Tous-Romy_…, …_Tous-Alix_…
Un fichier déjà généré n'est pas refait : on peut relancer après une coupure,
ou après avoir ajouté une nouvelle voix dans Sources (seules les répliques manquantes sont faites).
"""
import argparse, json, logging, os, pathlib, re, sys, time, unicodedata, warnings

# Pas de messages parasites des bibliothèques (dépréciations, ffmpeg, transformers…)
warnings.filterwarnings("ignore")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
logging.disable(logging.WARNING)

# Valeurs par défaut d'OmniVoice (affichées dans le résumé, et absentes du nom des essais)
DEFAUTS = {"etapes": 32, "guidance": 2.0, "vitesse": 1.0, "temperature": 0.0, "seed": 1234}

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "outils" / "voix.json"

OV_TAGS = ["laughter", "sigh", "surprise-oh", "surprise-ah", "surprise-wa", "surprise-yo",
           "dissatisfaction-hnn", "confirmation-en", "question-en", "question-ah", "question-oh",
           "question-ei", "question-yi"]
ROLE_RE = re.compile(r"^([A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ' ]{3,}?)(\s*\([^)]*\))?\s*:\s(.*)$")
SCENE_RE = re.compile(r"^###\s+(H\d+-\d+[a-z]?|Menu\d-[^\s_]+|Fin-[^\s_]+)(?=\s|$)")
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


def fichiers_scripts():
    """Menus.md d'abord, puis H1…H9."""
    return sorted((ROOT / "histoires").glob("*.md"), key=lambda p: (not p.stem.lower().startswith("menu"), p.name))


def lire_histoires(filtre=None):
    items = []
    for path in fichiers_scripts():
        hid = path.stem.split("-")[0].upper()  # H1…H9, ou MENUS
        if filtre and hid not in filtre:
            continue
        narrateur, scene, variante, compteur = "Papic", None, None, {}
        for ln in path.read_text(encoding="utf-8").splitlines():
            s = ln.strip()
            m_narr, m_scene = NARR_META_RE.match(s), SCENE_RE.match(s)
            m_version, m_role = VERSION_RE.match(s), ROLE_RE.match(s)
            if m_narr:
                narrateur = m_narr.group(1).capitalize()
            elif m_scene:
                scene, variante = m_scene.group(1), None
            elif scene and m_version:
                v = m_version.group(1).strip()
                variante = VERSIONS.get(v.lower()) or nom_propre(v.upper())
            elif scene and BLOC_RE.match(s):
                variante = "commun"
            elif scene and m_role:
                role, texte = m_role.group(1).strip(), nettoyer(m_role.group(3))
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


def cmp_nom(t):
    """Forme de comparaison des noms : minuscules, sans accents."""
    return sans_accents(t).lower()


def reference_pour(voix, cfg, refs):
    """Cherche l'échantillon de la voix : nom exact, Personnage-Interprete, puis voix de secours."""
    for cle in [voix] + cfg.get("secours", {}).get(voix, []):
        nom = cmp_nom(nom_propre(cle))
        for stem, r in refs.items():  # nom exact (sans tenir compte des majuscules/accents)
            if cmp_nom(stem) == nom:
                return stem, r
        for stem, r in refs.items():  # Personnage-Interprete (ex. Grumo-Papic)
            if cmp_nom(stem).startswith(nom + "-"):
                return stem, r
    return None, None


def dossier_prises(audio, hid):
    motif = "* Menus" if hid == "MENUS" else f"{hid} *"  # « 3 – Menus » dans le Drive
    for d in sorted(audio.glob(motif)):
        if d.is_dir():
            return d / "1 – Prises"
    return audio / "0 – À trier (dépôt)" / hid


def modele_en_cache():
    """Vrai si le modèle (et son tokenizer audio) sont déjà téléchargés dans le cache Hugging Face."""
    hub = pathlib.Path(os.environ.get("HF_HUB_CACHE") or
                       pathlib.Path(os.environ.get("HF_HOME", "~/.cache/huggingface")).expanduser() / "hub")
    def snaps(repo):
        d = hub / f"models--{repo.replace('/', '--')}" / "snapshots"
        return [s for s in d.iterdir() if s.is_dir()] if d.is_dir() else []
    ov = snaps("k2-fsa/OmniVoice")
    if not ov:
        return False
    return any((s / "audio_tokenizer").is_dir() for s in ov) or bool(snaps("eustlb/higgs-audio-v2-tokenizer"))


def charger_modele():
    if modele_en_cache():
        # Déjà téléchargé : pas de connexion à Hugging Face (ni vérification, ni barres de progression)
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    else:
        print("Premier lancement : téléchargement du modèle (quelques Go, une seule fois)…", flush=True)
    t0 = time.time()
    import torch
    from omnivoice import OmniVoice
    if torch.backends.mps.is_available():
        device, dtype = "mps", torch.float32
    elif torch.cuda.is_available():
        device, dtype = "cuda:0", torch.float16
    else:
        device, dtype = "cpu", torch.float32
    print(f"Chargement du modèle en mémoire ({device})…", flush=True)
    model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=device, dtype=dtype)
    print(f"Modèle prêt en {time.time() - t0:.0f} s.\n", flush=True)
    return model, torch


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
    for cle, nom in (("vitesse", "speed"), ("etapes", "num_step"), ("guidance", "guidance_scale"),
                     ("temperature", "class_temperature")):
        if cle in reglage:
            kw[nom] = reglage[cle]
    audio = model.generate(**kw)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    tmp = sortie.with_name(sortie.stem + ".part.wav")
    sf.write(str(tmp), audio[0], model.sampling_rate or 24000)
    tmp.rename(sortie)  # pas de fichier à moitié écrit dans le Drive


def regler(reglage, a):
    """Réglages de voix.json, remplacés par ceux donnés en ligne de commande."""
    r = dict(reglage)
    for cle in ("etapes", "guidance", "vitesse", "temperature", "seed"):
        if getattr(a, cle) is not None:
            r[cle] = getattr(a, cle)
    return r


def resume(taches):
    """Tableau des réglages réellement utilisés, par voix (seulement celles qui vont être générées)."""
    vus = {}
    for _, ref, reglage, seed, _, v in taches:
        cle = (v, tuple(sorted((k, reglage.get(k)) for k in DEFAUTS if k != "seed")), ref and ref[0].name)
        vus.setdefault(cle, [0, set()])
        vus[cle][0] += 1
        vus[cle][1].add(seed)
    if not vus:
        return
    print("\nRéglages utilisés (* = différent du défaut) :")
    print(f"  {'voix':<22}{'référence':<24}{'étapes':>7}{'guidance':>10}{'vitesse':>9}{'tempér.':>9}  seed      fichiers")
    for (v, regl, ref_nom), (n, seeds) in vus.items():
        regl = dict(regl)
        def val(k):
            x = regl.get(k)
            return f"{(DEFAUTS[k] if x is None else x):g}" + ("*" if x is not None and float(x) != DEFAUTS[k] else " ")
        s = ",".join(str(x) for x in sorted(seeds)[:3]) + ("…" if len(seeds) > 3 else "")
        s += "*" if seeds != {DEFAUTS["seed"]} else ""
        print(f"  {v:<22}{(ref_nom or 'voix décrite'):<24}{val('etapes'):>7}{val('guidance'):>10}"
              f"{val('vitesse'):>9}{val('temperature'):>9}  {s:<9} {n:>4}")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--histoire", nargs="*", help="ex. H1 H3 Menus (par défaut : toutes, menus compris)")
    ap.add_argument("--role", nargs="*", help="ex. PAILLETTE GRUMO (par défaut : tous)")
    ap.add_argument("--prises", type=int, default=None, help="nombre de prises par réplique")
    ap.add_argument("--liste", action="store_true", help="afficher sans générer")
    ap.add_argument("--essais", action="store_true", help="une phrase test par voix de référence")
    ap.add_argument("--refaire", action="store_true", help="régénérer les fichiers existants")
    ap.add_argument("--sans-reference", choices=["ignorer", "instruct"], default=None,
                    help="voix sans échantillon : ne pas générer (défaut) ou voix décrite (maquette)")
    ap.add_argument("--etapes", type=int, help="itérations (défaut 32 ; 64 = plus soigné, 2x plus lent)")
    ap.add_argument("--guidance", type=float, help="fidélité à la voix/au texte (défaut 2.0 ; 1.5 = plus doux, 3 = plus marqué)")
    ap.add_argument("--vitesse", type=float, help="débit (1.0 ; 0.9 = plus lent)")
    ap.add_argument("--temperature", type=float, help="variété (défaut 0 ; 0.3-0.7 = plus vivant, moins stable)")
    ap.add_argument("--seed", type=int, help="tirage aléatoire (défaut 1234) : change-le pour une autre interprétation")
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

    taches, manquantes, anciennes = [], {}, []
    if a.essais:
        voix_essai = []  # (nom affiché, échantillon ou None, clé dans voix.json)
        for stem, ref in refs.items():
            cle = next((k for k in cfg["voix"] if cmp_nom(nom_propre(k)) == cmp_nom(stem)), None) or \
                next((k for k in cfg["voix"] if cmp_nom(stem).startswith(cmp_nom(nom_propre(k)) + "-")), None)
            voix_essai.append((stem, ref, cle))
        if sans_ref == "instruct":  # voix sans échantillon (ni voix de secours) : voix décrite par « instruct »
            for cle, r in cfg["voix"].items():
                if not r.get("ignorer") and r.get("instruct") and not reference_pour(cle, cfg, refs)[1]:
                    voix_essai.append((nom_propre(cle) + "-decrite", None, cle))
        for stem, ref, cle in voix_essai:
            if roles and not ({stem.upper(), (cle or "").upper()} & roles):
                continue
            base = cfg["voix"].get(cle, {})
            reglage = regler(base, a)
            # Dans le nom : seulement ce qui diffère de voix.json (donc ce qui a été forcé en ligne de commande)
            suffixe = "".join(f"_{k}{reglage[k]:g}" for k in DEFAUTS
                              if getattr(a, k) is not None and float(reglage[k]) != float(base.get(k, DEFAUTS[k])))
            f = audio / "0 – À trier (dépôt)" / "essais-omnivoice" / f"Essai_{stem}{suffixe}_omnivoice1.wav"
            taches.append((cfg["phrase_essai"], ref, reglage, reglage.get("seed", 1234), f, stem))
    else:
        items = []
        for it in lire_histoires(filtre):
            if roles and it["role"] not in roles:
                continue
            # Réplique à plusieurs voix (ROMY ET ALIX, TOUS) : une prise par voix, à superposer au montage
            for v in cfg.get("ensemble", {}).get(it["voix"], []):
                items.append(dict(it, voix=v, qui=f"{it['qui']}-{nom_propre(v)}"))
            if it["voix"] not in cfg.get("ensemble", {}):
                items.append(it)
            else:  # prise à une seule voix, d'avant le passage de ce rôle en « ensemble »
                d = dossier_prises(audio, it["hid"])
                if d.is_dir():
                    anciennes += sorted(d.glob(f"{it['segment']}_{it['n']:02d}_{it['qui']}_omnivoice*.wav"))
        for it in items:
            reglage = regler(cfg["voix"].get(it["voix"], {}), a)
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
                               dossier_prises(audio, it["hid"]) / nom, nom_ref or nom_propre(it['voix']) + "-decrite"))

    if manquantes:
        print(f"Sans échantillon dans Sources ({'maquette voix décrite' if sans_ref == 'instruct' else 'non générées'}) : "
              + ", ".join(f"{k} ({v})" for k, v in sorted(manquantes.items())))
    if anciennes:
        print("Anciennes prises à une seule voix, remplacées par une prise par voix (à retirer du Drive, "
              "sinon elles s'ajoutent aux autres dans les prochains projets Audacity) :")
        for f in anciennes:
            print(f"  {f.parent.parent.name}/{f.name}")
    a_faire = [t for t in taches if a.refaire or not t[4].exists()]
    resume(a_faire)
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

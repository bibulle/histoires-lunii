#!/usr/bin/env python3
"""
Monte le volume de tous les sons d'un pack STUdio (.zip), sans toucher au reste.

Usage (dans Terminal) :
    python3 outils/normaliser_pack.py ~/Downloads/MonPack.zip
    python3 outils/normaliser_pack.py ~/Downloads/MonPack.zip --cible -14

Résultat : MonPack-fort.zip à côté de l'original (l'original n'est pas modifié).

Principe (mode par défaut, "gain global") :
  1. mesure le volume perçu (LUFS) de chaque son du pack ;
  2. calcule UN SEUL gain pour que le son "médian" arrive à la cible (-16 LUFS) ;
  3. applique ce même gain à tous les sons + un limiteur à -1 dB pour éviter la saturation.
  => les écarts voulus sont gardés (H9, l'histoire du dodo, reste plus douce).

Option --par-fichier : chaque son est mis exactement à la cible (tout au même niveau,
mais H9 deviendra aussi forte que les autres).

Prérequis : ffmpeg  (brew install ffmpeg)
"""
import argparse, json, os, re, shutil, statistics, subprocess, sys, tempfile, zipfile

AUDIO = (".mp3", ".ogg", ".wav")
LIMITE = 0.891  # -1 dBFS
ERREUR = ""


def trouver_ffmpeg():
    # Préfère le ffmpeg de Homebrew (récent) à une vieille version qui traînerait dans le PATH
    ici = os.path.dirname(os.path.abspath(__file__))
    candidats = (os.environ.get("FFMPEG", ""),
                 os.path.join(ici, "ffmpeg"),                  # outils/ffmpeg (binaire statique)
                 os.path.expanduser("~/bin/ffmpeg"),
                 "/opt/homebrew/bin/ffmpeg", "/usr/local/opt/ffmpeg/bin/ffmpeg")
    for c in candidats:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return shutil.which("ffmpeg")


FFMPEG = trouver_ffmpeg()


def mesurer(chemin):
    r = subprocess.run(
        [FFMPEG, "-hide_banner", "-nostats", "-i", chemin,
         "-af", "loudnorm=print_format=json", "-f", "null", "-"],
        capture_output=True, text=True)
    blocs = re.findall(r"\{[^{}]*\}", r.stderr)
    if not blocs:
        global ERREUR
        if not ERREUR:
            ERREUR = f"{chemin}\n" + "\n".join(r.stderr.strip().splitlines()[-8:])
        return None
    d = json.loads(blocs[-1])
    i = float(d["input_i"])
    return None if i == float("-inf") or i < -70 else d


def encoder_args(ext):
    if ext == ".mp3":
        return ["-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k",
                "-map_metadata", "-1", "-id3v2_version", "0", "-write_xing", "0"]
    if ext == ".ogg":
        return ["-ar", "44100", "-ac", "1", "-c:a", "libvorbis", "-q:a", "5", "-map_metadata", "-1"]
    return ["-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", "-map_metadata", "-1"]


def traiter(src, dst, filtre):
    ext = os.path.splitext(src)[1].lower()
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", src,
                    "-af", filtre] + encoder_args(ext) + [dst], check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("pack")
    p.add_argument("--cible", type=float, default=-16.0, help="LUFS visés (défaut -16)")
    p.add_argument("--gain-max", type=float, default=18.0, help="gain max en dB (défaut 18)")
    p.add_argument("--par-fichier", action="store_true")
    a = p.parse_args()

    if not FFMPEG:
        sys.exit("ffmpeg introuvable : brew install ffmpeg")
    filtres = subprocess.run([FFMPEG, "-filters"], capture_output=True, text=True)
    if "loudnorm" not in filtres.stdout + filtres.stderr:
        sys.exit(f"{FFMPEG} est trop ancien (pas de filtre loudnorm) : brew install ffmpeg")
    print(f"ffmpeg utilisé : {FFMPEG}")

    pack = os.path.abspath(os.path.expanduser(a.pack))
    sortie = os.path.splitext(pack)[0] + "-fort.zip"
    tmp = tempfile.mkdtemp(prefix="lunii-")

    with zipfile.ZipFile(pack) as z:
        z.extractall(tmp)
        noms = z.namelist()

    sons = [n for n in noms if n.lower().endswith(AUDIO)]
    print(f"{len(sons)} sons trouvés. Mesure…")
    mesures = {}
    for k, n in enumerate(sons, 1):
        m = mesurer(os.path.join(tmp, n))
        if m:
            mesures[n] = m
        print(f"\r  {k}/{len(sons)}", end="", flush=True)
    print()

    if ERREUR:
        print("Premier son illisible, message de ffmpeg :\n" + ERREUR)
    if not mesures:
        sys.exit("Aucun son mesurable.")

    niveaux = [float(m["input_i"]) for m in mesures.values()]
    med = statistics.median(niveaux)
    print(f"Volume actuel : médiane {med:.1f} LUFS (min {min(niveaux):.1f}, max {max(niveaux):.1f})")

    if not a.par_fichier:
        gain = min(a.cible - med, a.gain_max)
        print(f"Gain appliqué à tous les sons : {gain:+.1f} dB")
        if gain <= 0.5:
            print("Le pack est déjà assez fort, rien à faire.")
            return

    print("Traitement…")
    for k, (n, m) in enumerate(mesures.items(), 1):
        src = os.path.join(tmp, n)
        dst = src + ".tmp" + os.path.splitext(n)[1]
        if a.par_fichier:
            f = (f"loudnorm=I={a.cible}:TP=-1.5:LRA=11:"
                 f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                 f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
                 f"offset={m['target_offset']}:linear=true")
        else:
            f = f"volume={gain:.2f}dB,alimiter=limit={LIMITE}:level=false"
        traiter(src, dst, f)
        os.replace(dst, src)
        print(f"\r  {k}/{len(mesures)}", end="", flush=True)
    print()

    with zipfile.ZipFile(sortie, "w", zipfile.ZIP_DEFLATED) as z:
        for n in noms:
            chemin = os.path.join(tmp, n)
            if os.path.isdir(chemin):
                continue
            z.write(chemin, n)
    shutil.rmtree(tmp)
    print(f"OK : {sortie}")


if __name__ == "__main__":
    main()

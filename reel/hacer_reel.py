"""Voz clonada -> reel con gráficos, música y subtítulos. Usa el motor de la Sesión 15 del curso.
Uso, desde la raíz: python reel/generar_voz.py reel/recursos/mi_voz.m4a && python reel/hacer_reel.py"""
import json, sys
from pathlib import Path
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw
sys.path.insert(0, "reel")
import motor_sesion15 as m

AUTOR, FUENTE = "Hideki Harada", "INEI, ENAHO 2024. Música: creación propia"
S = Path("reel/recursos"); guion = json.load(open("reel/guion.json"))

def escena(e):
    c = Image.new("RGBA", (m.ANCHO, m.ALTO), (0, 0, 0, 0)); d = ImageDraw.Draw(c); y = 410; w = m.ANCHO - 2 * m.MARGEN
    if e["cifra"]:
        f = m._ajustar(d, e["cifra"], "Oswald", 700, w, 170); d.text((m.MARGEN, y), e["cifra"], font=f, fill=m.ACENTO); y += f.size + 40
    f = m._fuente("PublicSans", 44, 600)
    for l in m._envolver(d, e["etiqueta"], f, w): d.text((m.MARGEN, y), l, font=f, fill=m.TEXTO); y += 56
    im = Image.open(S / e["imagen"]).convert("RGB"); esc = min(w / im.width, (1265 - y) / im.height)
    im = im.resize((int(im.width * esc), int(im.height * esc))); c.paste(im, ((m.ANCHO - im.width) // 2, y + 10))
    return c
m._escena = escena

if "--prueba" in sys.argv:
    n = m.Narracion(np.zeros(240000, np.float32), 24000, [(i * 1.6 + .3, i * 1.6 + 1.6) for i in range(6)], [(.3, .9, "Subtítulo"), (.9, 1.2, "de"), (1.2, 2, "prueba")])
    for i in range(6):
        m._cuadro(m._base(guion["titulo"], FUENTE, AUTOR), [escena(e) for e in guion["escenas"]], n, n.escenas[i][0] + .6, m._bloques(n.palabras), m._fuente("PublicSans", 62, 800)).save(S / f"prueba_{i}.png")
    sys.exit()

# La voz ya está en narracion_N.wav (reel/generar_voz.py). Subtítulos y control con un Whisper pequeño.
m.ASR = "small"
wavs = [sf.read(S / f"narracion_{i}.wav", dtype="float32") for i in range(len(guion["escenas"]))]
sr = wavs[0][1]; partes = [np.zeros(int(m.INICIO * sr), np.float32)]; esc = []; t = m.INICIO
for e, (w, _) in zip(guion["escenas"], wavs):
    e["wer"] = m._wer(e["frase"], m._a16k(w, sr))
    esc.append((t, t + len(w) / sr)); partes += [w, np.zeros(int(m.PAUSA * sr), np.float32)]; t += len(w) / sr + m.PAUSA
partes.append(np.zeros(int(m.FINAL * sr), np.float32))
n = m.Narracion(np.concatenate(partes), sr, esc)
print("Duración", round(n.duracion, 1), "WER", [round(e["wer"], 2) for e in guion["escenas"]], flush=True)
m.subtitulos(n, guion)
def corrige(i, w):
    previa = n.palabras[i - 1][2] if i else ""
    if w == "menores" and previa == "Mientras": return "menor es"
    if w == "viven" and n.palabras[i + 1][2].startswith("pobreza"): return "vive en"
    if w == "niños," and n.palabras[i + 1][2] == "pobres,": return "niños"
    if w == "pobres,": return "pobres"
    return w
n.palabras = [(a, b, corrige(i, w)) for i, (a, b, w) in enumerate(n.palabras)]
m.a_srt(n, "reel/subtitulos.srt")
mus = m.cargar_audio(S / "musica_propia.wav", sr=n.sr)[:len(n.audio)]
fade = np.minimum(1, np.minimum(np.arange(len(mus)), np.arange(len(mus))[::-1]) / n.sr)
n.audio = n.audio + 0.06 * mus * fade   # la música queda muy por debajo de la voz
json.dump(guion, open("reel/guion.json", "w"), ensure_ascii=False, indent=1)
m.video(guion, n, "reel/reel.mp4", FUENTE, AUTOR); Path("reel/reel.wav").unlink(missing_ok=True); print("LISTO", n.duracion)

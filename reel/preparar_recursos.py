"""Crea los gráficos, el mapa y la música del reel a partir de los resultados verificados."""
import json
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, soundfile as sf
from matplotlib.patches import Polygon
from PIL import Image

R = json.load(open("datos/procesados/resultados.json")); S = Path("reel/recursos")
FON, TX, SU, AC, AZ = "#1C1A17", "#F7F3EC", "#B8AE9F", "#F08A4B", "#5FA8B8"
plt.rcParams.update({"figure.facecolor": FON, "axes.facecolor": FON, "text.color": TX, "font.size": 25, "xtick.color": TX, "axes.edgecolor": FON})
def barras(et, val, col, nom):
    f, a = plt.subplots(figsize=(9, 5.2)); b = a.bar(et, val, color=col)
    a.bar_label(b, [f"{v:.1f} %" for v in val], padding=6); a.set_yticks([]); a.set_ylim(0, max(val) * 1.18); a.tick_params(length=0)
    f.tight_layout(); f.savefig(S / nom, dpi=110); plt.close(f)
g = R["grupos"]; G = list(g)
barras(["Niños (0-17)", "Adultos (18+)"], [R["ninos"]["tasa"], R["adultos"]["tasa"]], [AC, AZ], "fig_ninos.png")
barras(G, [g[k]["tasa"] for k in G], [AC] * 3 + [AZ] * 3, "fig_edad.png")
f, a = plt.subplots(figsize=(9, 5.2)); u, r = R["ninos_urbano"]["pobres"] / 1e6, R["ninos_rural"]["pobres"] / 1e6
b = a.barh(["Rural", "Urbano"], [r, u], color=[AZ, AC]); a.bar_label(b, [f"{r:.2f} millones", f"{u:.2f} millones"], padding=8)
a.set_xlim(0, u * 1.6); a.set_xticks([]); a.tick_params(left=False); a.set_title("Niños pobres, 2024", color=SU, loc="left"); f.tight_layout(); f.savefig(S / "fig_area.png", dpi=110); plt.close(f)
dep = {d["cod"]: d["ninos"] for d in R["departamentos"]}; geo = json.load(open("web/data/departamentos.geojson"))
f, a = plt.subplots(figsize=(7, 7.6)); cm = plt.cm.YlOrRd
for x in geo["features"]:
    t = x["geometry"]; pol = t["coordinates"] if t["type"] == "MultiPolygon" else [t["coordinates"]]
    for p in pol: a.add_patch(Polygon(p[0], fc=cm(dep[x["properties"]["FIRST_IDDP"]] / 55), ec=FON, lw=.8))
a.set_xlim(-82, -68); a.set_ylim(-19, 0.5); a.set_aspect("equal"); a.axis("off")
a.text(-74, -5, "Loreto\n51.5 %", ha="center", fontweight="bold", color="#1C1A17"); a.annotate("Ica 9.2 %", (-75.5, -14.2), (-81.8, -17), arrowprops=dict(color=TX, arrowstyle="-"))
f.tight_layout(); f.savefig(S / "fig_mapa.png", dpi=110); plt.close(f)
Image.open(S / "capturas/dashboard_inicio.png").convert("RGB").resize((1000, 703)).save(S / "fig_tablero.png")
# Música propia: acordes lentos, graves y sobrios, acordes con un tema serio,, sin licencia de terceros
sr = 24000; dur = 90; t = np.arange(sr * dur) / sr; m = np.zeros_like(t)
for i, ac in enumerate([[110, 130.8, 164.8], [87.3, 110, 130.8], [65.4, 98, 130.8], [98, 123.5, 146.8]] * 12):
    a0 = int(i * 8 * sr); n = min(int(9 * sr), len(t) - a0)
    if n <= 0: break
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    for h in ac: m[a0:a0 + n] += env * np.sin(2 * np.pi * h * t[:n])
sf.write(S / "musica_propia.wav", (m / np.abs(m).max() * .9).astype(np.float32), sr)

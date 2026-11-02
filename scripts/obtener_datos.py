"""Descarga los microdatos de la ENAHO 2024 (INEI) y los límites departamentales."""
import urllib.request
from pathlib import Path

DESTINO = Path("datos/originales")
ARCHIVOS = {
    "966-Modulo34.zip": "https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip",
    "966-Modulo02.zip": "https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip",
    "peru_departamental_simple.geojson": "https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson",
}
DESTINO.mkdir(parents=True, exist_ok=True)
for nombre, url in ARCHIVOS.items():
    if not (DESTINO / nombre).exists():
        print("Descargando", nombre)
        urllib.request.urlretrieve(url, DESTINO / nombre)

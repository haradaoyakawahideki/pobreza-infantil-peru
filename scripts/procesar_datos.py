"""Une sumaria y miembros de la ENAHO 2024, valida contra el INEI y guarda la base de personas."""
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

ORIGEN, SALIDA = Path("datos/originales"), Path("datos/procesados")
HOGAR = ["conglome", "vivienda", "hogar"]
PERSONA = HOGAR + ["codperso"]


def leer(archivo, interno, llaves):
    with zipfile.ZipFile(ORIGEN / archivo) as z:
        df = pd.read_stata(io.BytesIO(z.read(f"{Path(archivo).stem}/{interno}")), convert_categoricals=False)
    df.columns = [c.lower() for c in df.columns]
    for k in llaves:
        df[k] = df[k].astype(str).str.strip()
    return df


sumaria = leer("966-Modulo34.zip", "sumaria-2024.dta", HOGAR + ["ubigeo"])
sumaria = sumaria[HOGAR + ["ubigeo", "estrato", "pobreza", "mieperho", "factor07"]]
miembros = leer("966-Modulo02.zip", "enaho01-2024-200.dta", PERSONA)

# Residentes habituales: definición del INEI para medir pobreza
residente = ((miembros.p204 == 1) & (miembros.p205 == 2)) | ((miembros.p204 == 2) & (miembros.p206 == 1))
personas = miembros.loc[residente, PERSONA + ["p207", "p208a", "facpob07"]]
base = personas.merge(sumaria, on=HOGAR, how="left", validate="m:1", indicator=True)

peso = sumaria.factor07 * sumaria.mieperho
nacional = 100 * peso[sumaria.pobreza <= 2].sum() / peso.sum()
extrema = 100 * peso[sumaria.pobreza == 1].sum() / peso.sum()
pruebas = {
    "personas únicas": not personas.duplicated(PERSONA).any(),
    "todas con hogar": (base.pop("_merge") == "both").all(),
    "residentes = 108,664": len(base) == 108_664,
    "pobreza oficial 27.6 %": abs(nacional - 27.6) < 0.1,
    "pobreza extrema oficial 5.5 %": abs(extrema - 5.5) < 0.1,
    "sin edad o sexo faltante": base[["p207", "p208a"]].notna().all().all(),
}
for nombre, ok in pruebas.items():
    print("OK   " if ok else "FALLA", nombre)
print(f"Pobreza nacional {nacional:.2f} %, extrema {extrema:.2f} %")
if not all(pruebas.values()):
    sys.exit("La validación falló.")

base["dep"] = base.ubigeo.str[:2]
base["area"] = (base.estrato <= 5).map({True: "Urbano", False: "Rural"})
base["sexo"] = base.p207.map({1: "Hombre", 2: "Mujer"})
base["pobre"] = base.pobreza <= 2
base["extremo"] = base.pobreza == 1
base["grupo"] = pd.cut(base.p208a, [-1, 5, 11, 17, 29, 59, 200],
                       labels=["0-5", "6-11", "12-17", "18-29", "30-59", "60+"]).astype(str)
SALIDA.mkdir(parents=True, exist_ok=True)
base.drop(columns=["p207", "pobreza"]).to_parquet(SALIDA / "personas_2024.parquet", index=False)
print("Guardado", len(base))

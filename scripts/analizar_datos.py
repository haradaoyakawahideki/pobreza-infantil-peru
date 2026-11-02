"""Construye indicadores, errores de muestreo y los datos que usa el dashboard."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

d = pd.read_parquet("datos/procesados/personas_2024.parquet")
d["w"] = d.facpob07.astype(float)
d["upm"] = d.conglome
# Estrato de diseño aproximado: departamento × área
d["estr"] = d.dep + d.area
NOMBRES = {"01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho", "06": "Cajamarca",
           "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco", "11": "Ica", "12": "Junín",
           "13": "La Libertad", "14": "Lambayeque", "15": "Lima", "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua",
           "19": "Pasco", "20": "Piura", "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali"}


def estima(sub, var="pobre"):
    """Tasa ponderada e IC 95 % por linealización, con conglomerados dentro de estratos (todo el diseño)."""
    x = d.assign(z=0.0)
    tot = sub.w.sum()
    r = (sub.w * sub[var]).sum() / tot
    x.loc[sub.index, "z"] = sub.w * (sub[var].astype(float) - r) / tot
    u = x.groupby(["estr", "upm"]).z.sum().reset_index()
    g = u.groupby("estr").z
    n = g.transform("size")
    var_r = (((u.z - g.transform("mean")) ** 2) * n / (n - 1).clip(lower=1)).sum()
    ee = var_r ** 0.5
    return {"tasa": round(100 * r, 2), "li": round(100 * (r - 1.96 * ee), 2), "ls": round(100 * (r + 1.96 * ee), 2),
            "n": int(len(sub)), "poblacion": round(tot), "pobres": round((sub.w * sub[var]).sum())}


nino, adulto = d[d.p208a < 18], d[d.p208a >= 18]
res = {"nacional": estima(d), "extrema": estima(d, "extremo"), "ninos": estima(nino), "adultos": estima(adulto),
       "ninos_extrema": estima(nino, "extremo"), "adultos_extrema": estima(adulto, "extremo"),
       "ninos_rural": estima(nino[nino.area == "Rural"]), "ninos_urbano": estima(nino[nino.area == "Urbano"]),
       "grupos": {g: estima(d[d.grupo == g]) for g in ["0-5", "6-11", "12-17", "18-29", "30-59", "60+"]}}
res["ninos_entre_pobres"] = round(100 * nino.w[nino.pobre].sum() / d.w[d.pobre].sum(), 2)
res["ninos_en_poblacion"] = round(100 * nino.w.sum() / d.w.sum(), 2)
res["urbanos_entre_ninos_pobres"] = round(100 * nino.w[nino.pobre & (nino.area == "Urbano")].sum() / nino.w[nino.pobre].sum(), 2)

# Tamaño del hogar, como posible canal de la brecha
hog = d.assign(tam=pd.cut(d.mieperho, [0, 3, 5, 99], labels=["1-3", "4-5", "6+"]).astype(str))
res["ninos_por_tamano"] = {t: estima(nino[hog.loc[nino.index].tam == t]) for t in ["1-3", "4-5", "6+"]}

filas = []
for c, nom in NOMBRES.items():
    k, a = nino[nino.dep == c], adulto[adulto.dep == c]
    fk, fa = estima(k), estima(a)
    filas.append({"cod": c, "departamento": nom, "ninos": fk["tasa"], "ninos_li": fk["li"], "ninos_ls": fk["ls"],
                  "adultos": fa["tasa"], "brecha": round(fk["tasa"] - fa["tasa"], 2), "ninos_pobres": fk["pobres"], "n": fk["n"]})
dep = pd.DataFrame(filas).sort_values("ninos", ascending=False)
dep.to_csv("datos/procesados/departamentos.csv", index=False)
res["departamentos"] = filas

cubo = (d.assign(p=d.w * d.pobre, e=d.w * d.extremo)
        .groupby(["dep", "area", "sexo", "grupo"]).agg(pob=("w", "sum"), pob_pobre=("p", "sum"), pob_ext=("e", "sum"), n=("w", "size")).reset_index())
cubo[["pob", "pob_pobre", "pob_ext"]] = cubo[["pob", "pob_pobre", "pob_ext"]].round(0).astype(int)
cubo.to_csv("datos/procesados/cubo.csv", index=False)

geo = json.load(open("datos/originales/peru_departamental_simple.geojson"))
print("props geo:", geo["features"][0]["properties"])
web = Path("web/data"); web.mkdir(parents=True, exist_ok=True)
json.dump({"cubo": cubo.values.tolist(), "cols": list(cubo.columns), "nombres": NOMBRES, "res": res}, open(web / "datos.json", "w"), ensure_ascii=False)
json.dump(res, open("datos/procesados/resultados.json", "w"), ensure_ascii=False, indent=1)
for k in ["nacional", "extrema", "ninos", "adultos", "ninos_extrema", "adultos_extrema", "ninos_rural", "ninos_urbano"]:
    print(k, res[k])
print(res["grupos"]); print(res["ninos_por_tamano"])
print({k: res[k] for k in ["ninos_entre_pobres", "ninos_en_poblacion", "urbanos_entre_ninos_pobres"]})
print(dep.to_string())
print((dep.brecha > 0).sum(), "de 25 con brecha positiva; IC sobre adultos:", (dep.ninos_li > dep.adultos).sum())

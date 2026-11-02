"""Prueba los filtros del dashboard en un navegador y guarda capturas (requiere playwright)."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765/web/"
SAL = Path("reel/recursos/capturas"); SAL.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
    pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
    errores = []
    pg.on("pageerror", lambda e: errores.append(str(e)))
    pg.on("console", lambda m: errores.append(m.text) if m.type == "error" else None)
    pg.goto(URL); pg.wait_for_selector("#mapa canvas", timeout=40000); pg.wait_for_timeout(3500)
    kp = lambda: [pg.inner_text(f"#k{i}") for i in range(1, 5)]
    print("inicial", kp()); pg.screenshot(path=SAL / "dashboard_inicio.png")
    pg.locator(".grid").first.screenshot(path=SAL / "dashboard_graficos.png")
    for sel, val in [("#fGrupo", "0-5"), ("#fArea", "Rural"), ("#fSexo", "Mujer"), ("#fDep", "16"), ("#fInd", "num")]:
        pg.select_option(sel, val); pg.wait_for_timeout(700); print(sel, val, kp())
    pg.fill("#buscar", "lore"); print("filas", pg.locator("#tab tbody tr").count())
    pg.screenshot(path=SAL / "dashboard_filtrado.png")
    with pg.expect_download() as d: pg.click("#bajar")
    print("descarga", d.value.suggested_filename)
    pg.reload(); pg.wait_for_selector("#mapa canvas"); pg.wait_for_timeout(3000)
    pg.locator("#hallazgos").screenshot(path=SAL / "dashboard_hallazgos.png")
    m = b.new_page(viewport={"width": 390, "height": 844}); m.goto(URL); m.wait_for_timeout(3000)
    print("desborde móvil", m.evaluate("document.documentElement.scrollWidth-innerWidth"))
    print("errores", errores)

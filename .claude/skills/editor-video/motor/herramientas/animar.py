"""Fase 4 · Animar con HyperFrames: la capa de motion graphics de la marca.

  kit.py animar <video> [--formato horizontal|vertical] [--desde S --hasta S --nombre reel1]
                        [--plantilla <nombre>]

La plantilla activa (estilos/<nombre>.json) decide el ritmo, los subtítulos, el tamaño de los
textos, el acento, si los logos van en 3D, los zooms y las transiciones. Ver la skill «estilo».

Genera un proyecto HyperFrames (HTML + GSAP + Three.js) por formato y lo renderiza con fondo
transparente (.mov con canal alfa). Además, por cada momento de «profundidad», una capa aparte
con el texto gigante que luego el compositor mete POR DETRÁS de la persona.

Piezas: logo 3D de entrada, rótulo con nombre, textos destacados, listas con ticks, tarjetas de
herramienta con su logo en 3D, transiciones de luz y subtítulos palabra a palabra.
Solo anima si el plan está aprobado.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

from comun import (ENTORNO, FORMATOS, MARCA, RAIZ, Cronometro, aviso, cargar_marca, carpeta_trabajo, ejecutar,
                   frase_cabe, frases_subtitulo,
                   entorno_hyperframes, escribir_json, fallo, hex_a_rgb, info_video, leer_json, ok, paso,
                   resolver_video, ruta_proyecto)
import estilo as E
import persona as P
import recursos as R

HF = ENTORNO / "node_modules" / "hyperframes" / "bin" / "hyperframes.mjs"
GSAP = ENTORNO / "node_modules" / "gsap" / "dist" / "gsap.min.js"
THREE = ENTORNO / "node_modules" / "three"
CAPA = Path(__file__).resolve().parent / "capa"
LOGOS = MARCA / "logos"

# Tres estilos elegibles en brand.json ("estilo"). "cristal" usa las tipografías de tu marca;
# "editorial" y "energia" traen su propio combo (siempre de Google Fonts, licencia OFL).
ESTILOS = {
    # por defecto: la identidad propia de D-IA. Cine editorial: Instrument Serif (clave en cursiva
    # coral), Archivo estructural y JetBrains Mono para cifras y órdenes. Coral + crema. Sin cajas.
    "dia-editorial": {"tit": "Archivo", "txt": "Archivo", "rem": "Instrument Serif", "mono": "JetBrains Mono",
                      "peso_tit": 700, "track": "-0.02em", "mayus": "none", "sub": "txt", "peso_sub": 600,
                      "mayus_sub": "none", "radio": 14, "cajas": False},
    # (versiones anteriores) sin cajas, énfasis por detrás: sin cajas ni tarjetas. Los énfasis salen en texto gigante POR DETRÁS de la persona,
    # cada uno de un color de la paleta; subtítulos limpios sobre el vídeo.
    "detras": {"tit": None, "txt": None, "rem": None, "mono": "JetBrains Mono", "peso_tit": 800,
               "track": "-0.03em", "mayus": "none", "sub": "tit", "peso_sub": 800, "mayus_sub": "none",
               "radio": 30, "cajas": False},
    "cristal": {"tit": None, "txt": None, "rem": None, "mono": "JetBrains Mono", "peso_tit": 800,
                "track": "-0.03em", "mayus": "none", "sub": "tit", "peso_sub": 800, "mayus_sub": "none",
                "radio": 30, "cajas": True},
    "editorial": {"tit": "Inter Tight", "txt": "Inter Tight", "rem": "Newsreader", "mono": "JetBrains Mono",
                  "peso_tit": 700, "track": "-0.042em", "mayus": "none", "sub": "txt", "peso_sub": 700,
                  "mayus_sub": "none", "radio": 22, "cajas": True},
    "energia": {"tit": "Archivo Black", "txt": "Inter Tight", "rem": None, "mono": "JetBrains Mono",
                "peso_tit": 400, "track": "-0.01em", "mayus": "uppercase", "sub": "tit", "peso_sub": 400,
                "mayus_sub": "uppercase", "radio": 18, "cajas": True},
}
# fuentes que necesita cada estilo (las descarga /empezar)
FUENTES_ESTILO = {"JetBrains Mono": [500, 600], "Inter Tight": [600, 700, 800], "Newsreader": ["500i", "600i"],
                  "Archivo Black": [400], "Instrument Serif": [400, "400i"], "Archivo": [500, 600, 700, 800]}

ICONOS = {  # trazos propios, dibujados a mano para el kit (24x24)
    "check": "M5 12.5l4.5 4.5L19 7.5",
    "flecha": "M12 4v15M6 13l6 6 6-6",
    "flecha-derecha": "M4 12h15M13 6l6 6-6 6",
    "rayo": "M13 3L5 13.5h6L10 21l8-11h-6z",
    "estrella": "M12 3.5l2.6 5.6 6 .7-4.5 4.1 1.2 6-5.3-3-5.3 3 1.2-6L3.4 9.8l6-.7z",
    "reloj": "M12 7v5l3.5 2M12 3.5a8.5 8.5 0 1 0 .01 0",
    "candado": "M7 11V8a5 5 0 0 1 10 0v3M5.5 11h13v9.5h-13z",
}

TAM = {
    "horizontal": {"radio_k": 1.0, "dest": 70, "dest_max": 620, "kicker": 22, "fila": 40, "rot_nombre": 48,
                   "rot_handle": 25, "logo_h": 84, "logo_txt": 30, "herr_nombre": 52, "sub": 56,
                   "sub_max": 1360, "margen": 90},
    "vertical": {"radio_k": 1.1, "dest": 82, "dest_max": 930, "kicker": 27, "fila": 50, "rot_nombre": 56,
                 "rot_handle": 30, "logo_h": 96, "logo_txt": 32, "herr_nombre": 60, "sub": 70,
                 "sub_max": 960, "margen": 60},
}


# ------------------------------------------------------------------ utilidades
def esc(t: str) -> str:
    return html.escape(t or "", quote=True)


def norm_w(t: str) -> str:
    t = unicodedata.normalize("NFKD", (t or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", t)


def rgb(h: str) -> str:
    return ",".join(str(x) for x in hex_a_rgb(h))


def fuentes_css() -> str:
    css = []
    carpeta = MARCA / "fuentes"
    for f in sorted(carpeta.glob("*.woff2")) if carpeta.exists() else []:
        m = re.match(r"(.+)-(\d{3})(i?)\.woff2$", f.name)
        if not m:
            continue
        fam = m.group(1).replace("_", " ")
        estilo = "italic" if m.group(3) else "normal"
        css.append(f"@font-face{{font-family:'{fam}';src:url('fuentes/{f.name}') format('woff2');"
                   f"font-weight:{m.group(2)};font-style:{estilo};font-display:block;}}")
    return "\n".join(css)


def estilo_de(marca: dict) -> dict:
    nombre = marca.get("estilo", "dia-editorial")
    if nombre == "detras":  # el estilo de versiones anteriores ya no existe
        nombre = "dia-editorial"
    e = dict(ESTILOS.get(nombre, ESTILOS["dia-editorial"]))
    e["nombre"] = nombre if nombre in ESTILOS else "dia-editorial"
    tip = marca.get("tipografia", {})
    if e["nombre"] == "dia-editorial":
        # la serif y la mono son de la identidad; lo estructural (subtítulos, etiquetas) va con la de tu marca
        e["tit"] = tip.get("titulos") or e["tit"]
        e["txt"] = tip.get("texto") or e["txt"]
    e["tit"] = e["tit"] or tip.get("titulos", "Inter")
    e["txt"] = e["txt"] or tip.get("texto", "Inter")
    e["rem"] = e["rem"] or e["tit"]
    return e


def fuente_3d(estilo: dict, texto: str, destino: Path) -> dict | None:
    """JSON de la fuente de títulos para el texto 3D (solo las letras que hacen falta)."""
    fam = estilo["tit"].replace(" ", "_")
    cands = sorted((MARCA / "fuentes").glob(f"{fam}-*.woff2"), key=lambda p: p.name, reverse=True)
    cands = [c for c in cands if not c.stem.endswith("i")]
    if not cands:
        return None
    r = subprocess.run(["node", str(Path(__file__).resolve().parent / "fuente3d.mjs"), str(cands[0]),
                        str(destino), texto + texto.upper() + texto.lower() + "?"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(ENTORNO))
    if r.returncode != 0 or not destino.exists():
        aviso("No he podido preparar la fuente 3D: " + (r.stdout or "")[-300:])
        return None
    return json.loads(destino.read_text(encoding="utf-8"))


def logo_svg(nombre: str) -> str | None:
    """SVG de un logo o icono. «claude» busca marca/logos/claude.svg y, si no está, lo baja del
    set «logos» de Iconify (CC0). «tabler:file-text» baja ese icono del set Tabler (MIT).
    Los logos son marcas de sus dueños: úsalos solo para referirte a esa herramienta."""
    if not nombre:
        return None
    LOGOS.mkdir(parents=True, exist_ok=True)
    if ":" in nombre:
        conj, nom = nombre.split(":", 1)
        cands = [(conj, nom)]
    else:
        conj, nom = "logos", re.sub(r"[^a-z0-9-]", "", nombre.lower().replace(" ", "-"))
        cands = [("logos", f"{nom}-icon"), ("logos", nom)]
    ruta = LOGOS / (f"{nom}.svg" if conj == "logos" else f"{conj}-{nom}.svg")
    if not ruta.exists():
        import urllib.request
        for c_, n_ in cands:
            try:
                req = urllib.request.Request(f"https://api.iconify.design/{c_}/{n_}.svg",
                                             headers={"User-Agent": "kit-editor-video"})
                svg = urllib.request.urlopen(req, timeout=15).read().decode()
                if svg.startswith("<svg") and ("<path" in svg or "<g" in svg):
                    ruta.write_text(svg, encoding="utf-8")
                    break
            except Exception:
                continue
    return ruta.read_text(encoding="utf-8") if ruta.exists() else None


def logo_png(nombre: str) -> dict | None:
    """Un logo en PNG (marca/logos/<nombre>.png, mejor con fondo transparente) listo para el 3D:
    su silueta en SVG (se extruye) y la propia imagen como textura de la cara. Sin fondo
    transparente, el color de las esquinas se toma como fondo."""
    import base64
    nom = re.sub(r"[^a-z0-9-]", "", (nombre or "").lower().replace(" ", "-"))
    ruta = next((LOGOS / f"{nom}{ext}" for ext in (".png", ".webp") if (LOGOS / f"{nom}{ext}").exists()), None)
    if not ruta:
        return None
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    img = cv2.imread(str(ruta), cv2.IMREAD_UNCHANGED)
    if img is None:
        return None
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    elif img.shape[2] == 3:
        bgr = img
        esquinas = np.array([bgr[0, 0], bgr[0, -1], bgr[-1, 0], bgr[-1, -1]], np.float32).mean(axis=0)
        dist = np.linalg.norm(bgr.astype(np.float32) - esquinas, axis=2)
        img = np.dstack([bgr, np.where(dist > 38, 255, 0).astype(np.uint8)])
    h, w = img.shape[:2]
    k = 512 / max(h, w)
    if k < 1:
        img = cv2.resize(img, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
        h, w = img.shape[:2]
    alfa = (img[:, :, 3] > 110).astype(np.uint8) * 255
    alfa = cv2.morphologyEx(alfa, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    conts, _ = cv2.findContours(alfa, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    trazos = []
    for c in conts:
        if cv2.contourArea(c) < 12:
            continue
        c = cv2.approxPolyDP(c, 0.7, True).reshape(-1, 2)
        if len(c) < 3:
            continue
        trazos.append("M" + " L".join(f"{x} {y}" for x, y in c) + " Z")
    if not trazos:
        return None
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"><path fill="#ffffff" '
           f'fill-rule="evenodd" d="{" ".join(trazos)}"/></svg>')
    ok_, png = cv2.imencode(".png", img)
    opacos = img[:, :, :3][img[:, :, 3] > 110]
    medio = opacos.mean(axis=0) if len(opacos) else np.array([128, 128, 128])
    lado = "#%02x%02x%02x" % tuple(int(v * 0.55) for v in medio[::-1])
    return {"svg": svg, "textura": "data:image/png;base64," + base64.b64encode(png.tobytes()).decode(),
            "colorLado": lado, "profundidad": round(max(w, h) * 0.07, 1), "ancho": w, "alto": h}


def palabras_en(palabras: list[dict], desde: float, hasta: float) -> list[dict]:
    return [w for w in palabras if desde - 0.05 <= w["s"] <= hasta]


def anclar(texto_pal: list[str], habladas: list[dict], t0: float) -> list[float | None]:
    """Para cada palabra del texto en pantalla, el segundo en que se dice (o None)."""
    res, j = [], 0
    for p in texto_pal:
        n = norm_w(p)
        t = None
        for k in range(j, len(habladas)):
            if n and norm_w(habladas[k]["w"]) == n:
                t, j = habladas[k]["s"], k + 1
                break
        res.append(t)
    return res


def numero_de(p: str) -> int | None:
    m = re.fullmatch(r"(\d{1,4})", re.sub(r"[^\d]", "", p) if re.fullmatch(r"\W*\d{1,4}\W*", p) else "")
    return int(m.group(1)) if m else None


# ------------------------------------------------------------------ geometría
def zonas(formato: str, pers: dict | None, plan: dict, t0: float, t1: float, iv: dict | None) -> dict:
    """Dónde cabe cada cosa sin tocar la cara, en píxeles del formato de salida."""
    W, H = FORMATOS[formato]
    cara = P.cara_media(pers, t0, t1) if pers else None
    z = {"cara": None}
    if formato == "horizontal":
        if cara:
            z["cara"] = [(cara[0] - cara[2] / 2) * W, (cara[1] - cara[3] / 2) * H,
                         (cara[0] + cara[2] / 2) * W, (cara[1] + cara[3] / 2) * H]
        return z
    # vertical: la franja 9:16 recortada del original y llevada a 1080x1920
    if cara and iv:
        cx = P.centro_vertical(plan, pers, iv["ancho"], iv["alto"], (t0 + t1) / 2)
        esc_v = H / iv["alto"]
        x0 = cx - iv["alto"] * 9 / 32
        z["cara"] = [((cara[0] - cara[2] / 2) * iv["ancho"] - x0) * esc_v, (cara[1] - cara[3] / 2) * H,
                     ((cara[0] + cara[2] / 2) * iv["ancho"] - x0) * esc_v, (cara[1] + cara[3] / 2) * H]
    return z


def barbilla(formato: str, pers, plan, t0, t1, iv) -> float:
    """Primera línea libre bajo la barbilla en vertical (con margen para los zooms de cámara)."""
    z = zonas(formato, pers, plan, t0, t1, iv)
    if z["cara"]:
        return min(max(z["cara"][3] + 70, 900), 1180)
    return 1080


def lado_libre(formato: str, preferido: str, z: dict) -> str:
    if formato == "vertical" or not z.get("cara"):
        return preferido if preferido in ("izquierda", "derecha") else "derecha"
    W = FORMATOS[formato][0]
    x0, _, x1, _ = z["cara"]
    libre_izq, libre_der = x0 - 90, W - 90 - x1
    # Si el usuario pide un lado («esa frase, al otro lado»), se respeta mientras quepa algo (300 px):
    # los textos van por detrás de la persona, así que pisarla un poco no tapa nada.
    if preferido in ("izquierda", "derecha"):
        if (libre_izq if preferido == "izquierda" else libre_der) >= 300:
            return preferido
    elif libre_der >= 520:
        return "derecha"
    return "izquierda" if libre_izq > libre_der else "derecha"


# ------------------------------------------------------------------ construcción de la capa
def construir(marca: dict, plan: dict, palabras: list[dict], duracion: float, formato: str,
              pers: dict | None, iv: dict | None, proyecto: Path, video_fuente: Path | None = None,
              pl: dict | None = None):
    """Devuelve (html, eventos de sonido, piezas de profundidad)."""
    pl = pl or E.cargar(None)
    esc_txt = float(pl.get("textos", {}).get("escala", 1.0))
    W, H = FORMATOS[formato]
    vert = formato == "vertical"
    T = TAM[formato]
    c = marca["colores"]
    e = estilo_de(marca)
    # un solo color de acento más el blanco: «color_enfasis» en brand.json o, si no, el acento
    principal = acento = color_acento(marca)
    sonidos: list[dict] = []
    extra = {"barridos": [], "vinetas": [], "latigos": [], "broll": [], "tapan": []}
    ventana_sub: dict = {}  # id -> (inicio, fin, ¿deja subtítulo?)
    piezas3d: list[dict] = []
    detras: list[dict] = []
    partes: list[str] = []
    beats_js: list[dict] = []
    fuente_json = None

    def f3d():
        nonlocal fuente_json
        if fuente_json is None:
            textos = "".join((b.get("texto") or "") for b in plan["beats"]) + monograma(marca)
            fuente_json = fuente_3d(e, textos, proyecto / "fuente3d.json") or {}
        return fuente_json or None

    claves_globales = set()
    beats = sorted([b for b in plan["beats"] if "inicio" in b], key=lambda b: b["inicio"])
    for b in beats:
        for x in (b.get("resaltar") or "").split():
            claves_globales.add(norm_w(x))

    paleta = paleta_enfasis(marca)
    n_enf = 0
    ctx = R.Ctx(formato, palabras, marca, e, lambda a, b_: zonas(formato, pers, plan, a, b_, iv), proyecto,
                duracion, video_fuente, acento, pl)
    for b in beats:
        tipo = ALIAS.get(b["tipo"], b["tipo"])
        i, d = float(b["inicio"]), float(b["duracion"])
        bid = re.sub(r"[^a-zA-Z0-9_-]", "", b["id"]) or "b"
        if tipo in RECURSOS:
            t0r, t1r = max(0.0, i - 0.12), min(duracion, i + d)
            res = R.construir(tipo, b, bid, t0r, t1r, ctx)
            if res.get("detras"):
                db = dict(res["detras"], tipo="profundidad", inicio=round(t0r, 3), duracion=round(t1r - t0r, 3))
                detras.append(db)
            if res.get("html"):
                partes.append(res["html"])
                beats_js.append(dict(res["js"], _global=True))
            for pz in res.get("piezas3d", []):
                pz = dict(pz)
                if pz["tipo"] == "golpe":
                    fj = f3d()
                    if not fj:
                        continue
                    pz["fuente"] = fj
                piezas3d.append(pz)
            sonidos += res.get("sonidos", [])
            if res.get("barrido"):
                extra["barridos"].append(res["barrido"])
            if res.get("vineta"):
                extra["vinetas"].append(res["vineta"])
            if tipo != "zoom" or "subtitulo" in b:  # un zoom solo mueve la cámara: no toca los subtítulos
                ventana_sub[bid] = (t0r, t1r, R.lleva_subtitulo(b))
            if res.get("latigo"):
                extra["latigos"].append(res["latigo"])
            if res.get("broll"):
                extra["broll"].append(res["broll"])
            if res.get("tapa"):
                extra["tapan"].append(res["tapa"])
            continue
        if not e["cajas"] and tipo in ("destacado", "herramienta"):
            b = a_detras(b)
            tipo = "profundidad"
        if tipo == "profundidad":
            b = dict(b)
            # entra 0,2 s antes de la palabra: así el golpe cae justo cuando se dice
            b["inicio"] = round(max(0.0, i - 0.2), 3)
            b["duracion"] = round(min(d + 0.1, duracion - b["inicio"]), 3)
            b.setdefault("color", acento if len(paleta) == 1 else paleta[n_enf % len(paleta)])
            b.setdefault("entrada", ENTRADAS[n_enf % len(ENTRADAS)])
            if b.get("logo") and "svg" not in b:
                b["svg"] = logo_svg(b["logo"])
            n_enf += 1
            detras.append(b)
            ventana_sub[bid] = (b["inicio"], b["inicio"] + b["duracion"], b.get("subtitulo", False))
            for x in (b.get("texto") or "").split():
                claves_globales.add(norm_w(x))
            continue
        if tipo == "logo":  # sin logo animado de marca en la identidad editorial
            continue
        if tipo == "logo" and vert:
            # en vertical los énfasis ocupan la franja de arriba: el logo espera a un hueco libre
            tipos_d = ("profundidad", "texto_detras", "halo", "notificacion", "visor") + (() if e["cajas"] else ("destacado", "herramienta"))
            ventanas = sorted((float(x["inicio"]) - 0.3, float(x["inicio"]) + float(x.get("duracion", 2)) + 0.1)
                              for x in beats if x["tipo"] in tipos_d)
            for a_, b_ in ventanas:
                if i < b_ and i + d > a_:
                    i = b_ + 0.2
            if i + d > duracion:
                continue
        t0 = max(0.0, i - (0.25 if tipo in ("destacado", "lista", "herramienta") else 0.0))
        t1 = min(duracion, i + d)
        if t1 - t0 < 0.6:
            continue
        dd = t1 - t0
        z = zonas(formato, pers, plan, t0, t1, iv)
        # tiempos locales (relativos al clip) para GSAP; los clips van con data-start propio
        ventana_sub[bid] = (t0, t1, R.lleva_subtitulo(b, tipo == "transicion"))
        clip = f'id="{bid}" data-start="{t0:.3f}" data-duration="{dd:.3f}" data-track-index="2"'

        if tipo == "logo":
            nombre = marca["canal"].get("marca") or marca["canal"]["nombre"]
            lh = T["logo_h"]
            ancho_txt = 0 if vert else int(len(nombre) * T["logo_txt"] * 0.64) + 34
            pill_w = lh + ancho_txt
            top = 150 if vert else 56
            right = 60 if vert else 64
            left = W - right - pill_w
            C = 600 if not vert else 640
            letras = "".join(f'<span class="l">{esc(ch) if ch != " " else "&nbsp;"}</span>' for ch in nombre)
            marca_html = "" if vert else f'<div class="marca" id="{bid}-m">{letras}</div>'
            svg = None
            logo = marca.get("logo")
            if logo and str(logo).lower().endswith(".svg") and ruta_proyecto(logo).exists():
                svg = ruta_proyecto(logo).read_text(encoding="utf-8")
            img = ""
            if logo and not svg and ruta_proyecto(logo).exists():
                (proyecto / "assets").mkdir(exist_ok=True)
                shutil.copy(ruta_proyecto(logo), proyecto / "assets" / Path(logo).name)
                img = (f'<img src="assets/{Path(logo).name}" style="position:absolute;left:{lh * 0.14:.0f}px;'
                       f'top:{lh * 0.14:.0f}px;width:{lh * 0.72:.0f}px;height:{lh * 0.72:.0f}px;'
                       f'border-radius:50%;object-fit:contain" alt="">')
            choca_ini = any(x.get("tipo") in ("profundidad", "texto_detras", "titulo", "referencias", "pantalla",
                                              "destacado", "herramienta") and "inicio" in x
                            and float(x["inicio"]) < t0 + 2.4 and x is not b
                            and float(x["inicio"]) + float(x.get("duracion", 2)) > t0 for x in beats)
            abre = (0.55 if choca_ini else 1.95) if not img else 0.2
            partes.append(
                f'<div class="clip bloque logo" {clip} style="right:{right}px;top:{top}px;height:{lh}px">'
                f'<div class="vidrio" id="{bid}-v"><span class="brillo" id="{bid}-br"></span>'
                f'{img}{marca_html}</div>'
                + (f'<canvas id="{bid}-c" width="{C}" height="{C}" style="left:{lh / 2 - C / 2:.0f}px;'
                   f'top:{lh / 2 - C / 2:.0f}px;width:{C}px;height:{C}px"></canvas>' if not img else "")
                + '</div>')
            beats_js.append({"tipo": "logo", "id": bid, "t0": 0, "t1": dd, "abre": abre,
                             "origen": f"{lh / 2:.0f}px 50%"})
            choca = any(x.get("tipo") in ("profundidad", "texto_detras", "titulo", "referencias", "pantalla")
                        + (() if e["cajas"] else ("destacado", "herramienta"))
                        and "inicio" in x and float(x["inicio"]) < t0 + 2.4
                        and float(x["inicio"]) + float(x.get("duracion", 2)) > t0 for x in beats)
            if not img:
                pieza = {"tipo": "logo", "canvas": f"{bid}-c", "w": C, "h": C, "t0": t0, "t1": t1,
                         "principal": principal, "acento": acento, "llegada": 1.2,
                         "medallon": tono_panel(c.get("panel", "#070b09")),
                         "encoger": {"desde": 1.55, "dur": 0.6, "escala": (lh * 0.84) / (C * 0.77)},
                         # grande: ~300 px de medallón, bajado para que no lo corte el borde de arriba
                         "grande": {"escala": 300 / (C * 0.77),
                                    "dy": -max(0.0, 250 - (top + lh / 2)) / (C / 3.59),
                                    "dx": -max(0.0, (left + lh / 2) - (W - 190)) / (C / 3.59)}}
                if choca:  # sin fase grande: entra girando directamente a su hueco
                    pieza.pop("grande")
                    pieza["encoger"] = {"desde": -1.0, "dur": 0.01, "escala": pieza["encoger"]["escala"] * 1.0}
                    pieza["llegada"] = 0.9
                if svg:
                    pieza["svg"] = svg
                    pieza.update({"cara": "#ffffff", "canto": "#888888"})
                else:
                    fj = f3d()
                    if not fj:
                        continue
                    pieza.update({"fuente": fj, "texto": monograma(marca), "cara": principal,
                                  "canto": oscurecer(principal, 0.42), "emisivo": principal,
                                  "emisivoFuerza": 0.08, "metal": 0.35, "rugosidad": 0.22})
                piezas3d.append(pieza)
            sonidos += [{"t": t0 + 0.02, "sonido": "whoosh", "dur": 0.9, "db": -2},
                        {"t": t0 + (0.8 if abre < 1 else 0.92), "sonido": "sub", "db": -3},
                        {"t": t0 + abre + 0.05, "sonido": "aire", "db": -4}]

        elif tipo == "rotulo":
            letras = "".join(f'<span class="l">{esc(ch) if ch != " " else "&nbsp;"}</span>'
                             for ch in b.get("titulo", ""))
            if vert:
                y = barbilla(formato, pers, plan, t0, t1, iv)
                pos = f"left:0;right:0;top:{y:.0f}px;display:flex;justify-content:center"
            else:
                pos = f"left:96px;bottom:230px"
            partes.append(
                f'<div class="clip bloque rot persp" {clip} style="{pos}">'
                + ('' if e["cajas"] else f'<div class="velo" id="{bid}-sh"></div>') +
                f'<div class="vidrio" id="{bid}-v"><span class="brillo" id="{bid}-br"></span>'
                f'<span class="barra" id="{bid}-b"></span><div>'
                f'<div class="nombre" id="{bid}-n">{letras}</div>'
                f'<div class="handle" id="{bid}-h">{esc(b.get("subtitulo", ""))}</div></div></div></div>')
            beats_js.append({"tipo": "rotulo", "id": bid, "t0": 0, "t1": dd})
            sonidos += [{"t": t0 + 0.0, "sonido": "whoosh", "dur": 0.5, "db": -5},
                        {"t": t0 + 0.2, "sonido": "aire", "db": -7}]

        elif tipo in ("destacado", "lista", "herramienta"):
            lado = lado_libre(formato, b.get("posicion"), z)
            if vert:
                y = barbilla(formato, pers, plan, t0, t1, iv)
                pos = f"left:0;right:0;top:{y:.0f}px;display:flex;justify-content:center"
            else:
                yc = 470
                if z.get("cara"):
                    yc = min(max((z["cara"][1] + z["cara"][3]) / 2 + 20, 380), 520)
                lado_css = f"left:{T['margen']}px" if lado == "izquierda" else f"right:{T['margen']}px"
                pos = f"{lado_css};top:{yc:.0f}px;transform-origin:50% 50%;translate:0 -50%"
            habladas = palabras_en(palabras, i - 0.3, t1)
            halo = f'<div class="halo" id="{bid}-halo"></div>'
            kick = (f'<div class="kicker" id="{bid}-k"><span class="punto"></span>{esc(b["etiqueta"])}</div>'
                    if b.get("etiqueta") else "")

            if tipo == "destacado":
                resaltar = {norm_w(x) for x in (b.get("resaltar") or "").split()}
                tokens = (b.get("texto") or "").split()
                tiempos = anclar(tokens, habladas, i)
                spans, pals = [], []
                ultimo = t0 + 0.12
                for k, p in enumerate(tokens):
                    num = numero_de(p)
                    clave = norm_w(p) in resaltar
                    tt = tiempos[k]
                    tt = (tt - 0.05) if tt is not None else ultimo + 0.07
                    tt = max(tt, t0 + 0.14 + k * 0.04)
                    ultimo = tt
                    dentro = esc(p)
                    if num is not None:
                        dentro = esc(p).replace(str(num), f'<span class="num">{num}</span>', 1)
                    cls = "p"
                    extra = ""
                    if clave or num is not None:
                        cls += " clave" + (" remate" if e["nombre"] == "editorial" else "")
                        extra = ('<svg class="subraya" viewBox="0 0 100 12" preserveAspectRatio="none">'
                                 '<path pathLength="1" d="M2 8 C 22 3, 48 11, 70 6 S 92 5, 98 7"/></svg>')
                    spans.append(f'<span class="{cls}" id="{bid}-p{k}">{dentro}{extra}</span>')
                    pals.append({"t": round(tt - t0, 3), "clave": bool(clave or num is not None), "num": num})
                    if clave or num is not None:
                        sonidos.append({"t": tt + 0.03, "sonido": "sub", "db": -4})
                icono = ""
                if b.get("icono") in ICONOS:
                    lado_ic = "right:-18px" if lado == "izquierda" or vert else "left:-18px"
                    icono = (f'<div class="icono" id="{bid}-i" style="{lado_ic}"><svg viewBox="0 0 24 24">'
                             f'<path pathLength="1" d="{ICONOS[b["icono"]]}"/></svg></div>')
                largo = len(b.get("texto") or "")
                fdest = T["dest"] if largo <= 16 else int(T["dest"] * (0.9 if largo <= 24 else 0.8))
                partes.append(
                    f'<div class="clip bloque dest persp" {clip} style="{pos};--dest:{fdest}px">{halo}'
                    f'<div class="vidrio" id="{bid}-v"><span class="brillo" id="{bid}-br"></span>'
                    f'{kick}<div class="titular">{"".join(spans)}</div></div>{icono}</div>')
                beats_js.append({"tipo": "destacado", "id": bid, "t0": 0, "t1": dd, "lado": lado, "palabras": pals})
                sonidos.insert(len(sonidos), {"t": t0 - 0.06, "sonido": "aire", "db": -3})

            elif tipo == "lista":
                filas, items = [], []
                previo = t0 + 0.25
                for k, it in enumerate(b.get("items", [])):
                    txt = it.get("texto", "") if isinstance(it, dict) else str(it)
                    cuando = it.get("cuando") if isinstance(it, dict) else None
                    tt = None
                    if cuando:
                        from plan import buscar_frase
                        r = buscar_frase(palabras, cuando, max(0.0, i - 1.0))
                        tt = r[0] - 0.05 if r else None
                    tt = max(tt if tt is not None else previo + 0.45, previo + 0.18 if k else t0 + 0.3)
                    previo = tt
                    items.append({"t": round(tt - t0, 3)})
                    filas.append(f'<div class="fila" id="{bid}-f{k}"><span class="check"><svg viewBox="0 0 24 24">'
                                 f'<path pathLength="1" d="{ICONOS["check"]}"/></svg></span><span>{esc(txt)}</span></div>')
                    sonidos.append({"t": tt + 0.18, "sonido": "tic", "db": 0})
                partes.append(
                    f'<div class="clip bloque lista persp" {clip} style="{pos}">{halo}'
                    f'<div class="vidrio" id="{bid}-v"><span class="brillo" id="{bid}-br"></span>{kick}'
                    f'{"".join(filas)}</div></div>')
                beats_js.append({"tipo": "lista", "id": bid, "t0": 0, "t1": dd, "lado": lado, "items": items})
                sonidos.append({"t": t0 - 0.06, "sonido": "aire", "db": -3})

            else:  # herramienta
                svg = logo_svg(b.get("logo") or b.get("titulo", ""))
                C = 300
                canvas = (f'<canvas id="{bid}-c" width="{C}" height="{C}" style="left:{101 - C / 2:.0f}px;'
                          f'top:{101 - C / 2:.0f}px;width:{C}px;height:{C}px"></canvas>')
                hueco = '<div class="hueco"></div>'
                if not svg:
                    ini = monograma({"canal": {"marca": b.get("titulo", "")}})
                    hueco = (f'<div class="hueco" style="display:flex;align-items:center;justify-content:center;'
                             f'font-family:var(--f-tit);font-weight:800;font-size:54px;color:var(--principal)">'
                             f'{esc(ini)}</div>')
                    canvas = ""
                partes.append(
                    f'<div class="clip bloque herr persp" {clip} style="{pos}">{halo}'
                    f'<div class="vidrio" id="{bid}-v"><span class="brillo" id="{bid}-br"></span>{hueco}'
                    f'<div><div class="nombre" id="{bid}-n">{esc(b.get("titulo", ""))}</div>'
                    + (f'<div class="sub" id="{bid}-s">{esc(b.get("subtitulo", ""))}</div>' if b.get("subtitulo") else
                       f'<div class="sub" id="{bid}-s"></div>')
                    + f'</div>{canvas}</div></div>')
                beats_js.append({"tipo": "herramienta", "id": bid, "t0": 0, "t1": dd, "lado": lado})
                if svg:
                    piezas3d.append({"tipo": "herr", "canvas": f"{bid}-c", "w": C, "h": C, "t0": t0 + 0.15,
                                     "t1": t1, "svg": svg, "principal": principal, "acento": acento,
                                     "llegada": 0.9, "metal": 0.15, "rugosidad": 0.3, "distancia": 7.6})
                for x in b.get("titulo", "").split():
                    claves_globales.add(norm_w(x))
                sonidos += [{"t": t0 - 0.06, "sonido": "aire", "db": -3}, {"t": t0 + 0.95, "sonido": "sub", "db": -4}]

        elif tipo == "transicion":
            t0 = max(0.0, i - 0.3)
            dd = min(0.9, duracion - t0)
            partes.append(f'<div class="clip trans" id="{bid}" data-start="{t0:.3f}" data-duration="{dd:.3f}" '
                          f'data-track-index="5"><div class="giro"><div class="haz" id="{bid}-h"></div></div></div>')
            beats_js.append({"tipo": "transicion", "id": bid, "t0": 0, "t1": dd})
            sonidos += [{"t": i - 1.15, "sonido": "subida", "db": -2}, {"t": i - 0.18, "sonido": "whoosh", "dur": 0.7},
                        {"t": i + 0.04, "sonido": "sub", "db": -5}]

    # ---------------------------------------------------------- subtítulos
    subs_js = []
    if plan.get("subtitulos", True) and palabras:
        cfg = marca.get("subtitulos", {})
        max_pal = cfg.get("palabras_por_linea_vertical" if vert else "palabras_por_linea_horizontal", 4 if vert else 6)
        grupos = agrupar(palabras, max_pal, 20 if vert else 38)
        if vert:
            # bajo la barbilla, por debajo de los textos destacados y por encima de los botones de la app
            sub_pos = "top:1475px"
        else:
            sub_pos = "bottom:76px"
        # subtítulos SOLO en los momentos que lo piden: tramos de beats con «subtitulo» (o los recursos
        # que no dicen nada con palabras). Nunca a la vez que un gráfico que dice lo mismo.
        modo = plan.get("subtitulos", True)
        modo_pl = pl.get("subtitulos", {}).get("modo", "momentos")
        if modo is True and not e["cajas"]:
            modo = modo_pl
        if modo == "nunca":
            grupos = []
        elif modo == "siempre":
            # subtítulos seguidos y cortos, pero nunca a la vez que un gráfico que ya lo dice con palabras
            mudos = [(a, b_) for a, b_, sub in ventana_sub.values() if not sub]
            # (el B-roll sí lleva subtítulos: tapa la cámara, pero la voz sigue)
            grupos = [g for g in grupos if not any(g[0]["s"] < b_ and g[-1]["e"] > a for a, b_ in mudos)]
        elif modo == "momentos":
            # cada subtítulo es UNA frase completa (de signo a signo de puntuación) que cabe entera
            # en un tramo marcado con «sí»; nunca un trozo cortado
            ventanas = [v for v in ventana_sub.values() if v[2]]
            grupos = [f for f in frases_subtitulo(palabras)
                      if any(frase_cabe(f, a, b_) for a, b_, _x in ventanas) and len(f) >= 3]
        for g_i, g in enumerate(grupos):
            gs = max(0.0, g[0]["s"] - 0.06)
            sig = grupos[g_i + 1][0]["s"] - 0.06 if g_i + 1 < len(grupos) else duracion
            ge = min(max(g[-1]["e"] + 0.3, gs + 0.7), sig, duracion)
            if ge - gs < 0.15:
                continue
            spans, ws = [], []
            for k, w in enumerate(g):
                clave = norm_w(w["w"]) in claves_globales or numero_de(w["w"]) is not None
                cls = "w clave" if clave else "w"
                spans.append(f'<span class="{cls}" id="s{g_i}w{k}">{esc(w["w"])}<span class="caja"></span></span>')
                ws.append({"t": round(max(w["s"], gs) - gs, 3), "clave": clave})
            partes.append(f'<div class="clip sub" id="s{g_i}" data-start="{gs:.3f}" data-duration="{ge - gs:.3f}" '
                          f'data-track-index="1" style="{sub_pos}"><div class="linea" id="s{g_i}l">{"".join(spans)}</div></div>')
            subs_js.append({"t0": 0, "t1": round(ge - gs, 3), "w": ws})

    # sonidos de marca: «dinero» -> caja.wav (marca/sonidos/mapa.json)
    try:
        import sonido as S
        sonidos += S.sonidos_de_marca(palabras)
    except Exception as ex:  # sin numpy (fuera del entorno del kit) no se añaden
        aviso(f"No he podido leer los sonidos de marca ({type(ex).__name__}).")

    # los tiempos de cada clip son locales: GSAP necesita el desplazamiento global
    inicios = re.findall(r'id="([^"]+)" data-start="([\d.]+)"', "\n".join(partes))
    inicio_de = {k: float(v) for k, v in inicios}
    for bj in beats_js:
        if bj.pop("_global", False):  # los recursos ya llegan con tiempos del vídeo
            continue
        base = inicio_de.get(bj["id"], 0.0)
        desplazar(bj, base)
    for g_i, sj in enumerate(subs_js):
        desplazar(sj, inicio_de.get(f"s{g_i}", 0.0), claves=("t0", "t1"))
        for w in sj["w"]:
            w["t"] = round(w["t"] + inicio_de.get(f"s{g_i}", 0.0), 3)

    conf = {"dur": duracion, "formato": formato, "estilo": e["nombre"], "beats": beats_js, "subs": subs_js, "W": W, "H": H,
            "colores": {"texto": c.get("texto", "#ffffff"), "principal": principal, "acento": acento,
                        "panel": c.get("panel", "#070b09")}}
    variables = {
        "--principal": principal, "--principal-rgb": rgb(principal), "--acento": acento, "--acento-rgb": rgb(acento),
        "--texto": c.get("texto", "#ffffff"), "--panel": c.get("panel", "#070b09"), "--panel-rgb": rgb(tono_panel(c.get("panel", "#070b09"))),
        "--f-tit": f"'{e['tit']}'", "--f-txt": f"'{e['txt']}'", "--f-rem": f"'{e['rem']}'", "--f-mono": f"'{e['mono']}'",
        "--f-sub": f"'{e['tit'] if e['sub'] == 'tit' else e['txt']}'",
        "--rem-estilo": "italic" if e["nombre"] == "editorial" else "normal",
        "--rem-peso": "600" if e["nombre"] == "editorial" else str(e["peso_tit"]),
        "--peso-tit": str(e["peso_tit"]), "--track-tit": e["track"], "--mayus-tit": e["mayus"],
        "--peso-sub": str(e["peso_sub"]), "--mayus-sub": e["mayus_sub"] if not marca.get("subtitulos", {}).get("mayusculas") else "uppercase",
        "--radio": f"{int(e['radio'] * T['radio_k'])}px",
        "--dest": f"{T['dest']}px", "--dest-max": f"{T['dest_max']}px", "--kicker": f"{T['kicker']}px",
        "--fila": f"{T['fila']}px", "--rot-nombre": f"{int(T['rot_nombre'] * (1.4 if not e['cajas'] else 1))}px",
        "--rot-handle": f"{int(T['rot_handle'] * (1.4 if not e['cajas'] else 1))}px",
        "--logo-h": f"{T['logo_h']}px", "--logo-txt": f"{T['logo_txt']}px", "--herr-nombre": f"{T['herr_nombre']}px",
        "--sub": f"{int(T['sub'] * min(esc_txt, 1.25))}px", "--sub-max": f"{T['sub_max']}px",
        "--f-serif": "'Instrument Serif'", "--crema": c.get("crema", "#F2EDE3"),
        "--t-kicker": f"{int((26 if not vert else 40) * esc_txt)}px",
        "--t-nombre-logo": f"{int(60 * esc_txt)}px",
        "--t-remate": f"{int((72 if not vert else 64) * esc_txt)}px",
        "--t-fase": f"{int((74 if not vert else 56) * min(esc_txt, 1.15))}px",
        "--t-cap": f"{int((84 if not vert else 76) * esc_txt)}px", "--t-etq": f"{int((84 if not vert else 72) * esc_txt)}px",
        "--t-etiqueta": f"{int((50 if not vert else 54) * esc_txt)}px",
    }
    raiz = ";".join(f"{k}:{v}" for k, v in variables.items())
    html_txt = pagina(W, H, duracion, raiz, "\n".join(partes), conf, piezas3d,
                      clase=("" if e["cajas"] else ("sin-cajas editorial" if e["nombre"] == "dia-editorial" else "sin-cajas"))
                      + (" vertical" if vert else ""))
    return html_txt, sonidos, detras, extra


def desplazar(obj: dict, base: float, claves=("t0", "t1")) -> None:
    for k in claves:
        if k in obj:
            obj[k] = round(obj[k] + base, 3)
    for p in obj.get("palabras", []) + obj.get("items", []):
        p["t"] = round(p["t"] + base, 3)


def pagina(W: int, H: int, duracion: float, raiz: str, cuerpo: str, conf: dict, piezas3d: list[dict],
           motor: str = "motor.js", extra_js: str = "", clase: str = "") -> str:
    tres = ""
    if piezas3d:
        tres = ('<script type="importmap">{"imports":{"three":"./three/three.module.js",'
                '"three/addons/":"./three/addons/"}}</script>\n'
                f'<script>window.CAPA3D = {json.dumps(piezas3d, ensure_ascii=False)};</script>\n'
                '<script type="module" src="motor3d.js"></script>')
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width={W}, height={H}">
<title>Capa de animaciones</title>
<script src="gsap.min.js"></script>
<link rel="stylesheet" href="capa.css">
<style>{fuentes_css()}
#root{{width:{W}px;height:{H}px;{raiz}}}</style>
</head>
<body>
<div id="root" class="{clase}" data-composition-id="capa" data-start="0" data-width="{W}" data-height="{H}" data-duration="{duracion:.3f}">
{cuerpo}
</div>
<script>window.CAPA = {json.dumps(conf, ensure_ascii=False)};</script>
<script>
{(CAPA / motor).read_text(encoding="utf-8")}
</script>
{extra_js}
{tres}
</body>
</html>
"""


# ------------------------------------------------------------------ capa de profundidad (por detrás)
ENTRADAS = ["alzar", "profundo", "golpe", "giro"]


def a_detras(b: dict) -> dict:
    """Un destacado o una herramienta, convertidos en énfasis por detrás de la persona."""
    n = dict(b, tipo="profundidad")
    texto = b.get("enfasis") or (b.get("titulo") if b["tipo"] == "herramienta" else b.get("texto")) or ""
    if b["tipo"] == "destacado" and len(texto) > 14 and not b.get("enfasis"):
        texto = b.get("resaltar") or texto
    n["texto"] = texto
    if b["tipo"] == "herramienta":
        n["logo"] = b.get("logo") or b.get("titulo")
    return n


def _hsl(h: str):
    import colorsys
    r, g, b_ = (x / 255 for x in hex_a_rgb(h))
    return colorsys.rgb_to_hls(r, g, b_)


def _de_hsl(hh, l, s_) -> str:
    import colorsys
    r, g, b_ = colorsys.hls_to_rgb(hh % 1.0, l, s_)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b_ * 255))


def paleta_enfasis(marca: dict) -> list[str]:
    """Colores de los énfasis: los de la marca y tres más con la misma luz y saturación que el
    principal (la paleta se nota coherente). Se puede fijar en brand.json: "paleta_enfasis"."""
    if marca.get("paleta_enfasis"):
        return list(marca["paleta_enfasis"])
    if not marca.get("multicolor"):
        return [color_acento(marca)]
    c = marca["colores"]
    h, l, s_ = _hsl(c["principal"])
    l = min(max(l, 0.55), 0.68)
    s_ = max(s_, 0.7)
    return [c["principal"], c["acento"], _de_hsl(h + 0.42, l, s_), _de_hsl(h - 0.4, l + 0.02, s_),
            _de_hsl(h + 0.22, l, s_)]


def color_acento(marca: dict) -> str:
    c = marca["colores"]
    return marca.get("color_enfasis") or c.get("acento") or c["principal"]


RECURSOS = ("tachado", "logos", "golpe3d", "contador", "fases", "terminal", "barrido", "cine", "capitulo",
            "luz", "subtitulo", "broll", "pantalla", "zoom", "etiqueta")
ALIAS = {"texto_detras": "profundidad", "palabra": "profundidad"}


def aclarar(h: str, k: float) -> str:
    r, g, b = hex_a_rgb(h)
    return "#%02x%02x%02x" % (int(r + (255 - r) * k), int(g + (255 - g) * k), int(b + (255 - b) * k))

def construir_editorial(marca, b, formato, z, d, acento, esc_txt: float = 1.0, delante: bool = False):
    """Palabra editorial: serif crema y la clave en cursiva coral subrayada. En horizontal va POR
    DETRÁS de la persona, a un lado (la cabeza solo roza el borde, nunca tapa la palabra); en
    vertical, delante y bajo la barbilla, que es donde se lee."""
    W, H = FORMATOS[formato]
    vert = formato == "vertical"
    l1 = (b.get("texto") or "").strip()
    l2 = (b.get("clave") or b.get("texto2") or "").strip()
    cara = z.get("cara")
    if vert:
        ancho = W - 192
        g1 = int(min(ancho / (max(4, len(l1)) * 0.5), 150 * esc_txt))
        g2 = int(min(ancho / (max(3, len(l2)) * 0.5), g1 * 1.35)) if l2 else 0
        top = min(max((cara[3] + 60) if cara else 1080, 900), 1160)
        caja = f"left:96px;right:96px;top:{top:.0f}px;text-align:center"
    else:
        if cara:
            izq, der = cara[0] - 90, W - 90 - cara[2]
            lado = "derecha" if der >= izq else "izquierda"
            # el lado que pide el usuario («esa frase, al otro lado») manda si cabe algo (300 px)
            pref = b.get("posicion")
            if pref in ("izquierda", "derecha") and (izq if pref == "izquierda" else der) >= 300:
                lado = pref
        else:
            lado = b.get("posicion") if b.get("posicion") in ("izquierda", "derecha") else "derecha"
        if lado == "derecha":
            x0 = (cara[2] - 40) if cara else W * 0.52
            ancho = W - 96 - x0
            # alineado al borde de fuera: la cabeza solo roza el arranque de la línea más larga
            caja_x = f"left:{x0:.0f}px;width:{ancho:.0f}px;text-align:right"
        else:
            x1 = (cara[0] + 40) if cara else W * 0.48
            ancho = x1 - 96
            caja_x = f"left:96px;width:{ancho:.0f}px;text-align:left"
        g1 = int(min(ancho / (max(4, len(l1)) * 0.5), H * 0.2 * esc_txt))
        g2 = int(min(ancho / (max(3, len(l2)) * 0.5), g1 * 1.6, H * 0.34 * esc_txt)) if l2 else 0
        alto = g1 * 0.95 + g2 * 0.95
        yc = ((cara[1] + cara[3]) / 2) if cara else H * 0.45
        caja = f"{caja_x};top:{max(40, yc - alto * 0.55):.0f}px"
    sub = ('<svg class="sub-ed" viewBox="0 0 100 10" preserveAspectRatio="none" style="width:100%">'
           '<path id="dt-s" pathLength="1" d="M1 6 C 25 3, 55 9, 99 5"/></svg>') if l2 else ""
    cuerpo = (f'<div class="clip detras" id="dt" data-start="0" data-duration="{d:.3f}" data-track-index="1" '
              f'style="display:block"><div class="ed" id="dt-g" style="position:absolute;{caja};--gig1:{g1}px;--gig2:{g2}px;'
              f'text-shadow:{"0 2px 4px rgba(0,0,0,0.85),0 0 18px rgba(0,0,0,0.7),0 0 42px rgba(0,0,0,0.45)" if vert else "0 12px 40px rgba(0,0,0,0.35)"}">'
              f'<span class="l1">{letras_span(l1)}</span>'
              + (f'<span class="l2" style="display:inline-block">{letras_span(l2)}{sub}</span>' if l2 else "")
              + '</div></div>')
    variables = (f"--principal:{acento};--principal-rgb:{rgb(acento)};--f-serif:'Instrument Serif';"
                 f"--crema:{marca['colores'].get('crema', '#F2EDE3')}")
    js = ("<script>(function(){const tl=window.__timelines['capa'];"
          "tl.fromTo('#dt-g .l1 .l',{autoAlpha:0,y:60,filter:'blur(14px)'},"
          "{autoAlpha:1,y:0,filter:'blur(0px)',duration:0.55,stagger:0.018,ease:'expo.out'},0.02);"
          "tl.fromTo('#dt-g .l2 .l',{autoAlpha:0,y:50,scale:1.15,filter:'blur(12px)'},"
          "{autoAlpha:1,y:0,scale:1,filter:'blur(0px)',duration:0.6,stagger:0.03,ease:'expo.out'},0.18);"
          + ("tl.fromTo('#dt-s',{strokeDashoffset:1},{strokeDashoffset:0,duration:0.45,ease:'power2.inOut'},0.55);" if l2 else "")
          + "tl.to('#dt-g',{autoAlpha:0,y:-24,filter:'blur(12px)',duration:0.32,ease:'power2.in'},%.2f);"
          "})();</script>") % max(0.5, d - 0.36)
    conf = {"dur": d, "beats": [], "subs": [], "colores": {}}
    sonidos = [{"t": 0.0, "sonido": "aire", "db": -4}, {"t": 0.22, "sonido": "sub", "db": -6}]
    return pagina(W, H, d, variables, cuerpo, conf, [], extra_js=js), sonidos, {"delante": vert or delante}


def letras_span(t: str) -> str:
    return "".join(f'<span class="l">{esc(ch) if ch != " " else "&nbsp;"}</span>' for ch in t)


def construir_detras(marca: dict, b: dict, formato: str, pers, plan, iv, proyecto: Path,
                     duracion: float, pl: dict | None = None) -> tuple[str, list[dict], dict]:
    W, H = FORMATOS[formato]
    vert = formato == "vertical"
    c = marca["colores"]
    e = estilo_de(marca)
    texto = (b.get("texto") or "").strip()
    d = float(b["duracion"])
    z = zonas(formato, pers, plan, b["inicio"], b["inicio"] + d, iv)
    # centro vertical del título: en horizontal, a la altura de la frente (la cabeza tapa una parte);
    # en vertical la cara ocupa casi todo el ancho, así que va como la cabecera de una portada de
    # revista: encima de la cabeza, con el pelo tapando solo el pie de las letras.
    n_car = max(3, len(texto))
    if vert:
        cap = min(W * 0.92 / (n_car * 0.62) * 0.72, 250)
        tope = z["cara"][1] if z.get("cara") else H * 0.12
        yc = max(tope - 0.2 * cap, cap / 2 + 110)  # por debajo de la barra de arriba de la app
    elif z.get("cara"):
        yc = z["cara"][1] + (z["cara"][3] - z["cara"][1]) * 0.42
    else:
        yc = H * 0.36
    estilo3d = False  # el 3D extruido de la v2 ya no se usa: para un golpe 3D está el recurso «golpe3d»
    if e["nombre"] == "dia-editorial":
        pl = pl or {}
        return construir_editorial(marca, b, formato, z, d, color_acento(marca),
                                   float(pl.get("textos", {}).get("escala", 1.0)), not pl.get("detras", True))
    piezas3d, cuerpo = [], ""
    color = b.get("color") or color_acento(marca)
    entrada = b.get("entrada") or "alzar"
    golpe = {"alzar": 0.42, "profundo": 0.5, "golpe": 0.32, "giro": 0.5}.get(entrada, 0.42)
    sonidos = [{"t": -0.05, "sonido": "whoosh", "dur": 0.75, "db": 0}, {"t": golpe, "sonido": "sub", "db": 0}]
    variables = (f"--principal:{color};--principal-rgb:{rgb(color)};--f-tit:'{e['tit']}';"
                 f"--acento-rgb:{rgb(c['acento'])}")
    fj = fuente_3d(e, texto, proyecto / "fuente3d.json") if estilo3d else None
    if estilo3d and fj:
        alto_c = int(H * (0.62 if not vert else 0.3))
        top = int(min(max(yc - alto_c / 2, 0), H - alto_c))
        cuerpo = (f'<div class="clip detras" id="dt" data-start="0" data-duration="{d:.3f}" data-track-index="1">'
                  f'<canvas id="dt-c" width="{W}" height="{alto_c}" style="top:{top}px;height:{alto_c}px;'
                  f'width:{W}px"></canvas></div>')
        piezas3d.append({"tipo": "titulo", "canvas": "dt-c", "w": W, "h": alto_c, "t0": 0.0, "t1": d,
                         "texto": texto.upper(), "fuente": fj, "principal": color, "acento": c["acento"],
                         "cara": aclarar(color, 0.18), "canto": oscurecer(color, 0.42), "metal": 0.25,
                         "emisivo": color, "emisivoFuerza": 0.12, "entrada": entrada, "svg": b.get("svg"),
                         "rugosidad": 0.3, "ocupa": 0.74 if not vert else 0.8, "camY": 0.0,
                         "alto": -0.36, "desplazaY": (yc - (top + alto_c / 2)) / alto_c,
                         "capMax": (0.3 * H if not vert else 230) / alto_c})
        conf = {"dur": d, "beats": [], "subs": [], "colores": {}}
        js = ""
    else:
        # plano: blanco + segunda línea en el acento, las dos por detrás de la persona
        l1 = texto.upper()
        l2 = (b.get("texto2") or "").strip().upper()
        ancho = W * (0.86 if not vert else 0.92)
        tope = (0.3 * H if not vert else 170) / 0.72
        g1 = int(min(ancho / (max(3, len(l1)) * 0.66), tope))
        g2 = int(min(ancho / (max(3, len(l2)) * 0.66), g1 * 0.82)) if l2 else 0
        en_linea = bool(l2 and (vert or len(l2) <= 5))  # una palabra corta abajo la taparía la cabeza
        if en_linea:
            # en vertical no hay sitio para dos líneas encima de la cabeza: una sola, con la
            # segunda parte en el acento
            g1 = g2 = int(min(ancho / ((len(l1) + len(l2) + 1) * 0.66), tope))
        alto_bloque = g1 * 0.92 + (g2 * 0.94 if l2 and not en_linea else 0)
        top = max(110 if vert else 20, (yc - alto_bloque * (0.5 if not vert else 0.62)))
        linea2 = f'<span class="l2"{" style=\"display:inline\"" if en_linea else ""}>{letras_span(l2)}</span>' if l2 else ""
        cuerpo = (f'<div class="clip detras" id="dt" data-start="0" data-duration="{d:.3f}" data-track-index="1" '
                  f'style="align-items:flex-start"><div class="dos-lineas" id="dt-g" style="--gig1:{g1}px;--gig2:{g2}px;'
                  f'margin-top:{top:.0f}px;text-shadow:0 20px 50px rgba(0,0,0,0.35)">'
                  f'<span class="l1"{" style=\"display:inline\"" if en_linea else ""}>{letras_span(l1 + (" " if en_linea else ""))}</span>{linea2}</div></div>')
        conf = {"dur": d, "beats": [], "subs": [], "colores": {}}
        js = ("<script>(function(){const tl=window.__timelines['capa'];"
              "tl.fromTo('#dt-g .l1 .l',{autoAlpha:0,y:140,scale:1.3,filter:'blur(20px)'},"
              "{autoAlpha:1,y:0,scale:1,filter:'blur(0px)',duration:0.8,stagger:0.035,ease:'expo.out'},0.02);"
              "tl.fromTo('#dt-g .l2 .l',{autoAlpha:0,y:90,filter:'blur(16px)'},"
              "{autoAlpha:1,y:0,filter:'blur(0px)',duration:0.7,stagger:0.03,ease:'expo.out'},0.22);"
              "tl.fromTo('#dt-g',{scale:1.05},{scale:1,duration:%.2f,ease:'power1.out'},0);"
              "tl.to('#dt-g .l',{autoAlpha:0,y:-50,filter:'blur(14px)',duration:0.35,stagger:0.015,ease:'power2.in'},%.2f);"
              "})();</script>") % (d, max(0.5, d - 0.5))
    raiz = variables
    return pagina(W, H, d, raiz, cuerpo, conf, piezas3d, extra_js=js), sonidos, {"yc": yc}


# ------------------------------------------------------------------ piezas pequeñas
# palabras con las que un trozo de subtítulo no debe acabar («conocer tu | proyecto»)
DEBILES_SUB = {"de", "del", "la", "el", "los", "las", "un", "una", "unos", "unas", "tu", "tus", "su", "sus", "mi",
               "mis", "a", "al", "en", "con", "por", "para", "que", "qué", "y", "o", "u", "e", "ni", "se", "te", "me",
               "lo", "le", "nos", "les", "si", "no", "muy", "más", "tan"}


def agrupar(palabras: list[dict], max_pal: int, max_car: int) -> list[list[dict]]:
    """Subtítulos en trozos cortos y con sentido. Cada frase (de signo a signo, o hasta una pausa
    larga) se reparte en trozos de hasta max_pal palabras: mejor en una coma, nunca justo después
    de un artículo o una preposición y sin una palabra suelta al final («datos.»)."""
    frases, actual = [], []
    for w in palabras:
        if actual and w["s"] - actual[-1]["e"] > 0.45:
            frases.append(actual)
            actual = []
        actual.append(w)
        if re.search(r"[.!?…:]$", w["w"]):
            frases.append(actual)
            actual = []
    if actual:
        frases.append(actual)

    def debil(w: dict) -> bool:
        return re.sub(r"[^\wáéíóúüñ]", "", w["w"].lower()) in DEBILES_SUB

    def coste(f: list[dict], j: int, i: int) -> float:
        t = f[j:i]
        c = abs(len(t) - min(max_pal, 3.5)) * 0.6  # lo ideal: unas 3 o 4 palabras
        if sum(len(x["w"]) + 1 for x in t) - 1 > max_car:
            c += 100
        if len(t) == 1 and not re.search(r"[,;.!?…:]$", t[0]["w"]):
            c += 8
        if re.search(r"[,;]$", t[-1]["w"]):
            c -= 2
        elif debil(t[-1]):
            c += 4
        elif i < len(f) and debil(f[i]):  # cortar justo antes de «si», «y», «con»… es natural
            c -= 0.5
        return c

    grupos = []
    for f in frases:  # el reparto más barato de cada frase (programación dinámica)
        n = len(f)
        mejor, corte = [0.0] + [float("inf")] * n, [0] * (n + 1)
        for i in range(1, n + 1):
            for j in range(max(0, i - max_pal), i):
                v = mejor[j] + coste(f, j, i)
                if v < mejor[i]:
                    mejor[i], corte[i] = v, j
        trozos, i = [], n
        while i > 0:
            trozos.append(f[corte[i]:i])
            i = corte[i]
        grupos += trozos[::-1]
    return grupos


def monograma(marca: dict) -> str:
    """«D-IA · El Campamento» -> «D-IA»; «Laura Gómez» -> «LG»."""
    nombre = marca["canal"].get("marca") or marca["canal"].get("nombre", "")
    tokens = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ0-9][\w-]*", nombre)
    if not tokens:
        return "·"
    if len(tokens[0]) <= 4 and (tokens[0].isupper() or "-" in tokens[0]):
        return tokens[0]
    return "".join(t[0] for t in tokens[:2]).upper()


def oscurecer(h: str, k: float) -> str:
    r, g, b = hex_a_rgb(h)
    return "#%02x%02x%02x" % (int(r * k), int(g * k), int(b * k))


def tono_panel(h: str) -> str:
    """El panel de cristal: el color oscuro de la marca, algo levantado para que no sea un agujero."""
    r, g, b = hex_a_rgb(h)
    return "#%02x%02x%02x" % (min(255, r + 10), min(255, g + 14), min(255, b + 14))


def preparar_proyecto(dest: Path, marca: dict, con_3d: bool = True) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    if not GSAP.exists():
        fallo("Falta GSAP.", "Lanza /empezar (o: python3 herramientas/kit.py instalar).")
    shutil.copy(GSAP, dest / "gsap.min.js")
    for f in ("capa.css", "motor3d.js"):
        shutil.copy(CAPA / f, dest / f)
    if (MARCA / "fuentes").exists():
        shutil.copytree(MARCA / "fuentes", dest / "fuentes")
    if con_3d and THREE.exists():
        t = dest / "three"
        (t / "addons").mkdir(parents=True)
        for f in ("three.module.js", "three.core.js"):
            shutil.copy(THREE / "build" / f, t / f)
        for f in ("loaders/FontLoader.js", "loaders/SVGLoader.js", "geometries/TextGeometry.js",
                  "environments/RoomEnvironment.js"):
            (t / "addons" / Path(f).parent).mkdir(parents=True, exist_ok=True)
            shutil.copy(THREE / "examples" / "jsm" / f, t / "addons" / f)


def hyperframes(*args: str, cwd: Path | None = None, comprobar: bool = True):
    if not HF.exists():
        fallo("HyperFrames no está instalado en el kit.", "Lanza /empezar (o: python3 herramientas/kit.py instalar).")
    return ejecutar(["node", str(HF), *args], cwd=cwd, comprobar=comprobar, env=entorno_hyperframes())


def revisar(proyecto: Path) -> None:
    lint = hyperframes("lint", str(proyecto), "--json", comprobar=False)
    try:
        datos = json.loads(lint.stdout[lint.stdout.index("{"):])
        errores = datos.get("errorCount", datos.get("errors", 0))
        if isinstance(errores, list):
            errores = len(errores)
    except Exception:
        errores = 0 if lint.returncode == 0 else 1
    if errores:
        print(lint.stdout[-2500:])
        fallo(f"La animación {proyecto.name} tiene errores de HyperFrames (arriba el detalle).")


def main(argv: list[str]) -> None:
    if not argv:
        fallo("Uso: kit.py animar <video> [--formato horizontal|vertical] [--desde S --hasta S --nombre N]")
    video = resolver_video(argv[0])
    opts = {argv[k].lstrip("-"): argv[k + 1] for k in range(1, len(argv) - 1, 2)}
    trabajo = carpeta_trabajo(video)
    plan = leer_json(trabajo / "plan.json")
    if not plan.get("aprobado"):
        fallo("El plan todavía no está aprobado.",
              "Enseña la tabla (kit.py plan tabla) y espera el OK antes de animar.")
    nombre_pl = E.nombre_activo(plan, opts.get("plantilla"), reel=bool(opts.get("nombre")))
    pl = E.cargar(nombre_pl)
    marca = E.aplicar_a_marca(cargar_marca(), pl)
    print(f"   Plantilla: {nombre_pl}", flush=True)
    pc = leer_json(trabajo / "palabras_cortado.json")
    formatos = [opts["formato"]] if "formato" in opts else plan["formatos"]
    pers = P.asegurar(video, trabajo) if (trabajo / "cortado.mp4").exists() else None
    iv = info_video(trabajo / "cortado.mp4") if (trabajo / "cortado.mp4").exists() else None

    desde = float(opts.get("desde", 0))
    hasta = float(opts.get("hasta", pc["duracion"]))
    nombre = opts.get("nombre")
    palabras = [dict(w, s=round(w["s"] - desde, 3), e=round(w["e"] - desde, 3))
                for w in pc["palabras"] if desde <= w["s"] < hasta]
    duracion = round(hasta - desde, 3)
    if nombre:  # reel: logo, subtítulos y las piezas que caigan dentro
        plan_local = dict(plan, beats=[dict(b, inicio=round(b["inicio"] - desde, 3)) for b in plan["beats"]
                                       if b["tipo"] not in ("logo", "rotulo") and "inicio" in b
                                       and desde <= b["inicio"] < hasta - 1])
        plan_local["beats"].insert(0, {"id": "logo", "tipo": "logo", "inicio": 0.2, "duracion": 4.0})
        if pers:
            pers = recortar_persona(pers, desde, hasta)
    else:
        plan_local = plan

    trabajos = []
    for formato in formatos:
        etiqueta = f"{nombre}-{formato}" if nombre else formato
        paso(f"Preparando la capa {etiqueta} ({duracion:.1f} s)")
        proyecto = trabajo / f"hf-{etiqueta}"
        preparar_proyecto(proyecto, marca)
        html_txt, sonidos, detras, extra = construir(marca, plan_local, palabras, duracion, formato, pers, iv,
                                                     proyecto, trabajo / "cortado.mp4", pl)
        (proyecto / "index.html").write_text(html_txt, encoding="utf-8")
        revisar(proyecto)
        trabajos.append((etiqueta, proyecto, trabajo / f"capa-{etiqueta}.mov"))
        capas_detras = []
        for b in detras:
            pid = re.sub(r"[^a-zA-Z0-9_-]", "", b["id"])
            pd = trabajo / f"hf-{etiqueta}-detras-{pid}"
            preparar_proyecto(pd, marca)
            h2, son2, info = construir_detras(marca, b, formato, pers, plan_local, iv, pd, duracion, pl)
            b = dict(b, delante=bool(info.get("delante")))
            (pd / "index.html").write_text(h2, encoding="utf-8")
            revisar(pd)
            salida = trabajo / f"detras-{etiqueta}-{pid}.mov"
            trabajos.append((f"{etiqueta} · por detrás «{b.get('texto', '')}»", pd, salida))
            sonidos += [dict(s, t=round(s["t"] + b["inicio"], 3)) for s in son2]
            capas_detras.append({"id": pid, "inicio": b["inicio"], "duracion": b["duracion"],
                                 "capa": salida.name, "atenuar": b.get("atenuar", 0.35),
                                 "opaca": b.get("estilo") == "halo", "delante": b.get("delante", False)})
        escribir_json(trabajo / f"eventos-{etiqueta}.json", {
            "sonidos": sorted(sonidos, key=lambda s: s["t"]), "detras": capas_detras,
            "camara": camara_de(plan_local, duracion, pl) + [{"tipo": "latigo", "t": t} for t in extra["latigos"]],
            "barridos": extra["barridos"], "vinetas": extra["vinetas"], "broll": extra["broll"],
            "tapan": extra["tapan"], "plantilla": nombre_pl, "zooms": pl["zooms"],
            "transicion": pl["transiciones"]["tipo"], "musica": pl["musica"],
            "nivel_efectos": float(pl.get("sonidos", {}).get("nivel", 1.0)),
            "duracion": duracion, "desde": desde, "hasta": hasta})
        ok(f"Capa {etiqueta} revisada con hyperframes lint ({len(detras)} momento(s) de profundidad)")

    # todo se renderiza a la vez: con dos formatos tarda casi lo mismo que con uno
    paso(f"Renderizando {len(trabajos)} capa(s) con HyperFrames (fondo transparente)…")
    env = dict(os.environ, HYPERFRAMES_TELEMETRY="0", DO_NOT_TRACK="1")
    with Cronometro(trabajo, "animar-" + "+".join(t[0].split(" ")[0] for t in trabajos[:1]) + (
            f"+{len(trabajos) - 1}" if len(trabajos) > 1 else "")):
        # como mucho 4 renders a la vez: cada uno abre su navegador
        max_a_la_vez = max(2, min(4, (os.cpu_count() or 4) // 3))
        pendientes = list(trabajos)
        activos: list = []
        while pendientes or activos:
            while pendientes and len(activos) < max_a_la_vez:
                t = pendientes.pop(0)
                activos.append((t, subprocess.Popen(
                    ["node", str(HF), "render", str(t[1]), "--format", "mov", "--fps", "30", "--quality",
                     "standard", "--output", str(t[2]), "--quiet"], stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", env=env)))
            (etiqueta, _, salida), proc = activos.pop(0)
            log = proc.communicate()[0] or ""
            if proc.returncode != 0 or not salida.exists() or salida.stat().st_size == 0:
                print(log[-2500:])
                fallo(f"El render de la capa {etiqueta} ha fallado.", "Lanza /comprobar para ver qué falta.")
            ok(f"Capa lista: {salida.name}")


SIN_GOLPE = ("transicion", "subtitulo", "zoom", "broll", "pantalla", "rotulo", "logo", "cine", "luz")


def camara_de(plan: dict, duracion: float, pl: dict | None = None) -> list[dict]:
    """Movimientos de cámara que pide el plan: empujes suaves en las piezas y en los cortes, los
    golpes de zoom de la plantilla y los zooms pedidos por frase («acércate cuando digo X»)."""
    movs = []
    z = (pl or {}).get("zooms", {})
    emp = float(z.get("empuje", 0.05))
    for b in plan.get("beats", []):
        if "inicio" not in b:
            continue
        t, d = float(b["inicio"]), float(b.get("duracion", 3))
        # zoom pedido a mano: un beat «zoom» o el campo «camara» en cualquier beat
        modo = b.get("modo") if b["tipo"] == "zoom" else b.get("camara")
        if modo in ("acercar", "zoom in", "zoom-in"):
            movs.append({"tipo": "empuje", "t": t - 0.05, "d": d, "zoom": float(b.get("zoom", 0.10))})
        elif modo in ("alejar", "zoom out", "zoom-out"):
            movs.append({"tipo": "alejar", "t": t, "d": d, "zoom": float(b.get("zoom", 0.12))})
        elif modo == "golpe":
            movs.append({"tipo": "golpe", "t": t - 0.03, "d": min(d, 1.4), "zoom": float(b.get("zoom", 0.09))})
        elif z.get("golpes") and b["tipo"] not in SIN_GOLPE:
            movs.append({"tipo": "golpe", "t": t - 0.03, "d": min(d, 1.2), "zoom": float(z.get("golpe_zoom", 0.07))})
        if b["tipo"] == "zoom":
            continue
        if b["tipo"] in ("destacado", "lista", "herramienta", "titulo", "iconos", "referencias", "notificacion"):
            movs.append({"tipo": "empuje", "t": t, "d": d, "zoom": emp})
        elif b["tipo"] in ("visor",):
            movs.append({"tipo": "empuje", "t": t, "d": d, "zoom": emp * 0.6})
        elif b["tipo"] in ("profundidad", "texto_detras", "halo"):
            movs.append({"tipo": "empuje", "t": t - 0.1, "d": d, "zoom": emp * 1.6, "lento": True})
        elif b["tipo"] == "transicion":
            movs.append({"tipo": "latigo", "t": t})
    return movs


def recortar_persona(pers: dict, desde: float, hasta: float) -> dict:
    f = pers["fps_muestreo"]
    a, b = int(desde * f), int(hasta * f) + 1
    out = dict(pers)
    out["muestras"] = [dict(m, t=round(m["t"] - desde, 3)) for m in pers["muestras"][a:b]]
    out["pista"] = pers["pista"][a:b]
    out["escenas"] = [round(t - desde, 2) for t in pers["escenas"] if desde < t < hasta]
    out["duracion"] = hasta - desde
    return out


if __name__ == "__main__":
    main(sys.argv[1:])

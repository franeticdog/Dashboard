"""Fase 3 · Planificar los beats: «cuando digas X, entra Y».

  kit.py plan borrador <video> [--plantilla N] -> crea trabajo/<video>/plan.json (rótulo, transiciones,
                                   la plantilla elegida y sugerencias de logos y sonidos de marca)
  kit.py plan buscar <video> "frase"  -> dice en qué segundo exacto dices esa frase
  kit.py plan tabla <video>      -> resuelve los tiempos y enseña la tabla para dar el OK
  kit.py plan aprobar <video>    -> marca el plan como aprobado (solo tras el OK del usuario)

Cada beat puede llevar "cuando": "frase literal del vídeo" y el tiempo se calcula solo.
Nada de cifras inventadas: los textos en pantalla salen de lo que se dice en el vídeo.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
import unicodedata

from comun import (cargar_marca, carpeta_trabajo, escribir_json, fallo, fmt_t, frase_cabe, frases_subtitulo,
                   leer_json,
                   ok, paso, resolver_video, aviso)

DUR_DEFECTO = {"rotulo": 2.2, "destacado": 2.2, "lista": 3.0, "herramienta": 2.4, "profundidad": 2.2,
               "palabra": 2.2, "texto_detras": 2.2, "transicion": 0.8, "tachado": 2.2, "logos": 2.2,
               "golpe3d": 2.2, "contador": 1.6, "fases": 2.8, "terminal": 3.0, "barrido": 4.0, "cine": 3.0,
               "capitulo": 1.8, "luz": 0.5, "subtitulo": 2.0, "broll": 2.2, "pantalla": 2.4, "zoom": 1.2,
               "etiqueta": 2.4}

# qué pone cada recurso en pantalla (columna «Qué aparece» de la tabla)
NOMBRES = {
    "palabra": "Frase editorial POR DETRÁS de ti (serif + clave en cursiva coral)",
    "profundidad": "Frase editorial POR DETRÁS de ti", "texto_detras": "Frase editorial POR DETRÁS de ti",
    "tachado": "Palabra tachada que se sustituye", "logos": "Logo real en 3D (o fila de logos)",
    "golpe3d": "Golpe en 3D con remate en serif (uno por clip)", "contador": "Contador en mono",
    "fases": "Fases numeradas con cabezal", "terminal": "Terminal de Claude Code que se escribe sola",
    "barrido": "Antes / ahora con deslizador", "cine": "Bandas de cine", "capitulo": "Título de capítulo",
    "luz": "Destello cálido", "subtitulo": "Solo subtítulo", "rotulo": "Rótulo con nombre (sin caja)",
    "lista": "Lista con ticks (sin caja)", "destacado": "Frase editorial POR DETRÁS de ti",
    "herramienta": "Logo real en 3D", "transicion": "Transición de luz",
    "broll": "B-roll a pantalla completa (imagen o vídeo de recurso)",
    "pantalla": "Pantalla completa con texto y SVG", "zoom": "Zoom de cámara (sin gráfico)",
    "etiqueta": "Texto pequeño a un lado (antetítulo + frase o lista con ticks, sin caja)",
}
# recursos que se ven (para medir el ritmo que pide la plantilla)
VISIBLES = {"palabra", "tachado", "logos", "golpe3d", "contador", "fases", "terminal", "barrido", "capitulo",
            "broll", "pantalla", "subtitulo", "destacado", "herramienta", "lista", "profundidad", "texto_detras",
            "etiqueta"}
# palabras con las que un texto en pantalla nunca debe acabar
FINALES_PROHIBIDOS = {"de", "del", "que", "y", "o", "en", "para", "como", "con", "a", "al", "el", "la", "los",
                      "las", "un", "una", "por", "su", "sus", "mi", "tu"}


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", "", t)


def buscar_frase(palabras: list[dict], frase: str, desde: float = 0.0):
    objetivo = norm(frase).split()
    if not objetivo:
        return None
    toks = [norm(w["w"]).strip() for w in palabras]
    n = len(objetivo)
    for j in range(len(toks) - n + 1):
        if palabras[j]["s"] < desde:
            continue
        if toks[j:j + n] == objetivo:
            return palabras[j]["s"], palabras[j + n - 1]["e"]
    # coincidencia parcial: las 3 primeras palabras
    if n >= 3:
        for j in range(len(toks) - 2):
            if palabras[j]["s"] >= desde and toks[j:j + 3] == objetivo[:3]:
                return palabras[j]["s"], palabras[min(j + n - 1, len(palabras) - 1)]["e"]
    return None


def borrador(video, plantilla: str | None = None) -> None:
    import estilo as E
    trabajo = carpeta_trabajo(video)
    pc = leer_json(trabajo / "palabras_cortado.json")
    marca = cargar_marca()
    origen = leer_json(trabajo / "origen.json")
    formatos = ["horizontal"] if origen["orientacion"] == "horizontal" else ["vertical"]
    nombre_pl = E.nombre_activo(None, plantilla)
    pl = E.cargar(nombre_pl)
    plan = {
        "plantilla": nombre_pl,
        "formatos": formatos,
        "subtitulos": marca.get("subtitulos", {}).get("activados", True),
        "encuadre_vertical": "auto",
        "beats": [
            {"id": "rotulo", "tipo": "rotulo", "inicio": 1.2, "duracion": 4.5,
             "titulo": marca["canal"]["nombre"], "subtitulo": marca["canal"]["handle"]},
        ],
        "reels": [],
        "aprobado": False,
    }
    # una transición de luz en cada cambio de plano que detecta el análisis de la persona
    try:
        import persona as P
        pers = P.asegurar(video, trabajo)
        tr = pl["transiciones"]
        if tr.get("en_cambios_de_plano", True) and tr.get("tipo") != "corte":
            for k, t in enumerate(pers.get("escenas", [])):
                plan["beats"].append({"id": f"t{k + 1}", "tipo": "transicion", "inicio": t, "duracion": 0.8})
    except Exception as e:  # sin MediaPipe el kit sigue funcionando, solo sin esto
        aviso(f"No he podido buscar los cambios de plano ({type(e).__name__}).")
    escribir_json(trabajo / "plan.json", plan)
    ok(f"Borrador en {trabajo.name}/plan.json (duración del vídeo cortado: {pc['duracion']:.1f} s)")
    print(f"\n   Plantilla «{nombre_pl}» (estilos/{nombre_pl}.md). Lo que pide:")
    for linea in E.en_llano(pl):
        print(f"   · {linea}")
    for linea in sugerencias(pc["palabras"]):
        print(linea)
    print("\n   Ahora Claude elige un recurso para cada frase con \"cuando\" (frase literal del vídeo).")


def sugerencias(palabras: list[dict]) -> list[str]:
    """Qué logos de marca/logos/ se nombran en el vídeo y qué palabras disparan un sonido de marca."""
    from comun import MARCA
    out = []
    logos = {}
    carpeta = MARCA / "logos"
    if carpeta.exists():
        for f in carpeta.iterdir():
            if f.suffix.lower() in (".svg", ".png", ".webp"):
                logos[norm(f.stem.replace("-", " "))] = f.stem
    vistos = set()
    toks = [norm(w["w"]) for w in palabras]
    for i, tk in enumerate(toks):
        for clave, stem in logos.items():
            trozos = clave.split()
            if trozos and toks[i:i + len(trozos)] == trozos and stem not in vistos:
                vistos.add(stem)
                out.append(f"   · Logo disponible: dices «{palabras[i]['w'].strip(',.')}» en {fmt_t(palabras[i]['s'])} "
                           f"-> recurso logos con «{stem}» (sale en 3D)")
    try:
        import sonido as S
        for e in S.sonidos_de_marca(palabras)[:10]:
            out.append(f"   · Sonido de marca: «{e['palabra']}» en {fmt_t(e['t'])} -> {e['archivo'].split('/')[-1]} (sale solo)")
    except Exception:
        pass
    if out:
        out.insert(0, "\n   Sugerencias de tus assets (marca/):")
    return out


def resolver(plan: dict, palabras: list[dict], duracion: float) -> list[str]:
    avisos = []
    for b in plan["beats"]:
        if b.get("cuando"):
            r = buscar_frase(palabras, b["cuando"], b.get("desde", 0.0))
            if r is None:
                avisos.append(f"No encuentro la frase «{b['cuando']}» ({b['id']}). Revisa la transcripción.")
                continue
            b["inicio"] = round(r[0], 2)
        b.setdefault("duracion", DUR_DEFECTO.get(b["tipo"], 3.0))
        if "inicio" not in b:
            avisos.append(f"El beat {b['id']} no tiene inicio ni frase.")
            continue
        b["inicio"] = max(0.0, min(b["inicio"], duracion - 0.5))
        b["duracion"] = round(min(b["duracion"], duracion - b["inicio"]), 2)
    # solapes de piezas que ocupan el mismo sitio
    orden = sorted([b for b in plan["beats"] if "inicio" in b], key=lambda b: b["inicio"])
    for a, b in zip(orden, orden[1:]):
        if a["tipo"] == b["tipo"] == "destacado" and a.get("posicion") == b.get("posicion") \
                and a["inicio"] + a["duracion"] > b["inicio"] - 0.4:
            avisos.append(f"{a['id']} y {b['id']} se pisan: deja al menos medio segundo entre textos.")
    sin_cajas = cargar_marca().get("estilo", "dia-editorial") in ("detras", "dia-editorial")
    tipos_detras = ("profundidad", "destacado", "herramienta") if sin_cajas else ("profundidad",)
    for b in orden:
        for campo in ("texto", "texto2", "clave", "nueva", "remate", "enfasis"):
            v = (b.get(campo) or "").strip().split()
            if v and v[-1].lower().strip(",.") in FINALES_PROHIBIDOS:
                avisos.append(f"{b['id']}: «{b.get(campo)}» acaba en «{v[-1]}». Usa un sintagma completo.")
    prof = [b for b in orden if b["tipo"] in tipos_detras]
    for a, b in zip(prof, prof[1:]):
        if a["inicio"] + a["duracion"] > b["inicio"] - 0.25:
            avisos.append(f"{a['id']} y {b['id']} (textos por detrás) se pisan: deja un respiro entre los dos.")
    for b in prof:
        if b["tipo"] != "profundidad":
            continue
        if len((b.get("texto") or "").replace(" ", "")) > 12:
            avisos.append(f"{b['id']}: «{b.get('texto')}» es largo para ir por detrás; mejor 1 o 2 palabras.")
    laterales = [b for b in orden if b["tipo"] in (("lista",) if sin_cajas else ("destacado", "lista", "herramienta"))]
    for a, b in zip(laterales, laterales[1:]):
        if a["inicio"] + a["duracion"] > b["inicio"] - 0.3 and "vertical" in plan.get("formatos", []):
            avisos.append(f"{a['id']} y {b['id']} coinciden en el tiempo: en vertical van en el mismo sitio.")
    # ritmo de la plantilla: huecos demasiado largos sin nada en pantalla, recursos que evita
    try:
        import estilo as E
        pl = E.cargar(plan.get("plantilla") or E.nombre_activo(plan))
        cada = float(pl["ritmo"]["recurso_cada_s"])
        vis = [b for b in orden if b["tipo"] in VISIBLES]
        marcas = [0.0] + [x for b in vis for x in (b["inicio"], b["inicio"] + b["duracion"])] + [duracion]
        huecos = [(a, b) for a, b in zip(marcas[::2], marcas[1::2]) if b - a > cada * 2]
        for a, b in huecos[:4]:
            avisos.append(f"Hueco de {b - a:.1f} s sin recurso ({fmt_t(a)} a {fmt_t(b)}): la plantilla "
                          f"«{pl['nombre']}» pide uno cada {cada:g} s.")
        for b in orden:
            if b["tipo"] in pl["recursos"].get("evitar", []):
                avisos.append(f"{b['id']}: la plantilla «{pl['nombre']}» evita «{b['tipo']}».")
        tapan = [b for b in vis if b["tipo"] in ("broll", "pantalla")]
        for t_ in tapan:
            for o in vis:
                if o is t_ or o["tipo"] == "subtitulo":
                    continue
                fin_o = o["inicio"] + o["duracion"]
                # lo que acaba en la entrada de una pantalla no se pisa: su círculo va en la misma capa, por
                # encima, y lo tapa en 1-2 fotogramas. Así el texto anterior se queda entero hasta que entra,
                # sin hueco ni salida a medias (el B-roll no: la capa va encima de él)
                if t_["tipo"] == "pantalla" and o["inicio"] < t_["inicio"] and fin_o <= t_["inicio"] + 0.45:
                    continue
                if o["inicio"] < t_["inicio"] + t_["duracion"] - 0.05 and t_["inicio"] < fin_o - 0.05:
                    avisos.append(f"{o['id']} coincide con {t_['id']} ({t_['tipo']}), que tapa la cámara: separa los dos.")
    except Exception as ex:
        avisos.append(f"No he podido medir el ritmo de la plantilla ({type(ex).__name__}).")
    for r in [b for b in orden if b["tipo"] == "rotulo"]:
        for d in [b for b in orden if b["tipo"] == "destacado" and b.get("posicion", "izquierda") == "izquierda"]:
            if d["inicio"] < r["inicio"] + r["duracion"] and r["inicio"] < d["inicio"] + d["duracion"]:
                avisos.append(f"{d['id']} sale a la izquierda mientras está el rótulo: ponlo a la derecha o muévelo.")
    # un «sí» sin ninguna frase entera dentro no enseña subtítulo: avisarlo aquí, no en el render
    import recursos as R
    frases = frases_subtitulo(palabras)
    try:
        import estilo as E
        modo_sub = E.cargar(plan.get("plantilla") or E.nombre_activo(plan))["subtitulos"]["modo"]
    except Exception:
        modo_sub = "momentos"
    if isinstance(plan.get("subtitulos"), str):  # el plan puede pedir «siempre» o «nunca» y manda
        modo_sub = plan["subtitulos"]
    for b in orden:
        if b["tipo"] == "transicion" or modo_sub != "momentos":
            continue
        sub = R.lleva_subtitulo(b)
        if sub and not any(frase_cabe(f, b["inicio"], b["inicio"] + b["duracion"]) for f in frases):
            campo = '"con_subtitulo": false' if b["tipo"] == "rotulo" else '"subtitulo": false'
            avisos.append(f"{b['id']}: pone subtítulo «sí», pero ninguna frase entera cabe en su tramo, así que "
                          f"no saldrá. Alarga la duración hasta el final de la frase o márcalo «no» ({campo}).")
    return avisos


def tabla(video) -> None:
    trabajo = carpeta_trabajo(video)
    pc = leer_json(trabajo / "palabras_cortado.json")
    plan = leer_json(trabajo / "plan.json")
    avisos = resolver(plan, pc["palabras"], pc["duracion"])
    escribir_json(trabajo / "plan.json", plan)
    paso(f"Plan de «{video.name}» · {pc['duracion']:.1f} s · formatos: {', '.join(plan['formatos'])} · "
         f"plantilla: {plan.get('plantilla') or 'la de brand.json'}")
    import recursos as R
    print("\n| # | Entra en | Cuando dices… | Recurso | Qué aparece | Texto en pantalla | Subtítulo |")
    print("|---|---|---|---|---|---|---|")
    for k, b in enumerate(sorted(plan["beats"], key=lambda b: b.get("inicio", 0)), 1):
        dice = b.get("cuando") or "(sin frase: segundo fijo)"
        items = " · ".join((i.get("texto") or i.get("titulo") or i.get("nombre") or i.get("logo") or i.get("icono") or "")
                           if isinstance(i, dict) else str(i) for i in b.get("items", []))
        if b["tipo"] == "contador":
            items = f"{b.get('hasta', '')} {b.get('unidad', '')}".strip()
        texto = " / ".join(x for x in [b.get("enfasis") or b.get("texto"), b.get("clave") or b.get("texto2") or b.get("nueva"),
                                        b.get("remate")] if x) or \
            " · ".join(x for x in [b.get("titulo"), b.get("subtitulo")] if x) or items or \
            {"destello": "(luz)", "logo": "logo", "zoom": b.get("modo", "acercar"),
             "broll": Path(str(b.get("archivo") or b.get("web") or "")).name}.get(b["tipo"], "")
        if b["tipo"] == "etiqueta" and b.get("kicker"):
            texto = f"{b['kicker'].upper()} · {texto}"
        if b.get("camara"):
            texto += f" · cámara: {b['camara']}"
        if b["tipo"] == "texto_detras" and b.get("estilo") == "3d":
            texto += " (3D)"
        sub = R.lleva_subtitulo(b)
        print(f"| {k} | {fmt_t(b.get('inicio', 0))} ({b.get('duracion')} s) | «{dice}» | `{b['tipo']}` | "
              f"{NOMBRES.get(b['tipo'], b['tipo'])} | {texto} | {'sí' if sub else 'no'} |")
    modo_sub = plan.get("subtitulos")
    if modo_sub is True:
        import estilo as E
        modo_sub = E.cargar(plan.get("plantilla")).get("subtitulos", {}).get("modo", "momentos")
    if modo_sub == "siempre":
        print("| · | todo el vídeo, menos donde pone «no» | | `subtitulos` | Subtítulos palabra a palabra | | |")
    elif modo_sub and modo_sub != "nunca":
        print("| · | solo donde pone «sí» | | `subtitulos` | Subtítulos palabra a palabra | | |")
    for r in plan.get("reels", []):
        rr = buscar_frase(pc["palabras"], r["cuando"]) if r.get("cuando") else None
        if rr:
            r["inicio"] = round(rr[0], 2)
        print(f"| Reel | {fmt_t(r.get('inicio', 0))} a {fmt_t(r.get('inicio', 0) + r.get('duracion', 0))} | "
              f"«{r.get('cuando', '')}» | Vertical aparte | {r.get('titulo', '')} |")
    escribir_json(trabajo / "plan.json", plan)
    for a in avisos:
        aviso(a)
    print("\nEstado:", "APROBADO" if plan.get("aprobado") else "ESPERANDO TU OK (no se anima nada hasta entonces)")


def aprobar(video) -> None:
    trabajo = carpeta_trabajo(video)
    plan = leer_json(trabajo / "plan.json")
    plan["aprobado"] = True
    escribir_json(trabajo / "plan.json", plan)
    ok("Plan aprobado. Ya se puede animar.")


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        fallo("Uso: kit.py plan borrador|tabla|buscar|aprobar <video> [frase]")
    orden, video = argv[0], resolver_video(argv[1])
    if orden == "borrador":
        pl = argv[argv.index("--plantilla") + 1] if "--plantilla" in argv and argv.index("--plantilla") + 1 < len(argv) else None
        borrador(video, pl)
    elif orden == "tabla":
        tabla(video)
    elif orden == "aprobar":
        aprobar(video)
    elif orden == "buscar":
        pc = leer_json(carpeta_trabajo(video) / "palabras_cortado.json")
        r = buscar_frase(pc["palabras"], " ".join(argv[2:]))
        print(f"«{' '.join(argv[2:])}»: " + (f"de {r[0]:.2f} s a {r[1]:.2f} s" if r else "no aparece"))
    else:
        fallo(f"No conozco la orden «{orden}».")


if __name__ == "__main__":
    main(sys.argv[1:])

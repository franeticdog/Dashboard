"""Plantillas de edición: que cada vídeo salga siempre igual («siempre el mismo estilo»).

  kit.py estilo lista                          -> las plantillas que hay y cuál está activa
  kit.py estilo ver <nombre>                   -> enseña una plantilla en llano
  kit.py estilo usar <nombre> [--reels]        -> la deja activa en brand.json (o la de los reels)
  kit.py estilo analizar <vídeo|capturas...> --nombre <nombre>
                                               -> saca fotogramas y cambios de plano de una
                                                  referencia y deja un borrador de plantilla
  kit.py estilo guardar <nombre>               -> revisa la plantilla y la da por buena

Una plantilla vive en estilos/<nombre>.json (lo que leen planificar, animar y componer) y
estilos/<nombre>.md (la misma plantilla contada en llano, para ti y para Claude).

REGLA DE LA CASA: de una referencia se toman PRINCIPIOS y RITMO (cada cuánto entra un recurso,
qué tipo de recursos, si hay subtítulos, tamaños, zooms, transiciones). Nunca se copian sus
assets, su tipografía exclusiva, sus colores de marca ni su logo. Los fotogramas de la
referencia se quedan en trabajo/_estilos/ para mirarlos y no entran en la plantilla.
"""
from __future__ import annotations

import copy
import re
import shutil
import sys
import time
from pathlib import Path

from comun import (BRAND, KIT, RAIZ, TRABAJO, aviso, cargar_marca, ejecutar, escribir_json, fallo, info_video,
                   leer_json, ok, paso, slug)

DIR = KIT / "estilos"
EXT_IMG = (".jpg", ".jpeg", ".png", ".webp")
EXT_VID = (".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi")
RECURSOS_VALIDOS = {"palabra", "tachado", "logos", "golpe3d", "contador", "fases", "terminal", "barrido",
                    "capitulo", "subtitulo", "rotulo", "broll", "pantalla", "zoom", "cine", "luz", "lista"}

# Lo que vale si una plantilla no dice nada (es el estilo de serie «youtube-editorial»)
DEFECTO = {
    "nombre": "youtube-editorial",
    "descripcion": "",
    "para": "youtube",
    "origen": "de serie",
    "ritmo": {"recurso_cada_s": 6.0, "gancho_cada_s": 3.0, "aire_s": 0.25},
    "recursos": {"preferidos": ["palabra", "logos", "tachado", "contador", "fases", "terminal", "golpe3d"],
                 "evitar": []},
    "subtitulos": {"modo": "momentos", "palabras_por_linea": None, "mayusculas": False},
    "textos": {"escala": 1.0},
    "acento": None,
    "tres_d": {"logos": True, "golpe": True},
    "detras": True,
    "transiciones": {"tipo": "latigo", "en_cambios_de_plano": True},
    "zooms": {"ken_burns": 0.03, "empuje": 0.05, "golpes": False, "golpe_zoom": 0.07},
    "musica": {"cama": False, "nivel_db": -24},
    "sonidos": {"nivel": 1.0},
    "notas": [],
}
MODOS_SUB = ("momentos", "siempre", "nunca")
TRANSICIONES = ("latigo", "desenfoque", "corte")


def _fusionar(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _fusionar(out[k], v)
        else:
            out[k] = v
    return out


def ruta(nombre: str) -> Path:
    return DIR / f"{slug(nombre)}.json"


def existentes() -> list[str]:
    return sorted(p.stem for p in DIR.glob("*.json")) if DIR.exists() else []


def cargar(nombre: str | None) -> dict:
    """La plantilla completa (con los valores por defecto donde no diga nada)."""
    if not nombre:
        return _fusionar(DEFECTO, {})
    p = ruta(nombre)
    if not p.exists():
        aviso(f"No existe la plantilla «{nombre}» (en estilos/). Uso la de serie «youtube-editorial».")
        return _fusionar(DEFECTO, leer_json(ruta("youtube-editorial"), defecto={}))
    return _fusionar(DEFECTO, leer_json(p))


def nombre_activo(plan: dict | None = None, cli: str | None = None, reel: bool = False) -> str:
    """Cuál manda: la que se pide en la orden, la del plan, la de brand.json y, si no, la de serie."""
    if cli:
        return slug(cli)
    marca = cargar_marca()
    if reel:  # los reels tienen su propia plantilla: la del plan es la del vídeo largo
        if plan and plan.get("plantilla_reels"):
            return slug(plan["plantilla_reels"])
        if marca.get("plantilla_reels"):
            return slug(marca["plantilla_reels"])
    if plan and plan.get("plantilla"):
        return slug(plan["plantilla"])
    return slug(marca.get("plantilla") or "youtube-editorial")


def activa(plan: dict | None = None, cli: str | None = None, reel: bool = False) -> dict:
    return cargar(nombre_activo(plan, cli, reel))


def aplicar_a_marca(marca: dict, pl: dict) -> dict:
    """La marca con lo que la plantilla cambia (acento, subtítulos). La marca manda en todo lo demás:
    la plantilla nunca trae colores de otro creador, solo si se quiere un acento distinto."""
    m = copy.deepcopy(marca)
    if pl.get("acento") and re.fullmatch(r"#[0-9a-fA-F]{6}", str(pl["acento"])):
        m["color_enfasis"] = pl["acento"]
    sub = pl.get("subtitulos", {})
    m.setdefault("subtitulos", {})
    if sub.get("palabras_por_linea"):
        m["subtitulos"]["palabras_por_linea_horizontal"] = sub["palabras_por_linea"]
        m["subtitulos"]["palabras_por_linea_vertical"] = sub["palabras_por_linea"]
    if sub.get("mayusculas"):
        m["subtitulos"]["mayusculas"] = True
    return m


def validar(pl: dict) -> list[str]:
    errores = []
    r = pl.get("ritmo", {})
    if not isinstance(r.get("recurso_cada_s"), (int, float)) or not 0.8 <= r["recurso_cada_s"] <= 30:
        errores.append("ritmo.recurso_cada_s tiene que ser un número de segundos entre 0,8 y 30")
    if pl.get("subtitulos", {}).get("modo") not in MODOS_SUB:
        errores.append(f"subtitulos.modo tiene que ser uno de: {', '.join(MODOS_SUB)}")
    if pl.get("transiciones", {}).get("tipo") not in TRANSICIONES:
        errores.append(f"transiciones.tipo tiene que ser uno de: {', '.join(TRANSICIONES)}")
    esc = pl.get("textos", {}).get("escala", 1.0)
    if not isinstance(esc, (int, float)) or not 0.6 <= esc <= 1.6:
        errores.append("textos.escala va de 0,6 a 1,6 (1 = el tamaño de serie)")
    for k in ("preferidos", "evitar"):
        malos = [x for x in pl.get("recursos", {}).get(k, []) if x not in RECURSOS_VALIDOS]
        if malos:
            errores.append(f"recursos.{k}: no conozco {', '.join(malos)}")
    ac = pl.get("acento")
    if ac and not re.fullmatch(r"#[0-9a-fA-F]{6}", str(ac)):
        errores.append("acento: un color #RRGGBB o null para usar el de tu marca")
    z = pl.get("zooms", {})
    for k in ("ken_burns", "empuje", "golpe_zoom"):
        if not isinstance(z.get(k, 0), (int, float)) or not 0 <= z.get(k, 0) <= 0.2:
            errores.append(f"zooms.{k} va de 0 a 0,2 (0,05 = un 5 %)")
    return errores


def _n(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def en_llano(pl: dict) -> list[str]:
    r, s, z, t = pl["ritmo"], pl["subtitulos"], pl["zooms"], pl["transiciones"]
    sub = {"momentos": "solo en los momentos importantes", "siempre": "siempre, en frases cortas",
           "nunca": "sin subtítulos"}[s["modo"]]
    if s.get("palabras_por_linea"):
        sub += f" ({s['palabras_por_linea']} palabras por línea como mucho)"
    tr = {"latigo": "látigo de zoom limpio", "desenfoque": "corte con desenfoque de movimiento",
          "corte": "corte seco"}[t["tipo"]]
    return [
        f"Ritmo: un recurso cada {_n(r['recurso_cada_s'])} s (en el gancho, cada {_n(r['gancho_cada_s'])} s)",
        f"Recursos que prefiere: {', '.join(pl['recursos']['preferidos']) or 'cualquiera'}"
        + (f" · evita: {', '.join(pl['recursos']['evitar'])}" if pl['recursos']['evitar'] else ""),
        f"Subtítulos: {sub}",
        f"Textos: {'tamaño de serie' if pl['textos']['escala'] == 1 else f'al {int(pl['textos']['escala'] * 100)} %'}"
        + f" · acento: {pl['acento'] or 'el de tu marca'}",
        f"3D: logos {'en 3D' if pl['tres_d']['logos'] else 'planos'} · frases {'por detrás de ti' if pl['detras'] else 'delante'}",
        f"Transiciones: {tr}" + ("" if t["en_cambios_de_plano"] else " (solo si se piden)"),
        f"Zooms: ken burns {z['ken_burns'] * 100:.0f} %, empuje {z['empuje'] * 100:.0f} %"
        + (f", golpe de zoom del {z['golpe_zoom'] * 100:.0f} % en cada recurso" if z["golpes"] else ""),
        f"Música de cama: {'sí' if pl['musica']['cama'] else 'no'}",
    ]


# ------------------------------------------------------------------ órdenes
def lista() -> None:
    marca = cargar_marca()
    act, act_r = marca.get("plantilla") or "youtube-editorial", marca.get("plantilla_reels")
    paso("Plantillas de edición (carpeta estilos/)")
    for n in existentes():
        pl = cargar(n)
        marcas = []
        if n == slug(act):
            marcas.append("ACTIVA")
        if act_r and n == slug(act_r):
            marcas.append("ACTIVA EN REELS")
        print(f"   · {n} ({pl.get('para', '?')}){' · ' + ' · '.join(marcas) if marcas else ''}: {pl.get('descripcion', '')}")
    print("\n   Elegir una: kit.py estilo usar <nombre> (o --reels para la de los reels).")
    print("   Solo para un vídeo: /editar <video> ambos --plantilla <nombre>.")


def ver(nombre: str) -> None:
    pl = cargar(nombre)
    paso(f"Plantilla «{nombre}» · {pl.get('descripcion', '')}")
    for linea in en_llano(pl):
        print(f"   · {linea}")
    for n in pl.get("notas", []):
        print(f"   · Nota: {n}")


def usar(nombre: str, reels: bool) -> None:
    if not ruta(nombre).exists():
        fallo(f"No existe la plantilla «{nombre}».", "Mira las que hay con: kit.py estilo lista")
    if not BRAND.exists():
        fallo("Todavía no hay brand.json.", "Lanza antes /empezar.")
    marca = leer_json(BRAND)
    marca["plantilla_reels" if reels else "plantilla"] = slug(nombre)
    escribir_json(BRAND, marca)
    ok(f"Plantilla «{slug(nombre)}» activa{' para los reels' if reels else ''} (guardado en brand.json)")


def _escenas(video: Path, umbral: float = 0.3) -> list[float]:
    r = ejecutar(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf",
                  f"select='gt(scene,{umbral})',showinfo", "-an", "-f", "null", "-"], comprobar=False)
    return [round(float(m.group(1)), 2) for m in re.finditer(r"pts_time:([\d.]+)", r.stdout or "")]


def _hoja(imagenes: list[Path], destino: Path, cols: int, ancho: int) -> None:
    tmp = destino.parent / "_seq"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    for n, c in enumerate(imagenes):
        ejecutar(["ffmpeg", "-v", "error", "-y", "-i", str(c), "-vf",
                  f"scale={ancho}:{ancho}:force_original_aspect_ratio=decrease,"
                  f"pad={ancho}:{ancho}:(ow-iw)/2:(oh-ih)/2:color=white", str(tmp / f"{n:03d}.jpg")])
    filas = -(-len(imagenes) // cols)
    ejecutar(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", str(tmp / "%03d.jpg"),
              "-vf", f"tile={cols}x{filas}:padding=6:color=white", "-frames:v", "1", str(destino)])
    shutil.rmtree(tmp, ignore_errors=True)


def analizar(entradas: list[str], nombre: str) -> None:
    nombre = slug(nombre)
    archivos: list[Path] = []
    for e in entradas:
        p = Path(e).expanduser()
        if not p.is_absolute():
            p = (Path.cwd() / p) if (Path.cwd() / p).exists() else RAIZ / p
        if p.is_dir():
            archivos += sorted(x for x in p.iterdir() if x.suffix.lower() in EXT_IMG + EXT_VID)
        elif p.exists():
            archivos.append(p)
        else:
            fallo(f"No encuentro «{e}».", "Pasa la ruta del vídeo o de las capturas (o arrástralos al chat).")
    if not archivos:
        fallo("No hay ningún vídeo ni captura que analizar.")
    carpeta = TRABAJO / "_estilos" / nombre
    shutil.rmtree(carpeta, ignore_errors=True)
    (carpeta / "fotogramas").mkdir(parents=True)
    paso(f"Analizando la referencia para la plantilla «{nombre}» ({len(archivos)} archivo(s))")
    fotos: list[Path] = []
    medidas: dict = {"videos": [], "capturas": 0}
    for a in archivos:
        if a.suffix.lower() in EXT_VID:
            iv = info_video(a)
            dur = iv["duracion"]
            cortes = [t for t in _escenas(a) if 0.2 < t < dur - 0.2]
            planos = [b - x for x, b in zip([0.0] + cortes, cortes + [dur])]
            medio = sum(planos) / len(planos) if planos else dur
            medidas["videos"].append({"archivo": a.name, "duracion_s": round(dur, 1), "orientacion": iv["orientacion"],
                                      "cambios_de_plano": len(cortes), "plano_medio_s": round(medio, 2),
                                      "cortes_por_minuto": round(len(cortes) / max(dur, 1) * 60, 1),
                                      "cortes_en": cortes[:60]})
            # un fotograma cada tanto (máximo 18) y uno justo después de cada cambio de plano (máximo 12)
            paso_s = max(1.0, dur / 18)
            momentos = [round(k * paso_s + 0.3, 2) for k in range(int(dur / paso_s))]
            momentos += [round(c + 0.2, 2) for c in cortes[:12]]
            for k, t in enumerate(sorted(set(m for m in momentos if m < dur - 0.1))):
                f = carpeta / "fotogramas" / f"{a.stem[:24]}-{t:06.2f}s.jpg"
                ejecutar(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(a), "-frames:v", "1",
                          "-vf", "scale=640:-2", "-q:v", "3", str(f)])
                fotos.append(f)
            ok(f"{a.name}: {dur:.1f} s, {len(cortes)} cambios de plano (uno cada {medio:.1f} s)")
        elif a.suffix.lower() in EXT_IMG:
            f = carpeta / "fotogramas" / f"captura-{len(fotos) + 1:02d}.jpg"
            ejecutar(["ffmpeg", "-v", "error", "-y", "-i", str(a), "-vf", "scale=640:-2", "-q:v", "3", str(f)])
            fotos.append(f)
            medidas["capturas"] += 1
    if medidas["capturas"]:
        ok(f"{medidas['capturas']} captura(s) listas")
    _hoja(fotos, carpeta / "hoja.jpg", cols=6 if len(fotos) > 12 else min(4, len(fotos)), ancho=420)
    escribir_json(carpeta / "analisis.json", medidas)
    # borrador de plantilla: lo medido ya va puesto; lo visual lo decide Claude mirando la hoja
    base = cargar(None)
    base.update({"nombre": nombre, "descripcion": "(Claude: descríbela en una línea)",
                 "origen": f"referencia analizada el {time.strftime('%Y-%m-%d')} (solo principios y ritmo)",
                 "por_revisar": True})
    if medidas["videos"]:
        medio = sum(v["plano_medio_s"] for v in medidas["videos"]) / len(medidas["videos"])
        base["ritmo"]["recurso_cada_s"] = round(min(max(medio, 1.5), 10.0), 1)
        base["ritmo"]["gancho_cada_s"] = round(min(max(medio * 0.6, 1.2), 4.0), 1)
        if any(v["orientacion"] == "vertical" for v in medidas["videos"]):
            base["para"] = "reels"
    destino = ruta(nombre)
    if destino.exists() and not leer_json(destino).get("por_revisar"):
        aviso(f"Ya hay una plantilla «{nombre}» guardada: no la piso. El borrador va a estilos/{nombre}.borrador.json.")
        destino = DIR / f"{nombre}.borrador.json"
    DIR.mkdir(exist_ok=True)
    escribir_json(destino, base)
    ok(f"Hoja de fotogramas: trabajo/_estilos/{nombre}/hoja.jpg")
    ok(f"Medidas: trabajo/_estilos/{nombre}/analisis.json")
    ok(f"Borrador de plantilla: estilos/{destino.name}")
    print("   Claude: abre la hoja (y los fotogramas que te dejen duda), rellena el borrador según la skill")
    print("   «estilo», escribe estilos/<nombre>.md y lanza: kit.py estilo guardar <nombre>")


def guardar(nombre: str) -> None:
    p = ruta(nombre)
    if not p.exists():
        fallo(f"No existe estilos/{p.name}.", "Lanza antes: kit.py estilo analizar <referencia> --nombre <nombre>")
    datos = leer_json(p)
    pl = _fusionar(DEFECTO, datos)
    errores = validar(pl)
    if "(Claude" in str(pl.get("descripcion", "")):
        errores.append("falta la descripción de la plantilla (una línea)")
    if not (DIR / f"{slug(nombre)}.md").exists():
        errores.append(f"falta estilos/{slug(nombre)}.md: la plantilla contada en llano")
    if errores:
        for e in errores:
            aviso(e)
        fallo("La plantilla todavía no está lista (arriba lo que falta).")
    datos.pop("por_revisar", None)
    escribir_json(p, datos)
    ok(f"Plantilla «{slug(nombre)}» guardada")
    for linea in en_llano(pl):
        print(f"   · {linea}")
    print(f"\n   Para usarla siempre: kit.py estilo usar {slug(nombre)} · solo en un vídeo: --plantilla {slug(nombre)}")


def main(argv: list[str]) -> None:
    if not argv:
        fallo("Uso: kit.py estilo lista | ver <nombre> | usar <nombre> [--reels] | "
              "analizar <vídeo o capturas...> --nombre <nombre> | guardar <nombre>")
    orden = argv[0]
    if orden == "lista":
        lista()
    elif orden == "ver" and len(argv) > 1:
        ver(argv[1])
    elif orden == "usar" and len(argv) > 1:
        usar(argv[1], "--reels" in argv)
    elif orden == "analizar":
        args = argv[1:]
        nombre = None
        if "--nombre" in args:
            k = args.index("--nombre")
            nombre = args[k + 1] if k + 1 < len(args) else None
            args = args[:k] + args[k + 2:]
        if not args:
            fallo("Dime qué referencia analizo: un vídeo, varias capturas o una carpeta con ellas.")
        analizar(args, nombre or f"referencia-{time.strftime('%Y%m%d-%H%M')}")
    elif orden == "guardar" and len(argv) > 1:
        guardar(argv[1])
    elif orden == "validar" and len(argv) > 1:
        errores = validar(cargar(argv[1]))
        for e in errores:
            aviso(e)
        if errores:
            sys.exit(1)
        ok(f"«{argv[1]}» está bien escrita")
    else:
        fallo(f"No conozco «{' '.join(argv)}».", "Prueba: kit.py estilo lista")


if __name__ == "__main__":
    main(sys.argv[1:])

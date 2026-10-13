"""La carpeta del proyecto y sus marcas (cuando el kit va como skill: «editor-video»).

  kit.py proyecto                       -> dónde está todo: proyecto, marca en uso, entorno
  kit.py proyecto marcas                -> las marcas guardadas
  kit.py proyecto nuevo <marca>         -> la carpeta de trabajo pasa a ser un proyecto de esa marca
  kit.py proyecto crear-marca <nombre>  -> una marca nueva (copia de la de ejemplo), y el proyecto la usa

Un proyecto es una carpeta cualquiera con proyecto.json ({"marca": "<nombre>"}) o con su propio brand.json.
Cada marca guardada vive en MARCAS/<nombre>/ (brand.json + marca/) y la comparten todos sus proyectos,
igual que en el kit clásico todos los vídeos comparten brand.json y marca/.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from comun import (BRAND, BRAND_EJEMPLO, EN_SKILL, ENTORNO, MARCA, MARCAS, PROYECTO_JSON, RAIZ, SITIO_MARCA,
                   escribir_json, fallo, leer_json, ok, paso, slug)

SUBCARPETAS_MARCA = ("musica", "sonidos", "logos", "broll", "fuentes")


def perfiles() -> list[Path]:
    if not MARCAS.exists():
        return []
    return sorted(c for c in MARCAS.iterdir() if (c / "brand.json").exists())


def resumen(brand: Path) -> str:
    m = leer_json(brand, defecto={})
    canal, col, tip = m.get("canal", {}), m.get("colores", {}), m.get("tipografia", {})
    return (f"{canal.get('nombre', '?')} ({canal.get('handle', '')}) · colores {col.get('principal', '?')} y "
            f"{col.get('acento', '?')} · tipografía {tip.get('titulos', '?')}")


def estado() -> None:
    paso("Dónde está todo")
    print(f"   Proyecto: {RAIZ}", flush=True)
    if BRAND.exists():
        de = "propia del proyecto" if SITIO_MARCA == RAIZ else f"la marca guardada «{SITIO_MARCA.name}»"
        print(f"   Marca: {de} · {resumen(BRAND)}")
        print(f"   brand.json: {BRAND}")
        print(f"   Assets de la marca (logo, música, sonidos, logos, B-roll): {MARCA}")
    else:
        print("   Marca: ninguna todavía (esta carpeta aún no es un proyecto)")
    instalado = (ENTORNO / ".kit-estado.json").exists()
    print(f"   Entorno: {ENTORNO} ({'instalado' if instalado else 'SIN INSTALAR: kit.py instalar'})")
    if EN_SKILL:
        print(f"   Marcas guardadas: {', '.join(p.name for p in perfiles()) or 'ninguna'}")


def marcas() -> None:
    ps = perfiles()
    if not ps:
        print("No hay marcas guardadas todavía.")
        return
    for p in ps:
        print(f"   {p.name}: {resumen(p / 'brand.json')}")


def _buscar_perfil(nombre: str) -> Path:
    p = Path(nombre).expanduser()
    if p.is_absolute() and (p / "brand.json").exists():
        return p
    if (MARCAS / nombre / "brand.json").exists():
        return MARCAS / nombre
    cands = [x for x in perfiles() if slug(nombre) in x.name or x.name in slug(nombre)]
    if len(cands) == 1:
        return cands[0]
    fallo(f"No encuentro la marca «{nombre}».",
          f"Marcas guardadas: {', '.join(x.name for x in perfiles()) or 'ninguna'} (kit.py proyecto marcas).")
    raise SystemExit(1)


def nuevo(nombre: str) -> None:
    perfil = _buscar_perfil(nombre)
    if (RAIZ / "brand.json").exists():
        fallo("Esta carpeta ya tiene su propio brand.json: ya es un proyecto con su marca.",
              "Si quieres que use una marca guardada, quita o renombra antes ese brand.json.")
    escribir_json(PROYECTO_JSON, {"marca": perfil.name if perfil.parent == MARCAS else str(perfil)})
    m = leer_json(perfil / "brand.json")
    for clave in ("brutos", "finales"):
        c = Path(m.get("carpetas", {}).get(clave, clave)).expanduser()
        (c if c.is_absolute() else RAIZ / c).mkdir(parents=True, exist_ok=True)
    ok(f"Proyecto listo en {RAIZ} con la marca «{perfil.name}»: {resumen(perfil / 'brand.json')}")


def crear_marca(nombre: str) -> None:
    perfil = MARCAS / slug(nombre)
    if (perfil / "brand.json").exists():
        fallo(f"Ya hay una marca guardada con ese nombre ({perfil}).",
              f"Para usarla: kit.py proyecto nuevo {perfil.name}")
    for c in SUBCARPETAS_MARCA:
        (perfil / "marca" / c).mkdir(parents=True, exist_ok=True)
    shutil.copy(BRAND_EJEMPLO, perfil / "brand.json")
    ok(f"Marca nueva en {perfil}. Rellena {perfil / 'brand.json'} y deja el logo en {perfil / 'marca'}")
    nuevo(perfil.name)


def main(argv: list[str]) -> None:
    if not argv:
        return estado()
    orden, resto = argv[0], argv[1:]
    if not EN_SKILL and orden != "estado":
        fallo("Las marcas guardadas y los proyectos sueltos son de la skill «editor-video».",
              "En el kit clásico, la marca es el brand.json de su carpeta.")
    if orden == "estado":
        estado()
    elif orden == "marcas":
        marcas()
    elif orden == "nuevo" and resto:
        nuevo(" ".join(resto))
    elif orden == "crear-marca" and resto:
        crear_marca(" ".join(resto))
    else:
        print(__doc__)

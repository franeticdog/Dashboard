#!/usr/bin/env python3
"""Puerta de entrada única del kit. Uso: python3 herramientas/kit.py <orden> [...]

Órdenes: instalar · comprobar · transcribir · cortar · persona · plan · animar · componer · verificar · tiempos
         estilo (plantillas) · broll (capturas de webs e imágenes propias) · sonido
         proyecto (dónde está todo, marcas guardadas y proyectos nuevos; en la skill «editor-video»)
Si existe el entorno .venv del kit, se relanza solo dentro de él.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from comun import python_venv  # noqa: E402

ORDENES = {
    "instalar": "instalar", "comprobar": "comprobar", "transcribir": "transcribir",
    "cortar": "cortar", "plan": "plan", "animar": "animar", "componer": "componer",
    "verificar": "verificar", "tiempos": "tiempos", "persona": "persona", "sonido": "sonido",
    "estilo": "estilo", "broll": "broll", "proyecto": "proyecto",
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ORDENES:
        print(__doc__)
        sys.exit(1)
    orden = sys.argv[1]
    py = python_venv()
    dentro = Path(sys.prefix).resolve() == py.parent.parent.resolve()
    if orden not in ("instalar",) and py.exists() and not dentro:
        sys.exit(subprocess.call([str(py), str(Path(__file__).resolve()), *sys.argv[1:]]))
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    modulo = __import__(ORDENES[orden])
    modulo.main(sys.argv[2:])


if __name__ == "__main__":
    main()

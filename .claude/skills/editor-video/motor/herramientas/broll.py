"""B-roll: imágenes y vídeos de recurso que tapan la cámara unos segundos mientras sigues hablando.

  kit.py broll lista                                 -> lo que hay en marca/broll/
  kit.py broll web <url> [--nombre N] [--movil]      -> captura una web EN LOCAL (Chrome sin ventana)
  kit.py broll html <archivo.html> [--nombre N] [--vertical]
                                                     -> dibuja una imagen que ha escrito Claude (HTML/SVG)

De dónde sale el B-roll, por orden de preferencia:
  1. Lo que dejas tú en marca/broll/ (fotos .jpg/.png/.webp o vídeos .mp4/.mov): tuyo o con licencia.
  2. Capturas de las webs que nombras en el vídeo, hechas en tu ordenador con el navegador del kit.
  3. Imágenes que Claude dibuja en HTML/SVG y el navegador del kit convierte en foto.
NUNCA con APIs de pago ni bancos de imágenes: el kit no descarga fotos de stock.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

from comun import ENTORNO, MARCA, aviso, ejecutar, entorno_hyperframes, fallo, ok, paso, ruta_proyecto, slug

CARPETA = MARCA / "broll"
EXT_IMG = (".jpg", ".jpeg", ".png", ".webp")
EXT_VID = (".mp4", ".mov", ".m4v", ".webm")
HF = ENTORNO / "node_modules" / "hyperframes" / "bin" / "hyperframes.mjs"
UA_MOVIL = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1")


def navegador() -> str:
    """El Chrome sin ventana que ya instaló HyperFrames (no hace falta otro)."""
    if not HF.exists():
        fallo("Falta HyperFrames (trae el navegador del kit).", "Lanza /empezar.")
    r = subprocess.run(["node", str(HF), "browser", "path"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, env={**__import__("os").environ, **entorno_hyperframes()})
    lineas = [l.strip() for l in (r.stdout or "").splitlines() if l.strip()]
    if r.returncode != 0 or not lineas or not Path(lineas[-1]).exists():
        fallo("No encuentro el navegador del kit.", "Lanza /empezar para que lo prepare.")
    return lineas[-1]


def _captura(destino: Path, url: str, ancho: int, alto: int, escala: float = 1.0, movil: bool = False) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    cmd = [navegador(), "--headless", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
           "--no-first-run", "--no-default-browser-check", f"--window-size={ancho},{alto}",
           f"--force-device-scale-factor={escala}", "--virtual-time-budget=9000",
           f"--screenshot={destino}"]
    if movil:
        cmd.append(f"--user-agent={UA_MOVIL}")
    cmd.append(url)
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=90)
    if not destino.exists() or destino.stat().st_size < 2000:
        print((r.stdout or "")[-800:])
        fallo(f"No he podido capturar {url}.", "Comprueba la dirección y tu conexión, o deja tú una captura en marca/broll/.")
    return destino


def web(url: str, nombre: str | None = None, movil: bool = False) -> Path:
    if not re.match(r"https?://", url):
        url = "https://" + url
    nombre = slug(nombre or re.sub(r"^https?://(www\.)?", "", url))[:40]
    destino = CARPETA / f"web-{nombre}{'-movil' if movil else ''}.png"
    if destino.exists():
        return destino
    paso(f"Capturando {url} en local{' (versión móvil)' if movil else ''}")
    t0 = time.time()
    if movil:
        _captura(destino, url, 430, 932, 2.5, movil=True)
    else:
        _captura(destino, url, 1920, 1080)
    ok(f"Guardada en marca/broll/{destino.name} ({time.time() - t0:.0f} s)")
    return destino


def html(archivo: str, nombre: str | None = None, vertical: bool = False) -> Path:
    p = ruta_proyecto(archivo)
    if not p.exists():
        fallo(f"No encuentro {archivo}.")
    destino = CARPETA / f"{slug(nombre or p.stem)}.png"
    ancho, alto = (1080, 1920) if vertical else (1920, 1080)
    _captura(destino, p.resolve().as_uri(), ancho, alto)
    ok(f"Imagen lista: marca/broll/{destino.name}")
    return destino


def resolver(b: dict) -> tuple[Path | None, str]:
    """El archivo de un beat de B-roll: «archivo» (en marca/broll o ruta) o «web» (se captura)."""
    if b.get("archivo"):
        a = Path(str(b["archivo"])).expanduser()
        for cand in (a, ruta_proyecto(a), CARPETA / a.name):
            if cand.exists():
                return cand.resolve(), ("video" if cand.suffix.lower() in EXT_VID else "imagen")
        # por nombre parecido dentro de marca/broll
        if CARPETA.exists():
            stem = slug(a.stem)
            for f in sorted(CARPETA.iterdir()):
                if stem and stem in slug(f.stem) and f.suffix.lower() in EXT_IMG + EXT_VID:
                    return f.resolve(), ("video" if f.suffix.lower() in EXT_VID else "imagen")
        aviso(f"No encuentro el B-roll «{b['archivo']}» (míralo en marca/broll/).")
        return None, ""
    if b.get("web"):
        try:
            return web(b["web"], b.get("nombre"), bool(b.get("movil"))), "imagen"
        except SystemExit:
            return None, ""
    return None, ""


def lista() -> None:
    paso("B-roll disponible en marca/broll/")
    fs = [f for f in sorted(CARPETA.iterdir()) if f.suffix.lower() in EXT_IMG + EXT_VID] if CARPETA.exists() else []
    for f in fs:
        print(f"   · {f.name}")
    if not fs:
        print("   (vacía) Deja fotos o vídeos tuyos, o pide «captura la web de …».")


def main(argv: list[str]) -> None:
    if not argv:
        fallo("Uso: kit.py broll lista | web <url> [--nombre N] [--movil] | html <archivo.html> [--nombre N] [--vertical]")
    opts = {argv[k].lstrip("-"): argv[k + 1] for k in range(1, len(argv) - 1) if argv[k].startswith("--")
            and not argv[k + 1].startswith("--")}
    if argv[0] == "lista":
        lista()
    elif argv[0] == "web" and len(argv) > 1:
        web(argv[1], opts.get("nombre"), "--movil" in argv)
    elif argv[0] == "html" and len(argv) > 1:
        html(argv[1], opts.get("nombre"), "--vertical" in argv)
    else:
        fallo(f"No conozco «{' '.join(argv)}».")


if __name__ == "__main__":
    main(sys.argv[1:])

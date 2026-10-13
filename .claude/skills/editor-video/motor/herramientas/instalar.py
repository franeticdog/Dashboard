"""Instalación del kit, paso a paso. Se puede lanzar las veces que haga falta:
lo que ya está instalado se detecta y se salta.

Cada pieza se prueba con un comando real, no basta con que «exista».
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from comun import (BRAND, BRAND_EJEMPLO, EN_SKILL, ENTORNO, ES_APPLE_SILICON, ES_MAC, ES_WINDOWS, KIT, MARCA,
                   RAIZ, VENV, aviso, ejecutar, entorno_hyperframes, escribir_json, fallo, leer_json, npm, ok,
                   paso, python_venv)

ESTADO = ENTORNO / ".kit-estado.json"
# pruebas de la instalación: en la skill, en los temporales del entorno (no ensucian el proyecto)
PRUEBAS = ENTORNO / "_tmp" if EN_SKILL else RAIZ / "trabajo"
UA_WOFF2 = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def version_de(cmd: list[str]) -> str | None:
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
        return r.stdout.strip().splitlines()[0] if r.returncode == 0 and r.stdout else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def instalar_sistema(paquete_brew: str, paquete_winget: str, nombre: str) -> None:
    if ES_MAC and shutil.which("brew"):
        print(f"   Instalando {nombre} con Homebrew (puede tardar un par de minutos)…", flush=True)
        ejecutar(["brew", "install", paquete_brew], capturar=False)
    elif ES_WINDOWS and shutil.which("winget"):
        print(f"   Instalando {nombre} con winget…", flush=True)
        ejecutar(["winget", "install", "--id", paquete_winget, "-e", "--silent",
                  "--accept-source-agreements", "--accept-package-agreements"], capturar=False)
        aviso(f"En Windows, cierra y vuelve a abrir Claude Code para que encuentre {nombre}. "
              "Luego lanza /empezar otra vez: seguirá donde lo dejó.")
        sys.exit(2)
    elif ES_MAC:
        fallo(f"Falta {nombre} y no tienes Homebrew.",
              "Instala Homebrew desde https://brew.sh (un comando) y vuelve a lanzar /empezar.")
    else:
        fallo(f"Falta {nombre}.", f"Instálalo con el gestor de paquetes de tu sistema ({paquete_brew}).")


def paso_ffmpeg() -> str:
    paso("1/7 · ffmpeg (el motor que corta y monta el vídeo)")
    v = version_de(["ffmpeg", "-version"])
    if not v or not version_de(["ffprobe", "-version"]):
        instalar_sistema("ffmpeg", "Gyan.FFmpeg", "ffmpeg")
        v = version_de(["ffmpeg", "-version"])
        if not v:
            fallo("ffmpeg sigue sin responder.", "Cierra y abre la terminal o Claude Code, y repite /empezar.")
    # prueba real: generar 1 s de vídeo
    ejecutar(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=30:duration=1",
              "-f", "null", "-"])
    ok(" ".join(v.split()[:3]))
    return v


def paso_node() -> str:
    paso("2/7 · Node.js 22 o más nuevo (lo necesita HyperFrames)")
    v = version_de(["node", "--version"])
    mayor = int(re.sub(r"[^\d.]", "", v).split(".")[0]) if v else 0
    if mayor < 22:
        if v:
            aviso(f"Tienes Node {v}, y HyperFrames pide la 22 o superior.")
        instalar_sistema("node", "OpenJS.NodeJS.LTS", "Node.js")
        v = version_de(["node", "--version"])
        mayor = int(re.sub(r"[^\d.]", "", v or "0").split(".")[0] or 0)
        if mayor < 22:
            fallo(f"Node sigue en {v}.", "Descarga la versión LTS de https://nodejs.org, instálala y repite /empezar.")
    ejecutar(["node", "-e", "process.exit(0)"])
    ok(f"Node {v}")
    return v


def paso_npm() -> str:
    paso("3/7 · HyperFrames, GSAP y Three.js (las animaciones y el 3D)")
    pkg = leer_json(KIT / "package.json")
    quiere = pkg["dependencies"]["hyperframes"]
    instalada = ENTORNO / "node_modules" / "hyperframes" / "package.json"
    gsap = ENTORNO / "node_modules" / "gsap" / "dist" / "gsap.min.js"
    three = ENTORNO / "node_modules" / "three" / "build" / "three.module.js"
    fk = ENTORNO / "node_modules" / "fontkit" / "package.json"
    if instalada.exists() and leer_json(instalada).get("version") == quiere and gsap.exists() \
            and three.exists() and fk.exists():
        ok(f"HyperFrames {quiere} ya estaba instalado")
    else:
        if ENTORNO != KIT:  # en la skill, los paquetes de Node se instalan en el entorno
            ENTORNO.mkdir(parents=True, exist_ok=True)
            for f in ("package.json", "package-lock.json"):
                if (KIT / f).exists():
                    shutil.copy(KIT / f, ENTORNO / f)
        ejecutar([npm(), "install", "--no-audit", "--no-fund", "--loglevel=error"], cwd=ENTORNO)
        ok(f"HyperFrames {quiere} y GSAP instalados en la carpeta del kit")
    hf = ENTORNO / "node_modules" / "hyperframes" / "bin" / "hyperframes.mjs"
    v = ejecutar(["node", str(hf), "--version"]).stdout.strip().splitlines()[-1]
    print("   Preparando el navegador con el que HyperFrames dibuja cada fotograma…", flush=True)
    ejecutar(["node", str(hf), "browser", "ensure"], env=entorno_hyperframes())
    ok(f"HyperFrames {v} responde y tiene su navegador listo")
    return v


def paso_python() -> str:
    paso("4/7 · Entorno de Python del kit: Whisper (transcripción) y MediaPipe (la persona)")
    if sys.version_info < (3, 9):
        fallo(f"Tu Python es {sys.version.split()[0]} y hace falta 3.9 o más nuevo.",
              "Instala Python desde https://www.python.org/downloads/ y repite /empezar.")
    py = python_venv()
    if not py.exists():
        ejecutar([sys.executable, "-m", "venv", str(VENV)])
        ok("Entorno .venv creado")
    motor = "mlx-whisper" if ES_APPLE_SILICON else "faster-whisper"
    modulo = "mlx_whisper" if ES_APPLE_SILICON else "faster_whisper"
    if subprocess.run([str(py), "-c", f"import {modulo}"], capture_output=True).returncode != 0:
        print(f"   Instalando {motor} (1 o 2 minutos la primera vez)…", flush=True)
        ejecutar([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check", motor])
    if not ES_APPLE_SILICON:
        # PyAV 19 quitó «metadata_errors», con el que faster-whisper 1.2.1 lee el audio
        ejecutar([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check", "av<19"])
    v = ejecutar([str(py), "-c", f"import importlib.metadata as m;print(m.version('{motor}'))"]).stdout.strip()
    ok(f"{motor} {v} ({'usa la GPU de tu Mac' if ES_APPLE_SILICON else 'usa el procesador'})")
    # MediaPipe (Google, Apache-2.0): encuentra la cara y recorta a la persona para los textos por detrás
    if subprocess.run([str(py), "-c", "import mediapipe, cv2, numpy"], capture_output=True).returncode != 0:
        print("   Instalando MediaPipe (la cara y el recorte de la persona, en local)…", flush=True)
        ejecutar([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check", "mediapipe", "numpy"])
    codigo = ("import sys;sys.path.insert(0,r'%s');import persona;"
              "[persona.modelo(n) for n in persona.URLS_MODELOS];print('ok')" % (KIT / "herramientas"))
    r = subprocess.run([str(py), "-c", codigo], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        print(r.stdout[-1500:])
        fallo("No he podido preparar MediaPipe y sus modelos.", "Comprueba tu conexión y repite /empezar.")
    ok("MediaPipe y su modelo listos (cara y recorte de la persona)")
    return f"{motor} {v}"


def paso_modelo() -> str:
    paso("5/7 · Modelo de Whisper (se descarga una vez, luego funciona sin internet)")
    marca = leer_json(BRAND) if BRAND.exists() else leer_json(BRAND_EJEMPLO)
    modelo = marca.get("transcripcion", {}).get("modelo", "turbo")
    # prueba real: transcribir 3 s de voz sintética no hace falta; basta con cargar el modelo
    wav = PRUEBAS / "_prueba.wav"
    wav.parent.mkdir(exist_ok=True)
    ejecutar(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
              "-ac", "1", "-ar", "16000", str(wav)])
    codigo = (
        "import sys;sys.path.insert(0,r'%s');from transcribir import transcribir_audio;"
        "transcribir_audio(r'%s','es','%s',[]);print('ok')" % (KIT / "herramientas", wav, modelo))
    t0 = time.time()
    print(f"   Descargando y probando el modelo «{modelo}» (la primera vez puede tardar 1-3 min)…", flush=True)
    r = subprocess.run([str(python_venv()), "-c", codigo], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    wav.unlink(missing_ok=True)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        fallo("Whisper no ha podido cargar el modelo.",
              "Comprueba tu conexión y repite /empezar. Si tu internet es lento, pon \"modelo\": \"small\" en brand.json.")
    ok(f"Modelo «{modelo}» listo ({time.time() - t0:.0f} s)")
    # el alineador fino de palabras (subtítulos al centésimo): solo hay modelo para algunos idiomas
    idioma = marca.get("transcripcion", {}).get("idioma", "es")
    codigo = ("import sys;sys.path.insert(0,r'%s');import comun, alinear;"
              "print(alinear.descargar() if alinear.disponible('%s') else 'no')" % (KIT / "herramientas", idioma))
    r = subprocess.run([str(python_venv()), "-c", codigo], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        aviso("No he podido bajar el alineador de palabras: los subtítulos usarán los tiempos de Whisper.")
    elif r.stdout.strip().splitlines()[-1] != "no":
        ok("Alineador de palabras listo (cada palabra del subtítulo, al centésimo)")
    return modelo


def descargar_fuentes(marca: dict) -> list[str]:
    """Tipografías de la marca y de los tres estilos del kit, todas de Google Fonts (licencia OFL).
    Los pesos terminados en «i» son cursivas (por ejemplo 500i)."""
    from animar import FUENTES_ESTILO
    carpeta = MARCA / "fuentes"
    carpeta.mkdir(parents=True, exist_ok=True)
    hechas = []
    familias: dict = {}
    familias.setdefault(marca["tipografia"].get("titulos", "Inter"), []).extend([700, 800])
    familias.setdefault(marca["tipografia"].get("texto", "Inter"), []).extend([500, 600, 700])
    for fam, pesos in FUENTES_ESTILO.items():
        familias.setdefault(fam, []).extend(pesos)
    for fam, pesos in familias.items():
        for peso in dict.fromkeys(pesos):
            cursiva = str(peso).endswith("i")
            num = str(peso).rstrip("i")
            destino = carpeta / f"{fam.replace(' ', '_')}-{num}{'i' if cursiva else ''}.woff2"
            if destino.exists() and destino.stat().st_size > 1000:
                hechas.append(destino.name)
                continue
            eje = f"ital,wght@1,{num}" if cursiva else f"wght@{num}"
            url = f"https://fonts.googleapis.com/css2?family={fam.replace(' ', '+')}:{eje}&display=block"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA_WOFF2})
                css = urllib.request.urlopen(req, timeout=20).read().decode()
                # el bloque «latin» incluye tildes y eñes
                bloques = re.findall(r"/\* ([\w-]+) \*/[^}]*?src: url\((https://[^)]+\.woff2)\)", css)
                elegida = next((u for nombre, u in bloques if nombre == "latin"), None) or \
                    re.findall(r"url\((https://[^)]+\.woff2)\)", css)[-1]
                destino.write_bytes(urllib.request.urlopen(elegida, timeout=30).read())
                hechas.append(destino.name)
            except Exception as e:  # sin internet o fuente que no está en Google Fonts
                aviso(f"No he podido descargar {fam} {peso} ({type(e).__name__}). Se usará una fuente del sistema.")
    return hechas


def paso_marca() -> list[str]:
    paso("6/7 · Tipografías de tu marca y de los tres estilos (Google Fonts, se guardan dentro del kit)")
    marca = leer_json(BRAND) if BRAND.exists() else leer_json(BRAND_EJEMPLO)
    hechas = descargar_fuentes(marca)
    ok(f"{len(hechas)} archivos de fuente listos en marca/fuentes")
    # carpetas de tus assets y la caja registradora de ejemplo (sintetizada por el kit)
    for c in ("musica", "sonidos", "logos", "broll"):
        (MARCA / c).mkdir(parents=True, exist_ok=True)
    if not (MARCA / "sonidos" / "caja.wav").exists():
        subprocess.run([str(python_venv()), str(KIT / "herramientas" / "kit.py"), "sonido", "caja"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ok("Carpetas de tus assets listas: marca/musica, marca/sonidos, marca/logos y marca/broll")
    return hechas


def paso_prueba_render() -> float:
    paso("7/7 · Prueba real: animar y renderizar 1,5 s (con el logo en 3D) con fondo transparente")
    import animar
    marca = leer_json(BRAND) if BRAND.exists() else leer_json(BRAND_EJEMPLO)
    plan = {"subtitulos": True, "beats": [
        {"id": "logo", "tipo": "logo", "inicio": 0.0, "duracion": 1.5},
        {"id": "rotulo", "tipo": "rotulo", "inicio": 0.0, "duracion": 1.5,
         "titulo": marca["canal"]["nombre"], "subtitulo": marca["canal"]["handle"]}]}
    palabras = [{"w": "Prueba", "s": 0.1, "e": 0.5}, {"w": "superada", "s": 0.5, "e": 0.9}]
    dest = PRUEBAS / "_prueba-render"
    animar.preparar_proyecto(dest, marca)
    html_txt, _s, _d, _x = animar.construir(marca, plan, palabras, 1.5, "horizontal", None, None, dest)
    (dest / "index.html").write_text(html_txt, encoding="utf-8")
    salida = dest / "prueba.mov"
    t0 = time.time()
    animar.hyperframes("render", str(dest), "--format", "mov", "--fps", "30", "--quality", "draft",
                       "--output", str(salida), "--quiet")
    if not salida.exists() or salida.stat().st_size == 0:
        fallo("HyperFrames no ha generado el vídeo de prueba.", "Lanza /comprobar para ver el detalle.")
    seg = time.time() - t0
    shutil.rmtree(dest, ignore_errors=True)
    ok(f"Render de prueba correcto ({seg:.0f} s)")
    return seg


def paso_skills_hyperframes() -> None:
    """Opcional: las skills oficiales de HyperFrames, solo para este proyecto (en la skill, no: no hay un
    proyecto fijo donde ponerlas, y el kit funciona sin ellas)."""
    destino = RAIZ / ".claude" / "skills" / "hyperframes-core"
    if EN_SKILL or destino.exists():
        return
    npx = "npx.cmd" if ES_WINDOWS else "npx"
    r = subprocess.run([npx, "-y", "skills@latest", "add", "heygen-com/hyperframes", "-a", "claude-code",
                        "-s", "hyperframes-core", "-s", "hyperframes-animation", "-s", "hyperframes-cli",
                        "-y", "--copy"], cwd=str(RAIZ), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode == 0 and destino.exists():
        ok("Skills oficiales de HyperFrames añadidas a este proyecto (para retocar animaciones a mano)")
    else:
        aviso("No he podido añadir las skills oficiales de HyperFrames. No pasa nada: el kit funciona sin ellas.")


def main(argv: list[str]) -> None:
    t0 = time.time()
    print("Instalando el Kit Editor de Vídeo. Si algo ya está, lo salto.", flush=True)
    estado = {
        "ffmpeg": paso_ffmpeg(),
        "node": paso_node(),
        "hyperframes": paso_npm(),
        "whisper": paso_python(),
        "modelo": paso_modelo(),
        "fuentes": paso_marca(),
        "render_prueba_s": round(paso_prueba_render(), 1),
    }
    if "--sin-skills" not in argv:
        paso_skills_hyperframes()
    estado["instalado"] = time.strftime("%Y-%m-%d %H:%M")
    estado["segundos_instalacion"] = round(time.time() - t0, 1)
    escribir_json(ESTADO, estado)
    print(f"\nTodo listo en {estado['segundos_instalacion']:.0f} s. Ya puedes editar: /editar <tu-video>")


if __name__ == "__main__":
    main(sys.argv[1:])

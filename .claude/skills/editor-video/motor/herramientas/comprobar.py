"""/comprobar · Chequeo previo y ensayo general (para antes de grabar o de editar en directo).

  kit.py comprobar            -> revisa todo y hace un ensayo completo con 8 s de vídeo
  kit.py comprobar --rapido   -> solo revisa, sin ensayo

No instala nada: si algo falla, dice exactamente qué hacer.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from comun import (BRAND, ENTORNO, ES_APPLE_SILICON, KIT, MARCA, RAIZ, TRABAJO, cargar_marca, ejecutar,
                   entorno_hyperframes, leer_json, python_venv, ruta_proyecto)

RESULTADOS: list[tuple[str, bool, str]] = []


def marca_resultado(nombre: str, bien: bool, detalle: str) -> bool:
    RESULTADOS.append((nombre, bien, detalle))
    print(f"   [{'OK' if bien else 'FALLO'}] {nombre}: {detalle}", flush=True)
    return bien


def salida(cmd: list[str], env: dict | None = None) -> str | None:
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120,
                           env={**os.environ, **env} if env else None)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def revisar() -> None:
    print("==> Revisando piezas", flush=True)
    v = salida(["ffmpeg", "-version"])
    marca_resultado("ffmpeg", bool(v), " ".join(v.split()[:3]) if v else "no responde · lanza /empezar")
    v = salida(["node", "--version"]) or ""
    mayor = int(re.sub(r"[^\d.]", "", v).split(".")[0] or 0) if v else 0
    marca_resultado("Node.js", mayor >= 22, v or "no está · lanza /empezar")
    hf = ENTORNO / "node_modules" / "hyperframes" / "bin" / "hyperframes.mjs"
    v = salida(["node", str(hf), "--version"]) if hf.exists() else None
    marca_resultado("HyperFrames", bool(v), f"versión {v.splitlines()[-1]}" if v else "no instalado · lanza /empezar")
    if v:
        p = salida(["node", str(hf), "browser", "path"], entorno_hyperframes())
        marca_resultado("Navegador de render", bool(p and Path(p.splitlines()[-1]).exists()),
                        "listo" if p else "falta · lanza /empezar")
    py = python_venv()
    mod = "mlx_whisper" if ES_APPLE_SILICON else "faster_whisper"
    okw = py.exists() and subprocess.run([str(py), "-c", f"import {mod}"], capture_output=True).returncode == 0
    marca_resultado("Whisper", okw, mod if okw else "falta el entorno .venv · lanza /empezar")
    try:  # el alineador fino de palabras no es imprescindible: sin él, los tiempos de Whisper
        import alinear
        from huggingface_hub import hf_hub_download
        idioma = cargar_marca().get("transcripcion", {}).get("idioma", "es")
        if alinear.disponible(idioma):
            hf_hub_download(alinear.REPO, alinear.MODELO, revision=alinear.REVISION, local_files_only=True)
            marca_resultado("Alineador de palabras", True, "listo (subtítulos al centésimo)")
    except Exception:
        marca_resultado("Alineador de palabras", True, "se bajará la primera vez que transcribas (355 MB)")
    okm = py.exists() and subprocess.run([str(py), "-c", "import mediapipe, cv2, numpy"],
                                         capture_output=True).returncode == 0
    modelo_ok = (ENTORNO / "modelos" / "selfie_multiclass.tflite").exists()
    marca_resultado("MediaPipe (la persona)", okm and modelo_ok,
                    "listo con su modelo" if okm and modelo_ok else "falta · lanza /empezar")
    three = (ENTORNO / "node_modules" / "three" / "build" / "three.module.js").exists()
    marca_resultado("Three.js (el 3D)", three, "listo" if three else "falta · lanza /empezar")
    marca_resultado("brand.json", BRAND.exists(), "tu marca" if BRAND.exists() else
                    "no existe todavía: se usará la de ejemplo · lanza /empezar para poner la tuya")
    marca = cargar_marca()
    colores_ok = all(re.fullmatch(r"#[0-9a-fA-F]{6}", marca["colores"].get(k, "")) for k in ("principal", "acento"))
    marca_resultado("Colores", colores_ok, f"{marca['colores'].get('principal')} y {marca['colores'].get('acento')}")
    logo = marca.get("logo")
    marca_resultado("Logo", (not logo) or ruta_proyecto(logo).exists(),
                    logo if logo and ruta_proyecto(logo).exists() else ("sin logo: se usan tus iniciales" if not logo else f"no encuentro {logo}"))
    fuentes = list((MARCA / "fuentes").glob("*.woff2")) if (MARCA / "fuentes").exists() else []
    marca_resultado("Tipografías", bool(fuentes), f"{len(fuentes)} archivos" if fuentes else "no descargadas · lanza /empezar")
    for clave in ("brutos", "finales"):
        c = Path(marca.get("carpetas", {}).get(clave, clave)).expanduser()
        c = c if c.is_absolute() else RAIZ / c
        try:
            c.mkdir(parents=True, exist_ok=True)
            prueba = c / ".kit-prueba"
            prueba.write_text("ok")
            prueba.unlink()
            marca_resultado(f"Carpeta de {clave}", True, str(c))
        except OSError:
            marca_resultado(f"Carpeta de {clave}", False, f"no puedo escribir en {c}")
    # plantillas y assets de marca/
    try:
        import estilo as E
        malas = [n for n in E.existentes() if E.validar(E.cargar(n))]
        act = E.nombre_activo()
        marca_resultado("Plantillas", not malas and (E.DIR / f"{act}.json").exists(),
                        f"{len(E.existentes())} ({', '.join(E.existentes())}); activa: {act}" if not malas
                        else f"mal escritas: {', '.join(malas)} · kit.py estilo validar <nombre>")
    except Exception as ex:
        marca_resultado("Plantillas", False, f"no he podido leerlas ({type(ex).__name__})")
    exts = (".wav", ".mp3", ".m4a", ".aac", ".aif", ".aiff", ".ogg", ".flac")
    mus = sorted(f.name for f in (MARCA / "musica").glob("*") if f.suffix.lower() in exts) if (MARCA / "musica").exists() else []
    marca_resultado("Música de cama", True, ", ".join(mus) if mus else "ninguna en marca/musica/ (opcional)")
    mapa = MARCA / "sonidos" / "mapa.json"
    if mapa.exists():
        try:
            import json
            m = json.loads(mapa.read_text(encoding="utf-8"))
            faltan = [v if isinstance(v, str) else v.get("archivo", "?") for k, v in m.items() if not k.startswith("_")
                      and not (MARCA / "sonidos" / (v if isinstance(v, str) else v.get("archivo", ""))).exists()]
            n = len([k for k in m if not k.startswith("_")])
            marca_resultado("Sonidos de marca", not faltan, f"{n} palabra(s) en mapa.json" if not faltan
                            else f"faltan en marca/sonidos/: {', '.join(sorted(set(faltan)))}")
        except Exception:
            marca_resultado("Sonidos de marca", False, "marca/sonidos/mapa.json no es un JSON válido")
    logos = [f for f in (MARCA / "logos").glob("*") if f.suffix.lower() in (".svg", ".png", ".webp")] \
        if (MARCA / "logos").exists() else []
    marca_resultado("Logos 3D", True, f"{len(logos)} en marca/logos/")
    libre = shutil.disk_usage(RAIZ).free / 1e9
    marca_resultado("Espacio en disco", libre > 5, f"{libre:.0f} GB libres")


def ensayo() -> None:
    print("\n==> Ensayo general con 8 s de vídeo (transcribir, cortar, plan, animar, componer, verificar)", flush=True)
    fuente = KIT / "demo" / "antes.mp4"
    carpeta = TRABAJO / "_ensayo"
    shutil.rmtree(carpeta, ignore_errors=True)
    carpeta.mkdir(parents=True)
    clip = carpeta / "ensayo.mp4"
    if fuente.exists():
        ejecutar(["ffmpeg", "-v", "error", "-y", "-ss", "2", "-t", "8", "-i", str(fuente),
                  "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", str(clip)])
    else:
        ejecutar(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=30:duration=8",
                  "-f", "lavfi", "-i", "sine=frequency=300:duration=8", "-c:v", "libx264", "-preset",
                  "ultrafast", "-c:a", "aac", "-shortest", str(clip)])
    os.environ["KIT_FINALES"] = str(carpeta / "finales")
    py = str(python_venv()) if python_venv().exists() else sys.executable
    kit = str(KIT / "herramientas" / "kit.py")
    pasos = [
        ("Transcribir", ["transcribir", str(clip)]),
        ("Cortar (analizar)", ["cortar", "analizar", str(clip)]),
        ("Cortar (aplicar)", ["cortar", "aplicar", str(clip)]),
        ("Persona", ["persona", str(clip)]),
        ("Plan", ["plan", "borrador", str(clip)]),
        ("Plan aprobado", ["plan", "aprobar", str(clip)]),
        ("Animar", ["animar", str(clip)]),
        ("Componer", ["componer", str(clip)]),
        ("Verificar", ["verificar", str(clip)]),
    ]
    t_total = time.time()
    for nombre, args in pasos:
        t0 = time.time()
        r = subprocess.run([py, kit, *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                           env=os.environ.copy())
        bien = r.returncode == 0
        marca_resultado(f"Ensayo · {nombre}", bien, f"{time.time() - t0:.1f} s" if bien else "falló")
        if not bien:
            print("\n".join(r.stdout.splitlines()[-25:]))
            break
    else:
        marca_resultado("Ensayo completo", True, f"{time.time() - t_total:.0f} s para 8 s de vídeo")


def main(argv: list[str]) -> None:
    print("Chequeo previo del Kit Editor de Vídeo\n", flush=True)
    revisar()
    if "--rapido" not in argv and all(b for n, b, _d in RESULTADOS if n not in ("brand.json", "Sonidos de marca")):
        ensayo()
    fallos = [n for n, b, _ in RESULTADOS if not b and n != "brand.json"]

    print()
    if fallos:
        print(f"HAY {len(fallos)} {'COSA' if len(fallos) == 1 else 'COSAS'} QUE ARREGLAR: {', '.join(fallos)}. Lanza /empezar y repite /comprobar.")
        sys.exit(1)
    print("TODO EN VERDE. Puedes grabar tranquilo.")


if __name__ == "__main__":
    main(sys.argv[1:])

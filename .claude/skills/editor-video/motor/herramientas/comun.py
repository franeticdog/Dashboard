"""Utilidades comunes del Kit Editor de Vídeo (D-IA · El Campamento).

Solo usa la biblioteca estándar de Python, para que funcione antes de instalar nada.
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

# Sitios distintos cuando el kit va empaquetado como skill (existe ubicaciones.json junto al código):
#   KIT      el código: herramientas/, estilos/, demo/ (la carpeta «motor» de la skill)
#   ENTORNO  lo pesado, instalado una vez por equipo: .venv, node_modules, modelos, temporales
#   RAIZ     la carpeta del proyecto: brutos, finales y trabajo
#   la marca brand.json y marca/: los del proyecto o un perfil guardado en MARCAS que comparten todos los
#            proyectos de esa marca (proyecto.json dice cuál: {"marca": "grupo-nergia"}), igual que en el kit
#            clásico todos los vídeos comparten brand.json: correcciones, glosario y plantilla valen para todos
# Sin ubicaciones.json (el kit clásico, todo en una carpeta) todo está en la misma.
KIT = Path(__file__).resolve().parent.parent
_UBICACIONES = KIT / "ubicaciones.json"
EN_SKILL = _UBICACIONES.exists()
MARCADORES = ("proyecto.json", "brand.json")  # lo que convierte una carpeta en un proyecto


def _leer(ruta: Path) -> dict:
    try:
        d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def _raiz_proyecto() -> Path:
    """La carpeta del proyecto: la de KIT_PROYECTO o, en la skill, la primera con proyecto.json o brand.json
    subiendo desde donde se lanza la orden (si no hay ninguna, esa misma: es un proyecto nuevo)."""
    if os.environ.get("KIT_PROYECTO"):
        return Path(os.environ["KIT_PROYECTO"]).expanduser().resolve()
    if not EN_SKILL:
        return KIT
    aqui = Path.cwd().resolve()
    return next((c for c in (aqui, *aqui.parents) if any((c / m).exists() for m in MARCADORES)), aqui)


_U = _leer(_UBICACIONES)  # rutas absolutas o relativas a KIT (así la carpeta entera se puede mover)
ENTORNO = (Path(os.environ["KIT_ENTORNO"]) if os.environ.get("KIT_ENTORNO")
           else (KIT / _U.get("entorno", ".")).resolve())
MARCAS = (KIT / _U["marcas"]).resolve() if _U.get("marcas") else ENTORNO.parent / "marcas"  # marcas guardadas
RAIZ = _raiz_proyecto()
TRABAJO = RAIZ / "trabajo"
PROYECTO_JSON = RAIZ / "proyecto.json"


def perfil_de_marca(nombre: str) -> Path:
    """La carpeta de un perfil de marca guardado: un nombre de MARCAS o una ruta."""
    p = Path(str(nombre)).expanduser()
    return p if p.is_absolute() else MARCAS / str(nombre)


def _sitio_marca() -> Path:
    """Dónde están brand.json y marca/: en el proyecto, o en el perfil que diga proyecto.json."""
    if (RAIZ / "brand.json").exists():
        return RAIZ
    perfil = _leer(PROYECTO_JSON).get("marca")
    return perfil_de_marca(perfil) if perfil else RAIZ


SITIO_MARCA = _sitio_marca()
BRAND = SITIO_MARCA / "brand.json"
MARCA = SITIO_MARCA / "marca"
BRAND_EJEMPLO = KIT / "brand.ejemplo.json"
VENV = ENTORNO / ".venv"
os.environ["KIT_ENTORNO"] = str(ENTORNO)  # los procesos hijos: fuente3d.mjs busca ahí fontkit
os.environ["KIT_PROYECTO"] = str(RAIZ)    # y el relanzamiento dentro de .venv sigue en el mismo proyecto
ES_WINDOWS = platform.system() == "Windows"
ES_MAC = platform.system() == "Darwin"
ES_APPLE_SILICON = ES_MAC and platform.machine() == "arm64"

# El modelo de Whisper se baja dentro del kit (modelos/), no a la caché del disco del sistema
os.environ.setdefault("HF_HOME", str(ENTORNO / "modelos" / "huggingface"))

# En Windows, HyperFrames guarda los fotogramas de cada render en la carpeta temporal del sistema.
# Si ese disco va justo (menos de 10 GB libres), los temporales van dentro del kit (trabajo/_tmp).
# En la skill, siempre junto al entorno: así nada de lo que hace el kit cae en el disco del sistema
if EN_SKILL:
    (ENTORNO / "_tmp").mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = os.environ["TMPDIR"] = str(ENTORNO / "_tmp")
    # y lo que se descargue al instalar (paquetes de Python y de Node), también
    os.environ.setdefault("PIP_CACHE_DIR", str(ENTORNO / "cache" / "pip"))
    os.environ.setdefault("npm_config_cache", str(ENTORNO / "cache" / "npm"))
elif ES_WINDOWS:
    try:
        _libre = shutil.disk_usage(os.environ.get("TEMP") or os.environ.get("TMP") or str(RAIZ)).free
    except OSError:
        _libre = None
    if _libre is not None and _libre < 10 * 1024 ** 3:
        (TRABAJO / "_tmp").mkdir(parents=True, exist_ok=True)
        os.environ["TEMP"] = os.environ["TMP"] = str(TRABAJO / "_tmp")

# En Windows, el ffmpeg que instala winget no entra en el PATH hasta reiniciar Claude Code:
# se busca en la carpeta donde lo deja winget
if ES_WINDOWS and not shutil.which("ffmpeg"):
    _winget = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet"
    _bin = next((c for c in [_winget / "Links", *sorted(_winget.glob("Packages/Gyan.FFmpeg*/*/bin"), reverse=True)]
                 if (c / "ffmpeg.exe").exists()), None)
    if _bin:
        os.environ["PATH"] = str(_bin) + os.pathsep + os.environ.get("PATH", "")

FORMATOS = {
    "horizontal": (1920, 1080),
    "vertical": (1080, 1920),
}


# ---------------------------------------------------------------- mensajes
def paso(texto: str) -> None:
    print(f"\n==> {texto}", flush=True)


def ok(texto: str) -> None:
    print(f"   [OK] {texto}", flush=True)


def aviso(texto: str) -> None:
    print(f"   [AVISO] {texto}", flush=True)


def fallo(texto: str, como_arreglarlo: str | None = None, salir: bool = True) -> None:
    print(f"   [FALLO] {texto}", flush=True)
    if como_arreglarlo:
        print(f"   Cómo arreglarlo: {como_arreglarlo}", flush=True)
    if salir:
        sys.exit(1)


# ---------------------------------------------------------------- procesos
def ejecutar(cmd: list[str], cwd: Path | None = None, capturar: bool = True,
             comprobar: bool = True, env: dict | None = None) -> subprocess.CompletedProcess:
    entorno = os.environ.copy()
    if env:
        entorno.update(env)
    res = subprocess.run(
        cmd, cwd=str(cwd) if cwd else None, env=entorno,
        stdout=subprocess.PIPE if capturar else None,
        stderr=subprocess.STDOUT if capturar else None,
        text=True, encoding="utf-8", errors="replace",
        shell=False,
    )
    if comprobar and res.returncode != 0:
        salida = (res.stdout or "")[-3000:]
        raise RuntimeError(f"Falló: {' '.join(map(str, cmd))[:300]}\n{salida}")
    return res


def npx() -> str:
    return "npx.cmd" if ES_WINDOWS else "npx"


def npm() -> str:
    return "npm.cmd" if ES_WINDOWS else "npm"


def python_venv() -> Path:
    if ES_WINDOWS:
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def entorno_hyperframes() -> dict:
    """Variables para lanzar HyperFrames. En la skill, su «carpeta de usuario» es ENTORNO/home: ahí guarda su
    navegador y sus cachés (~/.cache/hyperframes), en el mismo disco que el entorno y no en el del sistema."""
    env = {"HYPERFRAMES_TELEMETRY": "0", "DO_NOT_TRACK": "1"}
    if EN_SKILL:
        casa = ENTORNO / "home"
        casa.mkdir(parents=True, exist_ok=True)
        env.update({"USERPROFILE": str(casa), "HOME": str(casa)})
    return env


def ffprobe_json(ruta: Path) -> dict:
    res = ejecutar(["ffprobe", "-v", "error", "-print_format", "json",
                    "-show_format", "-show_streams", str(ruta)])
    return json.loads(res.stdout)


def info_video(ruta: Path) -> dict:
    d = ffprobe_json(ruta)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    if v is None:
        raise RuntimeError(f"{ruta.name} no tiene pista de vídeo")
    w, h = int(v["width"]), int(v["height"])
    # vídeos de móvil rotados
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = abs(int(float(sd["rotation"])))
    if rot in (90, 270):
        w, h = h, w
    num, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    return {
        "ancho": w, "alto": h, "fps": round(fps, 3),
        "duracion": float(d["format"].get("duration", 0)),
        "tiene_audio": a is not None,
        "orientacion": "vertical" if h > w else "horizontal",
    }


# ---------------------------------------------------------------- datos
def leer_json(ruta: Path, defecto=None):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except FileNotFoundError:
        if defecto is not None:
            return defecto
        raise


def escribir_json(ruta: Path, datos) -> None:
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def cargar_marca() -> dict:
    if BRAND.exists():
        return leer_json(BRAND)
    aviso("Todavía no hay brand.json: uso la marca de ejemplo (brand.ejemplo.json). "
          "Lanza /empezar para poner la tuya.")
    return leer_json(BRAND_EJEMPLO)


def ruta_proyecto(p) -> Path:
    """Una ruta escrita en brand.json o en el plan: absoluta, «marca/…» (la carpeta de marca, esté donde esté)
    o relativa a la carpeta del proyecto."""
    p = Path(str(p)).expanduser()
    if p.is_absolute():
        return p
    if p.parts and p.parts[0].lower() == "marca":
        return MARCA.joinpath(*p.parts[1:])
    return RAIZ / p


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t[:60] or "video"


def carpeta_trabajo(video: Path) -> Path:
    c = TRABAJO / slug(Path(video).stem)
    c.mkdir(parents=True, exist_ok=True)
    return c


EXT_VIDEO = (".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mts")
_avisados: set = set()


def carpeta_brutos() -> Path:
    marca = cargar_marca()
    brutos = Path(marca.get("carpetas", {}).get("brutos", "brutos")).expanduser()
    return brutos if brutos.is_absolute() else RAIZ / brutos


def _norm_nombre(t: str) -> str:
    t = unicodedata.normalize("NFKD", Path(t).stem.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", t)


def buscar_parecido(nombre: str) -> Path | None:
    """Si el vídeo no está donde dice, lo busca por nombre parecido en la carpeta de brutos y en la
    raíz del kit (y en sus subcarpetas de primer nivel, que es donde suele caer por error)."""
    import difflib
    brutos = carpeta_brutos()
    sitios = [brutos, RAIZ] + [c for c in sorted(RAIZ.iterdir()) if c.is_dir() and not c.name.startswith(".")
                                and c.name not in ("node_modules", "trabajo", "finales", "herramientas", "modelos",
                                                   "demo", "estilos", "marca") and c != brutos]
    cands = []
    for s in sitios:
        if s.exists():
            cands += [f for f in s.iterdir() if f.is_file() and f.suffix.lower() in EXT_VIDEO]
    if not cands:
        return None
    buscado = _norm_nombre(nombre)
    if not buscado:
        return None
    mejor, nota = None, 0.0
    for c in cands:
        n = _norm_nombre(c.name)
        r = difflib.SequenceMatcher(None, buscado, n).ratio()
        if buscado in n or n in buscado:
            r = max(r, 0.8)
        if r > nota:
            mejor, nota = c, r
    return mejor if nota >= 0.6 else None


def resolver_video(nombre: str) -> Path:
    """Acepta ruta completa o un nombre de la carpeta de brutos. Si no está, busca uno de nombre
    parecido en brutos/ y en la raíz del kit, lo usa y lo avisa."""
    p = Path(nombre).expanduser()
    if p.exists():
        return p.resolve()
    brutos = carpeta_brutos()
    for cand in [brutos / nombre] + sorted(brutos.glob(f"{nombre}*")):
        if cand.exists():
            return cand.resolve()
    parecido = buscar_parecido(nombre)
    if parecido:
        if nombre not in _avisados:
            _avisados.add(nombre)
            donde = parecido.parent.name if parecido.parent != RAIZ else \
                ("la carpeta del proyecto" if EN_SKILL else "la raíz del kit")
            aviso(f"No encuentro «{nombre}» tal cual, pero he encontrado «{parecido.name}» en {donde}. "
                  f"Uso ese. Si no es el que querías, dímelo.")
        return parecido.resolve()
    fallo(f"No encuentro el vídeo «{nombre}» ni ninguno de nombre parecido.",
          f"Déjalo en la carpeta de brutos ({brutos}) o pasa la ruta completa.")
    raise SystemExit(1)


def carpeta_finales() -> Path:
    if os.environ.get("KIT_FINALES"):  # lo usa el ensayo de /comprobar
        f = Path(os.environ["KIT_FINALES"])
        f.mkdir(parents=True, exist_ok=True)
        return f
    marca = cargar_marca()
    f = Path(marca.get("carpetas", {}).get("finales", "finales")).expanduser()
    if not f.is_absolute():
        f = RAIZ / f
    f.mkdir(parents=True, exist_ok=True)
    return f


# ---------------------------------------------------------------- tiempos
class Cronometro:
    """Apunta cuánto tarda cada fase en trabajo/<video>/tiempos.json."""

    def __init__(self, carpeta: Path, fase: str):
        self.ruta = Path(carpeta) / "tiempos.json"
        self.fase = fase

    def __enter__(self):
        self.t0 = time.time()
        return self

    def __exit__(self, *exc):
        seg = round(time.time() - self.t0, 1)
        datos = leer_json(self.ruta, defecto={})
        datos[self.fase] = seg
        escribir_json(self.ruta, datos)
        print(f"   (fase «{self.fase}»: {seg} s)", flush=True)
        return False


def hex_a_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgba(h: str, alfa: float) -> str:
    r, g, b = hex_a_rgb(h)
    return f"rgba({r},{g},{b},{alfa})"


def fmt_t(seg: float) -> str:
    m, s = divmod(max(0.0, seg), 60)
    return f"{int(m)}:{s:05.2f}"


def frases_subtitulo(palabras: list[dict]) -> list[list[dict]]:
    """Frases completas para los subtítulos «solo en los momentos»: se cortan en cada signo de
    puntuación, pero un trozo de menos de 3 palabras («Y no,») se une al siguiente para que el
    subtítulo nunca salga a trozos."""
    import re as _re
    trozos, actual = [], []
    for w in palabras:
        actual.append(w)
        if _re.search(r"[.!?…,:;]$", w["w"]):
            trozos.append(actual)
            actual = []
    if actual:
        trozos.append(actual)
    frases, pendiente = [], []
    for t in trozos:
        pendiente += t
        if len(pendiente) >= 3:
            frases.append(pendiente)
            pendiente = []
    if pendiente:
        if frases:
            frases[-1] = frases[-1] + pendiente
        else:
            frases.append(pendiente)
    return frases


def frase_cabe(f: list[dict], a: float, b: float) -> bool:
    """La frase entera cae dentro del tramo [a, b] marcado con subtítulo."""
    return a - 0.15 <= f[0]["s"] and f[-1]["e"] <= b + 0.35

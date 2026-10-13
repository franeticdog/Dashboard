"""Diseño de sonido del kit: efectos y cama musical SINTETIZADOS aquí mismo (sin muestras de
terceros, sin licencias que revisar) y mezcla con la voz.

  kit.py sonido muestras      -> escribe los efectos en trabajo/_sonidos/ para escucharlos
  kit.py sonido caja          -> vuelve a sintetizar marca/sonidos/caja.wav (el ejemplo del mapa)

Criterio (del proyecto Motion de D-IA):
- Cada golpe importante son DOS sonidos: «aire» (agudos, da el movimiento) y «sub» (graves, da
  el peso), el aire 60-100 ms antes. Nada de pitidos de interfaz en la banda de la voz.
- Máximo dos sonidos a la vez; en ráfagas se alternan variantes, nunca el mismo N veces.
- La música, si se usa, va muy baja (unos 25 dB por debajo de la voz) y plana, sin sorpresas.
"""
from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000


# ------------------------------------------------------------------ utilidades
def _rng(semilla: int) -> np.random.Generator:
    return np.random.default_rng(semilla)


def _env(n: int, ataque: float, caida: float, curva: float = 4.0) -> np.ndarray:
    t = np.arange(n) / SR
    a = np.clip(t / max(ataque, 1e-4), 0, 1) ** 1.5
    d = np.exp(-np.maximum(t - ataque, 0) / max(caida, 1e-4) * (curva / 4))
    return a * d


def _fft_filtro(x: np.ndarray, bajo: float | None = None, alto: float | None = None,
                orden: float = 2.0) -> np.ndarray:
    """Paso alto (bajo=Hz) y/o paso bajo (alto=Hz) suaves, en frecuencia."""
    n = len(x)
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if bajo:
        g *= 1 / np.sqrt(1 + (bajo / np.maximum(f, 1e-3)) ** (2 * orden))
    if alto:
        g *= 1 / np.sqrt(1 + (f / alto) ** (2 * orden))
    if X.ndim == 2:
        g = g[:, None]
    return np.fft.irfft(X * g, n=n, axis=0)


def _barrido(ruido: np.ndarray, centros: np.ndarray, q: float = 1.2) -> np.ndarray:
    """Filtro paso banda de estado variable cuyo centro cambia muestra a muestra."""
    y = np.zeros_like(ruido)
    lp = bp = 0.0
    amort = 1.0 / q
    f = 2 * np.sin(np.pi * np.clip(centros, 20, SR / 6) / SR)
    for i in range(len(ruido)):
        hp = ruido[i] - lp - amort * bp
        bp += f[i] * hp
        lp += f[i] * bp
        y[i] = bp
    return y


def _estereo(izq: np.ndarray, der: np.ndarray | None = None, pan: float = 0.0) -> np.ndarray:
    der = izq if der is None else der
    a = (pan + 1) * np.pi / 4
    return np.stack([izq * np.cos(a) * 1.414, der * np.sin(a) * 1.414], axis=1)


def _reverb(x: np.ndarray, cola: float = 0.9, mezcla: float = 0.18, semilla: int = 7) -> np.ndarray:
    n_ir = int(SR * cola)
    r = _rng(semilla)
    ir = r.standard_normal((n_ir, 2)) * np.exp(-np.arange(n_ir) / (SR * cola / 5))[:, None]
    ir = _fft_filtro(ir, alto=6000) * 0.02
    n = len(x) + n_ir
    X = np.fft.rfft(np.pad(x, ((0, n_ir), (0, 0))), axis=0)
    H = np.fft.rfft(np.pad(ir, ((0, len(x)), (0, 0))), axis=0)
    mojado = np.fft.irfft(X * H, n=n, axis=0)
    seco = np.pad(x, ((0, n_ir), (0, 0)))
    return seco * (1 - mezcla) + mojado * mezcla * 6


def _norm(x: np.ndarray, pico: float = 0.9) -> np.ndarray:
    m = np.abs(x).max()
    return x * (pico / m) if m > 0 else x


# ------------------------------------------------------------------ efectos
def aire(variante: int = 0) -> np.ndarray:
    """Destello de aire con brillo de cristal: agudos, rápido, sin tono de interfaz."""
    dur = 0.75
    n = int(SR * dur)
    r = _rng(11 + variante)
    ruido = r.standard_normal((n, 2))
    ruido = _fft_filtro(ruido, bajo=4200, alto=15000)
    env = _env(n, 0.035 + 0.01 * variante, 0.16)[:, None]
    brillo = np.zeros((n, 2))
    t = np.arange(n) / SR
    base = [2350, 3170, 4700][variante % 3]
    for k, (mult, amp) in enumerate([(1, 1.0), (1.498, 0.55), (2.003, 0.35), (2.66, 0.2)]):
        fase = r.uniform(0, 6.28)
        onda = np.sin(2 * np.pi * base * mult * t + fase) * amp * np.exp(-t / (0.22 + 0.05 * k))
        brillo[:, k % 2] += onda
    x = ruido * env * 0.55 + brillo * _env(n, 0.012, 0.3)[:, None] * 0.16
    return _norm(_reverb(x, 0.8, 0.22, 3 + variante), 0.7)


def sub(variante: int = 0) -> np.ndarray:
    """Golpe grave con cuerpo (sin clic agudo): da peso a lo que aterriza."""
    dur = 0.9
    n = int(SR * dur)
    t = np.arange(n) / SR
    f0, f1 = [(74, 41), (66, 38), (82, 46)][variante % 3]
    f = f1 + (f0 - f1) * np.exp(-t / 0.09)
    fase = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(fase) * np.exp(-t / 0.28)
    x = np.tanh(x * 1.6) / np.tanh(1.6)
    golpe = _fft_filtro(_rng(5 + variante).standard_normal(n), alto=900) * np.exp(-t / 0.018) * 0.35
    x = (x + golpe) * np.clip(t / 0.004, 0, 1)
    return _norm(_estereo(x), 0.95)


def whoosh(dur: float = 0.62, variante: int = 0, pan_de: float = -0.6, pan_a: float = 0.6) -> np.ndarray:
    """Paso de aire que cruza: ruido con filtro que barre y se desplaza en estéreo."""
    n = int(SR * dur)
    r = _rng(21 + variante)
    ruido = r.standard_normal(n)
    u = np.linspace(0, 1, n)
    pico = 0.62
    forma = np.where(u < pico, (u / pico) ** 2.2, np.exp(-(u - pico) / (1 - pico) * 3.2))
    centros = 260 + 1500 * np.sin(np.pi * np.clip(u / (pico * 1.6), 0, 1)) ** 2
    y = _barrido(ruido, centros, q=1.3) * forma
    cuerpo = _fft_filtro(r.standard_normal(n), bajo=110, alto=520) * forma * 0.9
    y = _fft_filtro(y + cuerpo, alto=4200, orden=2.5)
    pan = pan_de + (pan_a - pan_de) * u
    a = (pan + 1) * np.pi / 4
    x = np.stack([y * np.cos(a), y * np.sin(a)], axis=1) * 1.414
    return _norm(_reverb(x, 0.6, 0.12, 9 + variante), 0.8)


def tic(variante: int = 0) -> np.ndarray:
    """Clic seco y corto, de madera, para contadores y marcas de lista (muy bajo)."""
    n = int(SR * 0.09)
    t = np.arange(n) / SR
    f = [1650, 1900, 1450][variante % 3]
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.012)
    x += _fft_filtro(_rng(31 + variante).standard_normal(n), bajo=1800, alto=7000) * np.exp(-t / 0.004) * 0.6
    return _norm(_estereo(x), 0.5)


def subida(dur: float = 1.2) -> np.ndarray:
    """Tensión antes de un cambio: ruido que crece y se abre, acaba en seco."""
    n = int(SR * dur)
    u = np.linspace(0, 1, n)
    r = _rng(41)
    y = _barrido(r.standard_normal(n), 300 + 4200 * u ** 2.2, q=1.4) * u ** 2.4
    y2 = _barrido(r.standard_normal(n), 320 + 4000 * u ** 2.2, q=1.4) * u ** 2.4
    x = _fft_filtro(_estereo(y, y2), alto=6500, orden=2)
    return _norm(_reverb(x, 0.5, 0.1), 0.7)


def caja(variante: int = 0) -> np.ndarray:
    """Caja registradora sintetizada aquí (sin muestras de nadie): el cajón que se abre, dos
    monedas y la campanilla. Es el ejemplo de marca/sonidos/ («dinero» -> caja.wav)."""
    dur = 1.1
    n = int(SR * dur)
    t = np.arange(n) / SR
    r = _rng(61 + variante)
    x = np.zeros(n)
    # cajón: golpe grave de madera y el roce del carril
    golpe = np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.05) * 0.8
    roce = _fft_filtro(r.standard_normal(n), bajo=600, alto=3500) * np.exp(-t / 0.07) * 0.35
    x += golpe + roce
    # dos monedas (metal agudo, muy corto)
    for t0, f in ((0.09, 5200), (0.15, 6100)):
        tt = np.clip(t - t0, 0, None)
        on = (t >= t0).astype(float)
        x += on * (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.47 * tt)) * np.exp(-tt / 0.045) * 0.22
    # campanilla: dos parciales que brillan y se apagan despacio
    t0 = 0.2
    tt = np.clip(t - t0, 0, None)
    on = (t >= t0).astype(float)
    for f, a, cola in ((2093, 0.55, 0.42), (3136, 0.35, 0.3), (4186, 0.18, 0.22), (6272, 0.08, 0.12)):
        x += on * np.sin(2 * np.pi * f * tt) * np.exp(-tt / cola) * a
    x *= np.clip(t / 0.002, 0, 1)
    return _norm(_reverb(_estereo(x), 0.7, 0.14, 5), 0.85)


EFECTOS = {"aire": aire, "sub": sub, "whoosh": whoosh, "tic": tic, "subida": subida, "caja": caja}
_cache: dict = {}


def efecto(nombre: str, variante: int = 0) -> np.ndarray:
    clave = (nombre, variante)
    if clave not in _cache:
        _cache[clave] = EFECTOS[nombre](variante=variante) if nombre != "subida" else subida()
    return _cache[clave]


# ------------------------------------------------------------------ cama musical
def cama(duracion: float, semilla: int = 3) -> np.ndarray:
    """Pad ambiental plano (Re mayor), acordes de 4 s con fundidos. Sin ritmo que compita con la voz."""
    n = int(SR * (duracion + 2))
    t = np.arange(n) / SR
    acordes = [  # frecuencias en Hz: Dmaj9, Bm9, Gmaj7(#11), A6sus
        [146.83, 220.0, 277.18, 329.63, 369.99],
        [123.47, 185.0, 220.0, 293.66, 277.18 * 2],
        [98.0, 196.0, 246.94, 293.66, 369.99],
        [110.0, 164.81, 246.94, 293.66, 369.99],
    ]
    r = _rng(semilla)
    x = np.zeros((n, 2))
    seg = 4.0
    for k in range(int(np.ceil((duracion + 2) / seg)) + 1):
        acorde = acordes[k % len(acordes)]
        a, b = int((k * seg - 1.2) * SR), int(((k + 1) * seg + 1.2) * SR)
        a0, b0 = max(0, a), min(n, b)
        if a0 >= b0:
            continue
        tt = t[a0:b0]
        u = (tt - (k * seg - 1.2)) / (seg + 2.4)
        env = np.sin(np.pi * np.clip(u, 0, 1)) ** 1.6
        for j, f in enumerate(acorde):
            for lado in range(2):
                det = 1 + r.uniform(-0.003, 0.003)
                fase = r.uniform(0, 6.28)
                onda = np.sin(2 * np.pi * f * det * tt + fase) + 0.28 * np.sin(4 * np.pi * f * det * tt + fase)
                x[a0:b0, lado] += onda * env * (0.22 if j == 0 else 0.13)
    lfo = 0.8 + 0.2 * np.sin(2 * np.pi * t / 7.3)
    x *= lfo[:, None]
    x = _fft_filtro(x, bajo=70, alto=1400)
    x = _reverb(x, 1.6, 0.35, 17)[:n]
    ini = int(SR * 1.5)
    x[:ini] *= np.linspace(0, 1, ini)[:, None]
    fin = int(SR * 2.5)
    fin_i = int(SR * duracion)
    x[max(0, fin_i - fin):fin_i] *= np.linspace(1, 0, min(fin, fin_i))[:, None]
    x[fin_i:] = 0
    return _norm(x[:int(SR * duracion)], 0.5)


# ------------------------------------------------------------------ mezcla
def _db(x: np.ndarray) -> float:
    rms = np.sqrt(np.mean(np.square(x))) + 1e-9
    return 20 * np.log10(rms)


def _pico_db(x: np.ndarray) -> float:
    """Nivel (RMS) de los 60 ms más fuertes de un efecto."""
    m = np.abs(x).mean(axis=1) if x.ndim == 2 else np.abs(x)
    v = int(SR * 0.06)
    if len(m) <= v:
        return _db(x)
    c = np.convolve(np.square(m), np.ones(v) / v, mode="valid")
    return 10 * np.log10(c.max() + 1e-12)


def _rms_voz(voz: np.ndarray) -> float:
    """Nivel de la voz solo donde se habla (bloques de 400 ms con energía)."""
    bloque = int(SR * 0.4)
    m = voz.mean(axis=1)
    n = len(m) // bloque
    if n == 0:
        return _db(voz)
    niveles = [np.sqrt(np.mean(np.square(m[i * bloque:(i + 1) * bloque]))) for i in range(n)]
    niveles = np.array(niveles)
    activos = niveles[niveles > niveles.max() * 0.1]
    return 20 * np.log10(np.sqrt(np.mean(np.square(activos))) + 1e-9)


def leer_audio(ruta: Path, desde: float | None = None, hasta: float | None = None) -> np.ndarray:
    import subprocess
    cmd = ["ffmpeg", "-v", "error"]
    if desde is not None:
        cmd += ["-ss", f"{desde:.3f}"]
    if hasta is not None:
        cmd += ["-to", f"{hasta:.3f}"]
    cmd += ["-i", str(ruta), "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    datos = subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout
    return np.frombuffer(datos, np.float32).reshape(-1, 2).astype(np.float64)


_cache_archivos: dict = {}


def leer_archivo(ruta: Path) -> np.ndarray | None:
    """Un .wav/.mp3/.m4a/.aiff/.ogg/.flac de marca/ en estéreo a 48 kHz (lo decodifica ffmpeg)."""
    clave = str(ruta)
    if clave not in _cache_archivos:
        try:
            _cache_archivos[clave] = leer_audio(Path(ruta))
        except Exception:
            _cache_archivos[clave] = None
    return _cache_archivos[clave]


EXT_AUDIO = (".wav", ".mp3", ".m4a", ".aac", ".aif", ".aiff", ".ogg", ".flac")


def musica_de_marca(eleccion) -> Path | None:
    """La música de cama que has dejado en marca/musica/. «eleccion» puede ser el nombre de un
    archivo (brand.json: "musica": "mi-cama.mp3") o true (la primera por orden alfabético)."""
    from comun import MARCA, ruta_proyecto
    carpeta = MARCA / "musica"
    if isinstance(eleccion, str) and eleccion.strip():
        for cand in (Path(eleccion).expanduser(), ruta_proyecto(eleccion), carpeta / eleccion):
            if cand.exists() and cand.suffix.lower() in EXT_AUDIO:
                return cand
    if carpeta.exists():
        fs = sorted(f for f in carpeta.iterdir() if f.suffix.lower() in EXT_AUDIO)
        if fs:
            return fs[0]
    return None


def sonidos_de_marca(palabras: list[dict]) -> list[dict]:
    """Sonidos asociados a palabras (marca/sonidos/mapa.json): «dinero» -> caja.wav. Cada vez que
    se dice una palabra del mapa suena su sonido, con aire entre dos (el mismo, cada 3 s como mucho)."""
    import json
    import re
    import unicodedata
    from comun import MARCA
    carpeta = MARCA / "sonidos"
    mapa_p = carpeta / "mapa.json"
    if not mapa_p.exists():
        return []
    try:
        mapa = json.loads(mapa_p.read_text(encoding="utf-8"))
    except Exception:
        return []

    def norm(t: str) -> str:
        t = unicodedata.normalize("NFKD", (t or "").lower()).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9* ]", "", t).strip()

    reglas = []
    for clave, v in mapa.items():
        if clave.startswith("_"):
            continue
        archivo = v if isinstance(v, str) else (v or {}).get("archivo")
        if not archivo:
            continue
        ruta = carpeta / archivo
        if not ruta.exists():
            continue
        db = 0.0 if isinstance(v, str) else float((v or {}).get("db", 0))
        reglas.append((norm(clave).split(), ruta, db))
    if not reglas:
        return []
    toks = [norm(w["w"]) for w in palabras]
    out, ultimo_archivo, ultimo = [], {}, -9.0
    for i in range(len(toks)):
        for trozos, ruta, db in reglas:
            n = len(trozos)
            if i + n > len(toks):
                continue
            iguales = all((tk.startswith(tz[:-1]) if tz.endswith("*") else tk == tz)
                          for tk, tz in zip(toks[i:i + n], trozos))
            if not iguales:
                continue
            t = palabras[i]["s"]
            if t - ultimo_archivo.get(str(ruta), -9) < 3.0 or t - ultimo < 1.5:
                continue
            out.append({"t": round(t - 0.02, 3), "archivo": str(ruta), "db": db, "de_marca": True,
                        "palabra": palabras[i]["w"]})
            ultimo_archivo[str(ruta)] = t
            ultimo = t
            break
    return out


def escribir_wav(ruta: Path, x: np.ndarray) -> None:
    x = np.clip(x, -1, 1)
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def mezclar(voz: np.ndarray, eventos: list[dict], duracion: float, musica=False,
            nivel_efectos: float = 1.0, nivel_musica_db: float | None = None) -> np.ndarray:
    """Voz + efectos (en su segundo exacto) + cama opcional. Devuelve estéreo float.
    «musica»: False, True (cama sintetizada por el kit) o la ruta de un archivo de marca/musica/
    (va en bucle, con fundidos y bajando cuando hablas: ducking)."""
    n = int(SR * duracion)
    out = np.zeros((n, 2))
    v = voz[:n]
    out[:len(v)] += v
    ref = _rms_voz(v) if len(v) else -20.0
    efx = np.zeros((n, 2))
    usados: dict = {}
    sonando: list[float] = []
    ultimo: dict = {}
    # los sonidos de marca («dinero» -> caja) mandan: se colocan primero y apartan a los sintetizados
    de_marca = [e for e in eventos if e.get("archivo")]
    for ev in de_marca:
        s = leer_archivo(Path(ev["archivo"]))
        if s is None or not len(s):
            continue
        g = 10 ** ((ref - 11 + float(ev.get("db", 0)) - _pico_db(s)) / 20) * max(nivel_efectos, 0.4)
        a = int(max(0, ev["t"]) * SR)
        b = min(n, a + len(s))
        if b > a:
            efx[a:b] += s[: b - a] * g
    tiempos_marca = [e["t"] for e in de_marca]
    for ev in sorted([e for e in eventos if not e.get("archivo")], key=lambda e: e["t"]):
        if any(abs(ev["t"] - tm) < 0.35 for tm in tiempos_marca):
            continue
        nombre = ev["sonido"]
        # criterio de la casa: nunca más de dos golpes a la vez ni el mismo sonido repetido pegado
        sonando = [x for x in sonando if ev["t"] - x < 0.28]
        if len(sonando) >= 2 or ev["t"] - ultimo.get(nombre, -9) < 0.4:
            continue
        sonando.append(ev["t"])
        ultimo[nombre] = ev["t"]
        # variantes alternas para que una ráfaga no repita la misma muestra
        var = ev.get("variante", usados.get(nombre, 0) % 3)
        usados[nombre] = usados.get(nombre, 0) + 1
        s = efecto(nombre, var)
        if nombre == "whoosh" and ev.get("dur"):
            s = whoosh(ev["dur"], var)
        # nivel del tramo más fuerte del efecto, en dB relativos a la voz
        rel = {"aire": -15, "sub": -9, "whoosh": -13, "tic": -19, "subida": -15}.get(nombre, -15)
        rel += ev.get("db", 0)
        g = 10 ** ((ref + rel - _pico_db(s)) / 20) * nivel_efectos
        a = int(max(0, ev["t"]) * SR)
        b = min(n, a + len(s))
        if b > a:
            efx[a:b] += s[: b - a] * g
    out += efx
    archivo_musica = musica if isinstance(musica, (str, Path)) and str(musica) else None
    if archivo_musica:
        m = leer_archivo(Path(archivo_musica))
        if m is not None and len(m) > SR:
            reps = int(np.ceil(n / len(m)))
            m = np.tile(m, (reps, 1))[:n]
            ini, fin = int(SR * 1.2), int(SR * 2.5)
            m[:ini] *= np.linspace(0, 1, min(ini, n))[:, None][:len(m[:ini])]
            m[max(0, n - fin):] *= np.linspace(1, 0, min(fin, n))[:, None]
            nivel = -20.0 if nivel_musica_db is None else float(nivel_musica_db)
            g = 10 ** ((ref + nivel - _db(m)) / 20)
            # ducking: la música baja unos 9 dB mientras hablas y sube en las pausas (0,15 s / 0,5 s)
            env = np.abs(v.mean(axis=1)) if len(v) else np.zeros(n)
            env = np.pad(env, (0, max(0, n - len(env))))[:n]
            bloque = int(SR * 0.05)
            nb = max(1, n // bloque)
            rms = np.sqrt(np.mean(np.square(env[:nb * bloque].reshape(nb, bloque)), axis=1) + 1e-12)
            umbral = np.percentile(rms, 60) * 0.35
            habla = (rms > umbral).astype(float)
            suave = np.zeros_like(habla)
            acc = 0.0
            for i, h in enumerate(habla):
                k = 0.33 if h > acc else 0.1  # baja rápido, sube despacio
                acc += (h - acc) * k
                suave[i] = acc
            agache_b = 10 ** (-9 * suave / 20)
            agache = np.repeat(agache_b, bloque)
            agache = np.pad(agache, (0, max(0, n - len(agache))), mode="edge")[:n]
            out += m * g * agache[:, None]
        else:
            musica = True  # si el archivo no se puede leer, cama del kit
    if musica is True:
        m = cama(duracion)
        g = 10 ** ((ref - 25 - _rms_voz(m)) / 20)
        # la cama baja un poco más cuando se habla (compresión lateral suave)
        env = np.abs(v.mean(axis=1)) if len(v) else np.zeros(n)
        env = np.pad(env, (0, max(0, n - len(env))))[:n]
        k = int(SR * 0.3)
        suav = np.convolve(env, np.ones(k) / k, mode="same")
        agache = 1 - 0.35 * np.clip(suav / (suav.max() + 1e-9) * 3, 0, 1)
        out += m[:n] * g * agache[:, None]
    # volumen de entrega: la voz a unos -16 LUFS (lo que esperan YouTube e Instagram) y un
    # limitador suave para que ningún golpe sature
    out *= 10 ** ((-17.5 - ref) / 20)
    techo = 0.89
    over = np.abs(out) > techo * 0.8
    if over.any():
        k = techo * 0.8
        out = np.where(over, np.sign(out) * (k + (techo - k) * np.tanh((np.abs(out) - k) / (techo - k))), out)
    return out


def main(argv: list[str]) -> None:
    from comun import TRABAJO, ok
    destino = TRABAJO / "_sonidos"
    destino.mkdir(parents=True, exist_ok=True)
    from comun import MARCA
    if argv and argv[0] == "caja":
        (MARCA / "sonidos").mkdir(parents=True, exist_ok=True)
        escribir_wav(MARCA / "sonidos" / "caja.wav", caja())
        ok("Caja registradora sintetizada en marca/sonidos/caja.wav")
        return
    for nombre in ("aire", "sub", "whoosh", "tic", "subida", "caja"):
        for v in range(3 if nombre not in ("subida", "caja") else 1):
            escribir_wav(destino / f"{nombre}-{v}.wav", efecto(nombre, v))
    escribir_wav(destino / "cama-20s.wav", cama(20.0))
    ok(f"Efectos y cama de prueba en {destino}")


if __name__ == "__main__":
    main(sys.argv[1:])

"""Dónde está la persona en el plano: cara, cambios de escena y recorte (máscara).

  kit.py persona <video>     -> trabajo/<video>/persona.json

Todo en local con MediaPipe (Google, Apache-2.0) y un solo modelo, el segmentador de selfie
multiclase (distingue pelo, piel de la cara, cuerpo y ropa):
- la cara: para que los textos no la tapen, para centrar el vertical en la persona y para que
  los zooms de cámara vayan hacia ella;
- el recorte de la persona fotograma a fotograma, para poner textos POR DETRÁS de ella (efecto
  «profundidad»). Solo se usa en los momentos marcados.

La máscara se suaviza en el tiempo y se ajusta a los bordes reales del fotograma
(filtro guiado), para que no parpadee ni deje halos.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from comun import (ENTORNO, Cronometro, carpeta_trabajo, escribir_json, fallo, info_video, leer_json,
                   ok, paso, resolver_video)

MODELOS = ENTORNO / "modelos"
URLS_MODELOS = {
    "selfie_multiclass.tflite":
        "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite",
}
FPS_MUESTREO = 6
os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")


def modelo(nombre: str) -> Path:
    ruta = MODELOS / nombre
    if not ruta.exists() or ruta.stat().st_size < 10000:
        import urllib.request
        MODELOS.mkdir(exist_ok=True)
        print(f"   Descargando el modelo {nombre} (una sola vez)…", flush=True)
        ruta.write_bytes(urllib.request.urlopen(URLS_MODELOS[nombre], timeout=60).read())
    return ruta


def leer_fotogramas(video: Path, ancho: int, alto: int, fps: float | None = None,
                    desde: float | None = None, hasta: float | None = None):
    """Generador de fotogramas RGB (numpy) leídos con ffmpeg."""
    import numpy as np
    cmd = ["ffmpeg", "-v", "error"]
    if desde is not None:
        cmd += ["-ss", f"{desde:.3f}"]
    if hasta is not None:
        cmd += ["-to", f"{hasta:.3f}"]
    cmd += ["-i", str(video)]
    vf = f"scale={ancho}:{alto}:flags=area"
    if fps:
        vf = f"fps={fps}," + vf
    cmd += ["-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    tam = ancho * alto * 3
    try:
        while True:
            buf = proc.stdout.read(tam)
            if len(buf) < tam:
                break
            yield np.frombuffer(buf, np.uint8).reshape(alto, ancho, 3)
    finally:
        proc.stdout.close()
        proc.wait()


# ------------------------------------------------------------------ análisis
def analizar(video: Path, trabajo: Path) -> dict:
    import numpy as np
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision

    iv = info_video(video)
    aw = 480
    ah = int(round(aw * iv["alto"] / iv["ancho"] / 2) * 2)
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=mpt.BaseOptions(model_asset_path=str(modelo("selfie_multiclass.tflite"))),
        running_mode=vision.RunningMode.IMAGE, output_confidence_masks=True,
        output_category_mask=False))
    muestras, escenas, huellas = [], [], []
    for n, fr in enumerate(leer_fotogramas(video, aw, ah, fps=FPS_MUESTREO)):
        t = round(n / FPS_MUESTREO, 3)
        r = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(fr)))
        cm = r.confidence_masks
        # clases del modelo: 0 fondo, 1 pelo, 2 piel del cuerpo, 3 piel de la cara, 4 ropa, 5 otros
        cara_m = np.squeeze(cm[3].numpy_view()) > 0.5
        pelo_m = np.squeeze(cm[1].numpy_view()) > 0.5
        cara = None
        if cara_m.mean() > 0.004:
            ys, xs = np.nonzero(cara_m)
            # la cara es la mancha más grande: nos quedamos con el núcleo (percentiles) para ignorar manos
            x0, x1 = np.percentile(xs, [4, 96])
            y0, y1 = np.percentile(ys, [3, 97])
            if pelo_m.any():
                yp = np.nonzero(pelo_m[:, int(x0):int(x1) + 1])[0]
                if len(yp):
                    y0 = min(y0, np.percentile(yp, 3))
            hh, ww = cara_m.shape
            cara = [round((x0 + x1) / 2 / ww, 4), round((y0 + y1) / 2 / hh, 4),
                    round((x1 - x0) / ww, 4), round((y1 - y0) / hh, 4)]
            if cara[2] < 0.03:
                cara = None
        muestras.append({"t": t, "cara": cara})
        # para los cambios de plano: miniatura en grises + histograma (incluye fundidos)
        g = (fr[::4, ::4].mean(axis=2)).astype(np.float32)
        h = np.histogram(g, bins=32, range=(0, 255))[0].astype(np.float32)
        huellas.append((h / (h.sum() + 1e-6), g))
    # diferencia contra medio segundo antes: detecta cortes secos y fundidos
    k = max(1, FPS_MUESTREO // 2)
    d = np.zeros(len(huellas))
    for i in range(k, len(huellas)):
        d[i] = float(np.abs(huellas[i][0] - huellas[i - k][0]).sum()) * 0.5 + \
            float(np.abs(huellas[i][1] - huellas[i - k][1]).mean()) / 255
    umbral = max(0.2, 5 * float(np.median(d[k:])) if len(d) > k else 0.2)
    for i in range(k, len(d)):
        if d[i] > umbral and d[i] == d[max(0, i - FPS_MUESTREO):i + FPS_MUESTREO + 1].max():
            escenas.append(round(max(0.0, i / FPS_MUESTREO - 0.3), 2))
    datos = {"fps_muestreo": FPS_MUESTREO, "ancho": iv["ancho"], "alto": iv["alto"],
             "duracion": iv["duracion"], "muestras": muestras, "escenas": escenas}
    datos["pista"] = suavizar_pista(muestras)
    escribir_json(trabajo / "persona.json", datos)
    return datos


def suavizar_pista(muestras: list[dict]) -> list:
    """Rellena huecos y suaviza la posición de la cara para que la cámara no tiemble."""
    import numpy as np
    n = len(muestras)
    if not n:
        return []
    val = np.full((n, 4), np.nan)
    for i, m in enumerate(muestras):
        if m["cara"]:
            val[i] = m["cara"]
    visto = ~np.isnan(val[:, 0])
    if not visto.any():
        return [None] * n
    idx = np.arange(n)
    for k in range(4):
        val[:, k] = np.interp(idx, idx[visto], val[visto, k])
    # mediana corta + media móvil
    out = val.copy()
    for i in range(n):
        a, b = max(0, i - 2), min(n, i + 3)
        out[i] = np.median(val[a:b], axis=0)
    ker = np.ones(5) / 5
    for k in range(4):
        out[:, k] = np.convolve(np.pad(out[:, k], 2, mode="edge"), ker, mode="valid")
    # una cara que falta más de 1 s seguido (pantalla, b-roll) queda como «sin cara»
    res = []
    for i in range(n):
        a, b = max(0, i - 3), min(n, i + 4)
        res.append([round(float(x), 4) for x in out[i]] if visto[a:b].any() else None)
    return res


def cargar(trabajo: Path) -> dict | None:
    p = trabajo / "persona.json"
    return leer_json(p) if p.exists() else None


def cara_en(persona: dict | None, t: float):
    """Cara (cx, cy, w, h) normalizada en el segundo t, o None."""
    if not persona or not persona.get("pista"):
        return None
    pista = persona["pista"]
    i = t * persona["fps_muestreo"]
    a = int(max(0, min(len(pista) - 1, i)))
    b = min(len(pista) - 1, a + 1)
    pa, pb = pista[a], pista[b]
    if pa is None or pb is None:
        return pa or pb
    f = i - a
    return [pa[k] * (1 - f) + pb[k] * f for k in range(4)]


def cara_media(persona: dict | None, desde: float = 0, hasta: float = 1e9):
    """Posición media de la cara en un tramo (para colocar textos que duran varios segundos)."""
    if not persona:
        return None
    caras = [c for m, c in zip(persona["muestras"], persona.get("pista", []))
             if c and desde <= m["t"] <= hasta]
    if not caras:
        return None
    return [sum(c[k] for c in caras) / len(caras) for k in range(4)]


# ------------------------------------------------------------------ recorte de la persona
def filtro_guiado(guia, p, radio: int, eps: float):
    """Filtro guiado (He et al.) con filtros de caja: el borde de la máscara se pega al de la imagen.
    Hecho aquí porque cv2.ximgproc.guidedFilter (OpenCV 5) devuelve a veces NaN en medio cuadro: con la
    guía en 0-255, la resta de la varianza en coma flotante sale negativa. Aquí la guía va en 0-1 y la
    varianza nunca baja de cero."""
    import cv2
    import numpy as np
    k = (2 * radio + 1, 2 * radio + 1)

    def caja(x):
        return cv2.boxFilter(x, -1, k, borderType=cv2.BORDER_REFLECT)

    gi = guia.astype(np.float32) / 255.0
    p = p.astype(np.float32)
    m_i, m_p = caja(gi), caja(p)
    var = np.maximum(caja(gi * gi) - m_i * m_i, 0.0)
    a = (caja(gi * p) - m_i * m_p) / (var + eps)
    b = m_p - a * m_i
    return caja(a) * gi + caja(b)


class Recortador:
    """Máscara estable de la persona para un tramo de vídeo (textos por detrás)."""

    def __init__(self):
        import mediapipe as mp  # noqa
        from mediapipe.tasks import python as mpt
        from mediapipe.tasks.python import vision
        self.mp = mp
        self.seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=mpt.BaseOptions(model_asset_path=str(modelo("selfie_multiclass.tflite"))),
            running_mode=vision.RunningMode.IMAGE, output_confidence_masks=True,
            output_category_mask=False))
        self.previa = None

    def reiniciar(self):
        self.previa = None

    def mascara_rapida(self, rgb, centro=None):
        """Como mascara(), pero a un cuarto de resolución y sin filtro guiado: para efectos suaves
        como la luz de relleno, donde el borde fino no se ve. Mucho más rápida."""
        import cv2
        import numpy as np
        H, W = rgb.shape[:2]
        lado = min(H, W)
        cx = int((centro[0] if centro else 0.5) * W)
        cy = int((centro[1] if centro else 0.4) * H)
        x0 = int(max(0, min(W - lado, cx - lado // 2)))
        y0 = int(max(0, min(H - lado, cy - lado * 0.4)))
        sub = cv2.resize(rgb[y0:y0 + lado, x0:x0 + lado], (256, 256), interpolation=cv2.INTER_AREA)
        r = self.seg.segment(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(sub)))
        m = 1.0 - np.squeeze(r.confidence_masks[0].numpy_view()).astype(np.float32)
        h4, w4, l4, a, b = H // 4, W // 4, lado // 4, y0 // 4, x0 // 4
        full = np.zeros((h4, w4), np.float32)
        full[a:a + l4, b:b + l4] = cv2.resize(m, (l4, l4), interpolation=cv2.INTER_LINEAR)
        if a + l4 < h4:  # por debajo de la ventana se prolonga la última fila
            full[a + l4:, b:b + l4] = full[a + l4 - 1:a + l4, b:b + l4]
        full = cv2.GaussianBlur(np.clip((np.nan_to_num(full) - 0.35) / 0.3, 0, 1), (0, 0), 1.5)
        previa = getattr(self, "previa_r", None)
        if previa is not None and previa.shape == full.shape:
            full = previa * 0.4 + full * 0.6
        self.previa_r = full
        return full

    def mascara(self, rgb, centro=None):
        """rgb: fotograma HxWx3 uint8 (ya encuadrado); centro: (x, y) de la cara en fracción del
        fotograma. Devuelve la máscara float32 0..1 de la persona."""
        import cv2
        import numpy as np
        H, W = rgb.shape[:2]
        # ventana cuadrada alrededor de la persona: el modelo trabaja a 256x256 y así gana detalle
        lado = min(H, W)
        cx = int((centro[0] if centro else 0.5) * W)
        cy = int((centro[1] if centro else 0.4) * H)
        x0 = int(max(0, min(W - lado, cx - lado // 2)))
        y0 = int(max(0, min(H - lado, cy - lado * 0.4)))
        sub = np.ascontiguousarray(rgb[y0:y0 + lado, x0:x0 + lado])
        r = self.seg.segment(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=sub))
        fondo = np.squeeze(r.confidence_masks[0].numpy_view())
        m = 1.0 - fondo.astype(np.float32)
        m = cv2.resize(m, (lado, lado), interpolation=cv2.INTER_LINEAR)
        full = np.zeros((H, W), np.float32)
        full[y0:y0 + lado, x0:x0 + lado] = m
        if y0 + lado < H:  # por debajo de la ventana (torso en vertical) se prolonga la última fila
            full[y0 + lado:, x0:x0 + lado] = m[-1:, :]
        # borde fiel al fotograma: filtro guiado a media resolución
        peq = cv2.resize(rgb, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        mp_ = cv2.resize(full, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        mp_ = filtro_guiado(cv2.cvtColor(peq, cv2.COLOR_RGB2GRAY), mp_, 6, 1e-4)
        if not np.isfinite(mp_).all():  # red de seguridad: un fotograma malo no contagia a los siguientes
            mp_ = cv2.GaussianBlur(np.nan_to_num(cv2.resize(full, (W // 2, H // 2)), nan=0.0), (0, 0), 2)
        mp_ = np.clip((mp_ - 0.35) / 0.3, 0, 1)  # contraste de la máscara: sin velos grises
        # estable en el tiempo: media exponencial, más rápida donde hay movimiento fuerte
        if self.previa is not None and self.previa.shape == mp_.shape:
            dif = np.abs(mp_ - self.previa)
            alfa = np.clip(0.45 + dif * 1.2, 0.45, 1.0)
            mp_ = self.previa * (1 - alfa) + mp_ * alfa
        self.previa = mp_
        m = cv2.resize(mp_, (W, H), interpolation=cv2.INTER_LINEAR)
        return cv2.GaussianBlur(m, (0, 0), 1.2)


def asegurar(video: Path, trabajo: Path) -> dict:
    datos = cargar(trabajo)
    fuente = trabajo / "cortado.mp4"
    if datos and fuente.exists() and abs(datos.get("duracion", 0) - info_video(fuente)["duracion"]) < 0.2:
        return datos
    paso("Buscando la cara y los cambios de plano (MediaPipe, en local)")
    with Cronometro(trabajo, "persona"):
        datos = analizar(fuente, trabajo)
    con = sum(1 for m in datos["muestras"] if m["cara"])
    ok(f"Cara localizada en {con} de {len(datos['muestras'])} muestras; "
       f"{len(datos['escenas'])} cambio(s) de plano: {', '.join(f'{t:.1f} s' for t in datos['escenas']) or 'ninguno'}")
    return datos


def main(argv: list[str]) -> None:
    if not argv:
        fallo("Uso: kit.py persona <video>")
    video = resolver_video(argv[0])
    trabajo = carpeta_trabajo(video)
    if not (trabajo / "cortado.mp4").exists():
        fallo("Falta el vídeo cortado.", f"Lanza antes: kit.py cortar aplicar {argv[0]}")
    (trabajo / "persona.json").unlink(missing_ok=True)
    asegurar(video, trabajo)


if __name__ == "__main__":
    main(sys.argv[1:])


# ------------------------------------------------------------------ encuadre vertical
def tramos_de_escena(persona: dict | None, duracion: float) -> list[tuple[float, float]]:
    cortes = [0.0] + [t for t in (persona or {}).get("escenas", []) if 0.3 < t < duracion - 0.3] + [duracion]
    return list(zip(cortes, cortes[1:]))


def centro_vertical(plan: dict, persona: dict | None, ancho: int, alto: int, t: float) -> float:
    """Centro horizontal (en píxeles del original) de la franja 9:16 en el segundo t.

    "encuadre_vertical": número 0..1 (0 izquierda, 0,5 centro, 1 derecha) o "auto", que sigue a
    la persona en cada plano (y centra la pantalla cuando la cara es pequeña, p. ej. un tutorial).
    """
    cw = alto * 9 / 16
    enc = plan.get("encuadre_vertical", "auto")
    if not isinstance(enc, str):
        return cw / 2 + (ancho - cw) * float(enc)
    dur = (persona or {}).get("duracion", t + 1.0)
    for a, b in tramos_de_escena(persona, dur):
        if a <= t < b or b >= dur:
            c = cara_media(persona, a, b)
            if c and c[3] >= 0.25:
                return min(max(c[0] * ancho, cw / 2), ancho - cw / 2)
            return ancho / 2
    return ancho / 2

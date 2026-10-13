"""Fase 5 · Componer: el montaje final, fotograma a fotograma.

  kit.py componer <video> [--formato horizontal|vertical] [--desde S --hasta S --nombre reel1]

Por cada fotograma:
  1. Cámara: encuadre (el vertical sigue a la persona), un ken burns muy lento por plano, empujes
     suaves cuando entra una pieza y un «látigo» con desenfoque de zoom en las transiciones.
  2. Profundidad: en los momentos marcados, el texto gigante va POR DETRÁS de la persona (se la
     recorta con MediaPipe) y el fondo se oscurece un poco para que ella destaque.
  3. Cristal real: donde la capa tiene un panel, el vídeo de detrás se desenfoca y se ilumina.
  4. La capa animada encima, y una viñeta muy suave.
  5. Sonido: la voz, los efectos en su segundo exacto y, si se pide, la cama musical.
"""
from __future__ import annotations

import functools
import json
import math
import queue
import subprocess
import sys
import threading
from pathlib import Path

from comun import (FORMATOS, Cronometro, aviso, cargar_marca, carpeta_finales, carpeta_trabajo, ejecutar,
                   escribir_json, fallo, info_video, leer_json, ok, paso, resolver_video, slug)
import persona as P

FPS = 30


# ------------------------------------------------------------------ lectura en segundo plano
class Lector:
    """Lee fotogramas crudos de ffmpeg en un hilo aparte (así decodifica mientras componemos)."""

    def __init__(self, ruta: Path, ancho: int, alto: int, canales: int, desde: float | None = None,
                 hasta: float | None = None, filtro: str | None = None):
        cmd = ["ffmpeg", "-v", "error"]
        if desde is not None:
            cmd += ["-ss", f"{desde:.3f}"]
        if hasta is not None:
            cmd += ["-to", f"{hasta:.3f}"]
        cmd += ["-i", str(ruta)]
        vf = f"fps={FPS}"
        if filtro:
            vf += "," + filtro
        cmd += ["-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgba" if canales == 4 else "rgb24", "-"]
        self.shape = (alto, ancho, canales)
        self.tam = ancho * alto * canales
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=self.tam * 2)
        self.q: queue.Queue = queue.Queue(maxsize=6)
        self.hilo = threading.Thread(target=self._leer, daemon=True)
        self.hilo.start()

    def _leer(self):
        import numpy as np
        while True:
            buf = self.proc.stdout.read(self.tam)
            if len(buf) < self.tam:
                self.q.put(None)
                break
            self.q.put(np.frombuffer(buf, np.uint8).reshape(self.shape))

    def siguiente(self):
        return self.q.get()

    def cerrar(self):
        try:
            self.proc.stdout.close()
            self.proc.kill()
        except Exception:
            pass


# ------------------------------------------------------------------ curvas
def _suave(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _expo(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return 1 - math.pow(2, -10 * x) if x < 1 else 1.0


def zoom_en(t: float, movs: list[dict], tramos: list[tuple[float, float]], energia: float = 1.0,
            ken_burns: float = 0.03) -> tuple[float, float]:
    """(zoom, fuerza del látigo) en el segundo t. Nada mareante: el zoom máximo ronda 1,12."""
    z = 1.0
    # ken burns: 3 % a lo largo de cada plano, alternando acercar y alejar
    for k, (a, b) in enumerate(tramos):
        if a <= t < b or (k == len(tramos) - 1 and t >= b):
            u = (t - a) / max(0.5, b - a)
            z += ken_burns * (u if k % 2 == 0 else 1 - u)
            break
    latigo = 0.0
    for m in movs:
        if m["tipo"] == "empuje":
            a, d, amp = m["t"], m["d"], m["zoom"] * energia
            if m.get("lento"):
                sube = _suave((t - a) / max(0.6, d * 0.9))
            else:
                sube = _expo((t - a) / 0.55)
            baja = 1 - _suave((t - (a + d - 0.2)) / 0.9)
            if t >= a:
                z += amp * sube * baja
        elif m["tipo"] == "alejar":  # entra cerrado y se abre con suavidad
            a, d, amp = m["t"], m["d"], m["zoom"] * energia
            if a <= t < a + d:
                z += amp * (1 - _suave((t - a) / max(0.6, d)))
        elif m["tipo"] == "golpe":  # golpe de zoom: entra en 0,08 s, aguanta y suelta en 0,3 s
            a, d, amp = m["t"], m["d"], m["zoom"] * energia
            if a <= t < a + d + 0.3:
                sube = _expo((t - a) / 0.08)
                baja = 1 - _suave((t - (a + d)) / 0.3)
                z += amp * sube * baja
        elif m["tipo"] == "latigo":  # como mucho 0,25 s
            if abs(t - m["t"]) > 0.125:
                continue
            x = (t - m["t"]) / 0.09
            f = math.exp(-x * x)
            z += 0.16 * f
            latigo = max(latigo, f)
    return z, latigo


# ------------------------------------------------------------------ composición
def componer_formato(trabajo: Path, formato: str, etiqueta: str, plan: dict, marca: dict,
                     desde: float | None, hasta: float | None, salida: Path) -> dict:
    import cv2
    import numpy as np
    import sonido as S

    W, H = FORMATOS[formato]
    fuente = trabajo / "cortado.mp4"
    iv = info_video(fuente)
    sw, sh = iv["ancho"], iv["alto"]
    t_ini = desde or 0.0
    dur = (hasta if hasta is not None else iv["duracion"]) - t_ini
    n_total = int(round(dur * FPS))
    ev = leer_json(trabajo / f"eventos-{etiqueta}.json", defecto={"sonidos": [], "detras": [], "camara": []})
    pers = P.cargar(trabajo)
    if pers and desde is not None:
        import animar
        pers = animar.recortar_persona(pers, t_ini, t_ini + dur)
    tramos = P.tramos_de_escena(pers, dur)
    energia = 1.25 if marca.get("estilo") == "energia" else 1.0
    # los zooms de la plantilla; "zooms" en plan.json los ajusta para un vídeo ({"ken_burns": 0}: cámara fija)
    zooms = {**(ev.get("zooms") or {}), **(plan.get("zooms") or {})}
    ken = float(zooms.get("ken_burns", 0.03))
    transicion = ev.get("transicion", "latigo")
    tapan = [tuple(x) for x in ev.get("tapan", [])]
    # el desenfoque de cristal solo hace falta en los estilos con paneles
    con_cristal = marca.get("estilo", "detras") in ("cristal", "editorial", "energia")
    movs = ev.get("camara", [])

    # --- sonido primero: la mezcla es rápida y así el vídeo sale con su audio definitivo
    voz = S.leer_audio(fuente, t_ini, t_ini + dur) if iv["tiene_audio"] else np.zeros((1, 2))
    # música: la de marca/musica/ si la hay (con ducking bajo la voz); si no, la cama del kit
    # brand.json "musica": "auto" (por defecto: la de marca/musica/ si has dejado alguna), true (la
    # tuya o, si no hay, la cama del kit), false (nunca) o el nombre de un archivo de marca/musica/
    pide = marca.get("musica", "auto")
    pl_mus = ev.get("musica") or {}
    musica = False
    if pide == "auto":
        archivo = S.musica_de_marca(True)
        musica = archivo if archivo else bool(pl_mus.get("cama"))
    elif pide:
        archivo = S.musica_de_marca(pide)
        musica = archivo if archivo else True
    elif pl_mus.get("cama") and pide is not False:
        musica = True
    if musica:
        ok(f"Música de cama: {musica.name if isinstance(musica, Path) else 'la sintetizada del kit'}")
    mezcla = S.mezclar(voz, ev.get("sonidos", []), dur, musica=musica,
                       nivel_efectos=float(marca.get("nivel_efectos", 1.0)) * float(ev.get("nivel_efectos", 1.0)),
                       nivel_musica_db=pl_mus.get("nivel_db"))
    de_marca = [e for e in ev.get("sonidos", []) if e.get("archivo")]
    if de_marca:
        ok("Sonidos de marca: " + ", ".join(f"«{e.get('palabra', '').strip('.,;:!?¿¡')}» {e['t']:.1f} s" for e in de_marca[:8]))
    wav = trabajo / f"sonido-{etiqueta}.wav"
    S.escribir_wav(wav, mezcla)

    # --- entradas
    base = Lector(fuente, sw, sh, 3, desde, hasta)
    capa = trabajo / f"capa-{etiqueta}.mov"
    ov = Lector(capa, W, H, 4) if capa.exists() else None
    detras = []
    for d in ev.get("detras", []):
        ruta = trabajo / d["capa"]
        if ruta.exists():
            detras.append(dict(d, lector=None, ruta=ruta))
    barridos = ev.get("barridos", [])
    brolls = [dict(b, lector=None, img=None) for b in ev.get("broll", []) if Path(b["archivo"]).exists()]
    recortador = P.Recortador() if any(not d.get("delante") for d in detras) else None
    # luz de relleno sobre la persona: "luz_cara" en plan.json (o en brand.json para todos los vídeos)
    luz = float(plan.get("luz_cara", marca.get("luz_cara", 0)) or 0)
    relleno = P.Recortador() if luz > 0 and pers else None
    mascara_luz = None
    # grano fino de película: 6 texturas fijas que se alternan (deterministas, sin azar)
    rng = np.random.default_rng(7)
    granos = [cv2.GaussianBlur(rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (0, 0), 0.6)
              for _ in range(6)]
    granos = [cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR) * 4.5 for g in granos]
    # el grano y la viñeta son del acabado «dia-editorial»; se quitan con "grano": false o "vineta": false en
    # brand.json (el grano además cuesta nitidez: es lo que peor comprime)
    con_grano = marca.get("estilo", "dia-editorial") == "dia-editorial" and marca.get("grano", True)
    con_vineta = marca.get("vineta", True)

    # viñeta muy suave
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vinyeta = (1 - 0.16 * np.clip((r - 0.55) / 0.9, 0, 1) ** 1.6).astype(np.float32)
    vinyeta3 = cv2.merge([vinyeta, vinyeta, vinyeta])

    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
                            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow",
                            "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart", "-shortest", str(salida)], stdin=subprocess.PIPE)
    caras_tapadas = []
    s0 = (W / sw) if formato == "horizontal" and iv["orientacion"] == "horizontal" else None
    for n in range(n_total):
        t = n / FPS
        src = base.siguiente()
        if src is None:
            break
        # 1 · cámara ------------------------------------------------------------
        if formato == "vertical" and iv["orientacion"] == "horizontal":
            esc_ = H / sh
            cx_src = centro_suave(plan, pers, sw, sh, t, tramos)
            x0 = cx_src - sh * 9 / 32
            y0 = 0.0
        elif formato == iv["orientacion"]:
            esc_ = max(W / sw, H / sh)
            x0 = (sw - W / esc_) / 2
            y0 = (sh - H / esc_) / 2
        else:  # vertical a horizontal: centrado (el fondo lo rellena el borde replicado y desenfocado)
            esc_ = H / sh
            x0 = (sw - W / esc_) / 2
            y0 = 0.0
        z, latigo = zoom_en(t, movs, tramos, energia, ken)
        if transicion == "corte":
            latigo = 0.0
        z = max(z, 1.0)
        mascara_fr = None
        cara = P.cara_en(pers, t) if pers else None
        if cara and cara[3] >= 0.2:
            px = (cara[0] * sw - x0) * esc_
            py = ((cara[1] - cara[3] * 0.12) * sh - y0) * esc_
            px, py = min(max(px, W * 0.2), W * 0.8), min(max(py, H * 0.2), H * 0.7)
        else:
            px, py = W / 2, H / 2

        def matriz(zz):
            a = esc_ * zz
            return np.float32([[a, 0, px + zz * (-x0 * esc_ - px)], [0, a, py + zz * (-y0 * esc_ - py)]])

        # bicúbico: los zooms suaves de cámara amplían la imagen y el bilineal la ablanda
        frame = cv2.warpAffine(src, matriz(z), (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        if latigo > 0.05 and transicion == "desenfoque":
            # corte con desenfoque de movimiento: estela horizontal corta, sin zoom
            acum = frame.astype(np.float32)
            total = 1.0
            for k in range(1, 8):
                w = 0.8 ** k
                M = matriz(z)
                M[0, 2] += 9 * latigo * k
                acum += w * cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                total += w
            frame = (acum / total).astype(np.uint8)
        elif latigo > 0.05:  # desenfoque de zoom: 8 copias escaladas con pesos decrecientes
            acum = frame.astype(np.float32)
            total = 1.0
            for k in range(1, 8):
                w = 0.82 ** k
                acum += w * cv2.warpAffine(src, matriz(z + 0.018 * latigo * k), (W, H), flags=cv2.INTER_LINEAR,
                                           borderMode=cv2.BORDER_REFLECT)
                total += w
            frame = (acum / total).astype(np.uint8)

        # 1a · luz de relleno: más luz en la cara (y algo en el cuerpo), el fondo no se toca ------
        # (la máscara, suave y a un cuarto de resolución, se renueva un fotograma de cada dos)
        if relleno is not None and cara:
            if mascara_luz is None or n % 2 == 0:
                mascara_luz = mascara_de(relleno, frame, cara, matriz(z), sw, sh, W, H, rapida=True)
            frame = luz_relleno(frame, mascara_luz, cara, matriz(z), sw, sh, luz)

        # 1b · B-roll: la imagen o el vídeo de recurso tapan la cámara (la voz sigue) -----
        en_broll = False
        for br in brolls:
            if br["t0"] <= t < br["t1"]:
                img = broll_fotograma(br, t, W, H)
                if img is not None:
                    # entrada y salida limpias: 0,22 s de fundido con un desenfoque que se va
                    u = min(1.0, (t - br["t0"]) / 0.22, (br["t1"] - t) / 0.22)
                    u = _suave(u)
                    if u < 0.999:
                        radio = (1 - u) * 14
                        img_b = cv2.GaussianBlur(img, (0, 0), max(0.1, radio)) if radio > 0.4 else img
                        frame = cv2.addWeighted(img_b, u, frame, 1 - u, 0)
                    else:
                        frame = img.copy()
                    en_broll = u > 0.5
            elif t >= br["t1"] and br.get("lector") is not None:
                br["lector"].cerrar()
                br["lector"] = None
        tapado = en_broll or any(a <= t < b for a, b in tapan)

        # 2 · profundidad: texto por detrás de la persona ------------------------
        for d in detras:
            if tapado:
                continue
            a, b = d["inicio"], d["inicio"] + d["duracion"]
            if a <= t < b:
                if d["lector"] is None:
                    d["lector"] = Lector(d["ruta"], W, H, 4)
                    if recortador:
                        recortador.reiniciar()
                capa_d = d["lector"].siguiente()
                if capa_d is None:
                    continue
                if d.get("delante"):
                    al = capa_d[:, :, 3].astype(np.float32) / 255.0
                    frame = cv2.blendLinear(capa_d[:, :, :3], frame, al, 1 - al)
                    continue
                if mascara_fr is None:
                    mascara_fr = mascara_de(recortador, frame, cara, matriz(z), sw, sh, W, H)
                m = mascara_fr
                env = _suave((t - a) / 0.35) * (1 - _suave((t - (b - 0.4)) / 0.4))
                fondo = frame
                if env > 0.01:
                    peq = cv2.resize(frame, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
                    peq = cv2.GaussianBlur(peq, (0, 0), 2.2)
                    borroso = cv2.resize(peq, (W, H), interpolation=cv2.INTER_LINEAR)
                    k = float(d.get("atenuar", 0.35)) * env
                    fondo = cv2.addWeighted(frame, (1 - k) * (1 - 0.5 * env), borroso, (1 - k) * 0.5 * env, 0)
                # desenfoque de movimiento en la entrada y la salida: se mezclan los últimos fotogramas
                # de la capa (premultiplicados), como la estela de una cámara con obturador abierto
                al = capa_d[:, :, 3].astype(np.float32) / 255.0
                rgb_d = capa_d[:, :, :3]
                prem = rgb_d.astype(np.float32) * al[:, :, None]
                hist = d.setdefault("hist", [])
                hist.insert(0, (prem, al))
                del hist[3:]
                if (t - a < 0.6 or b - t < 0.4) and len(hist) > 1:
                    pesos = ([0.5, 0.3, 0.2] if t - a < 0.6 else [0.65, 0.35])[:len(hist)]
                    tot = sum(pesos)
                    prem = sum(w * h[0] for w, h in zip(pesos, hist)) / tot
                    al = sum(w * h[1] for w, h in zip(pesos, hist)) / tot
                    rgb_d = np.clip(prem / np.maximum(al[:, :, None], 1e-4), 0, 255).astype(np.uint8)
                con_texto = cv2.blendLinear(rgb_d, fondo, al, 1 - al)
                frame = cv2.blendLinear(frame, con_texto, m.astype(np.float32), (1 - m).astype(np.float32))
            elif t >= b and d["lector"] is not None:
                d["lector"].cerrar()
                d["lector"] = None
                d["hist"] = []

        # 2b · barrido antes / ahora: a la izquierda del deslizador, el plano apagado y sin color
        for bz in barridos:
            if bz["t0"] <= t < bz["t1"]:
                x = int(round(x_barrido(bz, t, W)))
                if x > 0:
                    zona = frame[:, :x].astype(np.float32)
                    gris = zona.mean(axis=2, keepdims=True)
                    frame[:, :x] = np.clip((zona * 0.25 + gris * 0.75) * 0.62, 0, 255).astype(np.uint8)
                break

        # 3 y 4 · cristal real + capa ---------------------------------------------
        if ov is not None:
            capa_f = ov.siguiente()
            if capa_f is not None:
                al8 = capa_f[:, :, 3]
                if al8.max() > 2:
                    al = al8.astype(np.float32) * (1 / 255.0)
                    gm = np.clip((al - 0.28) * (1 / 0.24), 0, 1)
                    if con_cristal and gm.max() > 0.01:
                        peq = cv2.resize(frame, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
                        peq = cv2.GaussianBlur(peq, (0, 0), 7)
                        cristal = cv2.resize(peq, (W, H), interpolation=cv2.INTER_LINEAR)
                        cristal = cv2.convertScaleAbs(cristal, alpha=1.18, beta=10)
                        gm = cv2.GaussianBlur(gm, (0, 0), 1.0)
                        frame = cv2.blendLinear(cristal, frame, gm, 1 - gm)
                    frame = cv2.blendLinear(capa_f[:, :, :3], frame, al, 1 - al)
                    if n % 6 == 0 and cara and cara[3] >= 0.2 and not tapado:
                        tap = tapa_cara(al, cara, matriz(z), sw, sh, W, H)
                        if tap > 0.06:
                            caras_tapadas.append({"t": round(t + t_ini, 2), "tapado": round(tap, 2)})
        if con_vineta:
            frame = cv2.multiply(frame, vinyeta3, dtype=cv2.CV_8U)
        if con_grano:
            g = granos[n % len(granos)]
            frame = np.clip(frame.astype(np.float32) + g[:, :, None], 0, 255).astype(np.uint8)
        enc.stdin.write(frame.tobytes())

    enc.stdin.close()
    enc.wait()
    base.cerrar()
    if ov:
        ov.cerrar()
    for d in detras:
        if d["lector"]:
            d["lector"].cerrar()
    for br in brolls:
        if br.get("lector"):
            br["lector"].cerrar()
    if enc.returncode != 0:
        fallo(f"ffmpeg no ha podido escribir {salida.name}.")
    return {"caras_tapadas": caras_tapadas}


def broll_fotograma(br: dict, t: float, W: int, H: int):
    """El fotograma de B-roll en el segundo t, ya encuadrado a W x H (cubriendo, sin bandas)."""
    import cv2
    import numpy as np
    dur = max(0.1, br["t1"] - br["t0"])
    u = (t - br["t0"]) / dur
    if br["clase"] == "video":
        if br.get("lector") is None:
            filtro = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}")
            br["lector"] = Lector(Path(br["archivo"]), W, H, 3, br.get("desde_s", 0.0), None, filtro)
        f = br["lector"].siguiente()
        if f is None:
            return br.get("ultimo")
        br["ultimo"] = f
        return f
    if br.get("img") is None:
        im = cv2.imread(br["archivo"], cv2.IMREAD_COLOR)
        if im is None:
            return None
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        h, w = im.shape[:2]
        ajuste = br.get("ajuste") or "auto"
        if ajuste in ("auto", "cubrir") and br.get("ajuste") != "cubrir":
            # una captura horizontal en un vertical (o al revés) se vería cortada: va entera
            ajuste = "entero" if max((w / h) / (W / H), (W / H) / (w / h)) > 1.45 else "cubrir"
        if ajuste == "entero":
            # entera sobre un fondo desenfocado de sí misma
            k = min(W / w, H / h)
            peq = cv2.resize(im, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
            k2 = max(W / w, H / h) * 1.1
            fondo = cv2.resize(im, (int(w * k2), int(h * k2)), interpolation=cv2.INTER_AREA)
            y0, x0 = (fondo.shape[0] - H) // 2, (fondo.shape[1] - W) // 2
            fondo = cv2.GaussianBlur(fondo[y0:y0 + H, x0:x0 + W], (0, 0), 30)
            fondo = (fondo * 0.55).astype(np.uint8)
            y1, x1 = (H - peq.shape[0]) // 2, (W - peq.shape[1]) // 2
            fondo[y1:y1 + peq.shape[0], x1:x1 + peq.shape[1]] = peq
            im = fondo
            h, w = im.shape[:2]
        br["img"] = im
    im = br["img"]
    h, w = im.shape[:2]
    base = max(W / w, H / h)
    mov = br.get("movimiento", "acercar")
    z = {"acercar": 1.0 + 0.07 * u, "alejar": 1.07 - 0.07 * u}.get(mov, 1.02)
    k = base * z
    dx = {"derecha": -0.04 * u, "izquierda": 0.04 * u}.get(mov, 0.0) * W
    M = np.float32([[k, 0, (W - w * k) / 2 + dx], [0, k, (H - h * k) / 2]])
    return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def P_hex(marca: dict) -> list[float]:
    from comun import hex_a_rgb
    c = marca["colores"]
    return list(hex_a_rgb(marca.get("color_enfasis") or c.get("acento") or c["principal"]))


def mascara_de(recortador, frame, cara, Mz, sw, sh, W, H, rapida=False):
    centro = None
    if cara:
        centro = ((Mz[0, 0] * cara[0] * sw + Mz[0, 2]) / W, (Mz[1, 1] * cara[1] * sh + Mz[1, 2]) / H)
    return (recortador.mascara_rapida if rapida else recortador.mascara)(frame, centro)


@functools.lru_cache(maxsize=2)
def _rejilla(H: int, W: int):
    import numpy as np
    return np.mgrid[0:H, 0:W].astype(np.float32)


def luz_relleno(frame, mascara, cara, Mz, sw, sh, fuerza):
    """Luz de relleno sobre la persona, como un reflector suave delante: lo máximo en la cara y
    menos hacia el pecho, solo dentro de su silueta (el fondo no se toca). Cada píxel se multiplica
    por 1 + k·(1 − luminosidad): aclara los medios tonos, deja el negro y el blanco donde estaban (no
    quema la piel) y conserva el color. El peso (máscara × foco en la cara) es suave: se calcula a un
    cuarto de resolución."""
    import cv2
    import numpy as np
    H, W = frame.shape[:2]
    h4, w4 = H // 4, W // 4
    m4 = mascara if mascara.shape == (h4, w4) else cv2.resize(mascara, (w4, h4), interpolation=cv2.INTER_AREA)
    yy, xx = _rejilla(h4, w4)
    cx, cy = (Mz[0, 0] * cara[0] * sw + Mz[0, 2]) / 4, (Mz[1, 1] * cara[1] * sh + Mz[1, 2]) / 4
    rx, ry = max(8.0, cara[2] * sw * Mz[0, 0] * 1.4 / 4), max(8.0, cara[3] * sh * Mz[1, 1] * 1.5 / 4)
    foco = np.exp(-0.5 * (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
    k4 = (1.1 * fuerza) * m4 * (0.35 + 0.65 * foco)
    ys, xs = np.nonzero(k4 > 0.002)
    if not len(ys):
        return frame
    # solo se toca la zona de la persona
    y0, y1, x0, x1 = ys.min() * 4, min(H, (ys.max() + 1) * 4), xs.min() * 4, min(W, (xs.max() + 1) * 4)
    k = cv2.resize(k4, (W, H), interpolation=cv2.INTER_LINEAR)[y0:y1, x0:x1]
    zona = frame[y0:y1, x0:x1].astype(np.float32)
    lum = zona @ np.float32([0.299 / 255, 0.587 / 255, 0.114 / 255])
    zona *= (1.0 + k * (1.0 - lum))[:, :, None]
    out = frame.copy()
    out[y0:y1, x0:x1] = np.clip(zona + 0.5, 0, 255).astype(np.uint8)
    return out


def x_barrido(bz: dict, t: float, W: int) -> float:
    """Misma curva que el deslizador de la capa (power2.inOut): de 0 a 62 % y vuelta a 38 %."""
    def io(x):
        x = min(1.0, max(0.0, x))
        return 2 * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 2 / 2
    if t < bz["corte"]:
        return -40 + (W * 0.62 + 40) * io((t - bz["t0"]) / max(0.1, bz["corte"] - bz["t0"]))
    d = max(0.4, bz["t1"] - bz["corte"] - 0.4)
    return W * 0.62 + (W * 0.38 - W * 0.62) * io((t - bz["corte"]) / d)


def tapa_cara(al, cara, M, sw, sh, W, H) -> float:
    """Qué parte de la cara (ojos y boca, el centro del óvalo) queda tapada por la capa."""
    cx, cy, cw, ch = cara
    x0, y0 = (cx - cw * 0.32) * sw, (cy - ch * 0.18) * sh
    x1, y1 = (cx + cw * 0.32) * sw, (cy + ch * 0.28) * sh
    X0 = int(M[0, 0] * x0 + M[0, 2]); Y0 = int(M[1, 1] * y0 + M[1, 2])
    X1 = int(M[0, 0] * x1 + M[0, 2]); Y1 = int(M[1, 1] * y1 + M[1, 2])
    X0, X1 = max(0, X0), min(W, X1)
    Y0, Y1 = max(0, Y0), min(H, Y1)
    if X1 <= X0 or Y1 <= Y0:
        return 0.0
    return float((al[Y0:Y1, X0:X1] > 0.5).mean())


_cache_centros: dict = {}


def centro_suave(plan, pers, sw, sh, t, tramos) -> float:
    """Centro de la franja vertical, con un cambio suave (0,5 s) cuando cambia el plano."""
    clave = round(t, 3)
    if clave in _cache_centros:
        return _cache_centros[clave]
    c = P.centro_vertical(plan, pers, sw, sh, t)
    for a, _b in tramos[1:]:
        if a - 0.25 <= t < a + 0.25:
            antes = P.centro_vertical(plan, pers, sw, sh, a - 0.3)
            despues = P.centro_vertical(plan, pers, sw, sh, a + 0.3)
            u = _suave((t - (a - 0.25)) / 0.5)
            c = antes * (1 - u) + despues * u
    _cache_centros[clave] = c
    return c


def main(argv: list[str]) -> None:
    if not argv:
        fallo("Uso: kit.py componer <video> [--formato ...] [--desde S --hasta S --nombre N]")
    video = resolver_video(argv[0])
    opts = {argv[k].lstrip("-"): argv[k + 1] for k in range(1, len(argv) - 1, 2)}
    trabajo = carpeta_trabajo(video)
    plan = leer_json(trabajo / "plan.json")
    marca = cargar_marca()
    formatos = [opts["formato"]] if "formato" in opts else plan["formatos"]
    nombre = opts.get("nombre")
    finales = carpeta_finales()
    P.asegurar(video, trabajo)
    desde = float(opts["desde"]) if "desde" in opts else None
    hasta = float(opts["hasta"]) if "hasta" in opts else None

    if len(formatos) > 1:
        # los dos formatos a la vez, cada uno en su proceso: un 30 % menos de espera
        paso(f"Componiendo {len(formatos)} formatos a la vez (cámara, énfasis por detrás y sonido)")
        kit = Path(__file__).resolve().parent / "kit.py"
        extra = [a for k in ("desde", "hasta", "nombre") if k in opts for a in (f"--{k}", opts[k])]
        # el reloj de verdad es el de los dos a la vez: «tiempos» usa este y no suma los de cada formato
        etiqueta_par = "componer-" + "+".join(f"{nombre}-{f}" if nombre else f for f in formatos)
        with Cronometro(trabajo, etiqueta_par):
            procs = [subprocess.Popen([sys.executable, str(kit), "componer", str(video), "--formato", f, *extra],
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) for f in formatos]
            mal = False
            for f, pr in zip(formatos, procs):
                salida_txt = pr.communicate()[0] or ""
                for linea in salida_txt.splitlines():
                    if linea.startswith(("   [", "   (fase")):
                        print(linea, flush=True)
                mal = mal or pr.returncode != 0
                if pr.returncode != 0:
                    print(salida_txt[-2000:])
        if mal:
            fallo("La composición de algún formato ha fallado (arriba el detalle).")
        return

    for formato in formatos:
        etiqueta = f"{nombre}-{formato}" if nombre else formato
        if not (trabajo / f"capa-{etiqueta}.mov").exists():
            fallo(f"Falta la capa animada capa-{etiqueta}.mov.", f"Lanza antes: kit.py animar {argv[0]}")
        salida = finales / f"{slug(video.stem)}-{etiqueta}.mp4"
        paso(f"Componiendo {salida.name} (cámara, énfasis por detrás y sonido)")
        with Cronometro(trabajo, f"componer-{etiqueta}"):
            res = componer_formato(trabajo, formato, etiqueta, plan, marca, desde, hasta, salida)
        escribir_json(trabajo / f"composicion-{etiqueta}.json", res)
        final = info_video(salida)
        ok(f"{salida.name}: {final['ancho']}x{final['alto']}, {final['duracion']:.1f} s, "
           f"audio: {'sí' if final['tiene_audio'] else 'NO'}")
        if res["caras_tapadas"]:
            peor = max(res["caras_tapadas"], key=lambda x: x["tapado"])
            aviso(f"Algún texto tapa la cara en {len(res['caras_tapadas'])} momento(s) "
                  f"(el peor en {peor['t']:.1f} s, {int(peor['tapado'] * 100)} %). Revísalo en verificar.")
        ok(f"Guardado en {salida}")


if __name__ == "__main__":
    main(sys.argv[1:])

"""Alineación fina de las palabras con el audio (para que cada palabra del subtítulo se ilumine
justo cuando se dice).

Whisper acierta el texto, pero sitúa cada palabra con un error de 0,2 a 0,5 s, unas veces antes
y otras después. Aquí, con el texto ya sabido, un modelo de reconocimiento por letras (wav2vec2
CTC en español, en local con onnxruntime) encaja cada letra en su trama de 20 ms (alineación
forzada de Viterbi) y cada palabra se queda con el tiempo de sus letras.

Modelo: jonatasgrosman/wav2vec2-large-xlsr-53-spanish (licencia Apache-2.0), exportado a ONNX en
XDcobra/wav2vec2-large-xlsr-53-spanish-ONNX. Se guarda en modelos/ (unos 355 MB, una sola vez).
"""
from __future__ import annotations

import json
import unicodedata
import wave
from pathlib import Path

REPO = "XDcobra/wav2vec2-large-xlsr-53-spanish-ONNX"
REVISION = "e85bd63cd513cd41f1bcc6c7d8c4e1af0255d448"
MODELO = "onnx/model_int8.onnx"
IDIOMAS = {"es"}
TRAMA = 0.02          # segundos por trama del modelo (320 muestras a 16 kHz)
MARGEN = 0.6          # ventana extra a cada lado del tramo de Whisper
MAX_VENTANA = 28.0    # el modelo atiende a todo el tramo: más largo se parte en dos
COLA = 0.08           # la última letra suele marcarse un poco antes de que acabe la palabra

_sesion = None
_vocab = None


def disponible(idioma: str) -> bool:
    return idioma in IDIOMAS


def descargar() -> Path:
    """Baja (una vez) el modelo y su vocabulario. Devuelve la ruta del modelo."""
    from huggingface_hub import hf_hub_download
    hf_hub_download(REPO, "vocab.json", revision=REVISION)
    return Path(hf_hub_download(REPO, MODELO, revision=REVISION))


def _cargar():
    global _sesion, _vocab
    if _sesion is None:
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download
        try:
            ruta = hf_hub_download(REPO, MODELO, revision=REVISION, local_files_only=True)
            voc = hf_hub_download(REPO, "vocab.json", revision=REVISION, local_files_only=True)
        except Exception:  # aún no está en modelos/: se baja ahora
            ruta, voc = str(descargar()), hf_hub_download(REPO, "vocab.json", revision=REVISION)
        _vocab = json.loads(Path(voc).read_text(encoding="utf-8"))
        _sesion = ort.InferenceSession(ruta, providers=["CPUExecutionProvider"])
    return _sesion, _vocab


def leer_wav(ruta: Path):
    import numpy as np
    with wave.open(str(ruta)) as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1, "hace falta audio mono a 16 kHz"
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def emisiones(audio):
    """Log-probabilidades por trama (20 ms) y letra."""
    import numpy as np
    sesion, _ = _cargar()
    x = (audio - audio.mean()) / np.sqrt(audio.var() + 1e-7)
    lg = sesion.run(None, {sesion.get_inputs()[0].name: x[None, :].astype(np.float32)})[0][0]
    lg = lg - lg.max(axis=1, keepdims=True)
    return lg - np.log(np.exp(lg).sum(axis=1, keepdims=True))


def letras_de(palabra: str, vocab: dict) -> list[int]:
    """Las letras de una palabra en el vocabulario del modelo (sin signos; tildes raras, a su vocal)."""
    out = []
    for ch in palabra.lower():
        if ch in vocab and ch not in ("|", "-", "'") and len(ch) == 1:
            out.append(vocab[ch])
            continue
        base = unicodedata.normalize("NFKD", ch)[0]
        if base.isalpha() and base in vocab:
            out.append(vocab[base])
    return out


def viterbi(E, fichas: list[int], blanco: int = 0):
    """Alineación forzada CTC: el estado (blanco o letra) de cada trama. None si no cabe."""
    import numpy as np
    T, L = E.shape[0], len(fichas)
    S = 2 * L + 1
    etiq = np.full(S, blanco, np.int64)
    etiq[1::2] = fichas
    # se puede saltar el blanco entre dos letras distintas (entre dos iguales, no: «ll», «rr»)
    salto = np.zeros(S, bool)
    salto[3::2] = etiq[3::2] != etiq[1:-2:2]
    if T < L + int((~salto[3::2]).sum()):
        return None
    NEG = -1e30
    alfa = np.full(S, NEG)
    alfa[0] = E[0, blanco]
    alfa[1] = E[0, etiq[1]]
    atras = np.zeros((T, S), np.int8)
    idx = np.arange(S)
    for t in range(1, T):
        a1 = np.concatenate(([NEG], alfa[:-1]))
        a2 = np.where(salto, np.concatenate(([NEG, NEG], alfa[:-2])), NEG)
        pila = np.stack([alfa, a1, a2])
        mejor = pila.argmax(0)
        alfa = pila[mejor, idx] + E[t, etiq]
        atras[t] = mejor
    s = S - 1 if alfa[S - 1] >= alfa[S - 2] else S - 2
    if alfa[s] <= NEG / 2:
        return None
    camino = np.empty(T, np.int64)
    for t in range(T - 1, -1, -1):
        camino[t] = s
        s -= int(atras[t, s])
    return camino


def _alinear_tramo(audio, palabras: list[dict], desde: float, hasta: float, vocab: dict) -> int:
    """Encaja las palabras de un tramo [desde, hasta] (segundos). Devuelve cuántas ha movido."""
    if hasta - desde > MAX_VENTANA and len(palabras) > 1:  # demasiado largo para una pasada
        mitad = len(palabras) // 2
        corte = (palabras[mitad - 1]["e"] + palabras[mitad]["s"]) / 2
        return (_alinear_tramo(audio, palabras[:mitad], desde, min(hasta, corte + MARGEN), vocab)
                + _alinear_tramo(audio, palabras[mitad:], max(desde, corte - MARGEN), hasta, vocab))
    import numpy as np
    a, b = int(desde * 16000), int(hasta * 16000)
    if b - a < 16000 * 0.3:
        return 0
    E = emisiones(audio[a:b])
    fichas, dueno = [], []
    for k, w in enumerate(palabras):
        ls = letras_de(w["w"], vocab)
        if not ls:
            continue
        if fichas:
            fichas.append(vocab["|"])
            dueno.append(-1)
        fichas += ls
        dueno += [k] * len(ls)
    if not fichas:
        return 0
    camino = viterbi(E, fichas)
    if camino is None:
        return 0
    tramas: dict[int, list[int]] = {}
    for t, st in enumerate(camino):
        if st % 2 == 1 and dueno[(st - 1) // 2] >= 0:
            tramas.setdefault(dueno[(st - 1) // 2], []).append(t)
    movidas = 0
    for k, w in enumerate(palabras):
        if k not in tramas:
            continue
        s = round(desde + min(tramas[k]) * TRAMA, 3)
        e = round(desde + (max(tramas[k]) + 1) * TRAMA, 3)
        if abs(s - w["s"]) > 1.2:  # demasiado lejos de lo que oyó Whisper: no me fío
            continue
        w["s"], w["e"] = s, e
        movidas += 1
    return movidas


def refinar(wav: Path, palabras: list[dict], idioma: str, segmentos: list[dict] | None = None) -> int:
    """Corrige en el sitio los tiempos («s», «e») de las palabras. Devuelve cuántas ha encajado."""
    if not disponible(idioma) or not palabras:
        return 0
    _, vocab = _cargar()
    audio = leer_wav(wav)
    dur = len(audio) / 16000
    # tramos: frases de Whisper (o todo junto si no las hay), con margen a los lados
    grupos = []
    if segmentos:
        for sg in segmentos:
            grupos.append([w for w in palabras if sg["i0"] <= w["i"] <= sg["i1"]])
    else:
        grupos = [palabras]
    movidas = 0
    for g in grupos:
        if g:
            movidas += _alinear_tramo(audio, g, max(0.0, g[0]["s"] - MARGEN), min(dur, g[-1]["e"] + MARGEN), vocab)
    # orden y continuidad: la palabra dura hasta poco después de su última letra, sin pisar la siguiente
    for k, w in enumerate(palabras):
        sig = palabras[k + 1]["s"] if k + 1 < len(palabras) else dur
        if k and w["s"] < palabras[k - 1]["s"]:
            w["s"] = palabras[k - 1]["s"]
        w["e"] = round(max(w["s"] + 0.06, min(w["e"] + COLA, sig)), 3)
    return movidas

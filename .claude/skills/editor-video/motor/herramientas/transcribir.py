"""Fase 1 · Transcribir con marcas de tiempo por palabra (Whisper en local, gratis).

Mac con chip Apple (M1 o superior): mlx-whisper, que usa la GPU del Mac.
Windows, Linux o Mac Intel: faster-whisper, en el procesador.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from comun import (ES_APPLE_SILICON, Cronometro, aviso, cargar_marca, carpeta_trabajo,
                   ejecutar, escribir_json, fmt_t, info_video, ok, paso, fallo)

MODELOS_MLX = {
    "turbo": "mlx-community/whisper-large-v3-turbo",
    "small": "mlx-community/whisper-small-mlx",
}
MODELOS_FW = {
    "turbo": "large-v3-turbo",
    "small": "small",
}


def extraer_audio(video: Path, destino: Path) -> Path:
    ejecutar(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1",
              "-ar", "16000", "-c:a", "pcm_s16le", str(destino)])
    return destino


def pista(glosario: list[str], idioma: str) -> str | None:
    """La pista para Whisper, escrita como una frase normal con mayúsculas y signos: con la lista
    de nombres sola, a veces transcribe todo en minúsculas y sin un punto."""
    if idioma != "es":
        return ", ".join(glosario) + "." if glosario else None
    if not glosario:
        return "Hola, ¿qué tal? Hoy te cuento algo."
    nombres = glosario[0] if len(glosario) == 1 else ", ".join(glosario[:-1]) + " y " + glosario[-1]
    return f"Hola, ¿qué tal? Hoy te hablo de {nombres}."


def transcribir_audio(wav: Path, idioma: str, modelo: str, glosario: list[str]) -> tuple[list, str]:
    prompt = pista(glosario, idioma)
    palabras = []
    if ES_APPLE_SILICON:
        import mlx_whisper  # noqa
        r = mlx_whisper.transcribe(str(wav), path_or_hf_repo=MODELOS_MLX.get(modelo, modelo),
                                   language=idioma, word_timestamps=True,
                                   initial_prompt=prompt)
        for seg in r["segments"]:
            for w in seg.get("words", []):
                palabras.append((w["word"], w["start"], w["end"], w.get("probability", 1.0)))
        motor = f"mlx-whisper ({MODELOS_MLX.get(modelo, modelo)})"
    else:
        from faster_whisper import WhisperModel  # noqa
        m = WhisperModel(MODELOS_FW.get(modelo, modelo), device="cpu", compute_type="int8")
        segs, _ = m.transcribe(str(wav), language=idioma, word_timestamps=True,
                               initial_prompt=prompt, vad_filter=False)
        for seg in segs:
            for w in seg.words or []:
                palabras.append((w.word, w.start, w.end, w.probability))
        motor = f"faster-whisper ({MODELOS_FW.get(modelo, modelo)})"
    return palabras, motor


def _limpia(t: str) -> str:
    return re.sub(r"[^\w.]", "", t.lower())


def aplicar_correcciones(palabras: list[dict], correcciones: dict) -> list[dict]:
    for mal, bien in sorted(correcciones.items(), key=lambda kv: -len(kv[0].split())):
        pm, pb = mal.split(), bien.split()
        n, j, salida = len(pm), 0, []
        while j < len(palabras):
            trozo = palabras[j:j + n]
            if len(trozo) == n and [_limpia(w["w"]).strip(".") for w in trozo] == [_limpia(x) for x in pm]:
                final = re.search(r"[.,;:!?…]+$", trozo[-1]["w"])
                cola = final.group(0) if final else ""
                if len(pb) == n:
                    for w, b in zip(trozo, pb):
                        salida.append(dict(w, w=b))
                    salida[-1]["w"] += cola
                else:
                    salida.append(dict(trozo[0], w=bien + cola, e=trozo[-1]["e"]))
                j += n
            else:
                salida.append(palabras[j])
                j += 1
        palabras = salida
    for k, w in enumerate(palabras):
        w["i"] = k
    return palabras


def a_segmentos(palabras: list[dict], hueco: float = 0.6) -> list[dict]:
    """Agrupa palabras en frases: corta en punto o en pausa larga."""
    segs, actual = [], []
    for i, w in enumerate(palabras):
        actual.append(w)
        fin_frase = re.search(r"[.!?…]$", w["w"])
        siguiente = palabras[i + 1] if i + 1 < len(palabras) else None
        pausa = siguiente and (siguiente["s"] - w["e"]) > hueco
        if fin_frase or pausa or siguiente is None:
            segs.append({"s": actual[0]["s"], "e": actual[-1]["e"],
                         "i0": actual[0]["i"], "i1": actual[-1]["i"],
                         "texto": " ".join(x["w"] for x in actual)})
            actual = []
    return segs


def texto_legible(segs: list[dict]) -> str:
    return "\n".join(f"[{fmt_t(s['s'])} a {fmt_t(s['e'])}] (palabras {s['i0']}-{s['i1']}) {s['texto']}"
                     for s in segs)


def main(argv: list[str]) -> None:
    if not argv:
        fallo("Uso: kit.py transcribir <video>")
    from comun import resolver_video
    video = resolver_video(argv[0])
    trabajo = carpeta_trabajo(video)
    marca = cargar_marca()
    cfg = marca.get("transcripcion", {})
    idioma = cfg.get("idioma", "es")
    modelo = cfg.get("modelo", "turbo")

    paso(f"Transcribiendo «{video.name}» (idioma: {idioma}, modelo: {modelo})")
    iv = info_video(video)
    if not iv["tiene_audio"]:
        fallo("El vídeo no tiene audio, no hay nada que transcribir.")
    ok(f"Vídeo {iv['ancho']}x{iv['alto']}, {iv['fps']} fps, {iv['duracion']:.1f} s")
    escribir_json(trabajo / "origen.json", {"video": str(video), **iv})

    with Cronometro(trabajo, "transcribir"):
        wav = extraer_audio(video, trabajo / "audio.wav")
        crudas, motor = transcribir_audio(wav, idioma, modelo, cfg.get("glosario", []))

    correcciones = cfg.get("correcciones", {})
    palabras = []
    for w, s, e, p in crudas:
        # Whisper a veces parte «5.5» en «5» + «.5»: lo que llega sin espacio delante va pegado
        if palabras and w and not w[0].isspace() and w.strip():
            palabras[-1]["w"] += w.strip()
            palabras[-1]["e"] = round(float(e), 3)
            continue
        if not w.strip():
            continue
        palabras.append({"i": len(palabras), "w": w.strip(), "s": round(float(s), 3),
                         "e": round(float(e), 3), "p": round(float(p), 3)})
    # correcciones del glosario, de una o varias palabras («Cloud Markdown» -> «CLAUDE.md»)
    palabras = aplicar_correcciones(palabras, correcciones)
    # Whisper sitúa cada palabra con 0,2-0,5 s de error: el alineador la encaja en el audio (alinear.py)
    import alinear
    if alinear.disponible(idioma):
        try:
            with Cronometro(trabajo, "alinear"):
                n = alinear.refinar(wav, palabras, idioma, a_segmentos(palabras))
            ok(f"{n} de {len(palabras)} palabras encajadas en el audio al centésimo (alineador wav2vec2)")
        except Exception as ex:  # sin el modelo o sin memoria: se quedan los tiempos de Whisper
            aviso(f"No he podido alinear las palabras con el audio ({type(ex).__name__}): uso los tiempos de Whisper.")
    segs = a_segmentos(palabras)
    escribir_json(trabajo / "palabras.json", {"motor": motor, "idioma": idioma,
                                              "duracion": iv["duracion"], "palabras": palabras,
                                              "segmentos": segs})
    (trabajo / "transcripcion.txt").write_text(texto_legible(segs), encoding="utf-8")
    ok(f"{len(palabras)} palabras con su tiempo exacto ({motor})")
    ok(f"Guardado en {trabajo.name}/palabras.json y {trabajo.name}/transcripcion.txt")
    dudosas = [w for w in palabras if w["p"] < 0.45]
    if dudosas:
        print(f"   Palabras dudosas (revisa si son nombres propios): "
              + ", ".join(sorted({w['w'] for w in dudosas})[:25]))


if __name__ == "__main__":
    main(sys.argv[1:])

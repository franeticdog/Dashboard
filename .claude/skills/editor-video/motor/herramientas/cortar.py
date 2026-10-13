"""Fase 2 · Cortar silencios, tomas repetidas y frases a medias.

  kit.py cortar analizar <video>   -> propone los cortes en trabajo/<video>/cortes.json
  kit.py cortar aplicar <video>    -> genera trabajo/<video>/cortado.mp4 y reajusta los tiempos

Entre las dos órdenes, Claude lee la transcripción y ajusta cortes.json
(añade o quita cortes por número de palabra). El script detecta; Claude decide.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from comun import (Cronometro, cargar_marca, carpeta_trabajo, ejecutar, escribir_json,
                   fallo, fmt_t, info_video, leer_json, ok, paso, resolver_video)

MULETILLAS = {"eh", "ehh", "ehm", "em", "emm", "mm", "mmm", "hmm", "uhm"}
CONECTORES = {"de", "que", "y", "el", "la", "los", "las", "en", "a", "para", "con", "por",
              "un", "una", "o", "pero", "porque", "como", "lo", "se", "del", "al", "tu", "mi"}


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", "", t).strip()


def silencios_audio(wav: Path, minimo: float, umbral_db: int = -35) -> list[tuple[float, float]]:
    res = ejecutar(["ffmpeg", "-hide_banner", "-nostats", "-i", str(wav), "-af",
                    f"silencedetect=noise={umbral_db}dB:d={minimo}", "-f", "null", "-"],
                   comprobar=False)
    ini, out = None, []
    for linea in (res.stdout or "").splitlines():
        m = re.search(r"silence_start: ([\d.]+)", linea)
        if m:
            ini = float(m.group(1))
        m = re.search(r"silence_end: ([\d.]+)", linea)
        if m and ini is not None:
            out.append((ini, float(m.group(1))))
            ini = None
    return out


def analizar(video: Path) -> None:
    trabajo = carpeta_trabajo(video)
    datos = leer_json(trabajo / "palabras.json")
    palabras, segs, dur = datos["palabras"], datos["segmentos"], datos["duracion"]
    cfg = cargar_marca().get("cortes", {})
    minimo, margen = cfg.get("silencio_min", 0.55), cfg.get("margen", 0.12)

    paso("Buscando silencios, tomas repetidas y frases a medias")
    quitar, revisar = [], []

    # 1) silencios: los que marca el audio y los huecos entre palabras
    huecos = silencios_audio(trabajo / "audio.wav", minimo)
    for i in range(len(palabras) - 1):
        a, b = palabras[i]["e"], palabras[i + 1]["s"]
        if b - a > minimo + 0.25:
            huecos.append((a, b))
    if palabras:
        if palabras[0]["s"] > minimo:
            huecos.append((0.0, palabras[0]["s"]))
        if dur - palabras[-1]["e"] > minimo:
            huecos.append((palabras[-1]["e"], dur))
    for a, b in huecos:
        s, e = a + margen, b - margen
        if a <= 0.01:
            s = 0.0
        if b >= dur - 0.01:
            e = dur
        # nunca cortar dentro de una palabra
        if any(w["s"] < e and w["e"] > s and (min(e, w["e"]) - max(s, w["s"])) > 0.08 for w in palabras):
            continue
        if e - s >= 0.2:
            quitar.append({"s": round(s, 3), "e": round(e, 3), "motivo": "silencio"})

    # 2) muletillas sueltas
    for w in palabras:
        if norm(w["w"]) in MULETILLAS:
            quitar.append({"s": w["s"], "e": w["e"], "motivo": f"muletilla «{w['w']}»",
                           "palabras": [w["i"], w["i"]]})

    # 3) tomas repetidas: una frase y, justo después, otra que empieza igual
    for k, seg in enumerate(segs):
        ini_k = norm(seg["texto"]).split()[:6]
        if len(ini_k) < 3:
            continue
        for sig in segs[k + 1:k + 3]:
            ini_s = norm(sig["texto"]).split()[:6]
            parecido = SequenceMatcher(None, ini_k, ini_s).ratio()
            if (ini_k[:3] == ini_s[:3] or parecido >= 0.7) and sig["s"] - seg["e"] < 25:
                quitar.append({"s": seg["s"], "e": sig["s"] - margen,
                               "motivo": "toma repetida (me quedo con la última)",
                               "palabras": [seg["i0"], sig["i0"] - 1], "texto": seg["texto"]})
                break

    # 4) frases a medias: acaban en conector y luego hay pausa larga
    for k, seg in enumerate(segs[:-1]):
        ult = norm(seg["texto"]).split()[-1:] or [""]
        pausa = segs[k + 1]["s"] - seg["e"]
        if ult[0] in CONECTORES and pausa > 0.5:
            revisar.append({"s": seg["s"], "e": seg["e"], "motivo": "frase a medias (decide Claude)",
                            "palabras": [seg["i0"], seg["i1"]], "texto": seg["texto"]})

    quitar.sort(key=lambda c: c["s"])
    total = sum(c["e"] - c["s"] for c in quitar)
    escribir_json(trabajo / "cortes.json", {
        "nota": "Claude: revisa 'revisar' leyendo transcripcion.txt. Para cortar algo más, añade a "
                "'quitar' un objeto con 'palabras': [desde, hasta] (números de palabra) y un 'motivo'.",
        "quitar": quitar, "revisar": revisar})
    ok(f"{len(quitar)} cortes propuestos ({total:.1f} s de {dur:.1f} s)")
    por_motivo = {}
    for c in quitar:
        clave = c["motivo"].split(" (")[0].split(" «")[0]
        por_motivo[clave] = por_motivo.get(clave, 0) + 1
    for m, n in por_motivo.items():
        print(f"     · {m}: {n}")
    for r in revisar:
        print(f"   Revisar {fmt_t(r['s'])}: «{r['texto'][:90]}»")
    ok(f"Propuesta en {trabajo.name}/cortes.json")


def rangos_a_quitar(cortes: dict, palabras: list[dict]) -> list[tuple[float, float]]:
    r = []
    por_indice = {w["i"]: w for w in palabras}
    for c in cortes.get("quitar", []):
        if "palabras" in c and c["palabras"]:
            i0, i1 = c["palabras"]
            if i0 in por_indice and i1 in por_indice:
                s = min(c.get("s", 1e9), por_indice[i0]["s"])
                e = max(c.get("e", 0), por_indice[i1]["e"])
                r.append((s, e))
                continue
        r.append((c["s"], c["e"]))
    r.sort()
    unidos = []
    for s, e in r:
        if unidos and s <= unidos[-1][1] + 0.05:
            unidos[-1] = (unidos[-1][0], max(unidos[-1][1], e))
        else:
            unidos.append((s, e))
    return unidos


def opcion_guion() -> str:
    """ffmpeg 7 cambió «-filter_complex_script» por «-/filter_complex», y la 9 ya no admite la vieja."""
    m = re.search(r"version n?(\d+)\.", ejecutar(["ffmpeg", "-version"]).stdout)
    return "-filter_complex_script" if m and int(m.group(1)) < 7 else "-/filter_complex"


def aplicar(video: Path) -> None:
    trabajo = carpeta_trabajo(video)
    datos = leer_json(trabajo / "palabras.json")
    cortes = leer_json(trabajo / "cortes.json")
    iv = info_video(video)
    dur = iv["duracion"]
    zoom = cargar_marca().get("cortes", {}).get("zoom_en_cortes", True)

    quitar = rangos_a_quitar(cortes, datos["palabras"])
    tramos, t = [], 0.0
    for s, e in quitar:
        if s - t > 0.25:
            tramos.append((t, s))
        t = max(t, e)
    if dur - t > 0.25:
        tramos.append((t, dur))
    if not tramos:
        fallo("Los cortes se comerían todo el vídeo. Revisa cortes.json.")

    paso(f"Montando el vídeo cortado: {len(tramos)} tramos")
    w, h = iv["ancho"], iv["alto"]
    filtros, etiquetas = [], []
    for k, (s, e) in enumerate(tramos):
        v = f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS"
        # zoom alterno: un tramo sí y otro no, para disimular el salto del corte. Anclado a la altura
        # de la cara (un tercio desde arriba), no al centro: así la cara no da un saltito en cada corte
        if zoom and k % 2 == 1:
            v += f",scale={int(w * 1.08) // 2 * 2}:-2:flags=lanczos,crop={w}:{h}:(iw-ow)/2:(ih-oh)*0.3"
        v += f",fps={iv['fps']},format=yuv420p[v{k}]"
        fa = min(0.02, (e - s) / 4)
        a = (f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,"
             f"afade=t=in:d={fa:.3f},afade=t=out:st={max(0, e - s - fa):.3f}:d={fa:.3f}[a{k}]")
        filtros += [v, a]
        etiquetas.append(f"[v{k}][a{k}]")
    filtros.append("".join(etiquetas) + f"concat=n={len(tramos)}:v=1:a=1[v][a]")
    guion = trabajo / "cortes.ffscript"
    guion.write_text(";\n".join(filtros), encoding="utf-8")
    salida = trabajo / "cortado.mp4"
    with Cronometro(trabajo, "cortar"):
        ejecutar(["ffmpeg", "-v", "error", "-y", "-i", str(video),
                  opcion_guion(), str(guion), "-map", "[v]", "-map", "[a]",
                  # intermedio casi sin pérdida: todavía hay que componer y volver a codificar encima
                  "-c:v", "libx264", "-preset", "veryfast", "-crf", "12",
                  "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(salida)])

    # reajustar los tiempos de cada palabra al vídeo cortado
    nuevas, mapa, acumulado = [], [], 0.0
    for s, e in tramos:
        mapa.append({"orig_s": round(s, 3), "orig_e": round(e, 3), "nuevo_s": round(acumulado, 3)})
        for wd in datos["palabras"]:
            centro = (wd["s"] + wd["e"]) / 2
            if s <= centro < e:
                nuevas.append({**wd, "s": round(max(0, wd["s"] - s) + acumulado, 3),
                               "e": round(min(e, wd["e"]) - s + acumulado, 3)})
        acumulado += e - s
    for j, wd in enumerate(nuevas):
        wd["i"] = j
    from transcribir import a_segmentos, texto_legible
    segs = a_segmentos(nuevas)
    escribir_json(trabajo / "palabras_cortado.json", {"duracion": round(acumulado, 3),
                                                      "palabras": nuevas, "segmentos": segs,
                                                      "mapa": mapa})
    (trabajo / "transcripcion_cortada.txt").write_text(texto_legible(segs), encoding="utf-8")
    ok(f"De {dur:.1f} s a {acumulado:.1f} s (fuera {dur - acumulado:.1f} s, un "
       f"{100 * (dur - acumulado) / dur:.0f} %)")
    ok(f"Vídeo cortado: {trabajo.name}/cortado.mp4")


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[0] not in ("analizar", "aplicar"):
        fallo("Uso: kit.py cortar analizar|aplicar <video>")
    video = resolver_video(argv[1])
    (analizar if argv[0] == "analizar" else aplicar)(video)


if __name__ == "__main__":
    main(sys.argv[1:])

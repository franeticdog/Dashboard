"""Fase 6 · Verificar: saca fotogramas en los momentos clave para que Claude los mire.

  kit.py verificar <video> [--formato horizontal|vertical] [--nombre reel1]

Hace comprobaciones automáticas (duración, audio, fotogramas negros) y guarda capturas
en trabajo/<video>/capturas/<formato>/ más una hoja de contactos (hoja.jpg).
Claude abre las capturas, revisa legibilidad, que nada tape la cara y que cada texto
entre cuando toca, y corrige antes de entregar.
"""
from __future__ import annotations

import re
import shutil
import sys

from comun import (Cronometro, carpeta_finales, carpeta_trabajo, ejecutar, escribir_json, fallo,
                   fmt_t, info_video, leer_json, ok, paso, resolver_video, slug, aviso)


def main(argv: list[str]) -> None:
    if not argv:
        fallo("Uso: kit.py verificar <video> [--formato ...] [--nombre N]")
    video = resolver_video(argv[0])
    opts = {argv[k].lstrip("-"): argv[k + 1] for k in range(1, len(argv) - 1, 2)}
    trabajo = carpeta_trabajo(video)
    plan = leer_json(trabajo / "plan.json")
    pc = leer_json(trabajo / "palabras_cortado.json")
    formatos = [opts["formato"]] if "formato" in opts else plan["formatos"]
    nombre = opts.get("nombre")

    for formato in formatos:
        etiqueta = f"{nombre}-{formato}" if nombre else formato
        final = carpeta_finales() / f"{slug(video.stem)}-{etiqueta}.mp4"
        if not final.exists():
            fallo(f"No existe {final.name}.", "Lanza antes componer.")
        paso(f"Verificando {final.name}")
        problemas = []
        with Cronometro(trabajo, f"verificar-{etiqueta}"):
            iv = info_video(final)
            esperada = pc["duracion"] if not nombre else None
            if esperada and abs(iv["duracion"] - esperada) > 0.5:
                problemas.append(f"Duración {iv['duracion']:.1f} s y esperaba {esperada:.1f} s")
            if not iv["tiene_audio"]:
                problemas.append("El vídeo final no tiene audio")
            negros = ejecutar(["ffmpeg", "-hide_banner", "-nostats", "-i", str(final), "-vf",
                               "blackdetect=d=0.4:pix_th=0.08", "-an", "-f", "null", "-"],
                              comprobar=False).stdout or ""
            for m in re.finditer(r"black_start:([\d.]+) black_end:([\d.]+)", negros):
                problemas.append(f"Pantalla en negro de {fmt_t(float(m.group(1)))} a {fmt_t(float(m.group(2)))}")

            # momentos a capturar: cada pieza ya asentada + subtítulos repartidos
            momentos = []
            # en un reel, las piezas del plan que caen en su tramo, con el tiempo del reel
            ev = leer_json(trabajo / f"eventos-{etiqueta}.json", defecto={}) if nombre else {}
            r0 = float(ev.get("desde", 0.0))
            r1 = float(ev.get("hasta", 1e9))
            if not nombre or ev:
                for b in plan["beats"]:
                    if "inicio" not in b or b["tipo"] == "rotulo" and nombre:
                        continue
                    if nombre:
                        if not (r0 <= b["inicio"] < r1 - 1):
                            continue
                        b = dict(b, inicio=b["inicio"] - r0)
                    if b["tipo"] == "transicion":
                        momentos.append((b["inicio"] + 0.02, f"transicion-{b['id']}"))
                    elif b["tipo"] == "logo":  # el logo grande y luego en su rótulo
                        momentos.append((b["inicio"] + 1.1, f"logo-3d-{b['id']}"))
                        momentos.append((b["inicio"] + min(3.0, b["duracion"] - 0.7), f"logo-{b['id']}"))
                    else:  # pieza ya asentada (con la palabra clave dentro)
                        momentos.append((b["inicio"] + min(1.4, b["duracion"] * 0.6), f"{b['tipo']}-{b['id']}"))
            dur = iv["duracion"]
            for k in range(1, 4):
                momentos.append((dur * k / 4, "subtitulos"))
            momentos.append((max(0.0, dur - 0.5), "final"))
            momentos = sorted((min(max(0.0, t), max(0.0, dur - 0.15)), q) for t, q in momentos)

            carpeta = trabajo / "capturas" / etiqueta
            if carpeta.exists():
                shutil.rmtree(carpeta)
            carpeta.mkdir(parents=True)
            capturas = []
            for n, (t, que) in enumerate(momentos, 1):
                ruta = carpeta / f"{n:02d}-{t:06.2f}s-{que}.jpg"
                ejecutar(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(final),
                          "-frames:v", "1", "-q:v", "3", "-vf",
                          "scale=960:-2" if formato == "horizontal" else "scale=540:-2", str(ruta)])
                capturas.append(ruta)
            # hoja de contactos
            tmp = carpeta / "_seq"
            tmp.mkdir()
            for n, c in enumerate(capturas):
                shutil.copy(c, tmp / f"{n:03d}.jpg")
            cols = 3 if formato == "horizontal" else 4
            filas = -(-len(capturas) // cols)
            ejecutar(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", str(tmp / "%03d.jpg"),
                      "-vf", f"scale={'640:-2' if formato == 'horizontal' else '360:-2'},"
                             f"tile={cols}x{filas}:padding=8:color=white",
                      "-frames:v", "1", str(carpeta / "hoja.jpg")])
            shutil.rmtree(tmp)

        comp = leer_json(trabajo / f"composicion-{etiqueta}.json", defecto={})
        for c in comp.get("caras_tapadas", []):
            if c["tapado"] >= 0.15:
                problemas.append(f"Un texto tapa la cara en {fmt_t(c['t'])} ({int(c['tapado'] * 100)} % de ojos y boca)")
        escribir_json(carpeta / "verificacion.json", {"final": str(final), "problemas": problemas,
                                                      "capturas": [c.name for c in capturas]})
        if problemas:
            for p in problemas:
                aviso(p)
        else:
            ok("Duración, audio y fotogramas negros: todo en orden")
        ok(f"{len(capturas)} capturas + hoja de contactos en {carpeta.relative_to(trabajo.parent.parent)}")
        print("   Claude: abre hoja.jpg y las capturas de cada pieza. Revisa: se lee bien, no tapa la cara,")
        print("   no se sale del encuadre, el texto coincide con lo que se dice. Si algo falla, corrige y repite.")


if __name__ == "__main__":
    main(sys.argv[1:])

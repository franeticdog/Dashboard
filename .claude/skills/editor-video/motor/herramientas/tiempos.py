"""Enseña cuánto ha tardado cada fase de un vídeo (para saber cuánto tiempo te ahorras)."""
from __future__ import annotations

import sys

from comun import carpeta_trabajo, fallo, leer_json, resolver_video


def main(argv: list[str]) -> None:
    if not argv:
        fallo("Uso: kit.py tiempos <video>")
    video = resolver_video(argv[0])
    t = leer_json(carpeta_trabajo(video) / "tiempos.json", defecto={})
    origen = leer_json(carpeta_trabajo(video) / "origen.json", defecto={})
    # los formatos que se componen a la vez cuentan una vez (el reloj del conjunto), no la suma
    en_paralelo = set()
    for fase in t:
        if fase.startswith("componer-") and "+" in fase:
            en_paralelo.update("componer-" + x for x in fase[len("componer-"):].split("+"))
    print(f"| Fase | Segundos |\n|---|---|")
    total = 0.0
    for fase, seg in t.items():
        if fase in en_paralelo:
            print(f"| {fase} (a la vez que el otro formato) | {seg} |")
            continue
        print(f"| {fase} | {seg} |")
        total += seg
    print(f"| **Total de máquina** | **{total:.0f} s ({total / 60:.1f} min)** |")
    if origen.get("duracion"):
        print(f"\nVídeo de {origen['duracion']:.0f} s: {total / origen['duracion']:.1f} s de proceso por cada segundo de vídeo.")


if __name__ == "__main__":
    main(sys.argv[1:])

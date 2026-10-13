> Las órdenes `kit.py …` se lanzan así, desde la carpeta del proyecto: `py "<carpeta de la skill>/motor/herramientas/kit.py" …` (ver SKILL.md). Donde pone `brand.json` y `marca/` son los de la marca en uso, compartidos por todos sus proyectos: `kit.py proyecto` dice dónde están.

# Estilo (plantillas de edición)

**Idioma:** responde siempre en español de España, también en el resumen final.

```
kit.py estilo lista                       # las que hay y cuál está activa
kit.py estilo ver <nombre>                 # una plantilla en llano
kit.py estilo analizar <refs...> --nombre N  # fotogramas + cambios de plano + borrador
kit.py estilo guardar <nombre>             # revisa y la da por buena
kit.py estilo usar <nombre> [--reels]      # la deja activa en brand.json
```

## REGLA DE LA CASA (no se rompe)

De una referencia se toman **principios y ritmo**: cada cuánto entra un recurso, qué tipo de
recursos, si hay subtítulos y cómo de cortos, qué tamaño tienen los textos, si hay 3D, qué
transiciones y qué zooms. **Nunca** se copian sus assets (stickers, fotos, música, efectos), su
tipografía exclusiva, sus colores de marca, su logo ni sus frases. Los fotogramas de la
referencia se quedan en `trabajo/_estilos/` para mirarlos; no entran en la plantilla ni en el
vídeo. La identidad visual sigue siendo la del usuario (`brand.json`).

## Qué miras en la hoja de fotogramas

| Pregunta | Campo |
|---|---|
| ¿Cada cuántos segundos cambia algo en pantalla? (`analisis.json` da el plano medio) | `ritmo.recurso_cada_s`, `ritmo.gancho_cada_s` |
| ¿Qué recursos usa? cifras grandes, frases, logos, fotos de recurso, pantallas completas, zooms | `recursos.preferidos` / `recursos.evitar` |
| ¿Subtítulos siempre, solo en momentos o nunca? ¿Cuántas palabras por línea? ¿Mayúsculas? | `subtitulos.modo` (`siempre`, `momentos`, `nunca`), `palabras_por_linea`, `mayusculas` |
| ¿Textos grandes o discretos? | `textos.escala` (0,6 a 1,6; 1 = de serie) |
| ¿Un color de acento distinto? (uno que case con la marca del usuario, no el del creador) | `acento` (`#RRGGBB` o `null`) |
| ¿Logos u objetos en 3D o planos? | `tres_d.logos`, `tres_d.golpe`, `tres_d.barrido_luz` |
| ¿Textos por detrás de la persona o delante? | `detras` |
| ¿Cómo pasa de un plano a otro? | `transiciones.tipo`: `latigo` (zoom con desenfoque), `desenfoque` (corte con estela lateral), `corte` (seco) |
| ¿Hay zooms? ¿golpes de zoom en cada frase? | `zooms.ken_burns`, `zooms.empuje`, `zooms.golpes`, `zooms.golpe_zoom` (0 a 0,2) |
| ¿Lleva música de fondo? | `musica.cama`, `musica.nivel_db` (unos -18 a -24 dB bajo la voz) |

Recursos válidos: palabra, tachado, logos, golpe3d, contador, fases, terminal, barrido, capitulo,
subtitulo, rotulo, broll, pantalla, zoom, cine, luz, lista.

## El `.md` de la plantilla

6 a 10 viñetas en llano, como `estilos/youtube-editorial.md`: ritmo, recursos, subtítulos,
textos, 3D, transiciones, zooms, música y, al final, «Tomado de la referencia: …» (principios) y
«No copiado: …» (lo que se ha dejado fuera a propósito).

## Cómo la usan las demás fases

- `plan borrador` la enseña y `plan tabla` avisa de huecos más largos que el ritmo y de
  recursos que la plantilla evita. Tú planificas siguiendo su ritmo y sus preferidos.
- `animar` aplica subtítulos, tamaño de textos, acento, 3D y «por detrás».
- `componer` aplica zooms, golpes de zoom, transiciones y música.
- Orden de prioridad: `--plantilla` en la orden > la del plan > `brand.json` (`"plantilla"`; en
  reels, `"plantilla_reels"`) > `youtube-editorial`.

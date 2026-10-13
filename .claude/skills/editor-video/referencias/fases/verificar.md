> Las órdenes `kit.py …` se lanzan así, desde la carpeta del proyecto: `py "<carpeta de la skill>/motor/herramientas/kit.py" …` (ver SKILL.md). Donde pone `brand.json` y `marca/` son los de la marca en uso, compartidos por todos sus proyectos: `kit.py proyecto` dice dónde están.

# Verificar (el bucle que evita entregar fallos)

**Idioma:** responde siempre en español de España, también en los resúmenes y cuando algo falle (aunque el error salga en inglés).

```
kit.py verificar <video> [--formato ...] [--nombre reel1]
```

Automático: duración correcta, que hay audio, que no hay tramos en negro y que ningún texto de la
capa tapa ojos o boca (lo mide `componer` fotograma a fotograma y aquí sale como problema).
Capturas en `trabajo/<video>/capturas/<formato>/`: una por pieza (el logo dos veces: en grande y
en su sitio; cada énfasis ya asentado; cada transición en el látigo), tres de subtítulos
repartidas y la del final, más `hoja.jpg` con todas juntas.

## Lo que miras tú (con Read, de verdad)

Primero `hoja.jpg`; luego, cada captura de pieza que te deje duda.

- [ ] **Se lee**: el texto contrasta con el fondo sin necesitar caja.
- [ ] **Por detrás de verdad**: en cada énfasis la persona queda DELANTE de las letras, con el
      borde limpio (sin halo ni trozos de fondo pegados al pelo) y el énfasis se sigue leyendo.
- [ ] **Sin cajas**: en el estilo «detrás» no aparece ninguna tarjeta ni panel.
- [ ] **No tapa la cara**: ni ojos ni boca. En vertical, lo que no es énfasis va bajo la barbilla.
- [ ] **No se sale**: nada cortado por los bordes; en vertical, nada en los 250 px de abajo
      (ahí van los botones de Instagram y TikTok).
- [ ] **Dice lo que se dice**: el destacado coincide con la frase de ese momento.
- [ ] **Sin choques**: dos piezas no se pisan; el rótulo y un destacado no comparten lado.
- [ ] **Marca correcta**: colores, nombre, @ y logo como en `brand.json`.
- [ ] **Subtítulos** sin palabras mal escritas; si hay alguna, a `correcciones`.

## Si algo falla

Corrige la causa, no el síntoma: posición, duración o texto en `plan.json`; una palabra en
`correcciones` (y relanza desde transcribir); el encuadre vertical en `"encuadre_vertical"`.
Después: animar, componer y verificar **solo del formato afectado**. Dos vueltas como máximo.
Al entregar, di qué has corregido en la verificación: le da confianza al usuario.

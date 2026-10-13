> Las órdenes `kit.py …` se lanzan así, desde la carpeta del proyecto: `py "<carpeta de la skill>/motor/herramientas/kit.py" …` (ver SKILL.md). Donde pone `brand.json` y `marca/` son los de la marca en uso, compartidos por todos sus proyectos: `kit.py proyecto` dice dónde están.

# /editor-video estilo $ARGUMENTS

> **Idioma:** responde siempre en español de España, también en el resumen final y cuando algo falle.

El usuario ha visto una edición que le gusta (en YouTube, Instagram, TikTok…) y te pasa el
vídeo descargado, un recorte o unas capturas. Tú aprendes **cómo está editada** y lo guardas como
plantilla en `estilos/<nombre>.json` + `estilos/<nombre>.md`. Sigue `fases/estilo.md`.

Sin argumentos: enseña las plantillas que hay (`kit.py estilo lista`) y
pregunta qué referencia quiere pasarte. Si arrastra archivos al chat, usa sus rutas.

## 1 · Analizar

```
kit.py estilo analizar <vídeo o capturas o carpeta> --nombre <nombre>
```

Si no da nombre, propón uno corto (`reels-cifras`, `entrevista-sobria`…). Con vídeo, el script
mide los cambios de plano (ritmo real) y saca fotogramas; con capturas, las prepara. Todo queda en
`trabajo/_estilos/<nombre>/` (hoja.jpg, fotogramas y analisis.json) y deja un borrador en
`estilos/<nombre>.json`.

## 2 · Mirar de verdad

Abre con Read `trabajo/_estilos/<nombre>/hoja.jpg` y los fotogramas que te dejen duda. Lee
`analisis.json`. Decide, con lo que ves, cada campo de la plantilla (`fases/estilo.md` explica
cada uno): ritmo, recursos que prefiere, subtítulos (sí/no/cuántas palabras), tamaño de textos,
acento, 3D, frases por detrás, transiciones y zooms.

**Regla de la casa:** tomas PRINCIPIOS y RITMO. Nunca copias sus assets, su tipografía exclusiva,
sus colores de marca, su logo, sus stickers ni sus textos. El acento, si lo cambias, es un color
que encaje con la marca del usuario, no el del otro creador. La identidad sigue siendo la suya.

## 3 · Guardar

Rellena `estilos/<nombre>.json`, escribe `estilos/<nombre>.md` (la plantilla contada en llano,
6-10 viñetas, con lo que has visto y por qué) y lanza:

```
kit.py estilo guardar <nombre>
```

## 4 · Contarlo

En cinco líneas: qué has aprendido de la referencia, qué NO has copiado y cómo usarla:
«Para usarla siempre: `kit.py estilo usar <nombre>` (o `--reels` para los reels). Solo en un
vídeo: `/editor-video editar mi-video ambos --plantilla <nombre>`». Pregunta si la deja activa.

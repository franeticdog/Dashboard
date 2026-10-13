// Convierte una fuente .woff2/.ttf (de Google Fonts, licencia OFL) al formato JSON que usa
// Three.js para el texto en 3D. Solo guarda las letras que hacen falta.
//   node herramientas/fuente3d.mjs <fuente.woff2> <salida.json> "<texto>"
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
// fontkit está en los node_modules del entorno del kit (KIT_ENTORNO); sin él, junto a este archivo
const require = createRequire(process.env.KIT_ENTORNO
  ? path.join(process.env.KIT_ENTORNO, "package.json") : import.meta.url);
const fontkit = require("fontkit");
const [, , origen, destino, texto = ""] = process.argv;
const font = fontkit.openSync(origen);
const chars = [...new Set([...texto, " ", ..."0123456789.,-·"])];
const r = (v) => Math.round(v);
const glyphs = {};
for (const ch of chars) {
  const run = font.layout(ch);
  const g = run.glyphs[0];
  if (!g) continue;
  const o = [];
  for (const c of g.path.commands) {
    const a = c.args;
    if (c.command === "moveTo") o.push("m", r(a[0]), r(a[1]));
    else if (c.command === "lineTo") o.push("l", r(a[0]), r(a[1]));
    else if (c.command === "quadraticCurveTo") o.push("q", r(a[2]), r(a[3]), r(a[0]), r(a[1]));
    else if (c.command === "bezierCurveTo") o.push("b", r(a[4]), r(a[5]), r(a[0]), r(a[1]), r(a[2]), r(a[3]));
  }
  const bb = g.bbox;
  glyphs[ch] = { ha: r(run.positions[0].xAdvance), x_min: r(bb.minX), x_max: r(bb.maxX), o: o.join(" ") };
}
const json = {
  glyphs, familyName: font.familyName, resolution: font.unitsPerEm,
  ascender: font.ascent, descender: font.descent,
  boundingBox: { yMin: font.bbox.minY, yMax: font.bbox.maxY, xMin: font.bbox.minX, xMax: font.bbox.maxX },
  underlineThickness: font.underlineThickness || 50, underlinePosition: font.underlinePosition || -100,
};
fs.writeFileSync(destino, JSON.stringify(json));
console.log(`fuente 3D: ${Object.keys(glyphs).length} letras de ${font.familyName}`);

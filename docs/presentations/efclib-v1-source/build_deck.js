// EFCLib v1 engineering briefing deck (docs/presentations/EFCLib_v1_Engineering_Briefing.pptx).
// Run: node build_deck.js  (needs pptxgenjs). Speaker notes come from notes.json, slide images from img/ and docs/previews/.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
// applyTheme writes THEME colors into the deck (pptx skill helper); pass its path in APPLY_THEME, or the deck keeps Office colors
const applyTheme = process.env.APPLY_THEME ? require(process.env.APPLY_THEME).applyTheme : async () => {};

const S = __dirname;
const REPO = path.resolve(__dirname, "../../..");
const OUT = process.argv[2] || path.join(S, "..", "EFCLib_v1_Engineering_Briefing.pptx");
const IMG = (n) => path.join(S, "img", n + ".png");
const PREV = (n) => path.join(REPO, "docs/previews/templates", n + ".png");
const AI = (n) => path.join(REPO, "steward/previews/renders/AnalogIndicator", n + ".png");

let NOTES = {};
try { NOTES = JSON.parse(fs.readFileSync(path.join(S, "notes.json"), "utf8")); } catch (e) { }

function pngSize(f) { const b = fs.readFileSync(f); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; }

const THEME = {
  name: "EFC ISA-101",
  headFontFace: "Arial",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F1F1F", lt1: "FFFFFF", dk2: "3A3A3A", lt2: "E6E6E6",
    accent1: "1F4E99", accent2: "F08000", accent3: "C00000", accent4: "00A3E0", accent5: "FFD200", accent6: "9E9E9E",
    hlink: "1F4E99", folHlink: "4D4D4D",
  },
};
// raw hex for literal ISA palette swatches (these are data, not theme)
const P = {
  screen: "D9D9D9", header: "C4C4C4", panel: "E6E6E6", card: "F0F0F0", border: "A6A6A6", borderDark: "7F7F7F",
  text: "1F1F1F", muted: "4D4D4D", running: "FFFFFF", stopped: "9E9E9E", transition: "C4C4C4", fault: "3A3A3A",
  editable: "1F4E99", simFill: "D7EEEB", simText: "00695C", bad: "B000B0", pBadge: "F08000", iBadge: "C00000",
  crit: "D50000", high: "FF7A00", med: "FFD200", low: "00A3E0", diag: "6E6E6E", ideal: "9DB4D0",
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.title = "EFCLib v1: Styles, Symbols, Templates and Dynamic Windows";
pres.author = "Adam Zinman";
pres.company = "EFC";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "EFC_TITLE",
  background: { color: P.fault },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.3, w: 11.7, h: 1.7, fontSize: 44, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.2, w: 11.7, h: 1.2, fontSize: 20, color: C.background2, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "EFC_CONTENT",
  background: { color: "FFFFFF" },
  margin: [0.5, 0.6, 0.5, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.62, w: 12.1, h: 0.75, fontSize: 32, bold: true, color: C.text1, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: "EFCLib v1  |  Styles, symbols and dynamic windows", options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: "9E9E9E", align: "right" },
});

// ---------------------------------------------------------------- helpers
const T = (s, txt, o) => s.addText(txt, Object.assign({ isTextBox: true, margin: 0, fontSize: 14, color: C.text1, valign: "top" }, o));

// the motif: an HMI-style bordered status chip
function chip(s, x, y, text, o = {}) {
  const h = o.h || 0.32;
  const w = o.w || Math.max(0.6, 0.12 * text.length + 0.3);
  s.addText(text, {
    isTextBox: true, x, y, w, h, margin: 0, align: "center", valign: "middle",
    fontFace: "Arial", fontSize: o.size || 11, bold: true, charSpacing: 1,
    color: o.color || P.text, fill: { color: o.fill || "FFFFFF" },
    line: { color: o.line || P.text, width: o.lw || 1, dashType: o.dash || "solid" },
    objectName: o.name || "chip " + text,
  });
  return w;
}
function sectionTag(s, text) { chip(s, 0.6, 0.18, text, { fill: P.fault, color: "FFFFFF", line: P.fault, size: 10, h: 0.3, name: "section tag" }); }
function card(s, x, y, w, h, o = {}) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: o.fill || P.card }, line: { color: o.line || "D0D0D0", width: 0.75 }, objectName: o.name || "card" });
}
function bullets(s, items, o) {
  const runs = items.map((it, i) => {
    const t = typeof it === "string" ? [{ text: it }] : it;
    return t.map((r, j) => {
      const o = j === 0 ? { bullet: { indent: 14 }, paraSpaceAfter: 6 } : {};
      if (j === t.length - 1 && i < items.length - 1) o.breakLine = true;
      return { text: r.text, options: Object.assign(o, r.o || {}) };
    });
  }).flat();
  s.addText(runs, Object.assign({ isTextBox: true, margin: 0, fontSize: 14, color: C.text1, valign: "top" }, o));
}
function img(s, file, x, y, o = {}) {
  const d = pngSize(file);
  let w = o.w, h = o.h;
  if (w && !h) h = w * d.h / d.w;
  else if (h && !w) w = h * d.w / d.h;
  else if (w && h) { const r = Math.min(w / d.w, h / d.h); const ww = d.w * r, hh = d.h * r; x += (w - ww) / 2; if (!o.top) y += (h - hh) / 2; w = ww; h = hh; }
  s.addImage({ path: file, x, y, w, h, altText: o.alt || path.basename(file), objectName: "img " + path.basename(file) });
  return { x, y, w, h };
}
function swatch(s, x, y, color, label, hex, o = {}) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w: o.sw || 0.5, h: o.sh || 0.5, fill: { color }, line: { color: o.border || P.borderDark, width: o.bw || 0.75 }, objectName: "swatch " + label });
  T(s, [{ text: label, options: { bold: true, breakLine: true } }, { text: "#" + hex, options: { color: P.muted, fontSize: 11 } }], { x: x + (o.sw || 0.5) + 0.12, y: y - 0.02, w: o.lw || 1.9, h: 0.55, fontSize: 13 });
}
function table(s, rows, o) {
  const head = rows[0].map(t => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: P.fault }, fontSize: o.fs || 12 } }));
  const body = rows.slice(1).map((r, i) => r.map((t, j) => ({ text: t, options: { fontSize: o.fs || 12, color: P.text, bold: j === 0 && o.boldFirst !== false, fill: { color: i % 2 ? "FFFFFF" : P.card } } })));
  s.addTable([head, ...body], Object.assign({ border: { type: "solid", pt: 0.5, color: "D0D0D0" }, margin: [3, 6, 3, 6], valign: "middle" }, o.opts));
}
function slide(title, tag) {
  const s = pres.addSlide({ masterName: "EFC_CONTENT", sectionTitle: CUR });
  s.addText(title, { placeholder: "title" });
  if (tag) sectionTag(s, tag);
  return s;
}
let CUR = "", N = 0;
function notes(s) { N++; s.addNotes(NOTES[String(N)] || "Speaker notes pending."); }
function section(t) { pres.addSection({ title: t }); CUR = t; }

// ================================================================ 1 Title
section("Introduction");
{
  const s = pres.addSlide({ masterName: "EFC_TITLE", sectionTitle: CUR });
  s.addText("EFCLib v1: Styles, Symbols, Templates and Dynamic Windows", { placeholder: "title" });
  s.addText("What changed, why we chose it, and how it behaves on the plant floor", { placeholder: "body" });
  let x = 0.8;
  for (const [t, f, c, l] of [["RUNNING", "FFFFFF", P.text, P.text], ["STOPPED", P.stopped, P.text, P.stopped], ["STARTING", P.transition, P.text, P.transition], ["FAULT", P.fault, "FFFFFF", P.crit]]) {
    x += chip(s, x, 1.55, t, { fill: f, color: c, line: l, lw: t === "FAULT" ? 2 : 1, h: 0.4, size: 13 }) + 0.15;
  }
  chip(s, x, 1.55, "P", { fill: P.pBadge, line: P.pBadge, w: 0.4, h: 0.4, size: 13 });
  chip(s, x + 0.55, 1.55, "I", { fill: P.iBadge, line: P.iBadge, color: "FFFFFF", w: 0.4, h: 0.4, size: 13 });
  T(s, "Ignition 8.1 Perspective  |  Modicon M580  |  EFC_Library project + PCLib T_ types", { x: 0.8, y: 6.5, w: 11, h: 0.4, fontSize: 14, color: P.stopped });
  notes(s);
}

// ================================================================ 2 At a glance
{
  const s = slide("EFCLib v1 at a glance", "OVERVIEW");
  const stats = [["1", "Perspective project", "EFC_Library replaces 7 separate projects"], ["64", "views", "templates, faceplates, windows and parts"],
  ["314", "style classes", "EFC_Styles: the only source of look"], ["28", "PLC T_ types", "PCLib v1.00 DDTs = Ignition UDTs"],
  ["10", "dynamic windows", "one per device family, 400 x 860"], ["214", "P&ID SVGs", "static symbols, same palette"]];
  stats.forEach(([n, l, d], i) => {
    const x = 0.6 + (i % 3) * 4.1, y = 1.65 + Math.floor(i / 3) * 2.45;
    card(s, x, y, 3.8, 2.15, { name: "stat " + l });
    T(s, n, { x: x + 0.3, y: y + 0.2, w: 3.2, h: 0.95, fontSize: 54, bold: true, fontFace: "Arial", color: C.accent1 });
    T(s, l, { x: x + 0.3, y: y + 1.17, w: 3.2, h: 0.35, fontSize: 18, bold: true });
    T(s, d, { x: x + 0.3, y: y + 1.55, w: 3.3, h: 0.45, fontSize: 13, color: P.muted });
  });
  T(s, "Every device template binds an EFCLib v1 T_ type through one tagPath, and a click opens that type's dynamic window.", { x: 0.6, y: 6.55, w: 12.1, h: 0.35, fontSize: 14, italic: true, color: P.muted });
  notes(s);
}

// ================================================================ 3 Standards
{
  const s = slide("Standards behind every decision", "REFERENCES");
  table(s, [
    ["Standard", "What it governs", "Where you see it in EFCLib v1"],
    ["ANSI/ISA-101.01", "HMI design: gray background, color only for abnormal", "Palette, state fills, no decorative color, flashing rules"],
    ["ISA-18.2 / IEC 62682", "Alarm priorities and the alarm state model", "4 priority colors, unacked blink, PV alarm letters, ACK"],
    ["ISA-5.1 / ISA-5.5", "Tag naming and graphic symbols", "Cfg_Tag (FT-101), HH/H/L/LL, P&ID symbol shapes"],
    ["NFPA 79", "Industrial machinery indicator colors", "Orange P (permissive) and red I (interlock) badges"],
    ["ANSI Z535 / OSHA 1910.144", "Safety colors", "Purple reserved; simulated moved to teal"],
    ["ISA-88 / IEC 61512", "Modes, states, ownership", "T_Mode AUTO / MAN (+ MAINT, OOS site extensions)"],
    ["NAMUR NE107 / NE43", "Device diagnostics, 4-20 mA failure levels", "NE107 chip in windows, T_AI bad-signal limits"],
    ["IEC 61511 / ISA-84", "Bypass management", "Reason, time limit, indication, audit; no SIS bypass"],
    ["IEC 61131-3 / VDI 2658 MTP", "PLC data types, modular plant objects", "Elementary types; each T_ type maps to an MTP object"],
  ], { fs: 13, opts: { x: 0.6, y: 1.55, w: 12.1, colW: [2.9, 4.3, 4.9], rowH: 0.47 } });
  notes(s);
}

// ================================================================ 4 Philosophy
{
  const s = slide("Gray is normal, color means abnormal", "PHILOSOPHY");
  const cols = [
    ["1", "Normal is grayscale", "Running is white, stopped is gray. No red/green run states, no colored process lines."],
    ["2", "Color only for abnormal", "Saturated color is reserved for alarms and blocking conditions, always backed by text or shape."],
    ["3", "Flashing only for unacked", "Only an active, unacknowledged alarm blinks. Everything else is steady."],
  ];
  cols.forEach(([n, h, d], i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.6, 3.8, 4.9, { name: "rule " + n });
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 1.9, w: 0.6, h: 0.6, fill: { color: P.fault }, line: { color: P.fault }, objectName: "rule number " + n });
    T(s, n, { x: x + 0.3, y: 1.9, w: 0.6, h: 0.6, align: "center", valign: "middle", fontSize: 22, bold: true, color: "FFFFFF" });
    T(s, h, { x: x + 0.3, y: 2.7, w: 3.3, h: 0.45, fontSize: 20, bold: true });
    T(s, d, { x: x + 0.3, y: 3.2, w: 3.25, h: 1.3, fontSize: 15, color: P.muted });
  });
  // visual examples
  let x = 0.9; for (const [t, f, l] of [["RUNNING", "FFFFFF", P.text], ["STOPPED", P.stopped, P.stopped]]) { x += chip(s, x, 4.9, t, { fill: f, line: l, h: 0.38 }) + 0.15; }
  s.addShape(pres.shapes.RECTANGLE, { x: 0.9, y: 5.5, w: 3.2, h: 0.5, fill: { color: P.screen }, line: { color: P.screen }, objectName: "screen sample" });
  T(s, "screen #D9D9D9", { x: 1.0, y: 5.5, w: 3, h: 0.5, valign: "middle", fontSize: 12, color: P.muted });
  x = 5.0; for (const [t, f, c] of [["HH", P.crit, "FFFFFF"], ["H", P.high, P.text], ["L", P.med, P.text], ["P", P.pBadge, P.text], ["I", P.iBadge, "FFFFFF"]]) { x += chip(s, x, 4.9, t, { fill: f, line: f, color: c, w: 0.5, h: 0.38 }) + 0.12; }
  T(s, "every color sits next to a letter or word", { x: 5.0, y: 5.5, w: 3.2, h: 0.5, fontSize: 12, color: P.muted, valign: "middle" });
  chip(s, 9.1, 4.9, "HI  ACTIVE, UNACKED", { fill: P.high, line: P.high, h: 0.38, w: 2.6 });
  chip(s, 9.1, 5.5, "HI  CLEARED, UNACKED", { fill: "FFD1A6", line: "FFD1A6", color: P.muted, h: 0.38, w: 2.6 });
  T(s, "blinks  /  steady and faded", { x: 9.1, y: 5.98, w: 3.2, h: 0.35, fontSize: 12, color: P.muted });
  notes(s);
}

// ================================================================ 5 Palette
section("Styles");
{
  const s = slide("Palette: structure and equipment states", "STYLES");
  T(s, "Structure", { x: 0.6, y: 1.55, w: 3.5, h: 0.4, fontSize: 18, bold: true });
  [["Screen", P.screen], ["Header", P.header], ["Panel", P.panel], ["Card", P.card], ["Border", P.border]].forEach(([l, c], i) => swatch(s, 0.6, 2.1 + i * 0.75, c, l, c));
  T(s, "Equipment states", { x: 4.4, y: 1.55, w: 3.5, h: 0.4, fontSize: 18, bold: true });
  [["Running / open", P.running], ["Stopped / closed", P.stopped], ["Transition", P.transition], ["Fault", P.fault]].forEach(([l, c], i) => swatch(s, 4.4, 2.1 + i * 0.75, c, l, c, { border: l === "Fault" ? P.crit : P.borderDark, bw: l === "Fault" ? 3 : 0.75, lw: 2.2 }));
  T(s, "Fault adds a 3 px red border and FAULT text", { x: 4.4, y: 5.2, w: 3.6, h: 0.6, fontSize: 12, italic: true, color: P.muted });
  T(s, "Meaningful accents", { x: 8.3, y: 1.55, w: 4, h: 0.4, fontSize: 18, bold: true });
  [["Editable / command", P.editable], ["Simulated (fill)", P.simFill], ["Simulated (text)", P.simText], ["Bad quality", P.bad], ["Manual M marker", P.med]].forEach(([l, c], i) => swatch(s, 8.3, 2.1 + i * 0.75, c, l, c, { lw: 2.6 }));
  T(s, "Transition gray #C4C4C4 is darker than the #D9D9D9 screen on purpose, so a travelling valve never disappears into the background.", { x: 0.6, y: 6.05, w: 12.1, h: 0.6, fontSize: 14, color: P.muted });
  notes(s);
}

// ================================================================ 6 Alarm & badges
{
  const s = slide("Alarm priorities and P / I badges", "STYLES");
  const pr = [["CRITICAL", "1", P.crit, "FFFFFF"], ["HIGH", "2", P.high, P.text], ["MEDIUM", "3", P.med, P.text], ["LOW", "4", P.low, P.text], ["DIAGNOSTIC", "-", P.diag, "FFFFFF"]];
  pr.forEach(([n, p, c, t], i) => {
    const y = 1.6 + i * 0.78;
    chip(s, 0.6, y, n, { fill: c, line: c, color: t, w: 2.0, h: 0.55, size: 13 });
    T(s, [{ text: "Priority " + p, options: { bold: true, breakLine: true } }, { text: "#" + c, options: { color: P.muted, fontSize: 12 } }], { x: 2.8, y: y + 0.0, w: 1.8, h: 0.6, fontSize: 14 });
  });
  T(s, "The only saturated colors on a screen (ISA-18.2 order).", { x: 0.6, y: 5.6, w: 4.4, h: 0.6, fontSize: 13, italic: true, color: P.muted });
  // badges
  card(s, 5.2, 1.6, 3.4, 4.5, { name: "badges card" });
  T(s, "Blocking badges (NFPA 79)", { x: 5.45, y: 1.8, w: 3, h: 0.4, fontSize: 16, bold: true });
  chip(s, 5.5, 2.45, "P", { fill: P.pBadge, line: P.pBadge, w: 0.6, h: 0.6, size: 20 });
  T(s, [{ text: "Permissive missing", options: { bold: true, breakLine: true } }, { text: "Orange #F08000, black text. Left of the symbol.", options: { color: P.muted } }], { x: 6.3, y: 2.4, w: 2.2, h: 1.1, fontSize: 13 });
  chip(s, 5.5, 3.85, "I", { fill: P.iBadge, line: P.iBadge, color: "FFFFFF", w: 0.6, h: 0.6, size: 20 });
  T(s, [{ text: "Interlock active", options: { bold: true, breakLine: true } }, { text: "Red #C00000, white text. Right of the symbol.", options: { color: P.muted } }], { x: 6.3, y: 3.8, w: 2.2, h: 1.1, fontSize: 13 });
  T(s, "Never placed on the process line.", { x: 5.45, y: 5.25, w: 3, h: 0.5, fontSize: 13, italic: true, color: P.muted });
  // deviations
  card(s, 8.9, 1.6, 3.8, 4.5, { name: "deviations card", fill: "FFFFFF", line: P.border });
  T(s, "Documented deviations", { x: 9.15, y: 1.8, w: 3.4, h: 0.4, fontSize: 16, bold: true });
  bullets(s, ["Manual M is yellow, same as Medium; it sits on a dark split chip so it never reads as an alarm",
    "Fault border uses Critical red, always with FAULT text and dark fill",
    "Editable blue #1F4E99 vs Low alarm #00A3E0: different hue and lightness; no other blues allowed"], { x: 9.15, y: 2.3, w: 3.35, h: 3.6, fontSize: 13 });
  notes(s);
}

// ================================================================ 7 Style classes
{
  const s = slide("Style classes: one library, no inline styles", "STYLES");
  card(s, 0.6, 1.6, 6.0, 2.3, { fill: P.fault, line: P.fault, name: "code card" });
  T(s, [
    { text: "props.style.classes =", options: { color: P.stopped, breakLine: true } },
    { text: "  \"Text/Value Text/Mod/Right\"", options: { color: "FFFFFF", breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "// bind the class to the state", options: { color: P.stopped, breakLine: true } },
    { text: "if({[.]Fault}, \"State/Fault\",", options: { color: "FFFFFF", breakLine: true } },
    { text: "  if({[.]Run}, \"State/Running\", \"State/Stopped\"))", options: { color: "FFFFFF" } },
  ], { x: 0.85, y: 1.8, w: 5.6, h: 2.0, fontFace: "Courier New", fontSize: 13 });
  bullets(s, ["Look comes from EFC_Styles classes only; generators move any static inline style into a class (decision 28)",
    "Change a color once in the generator and every view follows",
    "Folders: Text/, Container/, Button/, State/, Mode/, Indicator/, Alarm/, Util/"], { x: 0.6, y: 4.2, w: 6.0, h: 2.4, fontSize: 15 });
  // type scale
  T(s, "Type scale (px at 1080p, sized in vh)", { x: 7.1, y: 1.6, w: 5.6, h: 0.4, fontSize: 16, bold: true });
  const ts = [["XXS", 10, "Micro"], ["XS", 11, "Status, Units"], ["S", 12, "TagName, Label"], ["M", 14, "Body, Value"], ["L", 16, "Subheader"], ["XL", 20, "Header"], ["XXL", 24, "Title"], ["XXXL", 32, "ValueHero"]];
  ts.forEach(([k, px, u], i) => {
    const y = 2.1 + i * 0.5;
    T(s, k, { x: 7.1, y, w: 0.8, h: 0.45, fontSize: 12, bold: true, color: P.muted, valign: "middle" });
    T(s, "Aa", { x: 7.9, y, w: 1.0, h: 0.45, fontSize: Math.round(px * 0.9), valign: "middle" });
    T(s, px + " px  |  " + u, { x: 9.0, y, w: 3.6, h: 0.45, fontSize: 13, color: P.muted, valign: "middle" });
  });
  T(s, "1080p = 1x, 1440p = 1.33x, 2160p = 2x", { x: 7.1, y: 6.2, w: 5.6, h: 0.35, fontSize: 13, italic: true, color: P.muted });
  notes(s);
}

// ================================================================ 8 Anatomy of template
section("Symbols and device templates");
{
  const s = slide("Anatomy of a device template", "TEMPLATES");
  card(s, 0.6, 1.6, 6.2, 4.9, { fill: P.screen, line: P.screen, name: "template stage" });
  img(s, IMG("xv102"), 0.9, 1.8, { w: 5.6, h: 4.5, alt: "XV-102 solenoid valve template: tag above, P badge, closed status chip and manual command button" });
  const items = [["Tag name above", "From the type's tag; description shows as tooltip"], ["Status chip below", "Centered on the symbol centerline: OPEN, CLOSED, RUNNING, FAULT, NN %"],
  ["P left, I right", "Beside the actuator on valves, above the ports on pumps"], ["Command button", "Blank square, bottom left, only visible in Manual"],
  ["Alarm outline", "3 px in the highest active priority color"], ["Parameters", "tagPath (+ useButton, tType, dockId, dblCmd); everything else comes from the type"]];
  items.forEach(([h, d], i) => {
    const y = 1.6 + i * 0.82;
    s.addShape(pres.shapes.OVAL, { x: 7.2, y: y + 0.05, w: 0.42, h: 0.42, fill: { color: P.fault }, line: { color: P.fault }, objectName: "callout " + (i + 1) });
    T(s, String(i + 1), { x: 7.2, y: y + 0.05, w: 0.42, h: 0.42, align: "center", valign: "middle", fontSize: 14, bold: true, color: "FFFFFF" });
    T(s, [{ text: h, options: { bold: true, breakLine: true } }, { text: d, options: { color: P.muted, fontSize: 13 } }], { x: 7.8, y, w: 4.9, h: 0.78, fontSize: 15 });
  });
  notes(s);
}

// ================================================================ 9 State logic
{
  const s = slide("Equipment state logic", "TEMPLATES");
  const rows = [
    ["State", "Fill", "Discrete valve (ZSO / ZSC)", "Motor (Run vs Cmd)"],
    ["CLOSED / STOPPED", "", "ZSC made, ZSO not", "Run off, Cmd off"],
    ["OPEN / RUNNING", "", "ZSO made, ZSC not", "Run on, Cmd on"],
    ["OPENING / STARTING ...", "", "Neither switch made (travel)", "Run and Cmd disagree"],
    ["FAULT", "", "Both switches made, or fault bit", "Fault bit set"],
  ];
  table(s, rows, { fs: 14, opts: { x: 0.6, y: 1.6, w: 12.1, colW: [3.0, 1.2, 4.1, 3.8], rowH: 0.62 } });
  [[P.stopped, P.borderDark, 0.75], [P.running, P.borderDark, 0.75], [P.transition, P.borderDark, 0.75], [P.fault, P.crit, 3]].forEach(([c, l, w], i) => {
    s.addShape(pres.shapes.RECTANGLE, { x: 3.95, y: 2.33 + i * 0.62, w: 0.5, h: 0.4, fill: { color: c }, line: { color: l, width: w }, objectName: "state fill " + i });
  });
  card(s, 0.6, 5.05, 5.85, 1.5, { name: "feedback card" });
  T(s, [{ text: "No feedback?", options: { bold: true, breakLine: true } }, { text: "With feedback disabled the symbol follows the command, so it never shows a false travel or fault.", options: { color: P.muted } }], { x: 0.85, y: 5.2, w: 5.4, h: 1.25, fontSize: 14 });
  card(s, 6.85, 5.05, 5.85, 1.5, { name: "transition card" });
  T(s, [{ text: "Transition is a solid light gray", options: { bold: true, breakLine: true } }, { text: "The dashed travel outline was tried and removed: it read as noise and fought the alarm outline.", options: { color: P.muted } }], { x: 7.1, y: 5.2, w: 5.4, h: 1.25, fontSize: 14 });
  notes(s);
}

// ================================================================ 10 Valves
{
  const s = slide("Valves: head shows command, body shows feedback", "TEMPLATES");
  const v = [["Valves/Valve_OnOff_Pneumatic", "On/off pneumatic"], ["Valves/Valve_Solenoid", "Solenoid"], ["Valves/Valve_MOV", "Motor-operated"], ["Valves/Valve_Control", "Control valve"]];
  v.forEach(([f, l], i) => {
    const x = 0.6 + i * 3.05;
    card(s, x, 1.6, 2.8, 2.6, { fill: P.screen, line: P.screen, name: "valve " + l });
    img(s, PREV(f), x + 0.2, 1.7, { w: 2.4, h: 2.0, alt: l + " valve template" });
    T(s, l, { x, y: 3.75, w: 2.8, h: 0.35, align: "center", fontSize: 14, bold: true });
  });
  card(s, 0.6, 4.5, 5.9, 2.1, { name: "discrete valve card" });
  T(s, "Discrete valves (T_DValve)", { x: 0.85, y: 4.65, w: 5.4, h: 0.4, fontSize: 16, bold: true });
  bullets(s, ["Actuator head color = commanded state", "Body color = limit-switch feedback", "No ball circle in the body; stem runs to body center"], { x: 0.85, y: 5.1, w: 5.4, h: 1.4, fontSize: 14 });
  card(s, 6.8, 4.5, 5.9, 2.1, { name: "control valve card" });
  T(s, "Control valves (T_CValve)", { x: 7.05, y: 4.65, w: 5.4, h: 0.4, fontSize: 16, bold: true });
  bullets(s, ["Position bar left of the valve: fill = actual position", "Blue pointer = commanded output; overhangs so it shows at 0 % and 100 %", "Status chip shows NN %; no on-symbol button"], { x: 7.05, y: 5.1, w: 5.4, h: 1.4, fontSize: 14 });
  notes(s);
}

// ================================================================ 11 Rotating & heat
{
  const s = slide("Running equipment and heat transfer", "TEMPLATES");
  const r = ["Motor", "Pump_Centrifugal", "Pump_Vacuum", "Pump_PD_Rotary", "Pump_Diaphragm", "Pump_Reciprocating", "Compressor_Centrifugal", "Compressor_Diaphragm", "Blower", "Agitator"].map(n => ["Rotating/" + n, n.replace(/_/g, " ")]);
  r.push(["HeatTransfer/HX_AirCooled", "HX AirCooled"], ["HeatTransfer/Heater_Electric", "Heater Electric"]);
  r.forEach(([f, l], i) => {
    const x = 0.6 + (i % 6) * 1.68, y = 1.55 + Math.floor(i / 6) * 2.05;
    card(s, x, y, 1.55, 1.85, { fill: P.screen, line: P.screen, name: "tile " + l });
    img(s, PREV(f), x + 0.08, y + 0.05, { w: 1.39, h: 1.35, alt: l + " template" });
    T(s, l, { x: x + 0.03, y: y + 1.42, w: 1.5, h: 0.4, align: "center", fontSize: 10, color: P.muted });
  });
  card(s, 10.85, 1.55, 1.85, 3.95, { name: "type card" });
  T(s, [{ text: "Bound type", options: { bold: true, breakLine: true } }, { text: "T_Motor by default", options: { breakLine: true } }, { text: " ", options: { breakLine: true } }, { text: "tType = T_VFD", options: { bold: true, breakLine: true } }, { text: "for agitators and compressors on a drive", options: { color: P.muted, breakLine: true } }, { text: " ", options: { breakLine: true } }, { text: "Heater = T_Heater", options: { bold: true, breakLine: true } }, { text: "contactor, SSR or SCR", options: { color: P.muted } }], { x: 11.0, y: 1.7, w: 1.6, h: 3.7, fontSize: 13 });
  bullets(s, ["Same layout on all of them: tag above, status below, P above the left port, I above the right port",
    "Centrifugal pump and blower drop the I badge to lower right so it clears the top discharge"], { x: 0.6, y: 5.75, w: 12.1, h: 1.0, fontSize: 14 });
  notes(s);
}

// ================================================================ 12 Manual mode
{
  const s = slide("Manual mode and commanding from the symbol", "BEHAVIOUR");
  card(s, 0.6, 1.6, 3.6, 2.9, { fill: P.screen, line: P.screen, name: "useButton true" });
  img(s, IMG("xv102"), 0.75, 1.7, { w: 3.3, h: 2.2 });
  T(s, "useButton = true", { x: 0.6, y: 4.0, w: 3.6, h: 0.4, align: "center", fontSize: 15, bold: true });
  card(s, 4.5, 1.6, 3.6, 2.9, { fill: P.screen, line: P.screen, name: "useButton false" });
  img(s, IMG("xv103"), 4.65, 1.7, { w: 3.3, h: 2.2 });
  T(s, "useButton = false (touch)", { x: 4.5, y: 4.0, w: 3.6, h: 0.4, align: "center", fontSize: 15, bold: true });
  T(s, "Button mode: a blank raised key appears only in Manual. Touch mode: no button; a yellow M joins the status and the symbol itself is the command target.", { x: 0.6, y: 4.7, w: 7.5, h: 1.0, fontSize: 14, color: P.muted });
  card(s, 8.5, 1.6, 4.2, 4.95, { fill: "FFFFFF", line: P.border, name: "rules card" });
  T(s, "Command rules", { x: 8.75, y: 1.75, w: 3.8, h: 0.4, fontSize: 16, bold: true });
  bullets(s, ["Click the symbol: opens its dynamic window",
    "Double-tap: commands T_DValve / T_Motor only",
    "Only when in Manual, available, not interlocked, not blocked by a permissive, not Local, not faulted",
    "Opening or starting is blocked by P or I; from the symbol button, closing or stopping is always allowed",
    "Hand cursor only when a click would act",
    "The PLC still enforces every rule"], { x: 8.75, y: 2.25, w: 3.8, h: 4.2, fontSize: 14 });
  T(s, "Auto shows no marker: only abnormal modes are flagged.", { x: 0.6, y: 5.9, w: 7.5, h: 0.4, fontSize: 14, italic: true });
  notes(s);
}

// ================================================================ 13 Alarm/fault/quality
{
  const s = slide("Alarms, faults and bad data on a symbol", "BEHAVIOUR");
  [["xv104", "Interlock active"], ["p102", "Permissive + interlock"], ["xv105", "Fault (valve)"], ["k202", "Fault (compressor)"]].forEach(([f, l], i) => {
    const x = 0.6 + i * 2.15;
    card(s, x, 1.6, 2.0, 2.3, { fill: P.screen, line: P.screen, name: "example " + l });
    img(s, IMG(f), x + 0.1, 1.7, { w: 1.8, h: 1.75 });
    T(s, l, { x, y: 3.5, w: 2.0, h: 0.35, align: "center", fontSize: 12, bold: true });
  });
  // precedence ladder
  T(s, "Outline precedence", { x: 9.4, y: 1.6, w: 3.3, h: 0.4, fontSize: 16, bold: true });
  [["Fault: red 3 px border", P.crit, "FFFFFF"], ["Highest active alarm priority", P.high, P.text], ["No alarm: normal 1.5 px outline", P.stopped, P.text]].forEach(([t, c, tc], i) => {
    s.addText(t, { isTextBox: true, x: 9.4 + i * 0.2, y: 2.1 + i * 0.62, w: 3.3 - i * 0.2, h: 0.5, margin: 6, fontSize: 12, bold: true, color: tc, fill: { color: c }, valign: "middle", objectName: "ladder " + i });
  });
  T(s, "wins over", { x: 9.4, y: 4.0, w: 3.3, h: 0.3, fontSize: 11, italic: true, color: P.muted });
  bullets(s, [[{ text: "Alarm outline: ", o: { bold: true } }, { text: "the highest active priority on any member of the instance; shelved alarms are ignored" }],
  [{ text: "Fault: ", o: { bold: true } }, { text: "dark fill + red border + FAULT text, so it reads without color" }],
  [{ text: "Missing or bad tag: ", o: { bold: true } }, { text: "every read is wrapped in coalesce() with safe defaults (not interlocked, not manual), and the alarm lookup is quality-guarded so a bad member cannot turn the whole symbol red" }],
  [{ text: "Simulated / bad quality: ", o: { bold: true } }, { text: "flagged in the dynamic window (teal SIM chip, magenta bad-quality state), not by recoloring the symbol" }]], { x: 0.6, y: 4.35, w: 12.1, h: 2.3, fontSize: 14 });
  notes(s);
}

// ================================================================ 14 PV
section("Values, indicators and loops");
{
  const s = slide("Process value cards (T_AI)", "VALUES");
  card(s, 0.6, 1.6, 5.4, 3.2, { fill: P.screen, line: P.screen, name: "pv stage" });
  img(s, PREV("ProcessValues/PV_StatusStrip"), 0.85, 1.85, { w: 2.4 });
  img(s, PREV("ProcessValues/PV_RangeBar"), 3.4, 1.85, { w: 2.4 });
  T(s, "PV_StatusStrip", { x: 0.85, y: 3.15, w: 2.4, h: 0.35, align: "center", fontSize: 13, bold: true });
  T(s, "PV_RangeBar", { x: 3.4, y: 3.15, w: 2.4, h: 0.35, align: "center", fontSize: 13, bold: true });
  T(s, "100 x 50 cards, vh-scaled. Click opens dw_ProcessValue.", { x: 0.85, y: 3.7, w: 5, h: 0.8, fontSize: 13, color: P.muted });
  T(s, "Alarm letters, in fixed order", { x: 6.4, y: 1.6, w: 6.3, h: 0.4, fontSize: 16, bold: true });
  let x = 6.4; for (const [t, c, tc] of [["FLT", P.fault, "FFFFFF"], ["HH", P.crit, "FFFFFF"], ["H", P.high, P.text], ["L", P.high, P.text], ["LL", P.crit, "FFFFFF"], ["OVR", P.med, P.text], ["UNR", P.med, P.text], ["INH", P.diag, "FFFFFF"]]) { x += chip(s, x, 2.1, t, { fill: c, line: c, color: tc, w: 0.68, h: 0.42 }) + 0.08; }
  T(s, "Example priorities shown; each letter takes its configured priority color.", { x: 6.4, y: 2.6, w: 6.3, h: 0.35, fontSize: 11, italic: true, color: P.muted });
  bullets(s, ["At most 2 letters show; the rest collapse into +N with an \"Also: ...\" tooltip", "+N blinks if a hidden letter is unacknowledged",
    "Letter blinks while unacked, goes solid once acked, fades when cleared but unacked", "Hardware fault gets its own High alarm and shows dark gray"], { x: 6.4, y: 3.1, w: 6.3, h: 2.6, fontSize: 14 });
  card(s, 0.6, 5.1, 5.4, 1.45, { name: "why card" });
  T(s, [{ text: "Why letters and not just color?", options: { bold: true, breakLine: true } }, { text: "ISA-101: color must be backed by text. HH vs H is readable by a color-blind operator.", options: { color: P.muted } }], { x: 0.85, y: 5.2, w: 5, h: 1.3, fontSize: 14 });
  notes(s);
}

// ================================================================ 15 Analog indicators
{
  const s = slide("Analog indicators A to D (T_KPI, proposed)", "VALUES");
  card(s, 0.6, 1.6, 8.0, 4.95, { fill: P.screen, line: P.screen, name: "indicator stage" });
  img(s, AI("A_RangeBar"), 0.85, 1.85, { w: 4.0 });
  T(s, "A  Range Bar", { x: 0.85, y: 3.85, w: 4, h: 0.3, fontSize: 13, bold: true });
  img(s, AI("C_CompactRow"), 0.85, 4.35, { w: 4.0 });
  T(s, "C  Compact Row", { x: 0.85, y: 5.3, w: 4, h: 0.3, fontSize: 13, bold: true });
  img(s, AI("B_PointerScale"), 5.2, 1.8, { h: 4.3 });
  T(s, "B", { x: 5.2, y: 6.15, w: 0.4, h: 0.3, fontSize: 13, bold: true });
  img(s, AI("D_MiniColumn"), 7.25, 1.8, { h: 3.4 });
  T(s, "D", { x: 7.25, y: 5.3, w: 0.4, h: 0.3, fontSize: 13, bold: true });
  T(s, "Zones", { x: 9.0, y: 1.6, w: 3.7, h: 0.4, fontSize: 16, bold: true });
  [["LL / HH", "7F7F7F"], ["L / H", "C4C4C4"], ["Normal, off-ideal", "FFFFFF"], ["Ideal range", P.ideal]].forEach(([l, c], i) => swatch(s, 9.0, 2.1 + i * 0.7, c, l, c, { sw: 0.45, sh: 0.45 }));
  bullets(s, ["Pointer takes the alarm's priority color while in alarm", "Ideal blue is muted so it never competes with alarm colors"], { x: 9.0, y: 5.0, w: 3.7, h: 1.5, fontSize: 13 });
  notes(s);
}

// ================================================================ 16 Loops
{
  const s = slide("PID loop cards B1 to B4 (T_PID)", "VALUES");
  card(s, 0.6, 1.6, 7.6, 3.3, { fill: "DCDFE3", line: "DCDFE3", name: "loops stage" });
  img(s, IMG("loops"), 0.75, 1.7, { w: 7.3, h: 3.1 });
  const v = [["B1 Bar", "Vertical PV bar, SP pointer, alarm ticks"], ["B2 Horizontal", "Normal band between AlmLo and AlmHi"], ["B3 Sparkline", "B1 + 1 minute PV/SP trend + deviation chip"], ["B4 Column", "Twin bars: PV and output"]];
  v.forEach(([h, d], i) => {
    const y = 1.6 + i * 0.82;
    chip(s, 8.6, y + 0.05, h.split(" ")[0], { w: 0.6, h: 0.4, fill: P.fault, line: P.fault, color: "FFFFFF" });
    T(s, [{ text: h.split(" ").slice(1).join(" "), options: { bold: true, breakLine: true } }, { text: d, options: { color: P.muted, fontSize: 13 } }], { x: 9.35, y, w: 3.35, h: 0.78, fontSize: 15 });
  });
  bullets(s, ["Setpoint is blue: blue always means \"an operator can change this\"", "The whole card opens dw_Loop; the old LoopConfig popup is retired (decision 15)", "Mode chip, right of the tag: AUTO light gray, MAN dark (abnormal), CAS light blue. Orange diamond and outline = deviation alarm"], { x: 0.6, y: 5.15, w: 12.1, h: 1.5, fontSize: 14 });
  notes(s);
}

// ================================================================ 17 Shell
section("Dynamic windows");
{
  const s = slide("The screen shell and the dynamic-window region", "DYNAMIC WINDOWS");
  const r = img(s, IMG("Screen_Layout_normal"), 0.6, 1.6, { w: 8.9, alt: "1920x1080 screen shell with a P-101 dynamic window open on the right" });
  s.addShape(pres.shapes.RECTANGLE, { x: r.x, y: r.y, w: r.w, h: r.h, fill: { type: "none" }, line: { color: P.border, width: 0.75 }, objectName: "shell frame" });
  T(s, "Regions at 1920 x 1080", { x: 9.85, y: 1.6, w: 2.9, h: 0.4, fontSize: 16, bold: true });
  [["Header", "1920 x 80"], ["Left menu", "120 x 860"], ["Process area", "1400 x 860"], ["Dynamic window", "400 x 860"], ["Alarm bar", "1920 x 140"]].forEach(([a, b], i) => {
    T(s, [{ text: a, options: { bold: true, breakLine: true } }, { text: b + " px", options: { color: P.muted } }], { x: 9.85, y: 2.1 + i * 0.68, w: 2.9, h: 0.62, fontSize: 14 });
  });
  T(s, "Everything doubles at 3840 x 2160. The window is 37.04 vh x 79.63 vh.", { x: 9.85, y: 5.6, w: 2.9, h: 1.0, fontSize: 13, italic: true, color: P.muted });
  notes(s);
}

// ================================================================ 18 Open/close flow
{
  const s = slide("How a dynamic window opens and closes", "DYNAMIC WINDOWS");
  const steps = [["Click symbol", "operator clicks a template"], ["efc.ui.openDynamic", "picks the window from tType or dockId"], ["Session value", "efcDw[pageId] = path + tagPath"], ["Docks/Region", "embedded view swaps to the window"]];
  steps.forEach(([h, d], i) => {
    const x = 0.6 + i * 3.1;
    card(s, x, 1.65, 2.6, 1.35, { fill: i === 3 ? P.fault : P.card, line: i === 3 ? P.fault : "D0D0D0", name: "step " + h });
    T(s, [{ text: h, options: { bold: true, breakLine: true } }, { text: d, options: { fontSize: 12, color: i === 3 ? "E0E0E0" : P.muted } }], { x: x + 0.15, y: 1.78, w: 2.3, h: 1.15, fontSize: 15, color: i === 3 ? "FFFFFF" : P.text });
    if (i < 3) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.65, y: 2.17, w: 0.4, h: 0.32, fill: { color: P.borderDark }, line: { color: P.borderDark }, objectName: "arrow " + i });
  });
  T(s, "Close (X) calls efc.ui.closeDynamic and returns the region to the screen's defaultDock view. One window per page; a second click replaces it.", { x: 0.6, y: 3.2, w: 12.1, h: 0.6, fontSize: 14, color: P.muted });
  table(s, [["Type", "Window"], ["T_DValve", "dw_ValveDiscrete"], ["T_CValve", "dw_ValveAnalog"], ["T_Motor", "dw_Rotating"], ["T_VFD", "dw_VFD"], ["T_Heater", "dw_Heater"]], { fs: 12, opts: { x: 0.6, y: 4.0, w: 4.0, colW: [1.6, 2.4], rowH: 0.42 } });
  table(s, [["Type", "Window"], ["T_HeatEx", "dw_HeatTransfer"], ["T_AI, T_KPI", "dw_ProcessValue"], ["T_PID", "dw_Loop"], ["T_Station", "dw_Station"], ["x80 card DDT", "dw_IOCard"]], { fs: 12, opts: { x: 4.85, y: 4.0, w: 4.0, colW: [1.6, 2.4], rowH: 0.42 } });
  card(s, 9.15, 4.0, 3.55, 2.55, { name: "why embedded" });
  T(s, [{ text: "Why an embedded view, not Perspective docks?", options: { bold: true, breakLine: true } }, { text: "The region is a fixed part of the shell, so the process area never shifts or gets covered, and it matches the Controls Standard screen appendix (decision 24).", options: { color: P.muted, fontSize: 13 } }], { x: 9.35, y: 4.12, w: 3.2, h: 2.35, fontSize: 14 });
  notes(s);
}

// ================================================================ 19 Anatomy of window
{
  const s = slide("Anatomy of a dynamic window: dw_ValveDiscrete", "DYNAMIC WINDOWS");
  const r = img(s, IMG("Docks_ValveDiscrete"), 0.6, 1.5, { h: 5.35, alt: "dw_ValveDiscrete dynamic window for XV-101" });
  const items = [["Header", "Tag, description, close"], ["State banner + chips", "CLOSED plus SIM, LOCAL, INTLK, NOT PERM chips"], ["Mode row", "AUTO / MAN / MAINT / OOS; current mode highlighted"],
  ["Command row", "OPEN / CLOSE / RESET, with the enable reason underneath"], ["Permissives (P)", "Each named condition, OK / NOT OK, BYPASS"],
  ["Interlocks (I)", "First-out, LATCHED, BYPASSED + time left + who and why"], ["Alarms", "Priority dot, state, ACK"], ["History", "30 min trend with expand"], ["Maintenance / Configuration", "Collapsible, role-gated sections"]];
  items.forEach(([h, d], i) => {
    const y = 1.5 + i * 0.54;
    s.addShape(pres.shapes.OVAL, { x: 4.0, y: y + 0.06, w: 0.36, h: 0.36, fill: { color: P.fault }, line: { color: P.fault }, objectName: "callout " + (i + 1) });
    T(s, String(i + 1), { x: 4.0, y: y + 0.06, w: 0.36, h: 0.36, align: "center", valign: "middle", fontSize: 12, bold: true, color: "FFFFFF" });
    T(s, [{ text: h + "  ", options: { bold: true } }, { text: d, options: { color: P.muted } }], { x: 4.5, y, w: 8.2, h: 0.5, fontSize: 14, valign: "middle" });
  });
  T(s, "Approved rev 2 mockup (decision 8). Dashed purple = role-gated; the built view differs in detail (see notes).", { x: 4.5, y: 6.5, w: 8.2, h: 0.35, fontSize: 12, italic: true, color: P.muted });
  notes(s);
}

// ================================================================ 20 Roles
{
  const s = slide("Role gating: hidden, not greyed out", "DYNAMIC WINDOWS");
  const roles = [["0", "Guest", "View only"], ["1", "Operator", "Commands, mode AUTO/MAN, setpoints, ACK"], ["2", "Maintenance", "MAINT / OOS, JOG, simulate, maint reset"], ["3", "Supervisor", "Bypass with reason, alarm shelving"], ["4", "Engineer", "Alarm limits, configuration, tuning"], ["5", "Admin", "Everything"]];
  roles.forEach(([n, r, d], i) => {
    const x = 0.6 + i * 1.3, h = 0.9 + i * 0.6, y = 5.4 - h;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 1.2, h, fill: { color: i >= 3 ? P.fault : (i === 0 ? P.stopped : P.borderDark) }, line: { color: "FFFFFF", width: 1 }, objectName: "step " + r });
    T(s, n, { x, y: y + 0.1, w: 1.2, h: 0.45, align: "center", fontSize: 22, bold: true, color: "FFFFFF" });
    T(s, r, { x: x - 0.05, y: 5.5, w: 1.3, h: 0.35, align: "center", fontSize: 12, bold: true });
    T(s, d, { x: x - 0.02, y: 5.85, w: 1.24, h: 0.85, align: "center", fontSize: 10, color: P.muted });
  });
  card(s, 8.7, 1.6, 4.0, 5.0, { fill: "FFFFFF", line: P.border, name: "role rules" });
  T(s, "How it works", { x: 8.95, y: 1.75, w: 3.6, h: 0.4, fontSize: 16, bold: true });
  bullets(s, ["Level = highest role the user holds, read from session roles at login",
    "Controls above your level are hidden, so operators only see what they can use",
    "Every write goes through efc.ui.cmd, which re-checks the level on the gateway",
    "MAINT and above: audited writes (old -> new, user, time)"], { x: 8.95, y: 2.25, w: 3.6, h: 4.2, fontSize: 14 });
  notes(s);
}

// ================================================================ 21 Bypass
{
  const s = slide("Permissives, interlocks and bypass", "DYNAMIC WINDOWS");
  bullets(s, [[{ text: "Named groups in the PLC type: ", o: { bold: true } }, { text: "Perm and Intlk (T_Intlk) inside T_DValve, T_Motor, T_VFD, T_Heater; Prot in equipment modules. ANDed with the existing Inp_PermOK / Inp_IntlkOK" }],
  [{ text: "Up to 16 conditions per group, ", o: { bold: true } }, { text: "each with first-out, latched state and its own bypass time left (Sts_BypLeft)" }],
  [{ text: "BYPASS (Supervisor+): ", o: { bold: true } }, { text: "reason required, written to the audit log, times out at Cfg_BypassMax. Duration presets and the Inp_BypassPerm check are approved (decision 10) but not built yet" }],
  [{ text: "Each bypassed condition shows its own time left", o: { bold: true } }]], { x: 0.6, y: 1.6, w: 6.6, h: 3.6, fontSize: 15 });
  img(s, IMG("Docks_Parts_BypassConfirm"), 7.6, 1.6, { w: 5.1, alt: "BypassConfirm dialog with duration presets and required reason" });
  T(s, "Approved BypassConfirm mockup (decision 10)", { x: 7.6, y: 4.8, w: 5.1, h: 0.3, fontSize: 11, italic: true, color: P.muted });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 5.3, w: 12.1, h: 1.3, fill: { color: P.fault }, line: { color: P.fault }, objectName: "safety callout" });
  chip(s, 0.85, 5.55, "SAFETY", { fill: P.crit, line: P.crit, color: "FFFFFF", w: 1.2, h: 0.4 });
  T(s, "Safety signals (SIS, E-stops, safety interlocks) can never be bypassed or forced in software. Only process conditions engineering marked Cfg_Bypassable under MOC can be bypassed from the HMI (decision 29).", { x: 2.3, y: 5.42, w: 10.2, h: 1.05, fontSize: 15, color: "FFFFFF", valign: "middle" });
  notes(s);
}

// ================================================================ 22 Family
{
  const s = slide("One window per device family, same layout everywhere", "DYNAMIC WINDOWS");
  const w = [["Docks_ValveAnalog", "dw_ValveAnalog", "Presets 0/25/50/75/100 %"], ["Docks_VFD", "dw_VFD", "Speed, FWD/REV, load"], ["Docks_Loop", "dw_Loop", "PV / SP / CV, MAN AUTO CAS"], ["Docks_ProcessValue", "dw_ProcessValue", "Range, alarm limits, simulate"], ["Docks_IOCard", "dw_IOCard", "x80 channels and health"]];
  w.forEach(([f, n, d], i) => {
    const x = 0.6 + i * 2.45;
    img(s, IMG(f), x, 1.5, { w: 2.3, h: 4.45, top: true, alt: n + " dynamic window" });
    T(s, [{ text: n, options: { bold: true, breakLine: true } }, { text: d, options: { color: P.muted, fontSize: 12 } }], { x, y: 6.0, w: 2.3, h: 0.7, fontSize: 13 });
  });
  notes(s);
}

// ================================================================ 23 History / trend
{
  const s = slide("History and the expanded trend", "DYNAMIC WINDOWS");
  img(s, IMG("Docks_Parts_TrendExpanded"), 0.6, 1.5, { h: 5.35, alt: "Expanded trend inside the dynamic window" });
  bullets(s, ["Every window carries a short history trend, 30 min by default",
    "The expand button fills the window below its header, about 400 x 760 at 1080p",
    "Range buttons 5 m / 30 m / 1 h / 8 h / 24 h and collapse; pause / live and a last-events list are approved but not built yet",
    "The other sections hide while expanded and come back on collapse",
    "The region never widens, so the process area is never covered (decision 26)",
    "Expand state is local to the window, not a session value"], { x: 4.2, y: 1.6, w: 8.5, h: 3.0, fontSize: 16 });
  card(s, 4.2, 4.75, 8.5, 0.95, { name: "history prereq" });
  T(s, "Requires tag history on the pens the window trends (PV, SP, CV, position, current).", { x: 4.45, y: 4.85, w: 8.1, h: 0.75, fontSize: 14, valign: "middle" });
  notes(s);
}

// ================================================================ 24 Types
section("Wrap-up");
{
  const s = slide("PLC types behind the graphics (EFCLib v1 / PCLib)", "TYPES");
  table(s, [["Prefix", "Meaning", "HMI may write?"], ["Sts_", "Status from the PLC", "No, never"], ["Inp_", "Field / logic inputs", "No"], ["Cmd_", "Operator commands (one-shot)", "Yes"], ["Cfg_", "Configuration (limits, tag, bypassable)", "Yes, Engineer+"], ["Sim_", "Simulation", "Yes, Maintenance+"], ["Prm_", "Recipe parameters (batch)", "No (batch server)"], ["Prog_", "Commands from the owning phase / EM", "No (PLC owner)"]], { fs: 13, opts: { x: 0.6, y: 1.6, w: 6.6, colW: [1.4, 3.2, 2.0], rowH: 0.5 } });
  card(s, 7.6, 1.6, 5.1, 5.0, { name: "types card" });
  T(s, "What the types give the HMI", { x: 7.85, y: 1.75, w: 4.7, h: 0.4, fontSize: 16, bold: true });
  bullets(s, ["Modes and states as integers, so graphics need no color logic in the PLC",
    "NE107 status on every field device",
    "Alarms from T_Alarm: priority 1-4; ACK in Ignition writes Cmd_Ack, so the PLC stays authoritative",
    "ISA-88 ownership through T_Mode (acquire / release)",
    "I/O faceplates bind the native Modicon x80 DDTs; no extra type"], { x: 7.85, y: 2.25, w: 4.7, h: 4.2, fontSize: 14 });
  T(s, "ISA-101: the HMI never writes PLC status.", { x: 0.6, y: 5.95, w: 6.6, h: 0.4, fontSize: 14, italic: true, color: P.muted });
  notes(s);
}

// ================================================================ 25 Cheat sheet
{
  const s = slide("What happens when...?", "BEHAVIOUR");
  table(s, [
    ["Situation", "What the operator sees"],
    ["Comms lost / tag quality bad", "Safe defaults via coalesce(); bad quality in magenta; outline does not go red from bad data"],
    ["UDT member missing (older PLC)", "Treated as \"not missing / not active\"; template keeps working"],
    ["No alarms configured on the instance", "Alarm lookup returns no alarm instead of an error"],
    ["Interlock trips while running in Manual", "Red I badge; start/open blocked; stop/close allowed from the symbol button"],
    ["Both limit switches made", "FAULT: dark fill, red border, FAULT text"],
    ["Feedback disabled", "Symbol follows the command; no false travel"],
    ["User below the needed role", "Control not shown at all; gateway re-checks any write"],
    ["Bypass time runs out", "Condition returns to normal enforcement; time left was shown per condition"],
    ["Screen at 1440p or 4K", "All sizes in vh: 1.33x or 2x, same layout"],
  ], { fs: 13, opts: { x: 0.6, y: 1.55, w: 12.1, colW: [4.0, 8.1], rowH: 0.5 } });
  notes(s);
}

// ================================================================ 26 Open items
{
  const s = pres.addSlide({ masterName: "EFC_TITLE", sectionTitle: CUR });
  s.addText("Open items and next steps", { placeholder: "title" });
  s.addText("Decisions and build gaps before release", { placeholder: "body" });
  const cols = [["Symbols", ["2 px alarm outline on small valves?", "OPENING / CLOSING width", "Center status chip, or M + status?"]],
  ["Values", ["PV faded level 0.25 -> 0.4", "PV diagnostic gray -> #6E6E6E", "HW_Fault alarm in the UDT", "Finalize T_KPI + FB_KPI"]],
  ["Windows", ["Bypass presets + Inp_BypassPerm", "One close/stop rule when interlocked", "Pause / live + last events"]],
  ["Rollout", ["Gateway-test PV and loop cards", "Controls Standard edits in one batch", "Re-point HMI projects to EFC_Library"]]];
  cols.forEach(([h, items], i) => {
    const x = 0.8 + i * 3.0;
    chip(s, x, 4.95, h.toUpperCase(), { fill: P.fault, line: "FFFFFF", color: "FFFFFF", w: 1.6 });
    T(s, items.map((t, j) => ({ text: t, options: { bullet: { indent: 12 }, breakLine: j < items.length - 1, paraSpaceAfter: 4 } })), { x, y: 5.4, w: 2.8, h: 1.6, fontSize: 13, color: "E6E6E6" });
  });
  notes(s);
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT, "slides:", N);
})();

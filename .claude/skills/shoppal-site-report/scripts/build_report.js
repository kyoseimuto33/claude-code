// Build the site status report (.pptx) from a JSON config.
// Usage: node build_report.js <config.json> <out.pptx>
// See ../templates/example.json for every field. Asset values are computed here (never typed by hand).
const fs = require('fs');
const path = require('path');
let pptxgen;
try { pptxgen = require('pptxgenjs'); } catch (_) { pptxgen = require(path.join(require('child_process').execSync('npm root -g').toString().trim(), 'pptxgenjs')); }

const cfg = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const OUT = process.argv[3] || 'report.pptx';
const C = { navy: '1E2A38', blue: '2F6FB5', green: '3E9C79', orange: 'C9772B', gray: '6B7684', light: 'F5F7FA', line: 'E1E6EC', pale: 'CFE0F2', white: 'FFFFFF', mute: 'A8B2BF', tint: 'EEF4FB' };
const SITE_COLORS = [C.blue, C.green, C.orange];
const F = 'Noto Sans JP';
const ICON_DIR = path.join(__dirname, '..', 'assets', 'icons');
const IC = Object.fromEntries(fs.readdirSync(ICON_DIR).map(f => [path.basename(f, '.png'), 'image/png;base64,' + fs.readFileSync(path.join(ICON_DIR, f)).toString('base64')]));
const yen = n => Math.round(n).toLocaleString('en-US');
const sites = cfg.sites.map((s, i) => Object.assign({ color: SITE_COLORS[i % SITE_COLORS.length] }, s));
const margin = cfg.asset?.marginRate ?? 0.4;
const mult = cfg.asset?.multiple ?? 36;

const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = `事業レポート（${sites.map(s => s.name).join('・')}）`;
const FOOT = sites.map(s => `${s.name}（${s.url}）`).join('／ ');
let page = 0;

const txt = (s, text, o) => s.addText(text, Object.assign({ fontFace: F, color: C.navy, margin: 0, isTextBox: true, valign: 'top' }, o));
const card = (s, x, y, w, h, fill) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill || C.light }, line: { color: C.line, width: 0.75 } });
const bullets = items => items.map((t, i) => ({ text: t, options: { bullet: { indent: 12 }, breakLine: i < items.length - 1 } }));
function footer(s) {
  txt(s, FOOT, { x: 0.5, y: 5.28, w: 7.5, h: 0.2, fontSize: 7.5, color: C.mute });
  txt(s, String(page), { x: 9.0, y: 5.28, w: 0.5, h: 0.2, fontSize: 7.5, color: C.mute, align: 'right' });
}
function base(title, sub) {
  const s = pres.addSlide(); page++;
  s.background = { color: C.white };
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 0.38, w: 0.07, h: 0.38, fill: { color: C.blue }, line: { color: C.blue, width: 0 } });
  txt(s, title, { x: 0.7, y: 0.32, w: 8.8, h: 0.5, fontSize: 22, bold: true });
  if (sub) txt(s, sub, { x: 0.7, y: 0.84, w: 8.8, h: 0.3, fontSize: 11, color: C.gray });
  footer(s);
  return s;
}
function iconCircle(s, img, x, y, d) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: C.white }, line: { color: C.pale, width: 1 } });
  const p = d * 0.22;
  s.addImage({ data: IC[img] || IC.check, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
}
function takeaway(s, text, y = 4.55) {
  if (!text) return;
  card(s, 0.5, y, 9, 0.5, C.tint);
  s.addImage({ data: IC.check, x: 0.66, y: y + 0.12, w: 0.26, h: 0.26 });
  txt(s, text, { x: 1.05, y, w: 8.3, h: 0.5, fontSize: 11, valign: 'middle' });
}

// 1. Cover: white, large type, sites listed plainly.
{
  const s = pres.addSlide(); page++;
  s.background = { color: C.white };
  txt(s, cfg.cover?.title || '事業レポート', { x: 0.8, y: 0.75, w: 8.4, h: 0.95, fontSize: 48, bold: true });
  txt(s, cfg.cover?.subtitle || '現状のご報告', { x: 0.8, y: 1.7, w: 8.4, h: 0.55, fontSize: 24, color: C.gray });
  s.addShape(pres.shapes.LINE, { x: 0.8, y: 2.5, w: 8.4, h: 0, line: { color: C.line, width: 1 } });
  const step = sites.length > 2 ? 0.6 : 0.78;
  sites.forEach((st, i) => {
    const y = 2.7 + i * step;
    txt(s, st.name, { x: 0.8, y, w: 4.0, h: 0.6, fontSize: sites.length > 2 ? 24 : 30, bold: true, color: st.color, valign: 'middle' });
    txt(s, st.genre, { x: 4.8, y: y + 0.02, w: 4.4, h: 0.3, fontSize: 14, valign: 'middle' });
    txt(s, st.url, { x: 4.8, y: y + 0.32, w: 4.4, h: 0.26, fontSize: 12, color: C.gray, valign: 'middle' });
  });
  txt(s, cfg.date, { x: 0.8, y: 4.6, w: 4, h: 0.4, fontSize: 18 });
  txt(s, `※本資料に記載の数値は${cfg.asOf}時点のものです。`, { x: 0.8, y: 5.1, w: 8.4, h: 0.25, fontSize: 9, color: C.mute });
}

// 2. Decision timing (optional).
if (cfg.decision) {
  const s = pres.addSlide(); page++;
  s.background = { color: C.white };
  txt(s, cfg.decision.lead, { x: 0.5, y: 1.3, w: 9, h: 0.5, fontSize: 18, color: C.gray, align: 'center' });
  txt(s, '▼', { x: 0.5, y: 1.95, w: 9, h: 0.4, fontSize: 16, color: C.pale, align: 'center' });
  txt(s, cfg.decision.headline, { x: 0.5, y: 2.5, w: 9, h: 0.7, fontSize: 28, bold: true, align: 'center' });
  txt(s, cfg.decision.note || `本資料は、ご判断に向けた${sites.length > 1 ? sites.length + 'サイト' : 'サイト'}の現状をまとめたものです。`, { x: 0.5, y: 3.45, w: 9, h: 0.35, fontSize: 12, color: C.gray, align: 'center' });
  footer(s);
}

// 3. Summary (2–3 sites side by side).
if (sites.length > 1) {
  const s = base(`${sites.length}サイトの現況`, `${cfg.asOf}時点`);
  const w = sites.length === 2 ? 4.35 : 2.87, gap = sites.length === 2 ? 0.3 : 0.2;
  sites.forEach((st, k) => {
    const x = 0.5 + k * (w + gap);
    card(s, x, 1.3, w, 3.1);
    txt(s, st.name, { x: x + 0.3, y: 1.45, w: w - 0.6, h: 0.4, fontSize: 16, bold: true, color: st.color });
    if (sites.length === 2) txt(s, st.url, { x: x + w - 2.15, y: 1.52, w: 1.95, h: 0.3, fontSize: 9, color: C.gray, align: 'right' });
    st.summary.rows.forEach((r, i) => {
      const y = 1.95 + i * 0.44;
      s.addShape(pres.shapes.LINE, { x: x + 0.3, y: y - 0.04, w: w - 0.6, h: 0, line: { color: C.line, width: 0.75 } });
      txt(s, r[0], { x: x + 0.3, y, w: w * 0.5, h: 0.4, fontSize: 10.5, color: C.gray, valign: 'middle' });
      txt(s, r[1], { x: x + w * 0.4, y, w: w * 0.6 - 0.3, h: 0.4, fontSize: sites.length === 2 ? 15 : 13, bold: true, align: 'right', valign: 'middle' });
    });
    txt(s, st.summary.message, { x: x + 0.3, y: 3.75, w: w - 0.6, h: 0.55, fontSize: 10, valign: 'middle' });
  });
  takeaway(s, cfg.summaryTakeaway);
}

// 4. Per site: sales & access, then search ranks & actions.
for (const st of sites) {
  {
    const s = base(`${st.name}　売上とアクセス`, st.sales.subtitle);
    card(s, 0.5, 1.3, 5.6, 3.1, C.white);
    const max = Math.max(...st.sales.values) * 1.18 || 1;
    s.addChart(pres.charts.BAR, [{ name: '売上', labels: st.sales.labels, values: st.sales.values }], {
      x: 0.6, y: 1.38, w: 5.4, h: 2.95, barDir: 'col', barGapWidthPct: 55, chartColors: [st.color],
      showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '¥#,##0', dataLabelFontSize: 8.5, dataLabelColor: C.navy, dataLabelFontFace: F,
      catAxisLabelColor: C.gray, catAxisLabelFontSize: 10, catAxisLabelFontFace: F, valAxisHidden: true, valAxisMaxVal: max,
      valGridLine: { style: 'none' }, catGridLine: { style: 'none' }, catAxisLineShow: true, catAxisLineColor: C.line, showLegend: false,
      showTitle: true, title: st.sales.chartTitle || '月別売上', titleFontSize: 11, titleColor: C.navy, titleFontFace: F,
    });
    card(s, 6.35, 1.3, 3.15, 3.1);
    st.sales.stats.slice(0, 3).forEach((t, i) => {
      const y = 1.42 + i * 0.98;
      txt(s, t[0], { x: 6.6, y, w: 2.8, h: 0.25, fontSize: 10, color: C.gray });
      txt(s, t[1], { x: 6.6, y: y + 0.24, w: 2.8, h: 0.45, fontSize: 22, bold: true, color: st.color });
      txt(s, t[2] || '', { x: 6.6, y: y + 0.7, w: 2.8, h: 0.25, fontSize: 9.5 });
    });
    takeaway(s, st.sales.takeaway);
  }
  {
    const s = base(`${st.name}　検索順位と取り組み`, st.detail.subtitle);
    st.detail.cards.slice(0, 3).forEach((c, i) => {
      const x = 0.5 + i * 3.05, w = 2.9, y = 1.3, h = 3.1;
      card(s, x, y, w, h);
      iconCircle(s, c.icon, x + 0.2, y + 0.18, 0.42);
      txt(s, c.title, { x: x + 0.72, y: y + 0.18, w: w - 0.9, h: 0.42, fontSize: 13, bold: true, valign: 'middle' });
      txt(s, c.big, { x: x + 0.25, y: y + 0.78, w: w - 0.4, h: 0.5, fontSize: c.big.length > 12 ? 13 : c.big.length > 10 ? 15 : 17, bold: true, color: st.color });
      s.addShape(pres.shapes.LINE, { x: x + 0.25, y: y + 1.38, w: w - 0.5, h: 0, line: { color: C.line, width: 0.75 } });
      txt(s, bullets(c.items), { x: x + 0.25, y: y + 1.52, w: w - 0.4, h: h - 1.6, fontSize: 10, paraSpaceAfter: 6 });
    });
    takeaway(s, st.detail.takeaway);
  }
}

// 5. Priorities, one column per site.
{
  const s = base('今後の重点施策', '効果の大きい順に取り組みます');
  const n = sites.length, w = n === 1 ? 9 : n === 2 ? 4.35 : 2.87, gap = n === 2 ? 0.3 : 0.2;
  sites.forEach((st, k) => {
    const x = 0.5 + k * (w + gap);
    card(s, x, 1.3, w, 3.1);
    txt(s, st.name, { x: x + 0.3, y: 1.42, w: w - 0.6, h: 0.4, fontSize: 15, bold: true, color: st.color });
    st.priorities.slice(0, 3).forEach((it, i) => {
      const y = 1.95 + i * 0.8;
      s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: y + 0.03, w: 0.36, h: 0.36, fill: { color: st.color } });
      txt(s, String(i + 1), { x: x + 0.3, y: y + 0.03, w: 0.36, h: 0.36, fontSize: 12, bold: true, color: C.white, align: 'center', valign: 'middle' });
      txt(s, it[0], { x: x + 0.8, y, w: w - 1.0, h: 0.3, fontSize: n === 3 ? 11 : 12, bold: true });
      txt(s, it[1], { x: x + 0.8, y: y + 0.3, w: w - 1.0, h: 0.42, fontSize: 9.5, color: C.gray });
    });
  });
  takeaway(s, cfg.prioritiesTakeaway);
}

// 6. Asset value (computed: monthly sales × marginRate × multiple, unless grossProfit is given).
{
  const s = base('資産価値の試算', `月間粗利の${mult}倍を想定売却価格として算出（粗利率は${Math.round(margin * 100)}%で概算）`);
  const hdr = { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 10.5, align: 'center', valign: 'middle' };
  const cell = (t, o) => ({ text: t, options: Object.assign({ fontSize: 10.5, color: C.navy, valign: 'middle', align: 'right' }, o || {}) });
  const rows = [['サイト', '前提', '月間売上', '月間粗利', '想定資産価値'].map(t => ({ text: t, options: hdr }))];
  const totals = {};
  sites.forEach(st => st.asset.forEach((a, i) => {
    const gp = a.grossProfit ?? Math.round(a.sales * margin);
    const val = gp * mult;
    (totals[a.label] = totals[a.label] || []).push(val);
    console.log(`asset ${st.name} | ${a.label} | sales ${a.sales} | gp ${gp} | value ${val}`);
    const r = [cell(a.label, { align: 'left' }), cell(`${yen(a.sales)}円`), cell(`${yen(gp)}円`), cell(`${yen(val)}円`, { bold: true, color: st.color })];
    if (i === 0) r.unshift(cell(st.name, { align: 'left', bold: true, rowspan: st.asset.length }));
    rows.push(r);
  }));
  const rowH = Math.min(0.44, 2.3 / (rows.length - 1));
  s.addTable(rows, { x: 0.5, y: 1.3, w: 9, colW: [1.3, 3.35, 1.35, 1.3, 1.7], rowH: [0.42, ...Array(rows.length - 1).fill(rowH)], fontFace: F, border: { type: 'solid', color: C.line, pt: 0.75 }, fill: { color: C.white }, margin: [0, 0.1, 0, 0.1] });
  txt(s, `算出式：月間売上 × 粗利率${Math.round(margin * 100)}% = 月間粗利　／　月間粗利 × ${mult} = 想定資産価値`, { x: 0.5, y: 1.3 + 0.42 + (rows.length - 1) * rowH + 0.12, w: 9, h: 0.3, fontSize: 9.5, color: C.gray });
  takeaway(s, cfg.assetTakeaway);
}

// 7. Roadmap to the decision (3 steps).
if (cfg.roadmap) {
  const s = base(cfg.roadmap.title || 'ご判断までの進め方', cfg.roadmap.subtitle);
  cfg.roadmap.steps.slice(0, 3).forEach((st, i) => {
    const x = 0.5 + i * 3.1, last = i === cfg.roadmap.steps.length - 1;
    card(s, x, 1.3, 2.8, 2.65);
    txt(s, st.when, { x: x + 0.25, y: 1.45, w: 2.3, h: 0.3, fontSize: 11, bold: true, color: last ? C.green : C.blue });
    txt(s, st.title, { x: x + 0.25, y: 1.8, w: 2.3, h: 0.45, fontSize: 16, bold: true });
    txt(s, bullets(st.items), { x: x + 0.25, y: 2.45, w: 2.4, h: 1.4, fontSize: 11, paraSpaceAfter: 8 });
    if (!last) txt(s, '▶', { x: x + 2.8, y: 2.45, w: 0.3, h: 0.4, fontSize: 14, color: C.pale, align: 'center' });
  });
  takeaway(s, cfg.roadmap.takeaway, 4.2);
}

pres.writeFile({ fileName: OUT }).then(() => console.log('wrote', OUT));

// deck.html → PDF (A4 가로) + 페이지별 미리보기 PNG
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const out = process.argv[2] || 'algocare_quality_compare_GS.pdf';
  const shots = process.argv[3]; // 미리보기 폴더(선택)
  const src = process.argv[4] || 'deck.html';
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: Number(process.env.SCALE || 1) });
  await page.goto('file://' + path.resolve(__dirname, src), { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.body.dataset.fitted === '1');
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: path.resolve(__dirname, out), preferCSSPageSize: true, printBackground: true });
  if (shots) {
    await page.emulateMedia({ media: 'print' });
    await page.setViewportSize({ width: 1123, height: 794 });
    const n = await page.$$eval('.page', p => p.length);
    const els = await page.$$('.page');
    for (let i = 0; i < n; i++) await els[i].screenshot({ path: `${shots}/p${String(i + 1).padStart(2, '0')}.png` });
    // overflow 점검
    const over = await page.$$eval('.page', ps => ps.map((p, i) => {
      const r = p.getBoundingClientRect(); let bad = [];
      p.querySelectorAll('table,.content,.lu-grid,.split').forEach(e => {
        const b = e.getBoundingClientRect(); if (b.bottom > r.bottom - 40) bad.push(e.className + ':' + Math.round(b.bottom - r.top));
      });
      return bad.length ? `p${i + 1} ${bad.join(' ')}` : null;
    }).filter(Boolean));
    console.log('overflow check:', over.length ? over.join('\n') : 'none');
  }
  await browser.close();
})();

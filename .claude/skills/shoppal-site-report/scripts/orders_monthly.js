// Aggregate order count and paid amount per month from a Shoppal site's order list.
// Only the amount and creation date are read; no customer data is stored.
const { chromium } = require('/root/.npm/_npx/9833c18b2d85bc59/node_modules/playwright');
(async () => {
  const site = process.argv[2];
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'],
    proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined });
  const page = await (await browser.newContext()).newPage();
  await page.goto(`https://${site}.flumo-admin-server.com/orders`, { waitUntil: 'networkidle' });
  if (page.url().includes('/login')) {
    await page.fill('#email', process.env.SHOPPAL_ADMIN_USER);
    await page.fill('#password', process.env.SHOPPAL_ADMIN_PASS);
    await Promise.all([page.waitForLoadState('networkidle'), page.locator('button[type=submit], button').first().click()]);
    await page.waitForTimeout(3000);
    await page.goto(`https://${site}.flumo-admin-server.com/orders`, { waitUntil: 'networkidle' });
  }
  await page.waitForTimeout(4000);
  const rows = [];
  for (let p = 0; p < 20; p++) {
    const batch = await page.locator('table tbody tr').evaluateAll(trs => trs.map(tr => {
      const td = [...tr.querySelectorAll('td')].map(t => t.innerText.trim());
      const date = td.find(t => /^\d{1,2}\/\d{1,2}\/\d{4}/.test(t));
      return { amount: td[2], date };
    }));
    rows.push(...batch);
    const next = page.getByText('Next', { exact: true });
    const range = await page.getByText(/^\d+-\d+ \/ \d+$/).first().innerText().catch(() => '');
    const m = range.match(/(\d+)-(\d+) \/ (\d+)/);
    if (!m || +m[2] >= +m[3]) break;
    await next.click(); await page.waitForTimeout(3000);
  }
  const agg = {};
  for (const r of rows) {
    if (!r.date) continue;
    const [mo, , yr] = r.date.split(',')[0].split('/');
    const k = `${yr}-${mo.padStart(2, '0')}`;
    agg[k] = agg[k] || { orders: 0, amount: 0 };
    agg[k].orders++; agg[k].amount += parseInt((r.amount || '0').replace(/[^\d]/g, '')) || 0;
  }
  console.log(site, 'rows', rows.length);
  Object.keys(agg).sort().forEach(k => console.log(k, agg[k].orders, agg[k].amount));
  await browser.close();
})().catch(e => { console.error('ERR', e.message.slice(0, 300)); process.exit(1); });

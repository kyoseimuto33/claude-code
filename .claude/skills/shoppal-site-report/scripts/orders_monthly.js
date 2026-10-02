// Monthly order count and paid amount for one site, from its admin order list.
// Usage: node orders_monthly.js <service_id>   e.g. node orders_monthly.js shouldagg
// Reads only the amount and creation date of each row; customer data is never stored or printed.
const { openAdmin } = require('./pw');

(async () => {
  const site = process.argv[2];
  if (!site) throw new Error('usage: node orders_monthly.js <service_id>');
  const { browser, page } = await openAdmin(`https://${site}.flumo-admin-server.com/orders`);
  const rows = [];
  for (let p = 0; p < 50; p++) {
    rows.push(...await page.locator('table tbody tr').evaluateAll(trs => trs.map(tr => {
      const td = [...tr.querySelectorAll('td')].map(t => t.innerText.trim());
      return { amount: td[2], date: td.find(t => /^\d{1,2}\/\d{1,2}\/\d{4}/.test(t)) };
    })));
    const range = await page.getByText(/^\d+-\d+ \/ \d+$/).first().innerText().catch(() => '');
    const m = range.match(/(\d+)-(\d+) \/ (\d+)/);
    if (!m || +m[2] >= +m[3]) break;
    await page.getByText('Next', { exact: true }).click();
    await page.waitForTimeout(3000);
  }
  const agg = {};
  for (const r of rows) {
    if (!r.date) continue;
    const [mo, , yr] = r.date.split(',')[0].split('/');
    const k = `${yr}-${mo.padStart(2, '0')}`;
    agg[k] = agg[k] || { orders: 0, amount: 0 };
    agg[k].orders++;
    agg[k].amount += parseInt((r.amount || '0').replace(/[^\d]/g, ''), 10) || 0;
  }
  console.log(`# ${site}: ${rows.length} orders (month orders amount_yen)`);
  Object.keys(agg).sort().forEach(k => console.log(k, agg[k].orders, agg[k].amount));
  await browser.close();
})().catch(e => { console.error('ERR', e.message.slice(0, 300)); process.exit(1); });

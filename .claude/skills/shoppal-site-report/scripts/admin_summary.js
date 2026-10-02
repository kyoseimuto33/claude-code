// Site summary from the Shoppal admins: this month's counts (orders, added products/articles)
// from the Fulmo admin, and the dashboard's paid amount and cost for the default period.
// Usage: node admin_summary.js <service_id>
const { openAdmin } = require('./pw');

const grab = (text, label) => {
  const i = text.indexOf(label);
  if (i < 0) return null;
  const m = text.slice(i + label.length).match(/[\d,]+/);
  return m ? m[0] : null;
};

(async () => {
  const site = process.argv[2];
  if (!site) throw new Error('usage: node admin_summary.js <service_id>');
  let { browser, page } = await openAdmin(`https://admin.flumo-admin-server.com/service/${site}`);
  const svc = await page.locator('body').innerText();
  await browser.close();
  const keys = ['商品数', '記事数', '注文数'];
  const month = (svc.match(/(\d+)月の注文数/) || [])[1];
  for (const k of keys) console.log(`${k}: ${grab(svc, '\n' + k + '\n')}`);
  if (month) for (const k of ['追加商品数', '追加記事数', '注文数']) console.log(`${month}月の${k}: ${grab(svc, `${month}月の${k}`)}`);

  ({ browser, page } = await openAdmin(`https://${site}.flumo-admin-server.com/`));
  const dash = await page.locator('body').innerText();
  await browser.close();
  const period = (dash.match(/(\d{4}-\d{2}-\d{2}) から (\d{4}-\d{2}-\d{2}) 間の入金額/) || []).slice(1).join(' 〜 ');
  console.log(`ダッシュボード期間: ${period}`);
  console.log(`入金額: ${grab(dash, '間の入金額')}`);
  console.log(`原価金額: ${grab(dash, 'までの原価金額')}`);
})().catch(e => { console.error('ERR', e.message.slice(0, 300)); process.exit(1); });

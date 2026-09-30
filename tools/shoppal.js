// Log in to the Shoppal admin with SHOPPAL_ADMIN_USER / SHOPPAL_ADMIN_PASS and dump a page.
const { chromium } = require('/root/.npm/_npx/9833c18b2d85bc59/node_modules/playwright');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'],
    proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined });
  const ctxOpts = fs.existsSync('/tmp/shoppal_state.json') ? { storageState: '/tmp/shoppal_state.json' } : {};
  const ctx = await browser.newContext(ctxOpts);
  const page = await ctx.newPage();
  const url = process.argv[2] || 'https://admin.flumo-admin-server.com/';
  await page.goto(url, { waitUntil: 'networkidle' });
  if (page.url().includes('/login')) {
    const inputs = await page.locator('input').evaluateAll(els => els.map(e => ({ type: e.type, name: e.name, id: e.id, ph: e.placeholder })));
    console.error('login form inputs:', JSON.stringify(inputs));
    await page.locator('input[type=email], input[name*=mail i], input[name*=user i], input[type=text]').first().fill(process.env.SHOPPAL_ADMIN_USER);
    await page.locator('input[type=password]').first().fill(process.env.SHOPPAL_ADMIN_PASS);
    await Promise.all([page.waitForLoadState('networkidle'), page.locator('button[type=submit], input[type=submit], button').first().click()]);
    await page.waitForTimeout(2000);
    if (!page.url().includes(new URL(url).pathname) ) await page.goto(url, { waitUntil: 'networkidle' });
    await ctx.storageState({ path: '/tmp/shoppal_state.json' });
  }
  await page.waitForTimeout(parseInt(process.env.WAIT||'4000'));
  console.log('URL:', page.url(), '| title:', await page.title());
  const out = process.argv[3] || '/tmp/shoppal_page.txt';
  fs.writeFileSync(out, await page.locator('body').innerText());
  await page.screenshot({ path: out.replace(/\.txt$/, '.png'), fullPage: true });
  await browser.close();
})().catch(e => { console.error('ERR', e.message); process.exit(1); });

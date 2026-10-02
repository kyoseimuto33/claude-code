// Shared Playwright helpers for the Shoppal admin (https://<site>.flumo-admin-server.com).
// Credentials come from SHOPPAL_ADMIN_USER / SHOPPAL_ADMIN_PASS; nothing is written to disk.
const fs = require('fs');
const path = require('path');
const os = require('os');

function loadPlaywright() {
  try { return require('playwright'); } catch (_) { /* fall through to the npx cache */ }
  const npx = path.join(os.homedir(), '.npm', '_npx');
  if (fs.existsSync(npx)) {
    for (const d of fs.readdirSync(npx)) {
      const p = path.join(npx, d, 'node_modules', 'playwright');
      if (fs.existsSync(p)) return require(p);
    }
  }
  throw new Error('playwright not found: run scripts/setup.sh first');
}

async function openAdmin(url) {
  const { chromium } = loadPlaywright();
  if (!process.env.SHOPPAL_ADMIN_USER || !process.env.SHOPPAL_ADMIN_PASS) {
    throw new Error('SHOPPAL_ADMIN_USER / SHOPPAL_ADMIN_PASS are not set in the environment');
  }
  const browser = await chromium.launch({
    executablePath: fs.existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined,
    args: ['--no-sandbox'],
    proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined,
  });
  const page = await (await browser.newContext()).newPage();
  await page.goto(url, { waitUntil: 'networkidle' });
  if (page.url().includes('/login')) {
    await page.fill('#email', process.env.SHOPPAL_ADMIN_USER);
    await page.fill('#password', process.env.SHOPPAL_ADMIN_PASS);
    await Promise.all([page.waitForLoadState('networkidle'), page.locator('button[type=submit], button').first().click()]);
    await page.waitForTimeout(3000);
    if (page.url() !== url) await page.goto(url, { waitUntil: 'networkidle' });
  }
  await page.waitForTimeout(4000); // dashboards load client-side
  return { browser, page };
}

module.exports = { openAdmin };

/* Run after npm install --no-save playwright; HUGO_BIN may select the Hugo binary. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const { execFileSync } = require('node:child_process');

(async () => {
  const root = path.resolve(__dirname, '..');
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'archie-browser-'));
  const server = http.createServer((req, res) => {
    const relative = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    let file = path.join(temporary, relative);
    if (!file.startsWith(temporary + path.sep)) { res.writeHead(403); return res.end(); }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    if (!fs.existsSync(file)) { res.writeHead(404); return res.end(); }
    const mime = { '.css': 'text/css', '.js': 'text/javascript', '.html': 'text/html', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
    res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
    fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}/demo/`;
  let browser;
  try {
    execFileSync(process.env.HUGO_BIN || 'hugo', ['--source', path.join(root, 'exampleSite'), '--baseURL', base, '--destination', path.join(temporary, 'demo')], { stdio: 'inherit' });
    browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}) });
    for (const width of [320, 390, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 900 } });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
      await page.goto(base, { waitUntil: 'networkidle' });
      assert.equal(await page.locator('.tape-hero').count(), 1);
      assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
      const noOverflow = async () => assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), `Page overflow at ${width}px: ${page.url()}`);
      await noOverflow();
      await page.locator('#intro-title').evaluate(el => { el.textContent = 'Engineering Notes'; });
      await noOverflow();
      await page.locator('#intro-title').evaluate(el => { el.textContent = 'Supercalifragilisticexpialidocious'; });
      await page.locator('.wordmark').evaluate(el => { el.textContent = 'Supercalifragilisticexpialidocious'; });
      await page.locator('.tape-hero p').evaluate(el => { el.textContent = 'A long consumer tagline with a token: ' + 'unbroken'.repeat(25); });
      await noOverflow();
      await page.reload({ waitUntil: 'networkidle' });
      await page.locator('#dark-mode-toggle').click();
      assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
      await page.reload({ waitUntil: 'networkidle' });
      assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
      await page.locator('#dark-mode-toggle').click();
      await page.locator('#dark-mode-toggle').click();
      assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
      await page.goto(base + 'posts/hello/', { waitUntil: 'networkidle' });
      assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
      await noOverflow();
      assert.equal(await page.locator('.toc-disclosure').count(), 1);
      const initiallyOpen = width >= 1200;
      assert.equal(await page.locator('.toc-disclosure').evaluate(el => el.open), initiallyOpen);
      await page.locator('.toc-disclosure summary').click();
      assert.equal(await page.locator('.toc-disclosure').evaluate(el => el.open), !initiallyOpen);
      await page.locator('.toc-disclosure summary').click();
      assert.equal(await page.locator('.toc-disclosure').evaluate(el => el.open), initiallyOpen);
      assert.equal(await page.locator('.table-scroll').getAttribute('tabindex'), '0');
      assert.equal(errors.length, 0, errors.join('\n'));
      const screenshots = path.join(root, '.test-output/screenshots');
      fs.mkdirSync(screenshots, { recursive: true });
      await page.screenshot({ path: path.join(screenshots, `article-${width}.png`), fullPage: true });
      await page.goto(base, { waitUntil: 'networkidle' });
      await page.screenshot({ path: path.join(screenshots, `home-${width}.png`), fullPage: true });
      await context.close();
      console.log(`PASS retro home/article ${width}px, repeated toggle, persistence, TOC, subpath assets, no overflow/errors`);
    }
    const context = await browser.newContext();
    await context.addInitScript(() => { Object.defineProperty(window, 'localStorage', { get() { throw new Error('storage denied'); } }); });
    const page = await context.newPage();
    await page.goto(base, { waitUntil: 'networkidle' });
    await page.locator('#dark-mode-toggle').click();
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
    await context.close();
    console.log('PASS denied localStorage still allows color toggle');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
    fs.rmSync(temporary, { recursive: true, force: true });
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

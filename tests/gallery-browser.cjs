/* Real gallery navigation tests. npm install --no-save playwright; HUGO_BIN optional. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const { execFileSync } = require('node:child_process');

(async () => {
  const root = path.resolve(__dirname, '..');
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'archie-gallery-browser-'));
  const output = path.join(temporary, 'preview');
  const server = http.createServer((req, res) => {
    let file = path.resolve(temporary, '.' + decodeURIComponent(new URL(req.url, 'http://localhost').pathname));
    if (!file.startsWith(temporary + path.sep)) { res.writeHead(403); return res.end(); }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    if (!fs.existsSync(file)) {
      res.statusCode = 404;
      file = path.join(output, '404.html');
    }
    const mime = { '.css': 'text/css', '.js': 'text/javascript', '.html': 'text/html', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.xml': 'application/xml' };
    res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
    fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}/preview/`;
  let browser;
  try {
    execFileSync(process.env.PYTHON || 'python3', ['demo/build.py', '--destination', output, '--base-url', base], { cwd: root, stdio: 'inherit' });
    browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}) });
    for (const width of [320, 390, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 900 } });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('response', response => { if (response.status() >= 400 && !response.url().includes('missing-page')) errors.push(`${response.status()} ${response.url()}`); });
      const screenshots = path.join(root, '.test-output/gallery-screenshots');
      fs.mkdirSync(screenshots, { recursive: true });
      await page.goto(base, { waitUntil: 'networkidle' });
      await page.screenshot({ path: path.join(screenshots, `gallery-index-${width}.png`), fullPage: true });
      await page.locator('a[href$="stock/"]').first().click();
      await page.waitForURL(base + 'stock/');
      const nav = page.locator('nav.skin-gallery');
      await nav.locator('[data-skin-id="retro"]').click();
      await page.waitForURL(base + 'retro/');
      await page.waitForLoadState('networkidle');
      assert.equal(await page.locator('.tape-hero').count(), 1);
      const navFits = async () => assert.ok(await page.locator('nav.skin-gallery').evaluate(el => {
        const bounds = el.getBoundingClientRect();
        return bounds.left >= -1 && bounds.right <= innerWidth + 1 && el.scrollWidth <= el.clientWidth + 1;
      }), `Gallery navigation overflow at ${width}px`);
      await navFits();
      for (const relative of ['posts/hello/', 'tags/notes/']) {
        await page.goto(base + 'retro/' + relative + '?compare=1#keep-the-details', { waitUntil: 'networkidle' });
        const stock = page.locator('nav.skin-gallery [data-skin-id="stock"]');
        await stock.focus();
        await page.keyboard.press('Enter');
        await page.waitForURL(base + 'stock/' + relative + '?compare=1#keep-the-details');
        await page.waitForLoadState('networkidle');
        await navFits();
        assert.equal(await page.locator('nav.skin-gallery [data-skin-id="stock"]').getAttribute('aria-current') !== null, true);
        await page.locator('nav.skin-gallery [data-skin-id="retro"]').click();
        await page.waitForURL(base + 'retro/' + relative + '?compare=1#keep-the-details');
        await page.goBack({ waitUntil: 'networkidle' });
        assert.equal(new URL(page.url()).pathname, '/preview/stock/' + relative);
        await page.goForward({ waitUntil: 'networkidle' });
        assert.equal(new URL(page.url()).pathname, '/preview/retro/' + relative);
      }
      await page.goto(base + 'retro/posts/hello/', { waitUntil: 'networkidle' });
      await page.screenshot({ path: path.join(screenshots, `gallery-retro-${width}.png`), fullPage: true });
      await page.goto(base + 'stock/posts/hello/', { waitUntil: 'networkidle' });
      await page.screenshot({ path: path.join(screenshots, `gallery-stock-${width}.png`), fullPage: true });
      const notFound = await page.goto(base + 'retro/missing-page/', { waitUntil: 'networkidle' });
      assert.equal(notFound.status(), 404);
      await page.locator('a[href$="retro/"]').first().click();
      await page.waitForURL(base + 'retro/');
      assert.deepEqual(errors, []);
      await context.close();
      console.log(`PASS gallery ${width}px: isolated skins, keyboard switching, equivalent deep links, query/hash, history, 404 recovery, assets`);
    }
    const noJS = await browser.newContext({ javaScriptEnabled: false });
    const page = await noJS.newPage();
    await page.goto(base + 'retro/posts/hello/');
    await page.locator('nav.skin-gallery [data-skin-id="stock"]').click();
    await page.waitForURL(base + 'stock/posts/hello/');
    await noJS.close();
    console.log('PASS equivalent-page gallery switching without JavaScript');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
    fs.rmSync(temporary, { recursive: true, force: true });
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

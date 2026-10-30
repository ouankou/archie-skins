/* Build once, smoke-test the same files that Pages will publish. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { execFileSync } = require('node:child_process');

(async () => {
  const root = path.resolve(__dirname, '..');
  const output = path.join(root, '_site');
  const screenshots = path.join(root, 'screenshots');
  const site = new URL(process.env.SITE_URL || 'https://archie.ouankou.com/');
  assert.ok(['https:', 'http:'].includes(site.protocol) && !site.search && !site.hash);
  site.pathname = site.pathname.replace(/\/+$/, '') + '/';
  const base = site.href;
  const skins = JSON.parse(fs.readFileSync(path.join(root, 'demo/skins.json'), 'utf8'));
  execFileSync('python3', ['demo/build.py', '--destination', output, '--base-url', base], { cwd: root, stdio: 'inherit' });
  for (const file of fs.readdirSync(output, { recursive: true })) {
    assert.ok(!file.split(path.sep).some(part => ['.git', '.github', 'go.mod', 'go.sum'].includes(part)), `Source in public output: ${file}`);
    assert.ok(!fs.lstatSync(path.join(output, file)).isSymbolicLink(), `Symlink in public output: ${file}`);
  }
  fs.mkdirSync(screenshots, { recursive: true });
  const server = http.createServer((req, res) => {
    let pathname;
    try { pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname); }
    catch { res.writeHead(400); return res.end(); }
    if (!pathname.startsWith(site.pathname)) { res.writeHead(404); return res.end(); }
    let file = path.resolve(output, pathname.slice(site.pathname.length));
    if (file !== output && !file.startsWith(output + path.sep)) { res.writeHead(403); return res.end(); }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    if (!fs.existsSync(file)) { res.writeHead(404); return res.end(); }
    const mime = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.json': 'application/json' };
    res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
    fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const local = `http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    for (const width of [320, 1440]) {
      const errors = [];
      const context = await browser.newContext({ viewport: { width, height: 900 }, serviceWorkers: 'block' });
      // Production URLs stay untouched; only this local artifact may answer requests.
      await context.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (url.origin !== site.origin) {
          errors.push(`Unexpected external request: ${url.href}`);
          return route.abort('blockedbyclient');
        }
        const response = await route.fetch({ url: local + url.pathname + url.search, maxRedirects: 0 });
        await route.fulfill({ response });
      });
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      page.on('requestfailed', request => errors.push(`Failed request: ${request.url()}`));
      page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
      for (let i = 0; i < skins.length; i++) {
        const id = skins[i].id, next = skins[(i + 1) % skins.length].id;
        const article = 'posts/hello/?compare=1#keep-the-details';
        await page.goto(base + id + '/' + article, { waitUntil: 'networkidle' });
        assert.match(await page.locator('body').innerText(), /A notebook for the curious/);
        const nav = page.locator('nav.skin-gallery');
        assert.equal(await nav.locator('[data-skin-id]').count(), skins.length);
        assert.ok(await nav.evaluate(el => el.scrollWidth <= el.clientWidth + 1), `${id}: navigation overflow`);
        if (id === 'stock') {
          assert.equal(await page.locator('link[href*="/css/main."]').count(), 1);
          assert.equal(await page.locator('link[href*="/archie-skins/retro/"]').count(), 0);
        } else if (id === 'retro') {
          assert.equal(await page.locator('.site-header').count(), 1);
          const before = await page.locator('html').getAttribute('data-theme');
          await page.locator('#dark-mode-toggle').click();
          assert.notEqual(await page.locator('html').getAttribute('data-theme'), before);
          await page.locator('#dark-mode-toggle').click();
          assert.equal(await page.locator('html').getAttribute('data-theme'), before);
        } else {
          assert.equal(await page.locator(`link[href*="/archie-skins/${id}/tokens."]`).count(), 1);
          assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${id}: page overflow at ${width}px`);
        }
        await page.screenshot({ path: path.join(screenshots, `${id}-${width}.png`), fullPage: true });
        await nav.locator(`[data-skin-id="${next}"]`).focus();
        await page.keyboard.press('Enter');
        await page.waitForURL(base + next + '/' + article);
        await page.waitForLoadState('networkidle');
        assert.notEqual(await page.locator(`[data-skin-id="${next}"]`).getAttribute('aria-current'), null);
      }
      assert.deepEqual(errors, []);
      await context.close();
      console.log(`PASS: ${skins.length} skins at ${width}px, navigation, assets, overflow and retro toggle`);
    }
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
    // _site is deliberately retained: upload these tested bytes, without rebuilding.
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

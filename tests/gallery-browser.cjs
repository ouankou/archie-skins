/* Manifest-driven visual/navigation smoke tests. npm install --no-save playwright. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const { execFileSync } = require('node:child_process');

(async () => {
  const root = path.resolve(__dirname, '..');
  const skins = JSON.parse(fs.readFileSync(path.join(root, 'demo/skins.json'), 'utf8'));
  const ids = skins.map(skin => skin.id);
  assert.ok(ids.includes('stock') && ids.includes('retro'), 'Preserve both original gallery variants');
  assert.equal(new Set(ids).size, ids.length);
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'archie-gallery-browser-'));
  const output = path.join(temporary, 'preview');
  const screenshots = path.join(root, '.test-output/gallery-screenshots');
  fs.mkdirSync(screenshots, { recursive: true });
  const materialSamples = [];
  const server = http.createServer((req, res) => {
    let file = path.resolve(temporary, '.' + decodeURIComponent(new URL(req.url, 'http://localhost').pathname));
    if (!file.startsWith(temporary + path.sep)) { res.writeHead(403); return res.end(); }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    if (!fs.existsSync(file)) { res.statusCode = 404; file = path.join(output, '404.html'); }
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
      page.on('response', response => {
        if (response.status() >= 400 && !response.url().includes('missing-page')) errors.push(`${response.status()} ${response.url()}`);
      });
      const navFits = async () => {
        const nav = page.locator('nav.skin-gallery');
        assert.equal(await nav.locator('[data-skin-id]').count(), ids.length);
        assert.ok(await nav.evaluate(el => {
          const bounds = el.getBoundingClientRect();
          return bounds.left >= -1 && bounds.right <= innerWidth + 1 && el.scrollWidth <= el.clientWidth + 1;
        }), `Gallery navigation overflow at ${width}px: ${page.url()}`);
      };
      const pageFits = async id => {
        await navFits();
        // Stock is the unmodified upstream baseline, including its overflow behavior.
        if (id !== 'stock') assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
          `${id} page overflow at ${width}px: ${page.url()}`);
      };
      await page.goto(base, { waitUntil: 'networkidle' });
      assert.equal(await page.locator('.gallery-card').count(), ids.length);
      await page.screenshot({ path: path.join(screenshots, `gallery-index-${width}.png`), fullPage: true });

      for (let index = 0; index < skins.length; index++) {
        const { id } = skins[index];
        const next = ids[(index + 1) % ids.length];
        await page.goto(base + id + '/', { waitUntil: 'networkidle' });
        await pageFits(id);
        assert.equal(await page.locator('.tape-hero').count(), id === 'retro' ? 1 : 0);
        await page.screenshot({ path: path.join(screenshots, `gallery-${id}-home-${width}.png`), fullPage: true });

        await page.goto(base + id + '/posts/hello/', { waitUntil: 'networkidle' });
        await pageFits(id);
        assert.match(await page.locator('body').innerText(), /A notebook for the curious/);
        assert.match(await page.locator('body').innerText(), /Keep the details/);
        const sample = await page.evaluate(() => {
          const paragraph = document.querySelector('.body p, article p');
          const heading = document.querySelector('main h1, article h1');
          if (!paragraph || !heading) return null;
          const style = getComputedStyle(paragraph);
          const headingStyle = getComputedStyle(heading);
          const parse = value => (value.match(/[\d.]+/g) || []).map(Number);
          const ancestry = [];
          for (let element = paragraph; element; element = element.parentElement) ancestry.push(element);
          let background = [255, 255, 255];
          // Solid-color compositing smoke test; textures/gradients still need screenshot QA.
          for (const element of ancestry.reverse()) {
            const color = parse(getComputedStyle(element).backgroundColor);
            if (color.length < 3) continue;
            const alpha = color.length === 4 ? color[3] : 1;
            background = color.slice(0, 3).map((channel, index) => channel * alpha + background[index] * (1 - alpha));
          }
          const foreground = parse(style.color).slice(0, 3);
          const luminance = color => color.map(value => {
            value /= 255;
            return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
          }).reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);
          const light = luminance(foreground), dark = luminance(background);
          return {
            font: style.fontFamily, fontSize: parseFloat(style.fontSize), lineHeight: parseFloat(style.lineHeight),
            headingFont: headingStyle.fontFamily, headingSize: parseFloat(headingStyle.fontSize),
            color: style.color, background, backgroundImage: getComputedStyle(document.body).backgroundImage,
            contrast: (Math.max(light, dark) + 0.05) / (Math.min(light, dark) + 0.05),
          };
        });
        assert.ok(sample, `${id} has representative article typography`);
        if (id !== 'stock' && id !== 'retro') {
          assert.ok(sample.fontSize >= 14, `${id}: text too small (${sample.fontSize}px)`);
          assert.ok(sample.lineHeight / sample.fontSize >= 1.3, `${id}: cramped line height`);
          assert.ok(sample.headingSize >= 24, `${id}: heading hierarchy too small`);
          assert.ok(sample.contrast >= 4.5, `${id}: representative body-text contrast ${sample.contrast.toFixed(2)} < 4.5`);
          assert.equal(await page.locator('#dark-mode-toggle').count(), 0, `${id} is a fixed-palette skin`);
          const code = await page.locator('.highlight code').evaluate(el => {
            const ink = getComputedStyle(el).color;
            const tokens = [...el.querySelectorAll('span')].filter(span => !span.classList.contains('ln'));
            return { font: getComputedStyle(el).fontFamily, ink,
              bad: tokens.filter(span => getComputedStyle(span).color !== ink || getComputedStyle(span).fontStyle !== 'normal').length };
          });
          assert.equal(code.bad, 0, `${id} code tokens use native ink, not low-contrast upstream syntax colors`);
          assert.ok(!code.font.includes('IBM Plex Mono'), `${id} must not select upstream's italic-only Plex font`);
        }
        materialSamples.push({ id, width, ...sample });
        await page.screenshot({ path: path.join(screenshots, `gallery-${id}-article-${width}.png`), fullPage: true });

        if (id !== 'stock' && id !== 'retro') {
          await page.goto(base + id + '/search/', { waitUntil: 'networkidle' });
          const field = page.locator('.search-input');
          await field.fill('notebook');
          await page.waitForFunction(() => document.querySelector('#search-results a'));
          assert.match(await page.locator('#search-results').innerText(), /notebook/i);
          const palette = await field.evaluate(el => {
            const css = getComputedStyle(el), root = getComputedStyle(document.documentElement);
            const normalize = value => {
              const hex = value.trim().replace('#', '');
              return `rgb(${[0, 2, 4].map(i => parseInt(hex.slice(i, i + 2), 16)).join(', ')})`;
            };
            return { actual: [css.backgroundColor, css.color], expected: ['--inua-surface', '--inua-t0'].map(key => normalize(root.getPropertyValue(key))) };
          });
          assert.deepEqual(palette.actual, palette.expected, `${id} search field retains native palette`);
          await page.screenshot({ path: path.join(screenshots, `gallery-${id}-search-${width}.png`), fullPage: true });
          await pageFits(id);
        }

        for (const relative of ['posts/hello/', 'tags/notes/']) {
          await page.goto(base + id + '/' + relative + '?compare=1#keep-the-details', { waitUntil: 'networkidle' });
          const target = page.locator(`nav.skin-gallery [data-skin-id="${next}"]`);
          await target.focus();
          await page.keyboard.press('Enter');
          await page.waitForURL(base + next + '/' + relative + '?compare=1#keep-the-details');
          await page.waitForLoadState('networkidle');
          await pageFits(next);
          assert.notEqual(await page.locator(`nav.skin-gallery [data-skin-id="${next}"]`).getAttribute('aria-current'), null);
          await page.goBack({ waitUntil: 'networkidle' });
          assert.equal(new URL(page.url()).pathname, `/preview/${id}/${relative}`);
          await page.goForward({ waitUntil: 'networkidle' });
          assert.equal(new URL(page.url()).pathname, `/preview/${next}/${relative}`);
        }
      }
      const notFound = await page.goto(base + 'retro/missing-page/', { waitUntil: 'networkidle' });
      assert.equal(notFound.status(), 404);
      for (const id of ids) assert.equal(await page.locator(`[data-skin-id="${id}"]`).count(), 1);
      await page.locator('a[href$="retro/"]').first().click();
      await page.waitForURL(base + 'retro/');
      assert.deepEqual(errors, []);
      await context.close();
      console.log(`PASS gallery ${width}px: all ${ids.length} skins, typography/contrast smoke, home/article screenshots, keyboard/deep-link/history switching, 404 and assets`);
    }
    const noJS = await browser.newContext({ javaScriptEnabled: false });
    const page = await noJS.newPage();
    for (let index = 0; index < ids.length; index++) {
      const id = ids[index], next = ids[(index + 1) % ids.length];
      await page.goto(base + id + '/posts/hello/');
      await page.locator(`nav.skin-gallery [data-skin-id="${next}"]`).click();
      await page.waitForURL(base + next + '/posts/hello/');
    }
    await noJS.close();
    fs.writeFileSync(path.join(screenshots, 'typography-material-smoke.json'), JSON.stringify(materialSamples, null, 2));
    console.log(`PASS equivalent-page gallery switching without JavaScript for all ${ids.length} skins`);
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
    fs.rmSync(temporary, { recursive: true, force: true });
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

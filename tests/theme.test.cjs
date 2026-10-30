const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../skins/retro/static/archie-skins/retro/theme.js'), 'utf8');

function harness(mode, { saved, denied = false, dark = false } = {}) {
  let onChange;
  const attributes = {};
  const button = { dataset: {}, setAttribute: (k, v) => attributes[k] = v };
  const sheet = { disabled: false };
  const element = { dataset: { colorMode: mode } };
  const writes = [];
  const sandbox = {
    document: { documentElement: element, getElementById: id => id === 'darkModeStyle' ? sheet : mode === 'toggle' ? button : null },
    localStorage: { getItem: () => { if (denied) throw Error('denied'); return saved; }, setItem: (...args) => { if (denied) throw Error('denied'); writes.push(args); } },
    window: { matchMedia: () => ({ matches: dark, addEventListener: (_, fn) => onChange = fn }) },
  };
  vm.runInNewContext(source, sandbox);
  return { sandbox, attributes, sheet, element, writes, change: value => onChange({ matches: value }) };
}

test('toggle defaults dark, repeated toggles persist and expose accessible state', () => {
  const h = harness('toggle');
  assert.equal(h.element.dataset.theme, 'dark');
  assert.equal(h.attributes['aria-pressed'], 'true');
  h.sandbox.toggleTheme();
  assert.equal(h.element.dataset.theme, 'light');
  assert.equal(h.sheet.disabled, true);
  assert.equal(h.attributes['aria-label'], 'Switch to dark mode');
  h.sandbox.toggleTheme();
  assert.equal(h.element.dataset.theme, 'dark');
  assert.equal(h.writes.length, 3);
});
test('toggle restores stored light mode and survives denied storage', () => {
  assert.equal(harness('toggle', { saved: 'light' }).element.dataset.theme, 'light');
  const denied = harness('toggle', { denied: true });
  denied.sandbox.toggleTheme();
  assert.equal(denied.element.dataset.theme, 'light');
});
test('fixed modes ignore storage and do not overwrite preference', () => {
  for (const mode of ['light', 'dark']) {
    const h = harness(mode, { saved: mode === 'light' ? 'dark' : 'light' });
    assert.equal(h.element.dataset.theme, mode);
    assert.equal(h.writes.length, 0);
  }
});
test('auto uses system color and reacts to preference changes', () => {
  const h = harness('auto', { dark: false, saved: 'dark' });
  assert.equal(h.element.dataset.theme, 'light');
  h.change(true);
  assert.equal(h.element.dataset.theme, 'dark');
  h.change(false);
  assert.equal(h.element.dataset.theme, 'light');
  assert.equal(h.writes.length, 0);
});

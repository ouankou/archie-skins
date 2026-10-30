/* Keep Archie's storage key, with an analog-dark default and a usable no-storage path. */
function setTheme(mode) {
  const theme = mode === 'light' ? 'light' : 'dark';
  document.documentElement.dataset.theme = theme;
  try { if (document.documentElement.dataset.colorMode === 'toggle') localStorage.setItem('theme-storage', theme); } catch (_) { /* Private browsing may deny storage. */ }
  const sheet = document.getElementById('darkModeStyle');
  if (sheet) sheet.disabled = theme !== 'dark';
  const button = document.getElementById('dark-mode-toggle');
  if (button) {
    button.dataset.theme = theme;
    button.setAttribute('aria-label', 'Switch to ' + (theme === 'dark' ? 'light' : 'dark') + ' mode');
    button.setAttribute('aria-pressed', String(theme === 'dark'));
    button.innerHTML = theme === 'dark'
      ? '<svg class="feather" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></svg>'
      : '<svg class="feather" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 13A9 9 0 0 1 11 3a9 9 0 1 0 10 10Z"/></svg>';
  }
}
function toggleTheme() {
  setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
}
const colorMode = document.documentElement.dataset.colorMode;
let savedTheme = 'dark';
if (colorMode === 'toggle') {
  try { savedTheme = localStorage.getItem('theme-storage') || 'dark'; } catch (_) { /* Default without storage. */ }
} else if (colorMode === 'auto') {
  const preference = window.matchMedia('(prefers-color-scheme: dark)');
  savedTheme = preference.matches ? 'dark' : 'light';
  preference.addEventListener('change', event => setTheme(event.matches ? 'dark' : 'light'));
} else {
  savedTheme = colorMode;
}
setTheme(savedTheme);

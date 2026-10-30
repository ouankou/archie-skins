/* Demo-only navigation; native links remain usable with JavaScript disabled. */
document.querySelectorAll('.skin-gallery a[data-equivalent="true"]').forEach(link => {
  const target = new URL(link.href);
  target.search = window.location.search;
  target.hash = window.location.hash;
  link.href = target.href;
});
window.addEventListener('hashchange', () => {
  document.querySelectorAll('.skin-gallery a[data-equivalent="true"]').forEach(link => {
    const target = new URL(link.href);
    target.hash = window.location.hash;
    link.href = target.href;
  });
});

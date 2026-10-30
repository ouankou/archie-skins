document.addEventListener('DOMContentLoaded', () => {
  const disclosure = document.querySelector('.toc-disclosure');
  if (disclosure) {
    const desktop = matchMedia('(min-width: 75rem)');
    const syncLayout = () => { disclosure.open = desktop.matches; };
    syncLayout();
    desktop.addEventListener('change', syncLayout);
  }
  // Keep dense technical diagrams readable on small screens without changing content files.
  document.querySelectorAll('.body figure img').forEach((img) => {
    if (img.closest('a')) return;
    const link = document.createElement('a');
    link.className = 'diagram-link';
    link.href = img.src;
    link.setAttribute('aria-label', 'Open full-size image: ' + img.alt);
    img.replaceWith(link);
    link.appendChild(img);
  });
  // Keep wrapped code keyboard-focusable for selection and assistive technology.
  // Ordinary Markdown tables get their scroll region at build time via render-table.html.
  document.querySelectorAll('.body pre').forEach((block) => {
    block.tabIndex = 0;
    block.setAttribute('role', 'region');
    block.setAttribute('aria-label', 'Code block, long lines wrap');
  });
});


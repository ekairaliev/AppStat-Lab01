const tabs = [...document.querySelectorAll('[role="tab"]')];
const panels = [...document.querySelectorAll('[role="tabpanel"]')];
let activePanel;

function followHash() {
  const id = location.hash.slice(1);
  const target = document.getElementById(id);
  const panel = target?.closest('[role="tabpanel"]') ?? activePanel ?? panels[0];
  const switched = panel !== activePanel;

  for (const [index, element] of panels.entries()) {
    const selected = element === panel;
    element.hidden = !selected;
    tabs[index].setAttribute('aria-selected', String(selected));
    tabs[index].tabIndex = selected ? 0 : -1;
  }
  if (switched) document.querySelectorAll('.contents-drawer[open]').forEach(drawer => { drawer.open = false; });
  activePanel = panel;
  document.body.dataset.study = panel.id === 'colorlab' ? 'colorlab' : 'combustion';

  for (const link of document.querySelectorAll('.contents a[aria-current]')) {
    link.removeAttribute('aria-current');
  }
  if (target && target !== panel) {
    let chapter = target.closest('.chapter')?.id;
    if (panel.id === 'colorlab') {
      const headings = [...panel.querySelectorAll('article [id^="colorlab-"], article [data-experiment]')];
      chapter = headings.filter(anchor => anchor === target ||
        anchor.compareDocumentPosition(target) & Node.DOCUMENT_POSITION_FOLLOWING).at(-1)?.id;
    }
    const href = '#' + (chapter || id);
    [...panel.querySelectorAll('.contents a')].find(link => link.hash === href)
      ?.setAttribute('aria-current', 'location');
    requestAnimationFrame(() => target.scrollIntoView());
  } else if (switched || !id || target === panel) {
    window.scrollTo(0, 0);
  }
}

for (const [index, tab] of tabs.entries()) {
  tab.addEventListener('click', event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (tab.hash !== location.hash) location.hash = tab.hash;
    else followHash();
  });
  tab.addEventListener('keydown', event => {
    const destinations = {ArrowRight: index + 1, ArrowLeft: index - 1, Home: 0, End: tabs.length - 1};
    if (!(event.key in destinations)) return;
    event.preventDefault();
    const next = tabs[(destinations[event.key] + tabs.length) % tabs.length];
    next.focus();
    next.click();
  });
}
window.addEventListener('hashchange', followHash);
for (const drawer of document.querySelectorAll('.contents-drawer')) {
  drawer.addEventListener('click', event => {
    if (!event.target.closest('nav a')) return;
    drawer.open = false;
    if (event.target.closest('nav a').hash === location.hash) followHash();
  });
}
document.addEventListener('click', event => {
  for (const drawer of document.querySelectorAll('.contents-drawer[open]')) {
    if (!drawer.contains(event.target)) drawer.open = false;
  }
});
document.addEventListener('keydown', event => {
  const drawer = activePanel?.querySelector('.contents-drawer[open]');
  if (event.key !== 'Escape' || !drawer) return;
  drawer.open = false;
  drawer.querySelector('summary').focus();
});
if (window.katex) {
  for (const element of document.querySelectorAll('.arithmatex')) {
    const tex = element.textContent.trim().slice(2, -2);
    window.katex.render(tex, element, {displayMode: element.tagName === 'DIV', throwOnError: false, strict: 'ignore'});
  }
}
followHash();

const experiments = [...document.querySelectorAll('[data-experiment]')];
let start;
function loadExperiments() {
  if (start) return start;
  const module = new URL('marimo/islands/main.js', document.baseURI);
  const statuses = experiments.map(element => element.querySelector('.island-status'));
  for (const status of statuses) {
    status.textContent = 'Загружаются marimo и данные…';
    status.setAttribute('data-loading', '');
  }
  function finish(message) {
    for (const status of statuses) {
      status.removeAttribute('data-loading');
      status.textContent = message;
    }
  }
  start = import(module.href).then(({ initialize }) => initialize()).then(() => {
    finish('');
  }).catch(error => {
    finish('Интерактив не загрузился. Перезагрузите страницу, чтобы повторить.');
    console.error(error);
  });
  return start;
}

const observer = new IntersectionObserver(entries => {
  if (entries.some(entry => entry.isIntersecting)) {
    observer.disconnect();
    loadExperiments();
  }
}, {rootMargin: '240px'});
for (const element of experiments) observer.observe(element);


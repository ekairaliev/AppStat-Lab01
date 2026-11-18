const refresh = () => {
  if (window.parent === window) return;
  const root = document.getElementById('root');
  const experiment = document.getElementById('photo-experiment');
  const last = document.querySelector('.cl-grid-note');
  const height = Math.ceil(last
    ? last.getBoundingClientRect().bottom + window.scrollY + 48
    : (root ?? document.body).scrollHeight);
  window.parent.postMessage({type: 'appstat:marimo-height', height, ready: Boolean(experiment && last)}, location.origin);
};

new ResizeObserver(refresh).observe(document.body);
const observer = new MutationObserver(refresh);
observer.observe(document.body, {childList: true, subtree: true});
window.addEventListener('resize', refresh);
window.addEventListener('load', refresh);
refresh();

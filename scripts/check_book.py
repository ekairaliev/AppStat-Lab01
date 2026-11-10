"""Check rendered category links and embedded figures after the HTML build."""

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "book/_build/html"


class Page(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.ids = set()
        self.links = []
        self.images = []
        self.feed(content)

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"])
        if tag == "img" and attributes.get("src"):
            self.images.append(attributes["src"])


pages = {path.resolve(): Page(path.read_text(encoding="utf-8")) for path in HTML.rglob("*.html")}
checked_links = 0
referenced_figures = set()
for origin, page in pages.items():
    for href in page.links:
        url = urlsplit(href)
        if url.scheme or url.netloc or not url.fragment.startswith("cell-"):
            continue
        target = (origin.parent / unquote(url.path)).resolve() if url.path else origin
        assert target in pages, f"Missing category page: {origin} -> {href}"
        assert unquote(url.fragment) in pages[target].ids, f"Missing cell anchor: {origin} -> {href}"
        checked_links += 1
    for src in page.images:
        url = urlsplit(src)
        if url.scheme or url.netloc or not url.path.endswith(".png"):
            continue
        image = (origin.parent / unquote(url.path)).resolve()
        assert image.is_file(), f"Missing figure: {origin} -> {src}"
        if not (ROOT / "docs/_static" / image.name).is_file():
            referenced_figures.add(image)

source = json.loads((ROOT / "AppStat_Lab01.ipynb").read_text(encoding="utf-8"))
expected_figures = sum("image/png" in output.get("data", {}) for cell in source["cells"] for output in cell.get("outputs", []))
assert checked_links > 0, "Category navigation was not rendered"
assert len(referenced_figures) == expected_figures, (len(referenced_figures), expected_figures)
assert (HTML / "search.html").is_file()
assert (HTML / "searchindex.js").is_file()
references_path = (HTML / "references.html").resolve()
qr_name = "literature-qr-41e213d3.png"
qr_sources = [src for src in pages[references_path].images if urlsplit(src).path.endswith("/" + qr_name)]
assert len(qr_sources) == 1, "The current literature QR must appear exactly once"
rendered_qr = references_path.parent / unquote(urlsplit(qr_sources[0]).path)
assert rendered_qr.read_bytes() == (ROOT / "docs/_static" / qr_name).read_bytes(), "Outdated literature QR"
assert "https://disk.yandex.ru/d/gn0ul4mhawWwsw" in pages[references_path].links
print(f"Verified {checked_links} rendered cell links, {len(referenced_figures)} figures and search assets.")

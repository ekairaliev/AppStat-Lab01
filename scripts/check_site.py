"""Check the exported site and its notebook cross-references."""
import argparse
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("directory", type=Path, nargs="?", default=Path(__file__).resolve().parents[1] / "dist")
parser.add_argument("--allow-cdn", action="store_true")
args = parser.parse_args()
root = args.directory
doc = BeautifulSoup((root / "index.html").read_text(encoding="utf-8"), "html.parser")
assert [tag["id"] for tag in doc.select('[role="tabpanel"]')] == ["sprint1", "sprint2", "colorlab"]
assert not doc.select("iframe")
assert len(doc.select("[data-experiment]")) == 5
assert len(doc.select('[data-experiment] marimo-island')) == 15
assert doc.select_one("#colorlab article > :last-child .colab-callout")
assert (root / "marimo/islands/main.js").is_file()
assert len(doc.select("details.code")) > 120
assert len(doc.select("img[src^='figures/']")) == 39
assert len(doc.find_all(string="cat_mark_table")) == 2
assert doc.find(id="colorlab-11")
ids = Counter(element["id"] for element in doc.select("[id]"))
assert all(count == 1 for count in ids.values()), [key for key, count in ids.items() if count > 1]
for element in doc.select("[src], [href], [data-src]"):
    attribute = next(name for name in ("src", "href", "data-src") if element.has_attr(name))
    value = urlsplit(element[attribute])
    if value.scheme or value.netloc:
        continue
    if value.path:
        assert (root / unquote(value.path)).is_file(), value.path
    if not value.path and value.fragment:
        assert unquote(value.fragment) in ids, value.fragment
for filename in ["photo_color_data.csv", "cifar10_photos.zip", "combustion-populations.json"]:
    assert (root / "marimo/public/data" / filename).is_file(), filename
if not args.allow_cdn:
    for folder in ["pyodide", "packages"]:
        assert (root / "marimo" / folder).is_dir(), f"Missing offline bundle: {folder}"
print("Verified all three tabs, internal and local links, 39 figures, hidden code and five inline marimo experiments.")


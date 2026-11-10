"""Prepare a Jupyter Book without modifying or executing the original notebook."""

from __future__ import annotations

import copy
import hashlib
import json
import posixpath
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "AppStat_Lab01.ipynb"
BOOK = ROOT / "book"


def text(cell):
    source = cell.get("source", [])
    return source if isinstance(source, str) else "".join(source)


def heading(cell):
    if cell.get("cell_type") != "markdown":
        return ""
    line = text(cell).strip().splitlines()
    return re.sub(r"^#+\s*", "", line[0]).strip() if line and line[0].startswith("#") else ""


def prepare():
    original_bytes = SOURCE.read_bytes()
    notebook = json.loads(original_bytes)
    cells = notebook["cells"]

    def find(prefix, start=0):
        matches = [i for i in range(start, len(cells)) if heading(cells[i]).casefold().startswith(prefix.casefold())]
        if not matches:
            raise ValueError(f"Notebook section not found: {prefix}")
        return matches[0]

    preface = find("Предисловие")
    first_sprint = find("Lab01 - sprint 1")
    second_sprint = find("Lab01 - sprint 2")
    rv1 = find("Random Variable 01")
    rv2 = find("Random Variable 02")
    rv3 = find("Random Variable 03")
    resume1 = find("Lab resume", rv3)
    generators = [find(f"random {i:02d}", second_sprint) for i in range(1, 7)]
    resume2 = find("Lab resume", generators[-1])
    glossary = find("Глоссарий", resume2)
    references = find("Список использованных источников", glossary)

    pages = [
        ("intro", "Прикладная статистика", 0, preface),
        ("preface", "Предисловие", preface, first_sprint),
        ("sprint1/index", "Первый спринт", first_sprint, rv1),
        ("sprint1/temperature", "Температура воспламенения", rv1, rv2),
        ("sprint1/delay", "Задержка воспламенения", rv2, rv3),
        ("sprint1/speed", "Линейная скорость горения", rv3, resume1),
        ("sprint1/resume", "Итоги первого спринта", resume1, second_sprint),
        ("sprint2/index", "Второй спринт", second_sprint, generators[0]),
    ]
    generator_titles = [
        "Задержка: обратная ИФР",
        "Задержка: Бокс-Мюллер",
        "Температура: метод Неймана",
        "Температура: суперпозиция",
        "Скорость: метод отношений",
        "Скорость: суперпозиция",
    ]
    for i, start in enumerate(generators):
        end = generators[i + 1] if i + 1 < len(generators) else resume2
        pages.append((f"sprint2/random{i + 1:02d}", generator_titles[i], start, end))
    pages.extend([
        ("sprint2/resume", "Итоги второго спринта", resume2, glossary),
        ("glossary", "Глоссарий", glossary, references),
        ("references", "Список литературы", references, len(cells)),
    ])

    cell_pages = {}
    covered = []
    for page, _, start, end in pages:
        covered.extend(range(start, end))
        for cell in cells[start:end]:
            ident = cell.get("metadata", {}).get("id")
            if ident:
                if ident in cell_pages:
                    raise ValueError(f"Duplicate notebook cell id: {ident}")
                cell_pages[ident] = page
    assert covered == list(range(len(cells))), "Every notebook cell must belong to one page"

    BOOK.mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "docs/_config.yml", BOOK / "_config.yml")
    shutil.copytree(ROOT / "docs/_static", BOOK / "_static", dirs_exist_ok=True)

    for page, title, start, end in pages:
        output_cells = []
        added_title = False
        for index in range(start, end):
            cell = copy.deepcopy(cells[index])
            ident = cell.get("metadata", {}).get("id")
            if ident:
                output_cells.append({
                    "cell_type": "markdown", "metadata": {},
                    "source": [f'<a class="cell-anchor" id="cell-{ident}"></a>\n'],
                })
            if cell["cell_type"] == "markdown":
                source = text(cell)
                if not added_title:
                    if heading(cell):
                        source = re.sub(r"^\s*#+[^\n]*", f"# {title}", source, count=1)
                    else:
                        source = f"# {title}\n\n" + source
                    added_title = True
                # Colab accepts headings without spaces; CommonMark requires them.
                source = re.sub(r"(?m)^(#{1,6})(?=\S)", r"\1 ", source)
                source = re.sub(r"(?m)^###\s+", "## ", source)

                def rewrite_link(match):
                    target = match.group(1)
                    if target not in cell_pages:
                        raise ValueError(f"Broken Colab link: {target}")
                    target_page = cell_pages[target]
                    relative = posixpath.relpath(target_page + ".html", posixpath.dirname(page) or ".")
                    return ("" if target_page == page else relative) + f"#cell-{target}"

                source = re.sub(r"#scrollTo=([\w-]+)", rewrite_link, source)
                cell["source"] = source.splitlines(keepends=True)
            elif cell["cell_type"] == "code":
                tags = cell.setdefault("metadata", {}).setdefault("tags", [])
                if "hide-input" not in tags:
                    tags.append("hide-input")
                # Widgets' transient state is not required to render saved figures.
                cell.get("metadata", {}).pop("execution", None)
            output_cells.append(cell)

        if not added_title:
            output_cells.insert(0, {"cell_type": "markdown", "metadata": {}, "source": [f"# {title}\n"]})
        if page == "intro":
            output_cells.append({
                "cell_type": "markdown", "metadata": {},
                "source": [
                    "\n## Исследование\n\n",
                    "Температура воспламенения, задержка воспламенения и скорость горения металлических материалов.\n\n",
                    "Первый спринт посвящён анализу экспериментальных данных, второй - построению и проверке шести генераторов случайных чисел.\n\n",
                    "[Начать с первого спринта](sprint1/index.html) · [Генераторы второго спринта](sprint2/index.html)\n\n",
                    "[Открыть полный ноутбук в Colab](https://colab.research.google.com/github/ekairaliev/AppStat-Lab01/blob/main/AppStat_Lab01.ipynb) · ",
                    "[Исходный ноутбук на GitHub](https://github.com/ekairaliev/AppStat-Lab01/blob/main/AppStat_Lab01.ipynb)\n",
                ],
            })
        target = BOOK / (page + ".ipynb")
        target.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}
        target.write_text(json.dumps({"nbformat": 4, "nbformat_minor": 4, "metadata": metadata, "cells": output_cells}, ensure_ascii=False, indent=1), encoding="utf-8")

    toc = [
        "format: jb-book", "root: intro", "parts:",
        "  - caption: О работе", "    chapters:", "      - file: preface",
        "  - caption: Первый спринт", "    chapters:", "      - file: sprint1/index", "        sections:",
    ]
    for slug in ["temperature", "delay", "speed", "resume"]:
        toc.append(f"          - file: sprint1/{slug}")
    toc.extend(["  - caption: Второй спринт", "    chapters:", "      - file: sprint2/index", "        sections:"])
    toc.extend(f"          - file: sprint2/random{i:02d}" for i in range(1, 7))
    toc.extend(["          - file: sprint2/resume", "  - caption: Справочные материалы", "    chapters:", "      - file: glossary", "      - file: references"])
    (BOOK / "_toc.yml").write_text("\n".join(toc) + "\n", encoding="utf-8")

    assert SOURCE.read_bytes() == original_bytes, "The original notebook must remain byte-for-byte unchanged"
    original_images = sum("image/png" in o.get("data", {}) for c in cells for o in c.get("outputs", []))
    generated_images = 0
    for page, _, _, _ in pages:
        generated = json.loads((BOOK / (page + ".ipynb")).read_text(encoding="utf-8"))
        generated_images += sum("image/png" in o.get("data", {}) for c in generated["cells"] for o in c.get("outputs", []))
    assert original_images == generated_images
    print(f"Prepared {len(pages)} pages; preserved {original_images} figures and {len(cells)} original cells.")
    print(f"Original notebook SHA-256: {hashlib.sha256(original_bytes).hexdigest()}")


if __name__ == "__main__":
    prepare()

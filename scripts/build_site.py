"""Render the saved Colab outputs and export the inline marimo experiments."""
from __future__ import annotations

import argparse
import base64
from html import escape
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup
import markdown
from marimo import MarimoIslandGenerator

from install_islands import install_islands

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
COLOR = ROOT / "ktvd/ColorLab"
EXPERIMENTS = COLOR / "interactive/experiments.py"
MAIN_COLAB = "https://colab.research.google.com/github/ekairaliev/AppStat-Lab01/blob/main/AppStat_Lab01.ipynb"
COLOR_COLAB = "https://colab.research.google.com/github/ekairaliev/AppStat-Lab01/blob/main/ktvd/ColorLab/Photo%282%29.ipynb"

SPRINT_1 = [
    ("Предисловие", "preface", "Предисловие"),
    ("Random Variable 01", "temperature", "Температура воспламенения"),
    ("Random Variable 02", "delay", "Задержка воспламенения"),
    ("Random Variable 03", "speed", "Линейная скорость горения"),
    ("Lab resume", "sprint1-resume", "Итоги первого спринта"),
]
SPRINT_2 = [
    ("random 01", "random01", "Задержка · обратная ИФР"),
    ("random 02", "random02", "Задержка · Бокс-Мюллер"),
    ("random 03", "random03", "Температура · метод Неймана"),
    ("random 04", "random04", "Температура · суперпозиция"),
    ("random 05", "random05", "Скорость · метод отношений"),
    ("random 06", "random06", "Скорость · суперпозиция"),
    ("Дополнительное исследование", "generators", "Сравнение алгоритмов"),
    ("Lab resume", "sprint2-resume", "Итоги второго спринта"),
    ("Глоссарий", "glossary", "Глоссарий"),
    ("Список использованных источников", "references", "Список литературы"),
]
COLOR_SECTIONS = [
    ("colorlab-1", "Описание величин"),
    ("colorlab-2", "Разведочный анализ"),
    ("colorlab-3", "Связь яркости и насыщенности"),
    ("color-relation", "Интерактивная диаграмма"),
    ("colorlab-4", "Модели распределений"),
    ("colorlab-5", "Стандартизация"),
    ("colorlab-6", "Исследование выборок"),
    ("experiments", "Фото и выборка"),
    ("colorlab-7", "Состоятельность оценок"),
    ("colorlab-8", "Проверка качества моделей"),
    ("color-generator", "Генератор ColorLab"),
    ("colorlab-10", "Источники"),
    ("colorlab-11", "Таблица критериев"),
    ("colorlab-9", "Общий вывод"),
]

MD = markdown.Markdown(
    extensions=["tables", "fenced_code", "pymdownx.arithmatex", "pymdownx.magiclink"],
    extension_configs={"pymdownx.arithmatex": {"generic": True}},
)

def join(value):
    return "".join(value) if isinstance(value, list) else value

def source(cell):
    return join(cell["source"])

def read_cells(path):
    return json.loads(path.read_bytes())["cells"]

def first_heading(cell):
    if cell["cell_type"] != "markdown":
        return ""
    return re.sub(r"^#+\s*", "", source(cell).lstrip().split("\n", 1)[0])

def render_markdown(value):
    value = re.sub(r"(?m)^(#{1,6})(?=[^\s#])", r"\1 ", value)
    value = re.sub(r"#scrollTo=([\w-]+)", r"#cell-\1", value)
    value = re.sub(r"(?m)^# (Глоссарий|Список использованных источников|Предисловие|Lab01 - sprint [12])", r"## \1", value)
    soup = BeautifulSoup(MD.reset().convert(value), "html.parser")
    for table in soup.find_all("table"):
        wrapper = soup.new_tag("div", attrs={"class": "table-scroll", "tabindex": "0", "role": "region", "aria-label": "Таблица"})
        table.wrap(wrapper)
    return str(soup)

class NotebookRenderer:
    def __init__(self, output_dir, name):
        self.output_dir = output_dir
        self.name = name
        self.figures = 0

    def render_output(self, output, caption):
        if output["output_type"] == "stream":
            return f'<pre class="output">{escape(join(output["text"]))}</pre>'
        data = output.get("data", {})
        if "image/png" in data:
            self.figures += 1
            path = f"figures/{self.name}-{self.figures:02d}.png"
            (self.output_dir / path).write_bytes(base64.b64decode(join(data["image/png"])))
            alt = f"{caption}. График {self.figures}"
            return f'<figure><img src="{path}" loading="lazy" alt="{escape(alt)}"></figure>'
        if "text/html" in data:
            soup = BeautifulSoup(join(data["text/html"]), "html.parser")
            table = soup.find("table")
            if table:
                for tag in table.find_all(["script", "style"]):
                    tag.decompose()
                for tag in [table, *table.find_all(True)]:
                    tag.attrs = {}
                return f'<div class="table-scroll" tabindex="0" role="region" aria-label="Таблица результатов">{table}</div>'
        if "text/plain" in data:
            return f'<pre class="output">{escape(join(data["text/plain"]))}</pre>'
        return ""

    def render_cell(self, cell, caption, replacement=None):
        identifier = cell.get("metadata", {}).get("id")
        if cell["cell_type"] == "markdown":
            value = render_markdown(source(cell) if replacement is None else replacement)
        elif cell["cell_type"] == "code":
            code = escape(source(cell).rstrip())
            outputs = "".join(self.render_output(item, caption) for item in cell.get("outputs", []))
            value = f'<details class="code"><summary>Показать Python-код</summary><pre><code>{code}</code></pre></details>{outputs}'
        else:
            value = ""
        anchor = f' id="cell-{escape(identifier)}"' if identifier else ""
        return f'<div class="notebook-cell"{anchor}>{value}</div>'

def sprint_body(cells, sections, renderer):
    starts = []
    for title, _, _ in sections:
        start = starts[-1] + 1 if starts else 0
        starts.append(next(i for i in range(start, len(cells)) if first_heading(cells[i]).casefold().startswith(title.casefold())))
    body = []
    for (_, slug, label), start, end in zip(sections, starts, starts[1:] + [len(cells)]):
        chapter = "".join(renderer.render_cell(cell, label) for cell in cells[start:end])
        if slug == "references":
            chapter += """
            <p><a href="https://disk.yandex.ru/d/gn0ul4mhawWwsw">PDF литературы</a></p>
            <figure class="qr"><img src="static/literature-qr-41e213d3.png" alt="QR-код для PDF литературы" loading="lazy"></figure>"""
        body.append(f'<section class="chapter" id="{slug}" aria-label="{label}">{chapter}</section>')
    return "".join(body)

def experiment(slug, title, caption, cells):
    return f"""
<section class="experiment chapter" id="{slug}" data-experiment>
  <div class="experiment-title"><span class="experiment-mark" aria-hidden="true">✳</span>
  <div><p class="eyebrow">Эксперимент · marimo</p><h2>{title}</h2></div></div>
  <p>{caption}</p>
  <p class="island-status" role="status">Интерактив загружается при приближении к разделу.</p>
  <div class="islands">{"".join(cell.render() for cell in cells)}</div>
  <noscript>Для работы интерактива включите JavaScript.</noscript>
</section>"""

def make_islands():
    generator = MarimoIslandGenerator.from_file(str(EXPERIMENTS), display_code=False)
    color = generator.stubs
    if len(color) != 13:
        raise ValueError("Unexpected ColorLab cell layout.")
    sprint = [
        generator.add_code(cell.strip(), display_code=False)
        for cell in (SITE / "sprint_experiments.py").read_text(encoding="utf-8-sig").split("# %%")
        if cell.strip()
    ]
    return generator, {
        "bootstrap": color[0].render() + sprint[0].render(),
        "sampling": experiment("sampling-experiment", "Как объём выборки влияет на среднее?",
                               "Выбери одну из трёх величин. Для каждого способа отбора построены средние 500 выборок. Пунктир показывает среднее всей группы.", sprint[1:4]),
        "generation": experiment("generator-experiment", "Что генерируют две модели задержки?",
                                  "Сравни ИФР измерений с обратной эмпирической ИФР и моделью Бокса — Мюллера. Измени число значений и посмотри, как меняются график и расстояние KS.", sprint[4:]),
        "photo": experiment("experiments", "Фото и выборка", "Измени яркость или насыщенность снимка и сравни статистики выборки до и после.", color[2:7]),
        "relation": experiment("color-relation", "Связь на диаграмме рассеяния", "Наведи на точку, чтобы прочитать характеристики снимка. Можно показать все 10 000 изображений или выборку.", color[8:10]),
        "color_generator": experiment("color-generator", "Генератор ColorLab", "Сравни парный эмпирический метод и независимые модели яркости и насыщенности.", color[10:]),
    }

def color_body(cells, renderer, experiments):
    chunks = []
    conclusion = ""
    preparation = []
    after_criteria = False
    for i, cell in enumerate(cells):
        if cell.get("metadata", {}).get("id") == "9abf0e36":
            continue
        value = source(cell)
        if cell["cell_type"] == "markdown":
            if i == 0:
                value = re.sub(r"^# Lab01\s*", "", value)
            if i == 1:
                value = "[Открыть эксперимент с фотографией и выборкой](#experiments)"
            if '<a id="colorlab-9"' in value:
                conclusion = renderer.render_cell(cell, "ColorLab", replacement=value)
                continue
            if '<a id="colorlab-4"' in value:
                chunks.append(experiments["relation"])
            if '<a id="colorlab-7"' in value:
                chunks.append(experiments["photo"])
            if '<a id="colorlab-10"' in value:
                chunks.append(experiments["color_generator"])
            value = value.replace("https://ekairaliev.github.io/AppStat-Lab01/#colorlab", "#experiments")
            value = value.replace("[ColorLab на сайте лабораторной](#experiments) | Выполнено и опубликовано", "[Интерактивы marimo](#experiments) | Выполнено")
        rendered = renderer.render_cell(cell, "ColorLab", replacement=value)
        if after_criteria:
            preparation.append(rendered)
        else:
            chunks.append(rendered)
        if '<a id="colorlab-11"' in value:
            after_criteria = True
    chunks.append('<details class="cover"><summary>Код подготовки файлов</summary>' + "".join(preparation) + '</details>')
    chunks.append(f"""<section class="color-conclusion">{conclusion}
    <a class="colab-callout" href="{COLOR_COLAB}" target="_blank" rel="noopener">
    <span>Исходный Colab ColorLab</span><strong>Открыть ноутбук ↗</strong></a></section>""")
    return "".join(chunks)

def navigation(section_links, number=False):
    links = []
    for i, (slug, label) in enumerate(section_links, 1):
        index = f' <span class="index">{i:02d}</span>' if number else ""
        links.append(f'<li><a href="#{slug}">{index}<span>{label}</span></a></li>')
    return f'<nav class="contents" aria-label="Содержание раздела"><h2>Содержание</h2><ol>{"".join(links)}</ol></nav>'

def panel(slug, title, subtitle, links, body, colab, notebook, meta, theme, active=False):
    attrs = "" if active else " hidden"
    label = title
    experiment_id = {"sprint1": "sampling-experiment", "sprint2": "generator-experiment", "colorlab": "experiments"}[slug]
    if slug == "colorlab":
        art = '<div class="hero-photos">' + "".join(
            f'<img src="static/photo-{i}.webp" alt="Пример изображения CIFAR-10" width="128" height="128">'
            for i in range(1, 7)
        ) + '</div>'
        title = "Цвет — это <em>данные.</em>"
    else:
        art = '<div class="hero-ignition" aria-hidden="true"></div>'

    return f"""
    <section class="panel {theme}" id="{slug}" role="tabpanel" aria-labelledby="tab-{slug}"{attrs}>
      <div class="hero">
        <div>
          <p class="eyebrow">{meta}</p>
          <h1>{title}</h1>
          <p class="lede">{subtitle}</p>
          <div class="resources">
            <a href="{colab}" target="_blank" rel="noopener">Открыть в Colab ↗</a>
            <a href="#{experiment_id}">К эксперименту ↓</a>
            <a href="{notebook}" download>Скачать .ipynb ↓</a>
          </div>
        </div>
        {art}
      </div>
      <div class="reading">
        <details class="contents-drawer">
          <summary aria-label="Содержание"><span aria-hidden="true">☰</span><span class="drawer-label">Содержание</span></summary>
          {navigation(links, number=slug.startswith("sprint"))}
        </details>
        <article aria-label="{escape(label)}">{body}</article>
      </div>
    </section>"""

def build(output, offline):
    output.mkdir(parents=True, exist_ok=True)
    (output / "figures").mkdir(exist_ok=True)
    shutil.copytree(SITE / "static", output / "static", dirs_exist_ok=True)
    shutil.copy2(ROOT / "docs/_static/literature-qr-41e213d3.png", output / "static")
    shutil.copy2(ROOT / "docs/_static/cover.jpg", output / "static/ignition-cover.jpg")
    downloads = output / "downloads"
    downloads.mkdir(exist_ok=True)
    for path, name in [
        (ROOT / "AppStat_Lab01.ipynb", "AppStat_Lab01.ipynb"),
        (COLOR / "Photo(2).ipynb", "ColorLab.ipynb"),
    ]:
        shutil.copy2(path, downloads / name)

    main = read_cells(ROOT / "AppStat_Lab01.ipynb")
    color = read_cells(COLOR / "Photo(2).ipynb")
    split = next(i for i, cell in enumerate(main) if first_heading(cell) == "Lab01 - sprint 2")
    main_renderer = NotebookRenderer(output, "sprint")
    color_renderer = NotebookRenderer(output, "color")
    first = sprint_body(main[1:split], SPRINT_1, main_renderer)
    second = main_renderer.render_cell(main[split], "Спринт 2")
    second += sprint_body(main[split + 1:], SPRINT_2, main_renderer)
    cover = main_renderer.render_cell(main[0], "Титульный лист")
    first = f'<details class="cover"><summary>Титульный лист работы</summary>{cover}</details>' + first
    generator, experiments = make_islands()
    first = first.replace('<section class="chapter" id="sprint1-resume"', experiments["sampling"] + '<section class="chapter" id="sprint1-resume"', 1)
    second = second.replace('<section class="chapter" id="generators"', experiments["generation"] + '<section class="chapter" id="generators"', 1)
    first_links = [(slug, label) for _, slug, label in SPRINT_1]
    first_links.insert(-1, ("sampling-experiment", "Эксперимент с выборками"))
    second_links = [(slug, label) for _, slug, label in SPRINT_2]
    second_links.insert(6, ("generator-experiment", "Сравнить генераторы"))
    common = (MAIN_COLAB, "downloads/AppStat_Lab01.ipynb")
    panels = "".join([
        panel("sprint1", "Анализ экспериментальных данных", "Температура и задержка воспламенения, линейная скорость горения металлических материалов.", first_links, first, *common, "Спринт 1 · CombustionData", "analysis", active=True),
        panel("sprint2", "Генераторы случайных величин", "Шесть генераторов для трёх величин. Математические обоснования, реализации и проверки.", second_links, second, *common, "Спринт 2 · Моделирование", "models"),
        panel("colorlab", "ColorLab", "Яркость и насыщенность 10 000 изображений CIFAR-10. Дополнительное исследование Кристины Торховой.", COLOR_SECTIONS, color_body(color, color_renderer, experiments), COLOR_COLAB, "downloads/ColorLab.ipynb", "КТвД · Цвет и статистика", "color"),
    ])
    template = (SITE / "index.html").read_text(encoding="utf-8")
    html = template.replace("<!-- PANELS -->", panels)
    html = html.replace("<!-- ISLANDS -->", '<div hidden>' + experiments["bootstrap"] + '</div>' + generator.render_payload_script())
    (output / "index.html").write_text(html, encoding="utf-8")
    (output / ".nojekyll").touch()

    with TemporaryDirectory(prefix="appstat-runtime-", dir=output.parent) as scratch:
        runtime = Path(scratch) / "export"
        destination = output / "marimo"
        command = [sys.executable, "-m", "marimo", "export", "html-wasm", str(EXPERIMENTS),
                   "-o", str(runtime), "--mode", "run", "--no-sandbox"]
        if offline:
            command.append("--offline")
        subprocess.run(command, cwd=EXPERIMENTS.parent, check=True)
        resources = ["public", "pyodide", "lockfile", "packages"] if offline else ["public"]
        for folder in resources:
            shutil.copytree(runtime / folder, destination / folder, dirs_exist_ok=True)
        install_islands(SITE / "vendor", destination, runtime, offline)

    for cells, renderer in [(main, main_renderer), (color, color_renderer)]:
        expected = sum("image/png" in item.get("data", {}) for cell in cells for item in cell.get("outputs", []))
        if renderer.figures != expected:
            raise ValueError(f"{renderer.name}: exported {renderer.figures} figures, expected {expected}")
    print(f"Site: {output} ({main_renderer.figures + color_renderer.figures} figures)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--offline", action="store_true", help="Bundle Pyodide and Python packages for single-origin hosting.")
    args = parser.parse_args()
    build(args.output.resolve(), args.offline)


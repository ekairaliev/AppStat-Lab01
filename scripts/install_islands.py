"""Prepare the pinned marimo Islands frontend for same-origin hosting."""
from pathlib import Path
import re
import shutil
import tarfile

def install_islands(vendor: Path, export: Path, runtime: Path, offline: bool):
    dest = export / "islands"
    with tarfile.open(vendor / "marimo-islands-0.25.2.tgz", "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.startswith("package/dist/"):
                continue
            if member.name.endswith((".map", ".d.ts")):
                continue
            name = Path(member.name.removeprefix("package/dist/"))
            assert not name.is_absolute() and ".." not in name.parts
            target = dest / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, target.open("wb") as out:
                shutil.copyfileobj(source, out)
    shutil.copy2(vendor / "MARIMO-LICENSE", dest / "LICENSE")
    main = dest / "main.js"
    script = main.read_text(encoding="utf-8")
    script = script.replace(
        "https://cdn.jsdelivr.net/npm/mathjax-full@3.2.2/es5/tex-mml-svg.min.js",
        "./static/mathjax/tex-mml-svg.min.js",
    )
    script = script.replace('yB.textContent = "⚡ reactivity initializing..."',
                            'yB.textContent = "Подготовка интерактивов marimo…"')
    # Allow a cold browser cache time to load SciPy, Plotly and NumPy.
    script = script.replace("maxRequestTime: 2e4", "maxRequestTime: 12e4")
    main.write_text(script, encoding="utf-8")
    if not offline:
        return

    html = (runtime / "index.html").read_text(encoding="utf-8")
    lock = re.search(r'data-pyodide-lockfile-url="\./([^"]+)"', html)
    if lock is None:
        raise ValueError("The offline marimo export has no lockfile.")
    worker, = (dest / "assets").glob("worker-*.js")
    code = worker.read_text(encoding="utf-8")
    bootstrap = "bootstrap({version:e,pyodideVersion:t})"
    if code.count(bootstrap) != 1:
        raise ValueError("Unexpected worker bootstrap in pinned marimo Islands.")
    code = code.replace(
        bootstrap,
        'bootstrap({version:e,pyodideVersion:t,'
        'pyodideIndexUrl:new URL("../../pyodide/",import.meta.url).href,'
        f'pyodideLockfileUrl:new URL("../../{lock[1]}",import.meta.url).href,'
        'pypiIndexUrl:new URL("../../packages/index",import.meta.url).href})',
    )
    worker.write_text(code, encoding="utf-8")


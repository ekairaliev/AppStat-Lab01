# /// script
# dependencies = [
#   "numpy", "pandas", "matplotlib", "scipy", "plotly", "pillow"
# ]
# ///

import marimo

__generated_with = "0.18.0"
app = marimo.App(width="full")


@app.cell
async def _():
    import base64
    import io
    import zipfile
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.colors import rgb_to_hsv, hsv_to_rgb
    from scipy import stats
    import plotly.graph_objects as go
    from PIL import Image

    import sys
    import asyncio

    if sys.platform == "emscripten":
        from pyodide.http import pyfetch

        from urllib.parse import urljoin

        location = str(mo.notebook_location()).rstrip("/") + "/"
        base_url = urljoin(location, "../public/" if location.endswith("/islands/") else "public/").rstrip("/")
        root = Path("/tmp/colorlab_runtime")
        resources = ("data/photo_color_data.csv", "data/cifar10_photos.zip", "data/combustion-populations.json")

        async def download_resource(relative_name):
            destination = root / relative_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            last_error = None
            for attempt in range(3):
                try:
                    response = await pyfetch(f"{base_url}/{relative_name}")
                    if not response.ok:
                        raise OSError(f"HTTP {response.status}")
                    destination.write_bytes(await response.bytes())
                    return
                except Exception as exc:
                    last_error = exc
                    if attempt < 2:
                        await asyncio.sleep(0.7 * (attempt + 1))
            raise RuntimeError(
                f"Не удалось загрузить {relative_name} после 3 попыток: {last_error}. "
            )

        await asyncio.gather(*(download_resource(name) for name in resources))
    else:
        root = mo.notebook_location() / "public"

    csv_path = root / "data" / "photo_color_data.csv"
    photos_path = root / "data" / "cifar10_photos.zip"
    if not csv_path.is_file() or not photos_path.is_file():
        raise FileNotFoundError("Нет данных: проверьте файлы в папке data")
    table = pd.read_csv(csv_path)
    if not {"image_id", "brightness", "saturation"}.issubset(table.columns):
        raise ValueError("CSV должен содержать image_id, brightness, saturation")
    table = table.sort_values("image_id").reset_index(drop=True)
    if len(table) != 10000 or table[["image_id", "brightness", "saturation"]].isna().any().any():
        raise ValueError("CSV: ожидаются 10 000 строк без пропусков")
    with zipfile.ZipFile(photos_path) as _archive:
        ids = sorted(int(Path(_name).stem) for _name in _archive.namelist()
                     if _name.startswith("photos/") and _name.endswith(".png"))
    if not ids:
        raise ValueError("В ZIP не найдены изображения")

    def image_png(array):
        _buf = io.BytesIO()
        Image.fromarray(array).save(_buf, "PNG")
        return base64.b64encode(_buf.getvalue()).decode("ascii")

    def plot_png(fig):
        _buf = io.BytesIO()
        fig.savefig(_buf, format="png", dpi=145, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        return base64.b64encode(_buf.getvalue()).decode("ascii")

    def num(v, decimals=4):
        return f"{v:.{decimals}f}".replace(".", ",")

    return (mo, np, plt, stats, go, Image, zipfile, io, rgb_to_hsv, hsv_to_rgb,
            table, photos_path, ids, image_png, plot_png, num)


@app.cell
def _(mo):
    mo.Html("""
    <section class="cl cl-section" id="photo-experiment">
       <div class="cl-head"><h2>Фотография и выборка</h2></div>
       <p class="cl-sub">Выбери фотографию, попробуй сделать её светлее или насыщеннее. Посмотри на значения до и после, а затем на статистику выборки. Здесь меняются сами пиксели изображения.</p>
    </section>""")
    return


@app.cell
def _(mo, ids, table):
    photo_items = [f"Фото № {_i}" for _i in ids]
    photo_select = mo.ui.dropdown(options=photo_items, value=photo_items[0], label="Фотография")
    brightness_ui = mo.ui.slider(start=.2, stop=2.0, step=.1, value=1.0,
                                 label="Яркость ×", show_value=True)
    saturation_ui = mo.ui.slider(start=0.0, stop=2.0, step=.1, value=1.0,
                                 label="Насыщенность ×", show_value=True)
    size_ui = mo.ui.slider(start=100, stop=len(table), step=100, value=1000,
                           label="Размер выборки", show_value=True)
    sampling_ui = mo.ui.radio(options=["Без возвращения", "С возвращением"],
                              value="Без возвращения", label="Отбор")
    sample_refresh = mo.ui.button(label="Новая случайная выборка", value=0,
                                  on_click=lambda value: value + 1)
    chart_ui = mo.ui.radio(options=["Гистограммы", "Диаграммы размаха"],
                            value="Гистограммы", label="Вид графика")
    mo.vstack([
        mo.Html('<span class="cl-controls-marker cl-interactive-surface" aria-hidden="true"></span>'),
        mo.hstack([photo_select, size_ui], justify="start", gap=2, wrap=True),
        mo.hstack([brightness_ui, saturation_ui], justify="start", gap=2, wrap=True),
        mo.hstack([sampling_ui, chart_ui], justify="start", gap=2, wrap=True),
        sample_refresh,
        mo.md("*Множитель 1,0 соответствует исходному изображению. При анализе выборки изменяется одна выбранная фотография; остальные остаются исходными.*"),
    ], gap=2).style({"max-width":"1180px", "margin":"0 auto", "background":"transparent",
                    "color":"#244a49", "border-radius":"18px", "padding":"26px", "width":"100%"})
    return photo_select, brightness_ui, saturation_ui, size_ui, sampling_ui, chart_ui, sample_refresh


@app.cell
def _(np, Image, io, zipfile, photos_path, photo_select, brightness_ui, saturation_ui,
          rgb_to_hsv, hsv_to_rgb, image_png):
    chosen_photo_id = int(photo_select.value.replace("Фото № ", ""))
    with zipfile.ZipFile(photos_path) as _archive:
        with _archive.open(f"photos/{chosen_photo_id:05d}.png") as _handle:
            original = np.asarray(Image.open(io.BytesIO(_handle.read())).convert("RGB"))
    hsv0 = rgb_to_hsv(original.astype(np.float32)/255.0)
    hsv1 = hsv0.copy()
    hsv1[...,2] = np.clip(hsv0[...,2] * brightness_ui.value, 0, 1)
    hsv1[...,1] = np.clip(hsv0[...,1] * saturation_ui.value, 0, 1)
    altered = np.rint(hsv_to_rgb(hsv1) * 255).clip(0,255).astype(np.uint8)
    altered_hsv = rgb_to_hsv(altered.astype(np.float32)/255.0)
    b0 = float(hsv0[...,2].mean())
    s0 = float(hsv0[...,1].mean())
    b1 = float(altered_hsv[...,2].mean())
    s1 = float(altered_hsv[...,1].mean())
    original_b64 = image_png(original)
    altered_b64 = image_png(altered)
    return chosen_photo_id, b0, s0, b1, s1, original_b64, altered_b64


@app.cell
def _(mo, num, original_b64, altered_b64, chosen_photo_id, b0, s0, b1, s1):
    mo.Html(f"""
    <section class="cl cl-section" style="padding-top:15px">
      <div class="cl-live">
        <div class="cl-live-photo">
          <div class="cl-photo-box"><div class="cl-photo-title">Исходное изображение № {chosen_photo_id}</div>
             <img src="data:image/png;base64,{original_b64}" alt="Исходное фото CIFAR-10">
             <span class="cl-photo-cap">Яркость {num(b0,3)} · Насыщенность {num(s0,3)}</span></div>
          <div class="cl-photo-box"><div class="cl-photo-title">После изменения</div>
             <img src="data:image/png;base64,{altered_b64}" alt="Фотография после изменения HSV">
             <span class="cl-photo-cap">Яркость {num(b1,3)} · Насыщенность {num(s1,3)}</span></div>
        </div>
      </div>
    </section>""")
    return


@app.cell
def _(np, table, size_ui, sampling_ui, sample_refresh, chosen_photo_id, b1, s1):
    n = int(size_ui.value)
    replacement = sampling_ui.value == "С возвращением"
    _rng = np.random.default_rng(42 + int(sample_refresh.value))
    _others = table.loc[table.image_id != chosen_photo_id, "image_id"].to_numpy()
    _ids = np.concatenate(([chosen_photo_id], _rng.choice(_others, n-1, replace=replacement)))
    subset_before = table.set_index("image_id").loc[_ids].reset_index()
    subset_after = subset_before.copy()
    subset_after.loc[0,"brightness"] = b1
    subset_after.loc[0,"saturation"] = s1
    return n, subset_before, subset_after


@app.cell
def _(mo, np, num, plt, plot_png, subset_before, subset_after, n, chart_ui):
    _stats = []
    for _col, _label in [("brightness","Яркость"),("saturation","Насыщенность")]:
        _old = float(subset_before[_col].mean())
        _new = float(subset_after[_col].mean())
        _stats.append(f'<div><div>{_label}</div><div class="value">{num(_new)}</div><div>Изменение: {num(_new-_old,6)}</div></div>')
    _corr_old = subset_before.brightness.corr(subset_before.saturation)
    _corr_new = subset_after.brightness.corr(subset_after.saturation)
    _stats.append(f'<div><div>Корреляция Пирсона</div><div class="value">{num(_corr_new)}</div><div>Было: {num(_corr_old)}</div></div>')
    _fig, _axs = plt.subplots(1,2,figsize=(10.8,3.3),facecolor="white")
    for _ax,_col,_color in zip(_axs,["brightness","saturation"],["#d4b441","#6ca478"]):
        if chart_ui.value == "Гистограммы":
            _ax.hist(subset_before[_col], bins=np.linspace(0,1,27), color=_color, alpha=.45, label="До")
            _ax.hist(subset_after[_col], bins=np.linspace(0,1,27), histtype="step", color="#275841", linewidth=2,label="После")
            _ax.set(xlim=(0,1), title="Яркость" if _col=="brightness" else "Насыщенность",xlabel="Значение",ylabel="Количество")
            _ax.legend(frameon=False)
        else:
            _ax.boxplot([subset_before[_col],subset_after[_col]],vert=False,patch_artist=True,
                        tick_labels=["До","После"],widths=.45,
                        boxprops=dict(facecolor=_color, alpha=.6,edgecolor="#275841"),
                        medianprops=dict(color="#154f38",linewidth=2),
                        flierprops=dict(marker=".", markersize=2, markerfacecolor="#275841",markeredgecolor="#275841",alpha=.2))
            _ax.set(xlim=(0,1), title="Яркость" if _col=="brightness" else "Насыщенность",xlabel="Значение от 0 до 1")
        _ax.spines[["top","right"]].set_visible(False)
        _ax.grid(alpha=.1)
    _fig.tight_layout()
    _plot = plot_png(_fig)
    mo.Html(f"""
    <section class="cl cl-section" style="padding-top:12px">
      <div class="cl-comp">{''.join(_stats)}</div>
      <div class="cl-box" style="margin-top:15px"><img class="cl-chart" src="data:image/png;base64,{_plot}" alt="Графики выборки до и после обработки"></div>
      <p class="cl-grid-note">Эксперимент: n = {n} изображений. Одна фотография заменена обработанной; изменение средних может быть очень малым при большой выборке. Можно переключаться между гистограммами и boxplot; все показатели пересчитываются по выбранной выборке.</p>
    </section>""")
    return


@app.cell
def _(mo):
    mo.Html("""
    <section class="cl cl-section" id="experiment-relation">
      <div class="cl-head"><h2>Связь яркости и насыщенности</h2></div>
      <p class="cl-sub">Каждая точка на графике соответствует одной фотографии CIFAR-10. Наведи на неё курсор, чтобы узнать значения, или увеличь интересующую область.</p>
    </section>""")
    return


@app.cell
def _(mo, table):
    relation_count = mo.ui.slider(start=200, stop=10000, step=200, value=2000,
                                   label="Сколько изображений на графике", show_value=True)
    relation_view = mo.ui.dropdown(options=["Все данные", "Случайная выборка"],
                                   value="Случайная выборка", label="Режим просмотра")
    mo.vstack([mo.Html('<span class="cl-interactive-surface" aria-hidden="true"></span>'),
               mo.hstack([relation_view, relation_count], gap=2, justify="start", wrap=True)], gap=0).style(
        {"max-width":"1180px", "margin":"0 auto", "background":"transparent",
         "border-radius":"16px","padding":"17px 23px","color":"#244a49"})
    return relation_count, relation_view


@app.cell
def _(mo, np, table, go, relation_count, relation_view, sample_refresh):
    _amount = len(table) if relation_view.value == "Все данные" else int(relation_count.value)
    _rng = np.random.default_rng(704 + int(sample_refresh.value))
    _chosen = _rng.choice(len(table), size=_amount, replace=False)
    _part = table.iloc[_chosen]
    _fig = go.Figure(go.Scattergl(
        x=_part["brightness"], y=_part["saturation"], mode="markers",
        marker={"size": 6, "color": "#43865c", "opacity": .48,
                "line": {"width":0}},
        customdata=np.column_stack([_part.image_id.to_numpy()]),
        hovertemplate="Фото № %{customdata[0]}<br>Яркость: %{x:.3f}<br>Насыщенность: %{y:.3f}<extra></extra>",
        name="CIFAR-10"
    ))
    _fig.update_layout(template="plotly_white", height=445,
                       margin={"l":45,"r":20,"t":22,"b":43},
                       dragmode="zoom", paper_bgcolor="white",plot_bgcolor="white",
                       font={"family":"Arial Narrow,Arial,sans-serif","size":14,"color":"#2c5847"},
                       xaxis={"title":"Средняя яркость HSV V", "range":[0,1], "gridcolor":"#e8f0ea"},
                       yaxis={"title":"Средняя насыщенность HSV S", "range":[0,1], "gridcolor":"#e8f0ea"})
    relation_plot = mo.ui.plotly(_fig, config={"displaylogo": False, "responsive": True})
    mo.vstack([mo.Html('<span class="cl-interactive-surface" aria-hidden="true"></span>'), relation_plot,
               mo.md(f"**На графике:** {_amount:,} изображений. "
                     f"Корреляция Пирсона: **{_part.brightness.corr(_part.saturation):.4f}**. "
                     "Масштабируй колесом или прямоугольником; наведи на точку, чтобы увидеть её данные.")],
              gap=2).style({"max-width":"1180px","margin":"0 auto","padding":"18px",
                             "border-radius":"16px","background":"transparent","color":"#244a49"})
    return relation_plot,


@app.cell
def _(mo):
    mo.Html("""
    <section class="cl cl-section" id="generator">
      <div class="cl-head"><h2>Датчик случайных величин</h2></div>
      <p class="cl-sub">Здесь генерируются пары чисел: яркость и насыщенность. Это не новые фотографии. Можно сравнить два метода и посмотреть, насколько результаты похожи на исходный CIFAR-10.</p>
      <div class="cl-grid2">
        <div class="cl-box"><span class="cl-tag">Парный эмпирический</span>
          <p>Генерируем U от 0 до 1 и выбираем изображение с номером ⌊10 000U⌋. Берём его реальные яркость и насыщенность. Такой метод воспроизводит их совместное эмпирическое распределение и сохраняет зависимость.</p></div>
        <div class="cl-box"><span class="cl-tag">Независимые теоретические модели</span>
          <p>Яркость получаем по обратной функции распределения нормальной модели с ограничением 0–1; насыщенность, из смеси нуля и бета-модели. Два независимых числа U не сохраняют связь между характеристиками, это важное ограничение модели.</p></div>
      </div>
    </section>""")
    return


@app.cell
def _(mo):
    generator_method = mo.ui.dropdown(
        options=["Парный эмпирический", "Независимые теоретические модели"],
        value="Парный эмпирический", label="Метод генерации")
    generator_count = mo.ui.slider(start=100, stop=5000, step=100, value=1000,
                                   label="Количество случайных пар", show_value=True)
    generator_rng = mo.ui.dropdown(options=["NumPy PCG64", "Park–Miller (ЛКГ)", "RANDU (исторический)"],
                                   value="NumPy PCG64", label="Базовый датчик U(0,1)")
    generator_refresh = mo.ui.button(label="Сгенерировать заново", value=0,
                                     on_click=lambda value: value + 1)
    mo.vstack([
        mo.Html('<span class="cl-interactive-surface" aria-hidden="true"></span>'),
        mo.hstack([generator_method, generator_rng], gap=2, justify="start", wrap=True),
        mo.hstack([generator_count, generator_refresh], gap=2, justify="start", wrap=True)
    ], gap=3).style({"max-width":"1180px","margin":"0 auto",
              "background":"transparent","color":"#264a42","border-radius":"18px","padding":"22px"})
    return generator_method, generator_count, generator_rng, generator_refresh


@app.cell
def _(mo, np, plt, stats, table, plot_png, num, generator_method, generator_count, generator_rng, generator_refresh):
    _rng = np.random.default_rng(852 + int(generator_refresh.value))
    _n = int(generator_count.value)
    _pop = table[["brightness","saturation"]].to_numpy()
    if generator_rng.value == "NumPy PCG64":
        _uniform = _rng.random(2 * _n)
    else:
        _modulus = (2**31 - 1) if generator_rng.value == "Park–Miller (ЛКГ)" else 2**31
        _factor = 16807 if generator_rng.value == "Park–Miller (ЛКГ)" else 65539
        _state = (2026 + int(generator_refresh.value)) % _modulus
        _state = max(_state, 1)
        _uniform = np.empty(2 * _n, dtype=np.float64)
        for _i in range(2 * _n):
            _state = (_factor * _state) % _modulus
            _uniform[_i] = _state / _modulus
    _u1 = _uniform[:_n]
    _u2 = _uniform[_n:]
    _u_ks = stats.kstest(_uniform, "uniform").statistic
    if generator_method.value == "Парный эмпирический":
        _indices = np.minimum((_u1 * len(_pop)).astype(int), len(_pop)-1)
        _g = _pop[_indices]
    else:
        _mu, _sd = stats.norm.fit(_pop[:,0])
        _low, _high = (0-_mu)/_sd, (1-_mu)/_sd
        _gb = stats.truncnorm.ppf(np.clip(_u1,1e-10,1-1e-10), _low, _high, loc=_mu, scale=_sd)
        _positive = _pop[_pop[:,1]>0,1]
        _a,_b,_,_ = stats.beta.fit(_positive,floc=0,fscale=1)
        _pzero = 1 - len(_positive)/len(_pop)
        _gs = np.zeros(_n)
        _mask = _u2 > _pzero
        _q = np.clip((_u2[_mask]-_pzero)/(1-_pzero), 1e-10, 1-1e-10)
        _gs[_mask] = stats.beta.ppf(_q, _a, _b)
        _g = np.column_stack([_gb,_gs])
    _corr = float(np.corrcoef(_g[:,0],_g[:,1])[0,1])
    _ks_b = stats.ks_2samp(_g[:,0],_pop[:,0]).statistic
    _ks_s = stats.ks_2samp(_g[:,1],_pop[:,1]).statistic
    _fig,_axes=plt.subplots(1,3,figsize=(12,3.2),facecolor="white")
    for _axis,_j,_color,_name in zip(_axes[:2],[0,1],["#e3b847","#6da97c"],["Яркость","Насыщенность"]):
        _axis.hist(_pop[:,_j],bins=np.linspace(0,1,31),density=True,alpha=.30,
                   color="#98b0a9",label="CIFAR-10")
        _axis.hist(_g[:,_j],bins=np.linspace(0,1,31),density=True,histtype="step",
                   linewidth=2.2,color=_color,label="Генератор")
        _axis.set(xlim=(0,1),title=_name,xlabel="Значение HSV",ylabel="Плотность")
        _axis.grid(alpha=.12);_axis.legend(fontsize=7,frameon=False)
        _axis.spines[["top","right"]].set_visible(False)
    _axes[2].scatter(_g[:,0],_g[:,1],s=5,alpha=.17,c="#398b59")
    _axes[2].set(title="Сгенерированные пары",xlabel="Яркость",ylabel="Насыщенность",xlim=(0,1),ylim=(0,1))
    _axes[2].grid(alpha=.12);_axes[2].spines[["top","right"]].set_visible(False)
    _fig.tight_layout()
    _plot=plot_png(_fig)
    mo.Html(f"""
    <section class="cl cl-section" style="padding-top:10px">
      <div class="cl-box"><img class="cl-chart" src="data:image/png;base64,{_plot}" alt="Гистограммы и диаграмма сгенерированных значений"></div>
      <div class="cl-grid3" style="margin-top:16px">
         <div class="cl-box"><span class="cl-tag">Корреляция генератора</span><p class="cl-reading-number">{num(_corr)}</p><p>В оригинале: −0,1889</p></div>
         <div class="cl-box"><span class="cl-tag">Расстояние KS яркости</span><p class="cl-reading-number">{num(_ks_b)}</p><p>Между сгенерированными и исходными данными</p></div>
         <div class="cl-box"><span class="cl-tag">Расстояние KS насыщенности</span><p class="cl-reading-number">{num(_ks_s)}</p><p>Чем ближе к нулю, тем ближе эмпирические функции распределения</p></div>
      </div>
      <p class="cl-grid-note">Базовый датчик: <b>{generator_rng.value}</b> · KS от U(0,1): <b>{num(_u_ks)}</b> для {2*_n} чисел. Генератор использует воспроизводимое начальное состояние, по кнопке создаёт новую последовательность. KS помогает сравнить распределения, но по одному этому числу нельзя оценить качество генератора полностью. RANDU здесь оставлен для сравнения как исторический пример с известными недостатками.</p>
    </section>""")
    return



if __name__ == "__main__":
    app.run()

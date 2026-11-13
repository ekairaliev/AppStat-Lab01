import marimo

__generated_with = "0.18.0"
app = marimo.App(width="full", css_file="colorlab.css")


@app.cell
def _():
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

    root = Path(__file__).resolve().parent
    csv_path = root / "data" / "photo_color_data.csv"
    photos_path = root / "data" / "cifar10_photos.zip"
    asset_dir = root / "assets"
    if not csv_path.is_file() or not photos_path.is_file():
        raise FileNotFoundError("Нет данных: проверьте файлы в папке data")
    table = pd.read_csv(csv_path).sort_values("image_id").reset_index(drop=True)
    if len(table) != 10000 or table[["image_id", "brightness", "saturation"]].isna().any().any():
        raise ValueError("CSV: ожидаются 10 000 строк без пропусков")
    if not {"image_id", "brightness", "saturation"}.issubset(table.columns):
        raise ValueError("CSV должен содержать image_id, brightness, saturation")
    with zipfile.ZipFile(photos_path) as _archive:
        ids = sorted(int(Path(_name).stem) for _name in _archive.namelist()
                     if _name.startswith("photos/") and _name.endswith(".png"))
    if not ids:
        raise ValueError("В ZIP не найдены изображения")

    def asset_base64(name):
        return base64.b64encode((asset_dir / name).read_bytes()).decode("ascii")

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

    texture = asset_base64("texture.jpg")
    wing = asset_base64("wing.svg")
    flower = asset_base64("flower.svg")
    divider = asset_base64("divider.svg")
    return (mo, np, plt, stats, go, Image, zipfile, io, rgb_to_hsv, hsv_to_rgb,
            table, photos_path, ids, image_png, plot_png, num,
            texture, wing, flower, divider)


@app.cell
def _(mo, texture, wing, flower, divider):
    mo.Html(f"""
    <header class="cl cl-hero" id="top">
      <nav class="cl-nav"><div class="cl-logo"><img src="data:image/svg+xml;base64,{wing}"><img src="data:image/svg+xml;base64,{wing}"></div>
       <div class="cl-navlinks"><a href="#top">Проект</a><a href="#data">Данные</a>
       <a href="#results">Результаты</a><a href="#interactive">Интерактив</a><a href="#conclusion">Вывод</a></div>
       <a class="gh" href="https://github.com/ekairaliev/AppStat-Lab01" target="_blank">GitHub ↗</a></nav>
      <h1>Яркость и насыщенность цифровых изображений</h1>
      <div class="cl-hero-grid">
       <div class="cl-hero-art"><img class="texture" src="data:image/jpeg;base64,{texture}">
         <img class="leftwing" src="data:image/svg+xml;base64,{wing}">
         <img class="rightwing" src="data:image/svg+xml;base64,{wing}"></div>
       <div class="cl-hero-copy"><div class="cl-ribbon">Интерактивное статистическое исследование на основе CIFAR-10</div>
         <p>Как связаны яркость и насыщенность фотографий?</p>
         <p>Можно ли описать их с помощью математических распределений?</p>
         <p>Насколько точно небольшая выборка отражает весь набор?</p>
         <p>Я взяла 10 000 изображений, посчитала их цветовые характеристики, сравнила распределения и проверила, связаны ли яркость с насыщенностью.</p>
       </div>
      </div>
      <div class="cl-divider"></div>
      <div class="cl-statement">У каждого изображения есть три цветовых канала RGB. Для анализа я преобразовала их в HSV, чтобы отдельно рассматривать цветовой тон, насыщенность и яркость.
        <img class="flower" src="data:image/svg+xml;base64,{flower}" alt=""></div>
    </header>
    """)
    return


@app.cell
def _(mo):
    mo.Html("""
    <section class="cl cl-section" id="data">
      <div class="cl-head"><h2>Что исследуется</h2></div>
      <div class="cl-grid3">
        <div class="cl-box"><div class="cl-infokey">▱</div><span class="cl-tag">Датасет</span>
          <p>10 000 тестовых изображений CIFAR-10, размером 32 × 32 пикселя.</p></div>
        <div class="cl-box"><div class="cl-infokey">☷</div><span class="cl-tag">Переменные</span>
          <p>Средняя яркость HSV V и средняя насыщенность HSV S. Каждая, в диапазоне 0–1.</p></div>
        <div class="cl-box"><div class="cl-infokey">◎</div><span class="cl-tag">Цель</span>
          <p>Изучить распределения, зависимость и точность оценок по выборкам.</p></div>
      </div>
      <p class="cl-grid-note">Если случайно выбрать фотографию, заранее неизвестно, какой у неё будет средняя яркость или насыщенность. Обе величины берутся из одних и тех же пикселей, поэтому я отдельно проверяю, есть ли между ними связь.</p>
      <div class="cl-formula-grid">
        <div class="cl-formula-card"><span>Средняя яркость X</span><div class="cl-formula">X = (V₁ + V₂ + … + V₁₀₂₄) / 1024</div><small>Среднее значение HSV V по 1024 пикселям</small></div>
        <div class="cl-formula-card"><span>Средняя насыщенность Y</span><div class="cl-formula">Y = (S₁ + S₂ + … + S₁₀₂₄) / 1024</div><small>Среднее значение HSV S по 1024 пикселям</small></div>
      </div>
    </section>""")
    return


@app.cell
def _(mo, table, num):
    _mean_b = float(table.brightness.mean())
    _mean_s = float(table.saturation.mean())
    _pearson = float(table.brightness.corr(table.saturation))
    _spearman = float(table.brightness.corr(table.saturation, method="spearman"))
    _zero = int((table.saturation == 0).sum())
    _metric_list = [
        ("Средняя<br>яркость", num(_mean_b)),
        ("Средняя<br>насыщенность", num(_mean_s)),
        ("Корреляция<br>Пирсона", num(_pearson)),
        ("Корреляция<br>Спирмена", num(_spearman)),
        ("p-value<br>перестановочного теста", "0,0005"),
        ("Нулевых значений<br>насыщенности", f"{_zero} (1,06%)"),
    ]
    _cards = "".join(f'<div class="cl-metric"><div class="cl-metric-label">{_label}</div><span class="cl-metric-value">{_value}</span></div>' for _label, _value in _metric_list)
    mo.Html(f"""
    <section class="cl cl-section" id="results">
       <div class="cl-head"><h2>Основные результаты</h2></div>
       <div class="cl-metrics">{_cards}</div>
       <p class="cl-grid-note">Медиана яркости, 0,5370, стандартное отклонение, 0,1279; медиана насыщенности, 0,2539, стандартное отклонение, 0,1403.</p>
    </section>""")
    return




@app.cell
def _(mo):
    mo.Html('<section class="cl cl-section cl-conclusions-inset"><details class="cl-verbatim"><summary><span>Вывод по исследованию</span><strong>Описательная статистика</strong><span class="cl-expand-icon" aria-hidden="true">+</span></summary><div class="cl-verbatim-body"><p>Я рассчитала основные статистические характеристики для 10 000 изображений CIFAR-10.</p>\n<ol>\n<li><p>Средняя яркость составила <mark class="cl-key cl-key-yellow">0,5427</mark>, а средняя насыщенность <mark class="cl-key cl-key-green">0,2725</mark>. Получается, что изображения в среднем имеют умеренную яркость, но насыщенность цветов заметно ниже.</p>\n</li>\n<li><p>Стандартное отклонение насыщенности 0,1403 немного больше, чем у яркости 0,1279. Это говорит о том, что насыщенность сильнее изменяется относительно своего среднего значения в абсолютных единицах шкалы HSV.</p>\n</li>\n<li><p>Также я заметила, что у обеих величин среднее немного больше медианы. Особенно это заметно у насыщенности, поэтому можно предположить, что её распределение имеет правостороннюю асимметрию но еще не факт, поэтому следующим шагом построю гистограммы распределений.</p>\n</li>\n</ol>\n</div></details></section>')
    return

@app.cell
def _(np, plt, table, plot_png, mo, num):
    _bright = table.brightness.to_numpy()
    _saturated = table.saturation.to_numpy()
    _fig, _axs = plt.subplots(1, 2, figsize=(10.5, 3.0), facecolor="white")
    for _ax, _values, _color, _name in zip(
        _axs, (_bright, _saturated), ("#d4b441", "#6ca478"), ("Яркость", "Насыщенность")
    ):
        _ax.boxplot(_values, vert=False, patch_artist=True, widths=.38,
                    boxprops=dict(facecolor=_color, edgecolor="#376c56", alpha=.65),
                    medianprops=dict(color="#244a3d",linewidth=2),
                    flierprops=dict(marker=".",markersize=3,alpha=.18,
                                    markerfacecolor="#376c56",markeredgecolor="#376c56"))
        _ax.set(xlim=(0,1), xlabel="Значение от 0 до 1", title=_name)
        _ax.set_yticks([])
        _ax.spines[["top", "right", "left"]].set_visible(False)
        _ax.grid(axis="x",alpha=.12)
    _fig.tight_layout()
    _plot = plot_png(_fig)
    _bq = np.quantile(_bright,[.25,.75])
    _sq = np.quantile(_saturated,[.25,.75])
    mo.Html(f"""
    <section class="cl cl-section" id="eda">
       <div class="cl-head"><h2>Разброс и выбросы</h2></div>
       <div class="cl-box"><img class="cl-chart" src="data:image/png;base64,{_plot}" alt="Диаграммы размаха яркости и насыщенности"></div>
       <p class="cl-grid-note">Квартильные интервалы по данным: яркость, {num(_bq[0],3)}–{num(_bq[1],3)}, насыщенность, {num(_sq[0],3)}–{num(_sq[1],3)}.</p>
    </section>""")
    return




@app.cell
def _(mo):
    mo.Html('<section class="cl cl-section cl-conclusions-inset"><details class="cl-verbatim"><summary><span>Вывод по исследованию</span><strong>Диаграммы размаха</strong><span class="cl-expand-icon" aria-hidden="true">+</span></summary><div class="cl-verbatim-body"><p>Яркость (розовый): основная половина значений находится примерно между 0,46 и 0,62. Медиана составляет 0,537. Есть потенциальные выбросы как среди очень тёмных, так и среди очень светлых изображений.</p>\n<p>Насыщенность (голубой): основная половина значений находится между 0,17 и 0,36. Медиана равна 0,254. Особенно хорошо заметны потенциальные выбросы с высокой насыщенностью. При этом среднее расположено выше медианы, что согласуется с предположением о правосторонней асимметрии.</p>\n</div></details></section>')
    return

@app.cell
def _(np, plt, stats, table, plot_png, mo, num):
    _brightness = table.brightness.to_numpy()
    _positive = table.loc[table.saturation > 0, "saturation"].to_numpy()
    _mu, _sigma = stats.norm.fit(_brightness)
    _alpha, _beta, _, _ = stats.beta.fit(_positive, floc=0, fscale=1)
    _xs = np.linspace(0.001, .999, 320)
    _model_cards = []
    for _values, _color, _label, _density, _note in [
        (_brightness, "#D4B441", "Яркость, нормальная модель",
         stats.norm.pdf(_xs, _mu, _sigma), "Форма близка к симметричной. KS = 0,02295; AIC = −12 747,89."),
        (_positive, "#6CA478", "Насыщенность, бета-модель",
         stats.beta.pdf(_xs, _alpha, _beta), "Для 9894 положительных значений: a = 2,6313; b = 6,8900. KS = 0,01953; AIC = −12 116,20.")
    ]:
        _fig, _ax = plt.subplots(figsize=(6.8,3.1), facecolor="white")
        _ax.set_facecolor("white")
        _ax.hist(_values, bins=35, density=True, color=_color, alpha=.55, edgecolor="white", linewidth=.35)
        _ax.plot(_xs, _density, color="#356d54", linewidth=2.2)
        _ax.set(xlim=(0,1), xlabel="Значение от 0 до 1", ylabel="Плотность")
        _ax.spines[["top","right"]].set_visible(False)
        _ax.grid(alpha=.1)
        _fig.tight_layout()
        _img = plot_png(_fig)
        _model_cards.append(f'<div class="cl-box"><div class="cl-photo-title">{_label}</div><img class="cl-chart" src="data:image/png;base64,{_img}" alt="{_label}"><p class="cl-result-note">{_note}</p></div>')
    mo.Html(f"""
    <section class="cl cl-section" id="distributions">
      <div class="cl-head"><h2>Распределения</h2></div>
      <div class="cl-grid2">{''.join(_model_cards)}</div>
      <div class="cl-math-legend"><strong>Как читать параметры бета-модели</strong>
        <div><span class="cl-math-badge"><i>a</i> = 2,6313</span><span class="cl-math-badge"><i>b</i> = 6,8900</span></div>
        <p>Числа <i>a</i> и <i>b</i> задают форму кривой бета-распределения. Это параметры модели, подобранные по 9894 изображениям с положительной насыщенностью, а не значения конкретной фотографии.</p>
      </div>
      <p class="cl-grid-note">Сравнение AIC выполнено отдельно для яркости на 10 000 значениях и для положительной насыщенности на 9894 значениях; 106 нулей учитываются отдельно.</p>
    </section>""")
    return




@app.cell
def _(mo):
    mo.Html('<section class="cl cl-section cl-conclusions-inset"><details class="cl-verbatim"><summary><span>Вывод по исследованию</span><strong>Предварительное сравнение моделей</strong><span class="cl-expand-icon" aria-hidden="true">+</span></summary><div class="cl-verbatim-body"><p>Для яркости нормальное распределение визуально подходит достаточно хорошо, поскольку гистограмма имеет почти симметричную колоколообразную форму. Бета-распределение также близко к данным.</p>\n<p>Для насыщенности ситуация другая. Гистограмма имеет заметную правостороннюю асимметрию, поэтому нормальное распределение описывает её хуже. Бета-распределение лучше учитывает форму распределения, хотя тоже не полностью совпадает с гистограммой.</p>\n<p>Равномерное распределение не подходит ни для одной из величин, поскольку значения распределены по диапазону неравномерно.</p>\n<p>Пока это только визуальное сравнение. Чтобы выбрать более подходящую модель, необходимо дополнительно сравнить численные показатели и проверить качество соответствия распределений данным, что я и сделаю далее.</p>\n</div></details><details class="cl-verbatim"><summary><span>Вывод по исследованию</span><strong>Сравнение моделей по AIC</strong><span class="cl-expand-icon" aria-hidden="true">+</span></summary><div class="cl-verbatim-body"><p>Я сравнила нормальное, бета- и равномерное распределения с помощью критерия AIC. Чем меньше значение AIC, тем предпочтительнее модель среди рассмотренных вариантов при сравнении на одинаковых данных.</p>\n<p>Для яркости наименьшее значение AIC получилось у нормального распределения −12747,89. Поэтому именно его я выбрала для приближённого описания яркости изображений.</p>\n<p>Для положительной насыщенности наименьшее значение AIC получилось у бета-распределения −12116,20. Оно оказалось предпочтительнее нормального и равномерного распределений.</p>\n<p>При этом среди 10 000 изображений нашлось 106 с нулевой насыщенностью. Поэтому для полного описания насыщенности я использовала смешанную модель, то есть вероятность нулевого значения составляет <mark class="cl-key cl-key-green">1,06%</mark>, а остальные значения описываются <mark class="cl-key cl-key-green">бета-распределением</mark>.</p>\n<p>Полученные модели не являются точным описанием данных, но позволяют достаточно хорошо приблизить их распределения. Дополнительно я проверила их с помощью Q–Q графиков и статистики Колмогорова и Смирнова.</p>\n</div></details><details class="cl-verbatim"><summary><span>Вывод по исследованию</span><strong>Бета-модель насыщенности</strong><span class="cl-expand-icon" aria-hidden="true">+</span></summary><div class="cl-verbatim-body"><p>Для <mark class="cl-key cl-key-green">9 894 изображений</mark> с положительной насыщенностью я подобрала бета-распределение.</p>\n<p>В результате я получила следующие параметры бета-распределения:</p>\n<ul>\n<li>Параметр <span class="cl-math-inline"><i>a</i> = 2,6313</span></li>\n<li>Параметр <span class="cl-math-inline"><i>b</i> = 6,8900</span></li>\n</ul>\n<p>По графику видно, что полученная кривая достаточно близко повторяет форму гистограммы. Максимум находится примерно в области 0,2–0,3, после чего плотность постепенно уменьшается. При этом кривая не полностью совпадает с данными, особенно в области самых распространённых значений. Поэтому я рассматриваю бета-распределение как приближённую модель, а не как точное описание. Для всех 10 000 изображений отдельно учитывается вероятность нулевой насыщенности, <mark class="cl-key cl-key-green">1,06%</mark>. Это позволяет сохранить реальные значения данных и описать распределение намного корректнее.</p>\n</div></details></section>')
    return

@app.cell
def _(np, plt, stats, table, plot_png, mo):
    _x = table.brightness.to_numpy()
    _y = table.saturation.to_numpy()
    _positive = _y[_y > 0]
    _mu, _sd = stats.norm.fit(_x)
    _a, _b, _, _ = stats.beta.fit(_positive, floc=0, fscale=1)
    _fig, _ax = plt.subplots(figsize=(6.4,3.4), facecolor="white")
    _ax.set_facecolor("white")
    _heat = _ax.hexbin(_x,_y,gridsize=38,extent=(0,1,0,1),mincnt=1,cmap="YlGn")
    _ax.set(xlabel="Яркость",ylabel="Насыщенность",xlim=(0,1),ylim=(0,1))
    _ax.spines[["top","right"]].set_visible(False)
    _fig.colorbar(_heat,ax=_ax,label="Число изображений",fraction=.04)
    _fig.tight_layout()
    _scatter = plot_png(_fig)
    _fig2,_axs=plt.subplots(1,2,figsize=(7.1,3.0),facecolor="white")
    for _vals,_ppf,_axis,_accent in [
        (_x,stats.norm.ppf,_axs[0],"#d4b441"),
        (_positive,stats.beta.ppf,_axs[1],"#6ca478")
    ]:
        _prob=(np.arange(len(_vals))+.5)/len(_vals)
        _theory=(_ppf(_prob,_mu,_sd) if _axis==_axs[0] else _ppf(_prob,_a,_b))
        _axis.scatter(_theory,np.sort(_vals),s=1,alpha=.25,color=_accent)
        _axis.plot([0,1],[0,1],color="#315d48",lw=1.2,linestyle="--")
        _axis.set(xlim=(0,1),ylim=(0,1),xlabel="Теоретические",ylabel="Эмпирические")
        _axis.spines[["top","right"]].set_visible(False)
    _axs[0].set_title("Яркость",fontsize=12)
    _axs[1].set_title("Насыщенность > 0",fontsize=12)
    _fig2.tight_layout()
    _qq=plot_png(_fig2)
    mo.Html(f"""
    <section class="cl cl-section" id="dependence">
       <div class="cl-head"><h2>Проверка моделей и зависимости</h2></div>
       <div class="cl-grid2">
         <div class="cl-box"><div class="cl-photo-title">Связь двух характеристик</div>
           <img class="cl-chart" src="data:image/png;base64,{_scatter}" alt="Диаграмма плотности корреляции">
           <p class="cl-result-note">Коэффициент Пирсона: −0,1889; Спирмена: −0,1904.</p></div>
         <div class="cl-box"><div class="cl-photo-title">Q–Q графики моделей</div>
           <img class="cl-chart" src="data:image/png;base64,{_qq}" alt="Q-Q сравнение с теоретическими моделями">
           <p class="cl-result-note">KS яркости: 0,02295; KS положительной насыщенности: 0,01953.</p></div>
       </div>

    </section>""")
    return




@app.cell
def _(mo):
    mo.Html('<section class="cl cl-section cl-conclusions-inset"><details class="cl-verbatim"><summary><span>Вывод по исследованию</span><strong>Проверка гипотезы</strong><span class="cl-expand-icon" aria-hidden="true">+</span></summary><div class="cl-verbatim-body"><p>Как я и говорила ранее, для проверки независимости яркости и насыщенности я провела перестановочный тест на основе коэффициента корреляции Пирсона.</p>\n<p>Наблюдаемая корреляция составила <mark class="cl-key cl-key-green">−0,1889</mark>. После 2000 случайных перестановок получилось p-value ≈ <mark class="cl-key cl-key-green">0,0005</mark>.</p>\n<p>Поскольку полученное значение меньше выбранного уровня значимости 0,05, <mark class="cl-key cl-key-green">нулевая гипотеза о независимости отвергается</mark>.</p>\n<p>Таким образом, в исследуемом наборе изображений обнаружена <mark class="cl-key cl-key-green">статистически значимая отрицательная корреляция</mark> между яркостью и насыщенностью. При этом сама связь слабая, так как коэффициент корреляции близок к нулю. Это означает, что по одной только яркости нельзя достаточно точно определить насыщенность фотографии. Я также учитываю, что перестановочный тест с коэффициентом Пирсона в первую очередь чувствителен к линейной связи, поэтому его результат не описывает все возможные формы зависимости.</p>\n</div></details><details class="cl-verbatim"><summary><span>Вывод по исследованию</span><strong>Проверка распределений (Q–Q и KS)</strong><span class="cl-expand-icon" aria-hidden="true">+</span></summary><div class="cl-verbatim-body"><p>Для яркости статистика KS составила 0,02295. На графике большая часть точек находится близко к диагонали, но на краях есть небольшие отклонения. Поэтому нормальное распределение можно использовать как приближённую модель яркости.</p>\n<p>Для положительной насыщенности статистика KS составила 0,01953. Бета-распределение тоже достаточно близко описывает данные, но в области высоких значений насыщенности заметны расхождения с теоретической кривой. При этом для насыщенности я отдельно учитываю 106 нулевых значений, которые не входят в стандартную бета-модель.</p>\n<p>Таким образом, обе модели подходят для приближённого описания формы данных, но не полностью совпадают с реальными распределениями. По этим результатам нельзя утверждать, что данные точно следуют выбранным теоретическим законам.</p>\n</div></details></section>')
    return

@app.cell
def _(mo):
    mo.Html("""
    <section class="cl cl-section" id="interactive">
       <div class="cl-head"><h2>Интерактив</h2></div>
       <p class="cl-sub">Выбери фотографию, попробуй сделать её светлее или насыщеннее. Посмотри на значения до и после, а затем на статистику выборки. Здесь меняются сами пиксели изображения.</p>
    </section>""")
    return


@app.cell
def _(mo, ids, table):
    photo_items = [f"Фото № {_i}" for _i in ids]
    photo_select = mo.ui.dropdown(options=photo_items, value=photo_items[0], label="Фотография")
    brightness_ui = mo.ui.slider(start=.2, stop=2.0, step=.1, value=1.0,
                                 label="🟡 Яркость ×", show_value=True)
    saturation_ui = mo.ui.slider(start=0.0, stop=2.0, step=.1, value=1.0,
                                 label="🟢 Насыщенность ×", show_value=True)
    size_ui = mo.ui.slider(start=100, stop=len(table), step=100, value=1000,
                           label="Размер выборки", show_value=True)
    sampling_ui = mo.ui.radio(options=["Без возвращения", "С возвращением"],
                              value="Без возвращения", label="Отбор")
    sample_refresh = mo.ui.button(label="↻ Новая случайная выборка", value=0,
                                  on_click=lambda value: value + 1)
    chart_ui = mo.ui.radio(options=["Гистограммы", "Диаграммы размаха"],
                            value="Гистограммы", label="Вид графика")
    mo.vstack([
        mo.Html('<span class="cl-controls-marker cl-interactive-surface" aria-hidden="true"></span>'),
        mo.hstack([photo_select, size_ui], justify="start", gap=3),
        mo.hstack([brightness_ui, saturation_ui], justify="start", gap=3),
        mo.hstack([sampling_ui, chart_ui], justify="start", gap=4),
        sample_refresh,
        mo.md("*Множитель 1,0, исходное изображение. При анализе выборки изменяется одна выбранная фотография; остальные остаются исходными.*"),
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
             <span class="cl-photo-cap">🟡 Яркость {num(b0,3)} · 🟢 Насыщенность {num(s0,3)}</span></div>
          <div class="cl-photo-box"><div class="cl-photo-title">После изменения</div>
             <img src="data:image/png;base64,{altered_b64}" alt="Фотография после изменения HSV">
             <span class="cl-photo-cap">🟡 Яркость {num(b1,3)} · 🟢 Насыщенность {num(s1,3)}</span></div>
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
def _(np, table, mo, num):
    _z = (table[["brightness","saturation"]] - table[["brightness","saturation"]].mean()) / table[["brightness","saturation"]].std(ddof=0)
    _m_b = float(_z.brightness.mean())
    _m_s = float(_z.saturation.mean())
    _std_b = float(_z.brightness.std(ddof=0))
    _std_s = float(_z.saturation.std(ddof=0))
    mo.Html(f"""
    <section class="cl cl-section" id="standardization">
      <div class="cl-head"><h2>Стандартизация</h2></div>
      <div class="cl-grid2">
        <div class="cl-box"><span class="cl-tag">Метод</span>
           <div class="cl-formula" style="font-size:27px">Z = (x − μ) / σ</div><p>Здесь x это значение изображения, μ это среднее по всему набору, σ это стандартное отклонение. Формула показывает, насколько значение отклоняется от среднего в единицах стандартного отклонения.</p></div>
        <div class="cl-box"><span class="cl-tag">Результат</span>
           <p>Средние Z: {num(_m_b,3)} и {num(_m_s,3)}; стандартные отклонения: {num(_std_b,2)} и {num(_std_s,2)}.</p></div>
      </div>
    </section>""")
    return




@app.cell
def _(mo):
    mo.Html('<section class="cl cl-section cl-conclusions-inset"><details class="cl-verbatim"><summary><span>Вывод по исследованию</span><strong>Стандартизация</strong><span class="cl-expand-icon" aria-hidden="true">+</span></summary><div class="cl-verbatim-body"><p>До преобразования средняя яркость составляла <mark class="cl-key cl-key-yellow">0,5427</mark>, а средняя насыщенность <mark class="cl-key cl-key-green">0,2725</mark>. После стандартизации <mark class="cl-key cl-key-green">средние значения обеих величин стали практически равны нулю</mark>, а <mark class="cl-key cl-key-green">стандартные отклонения единице</mark>.</p>\n<p>Стандартизация выполнена правильно. Теперь можно сравнивать, насколько отдельные изображения отличаются от среднего значения по каждой характеристике. При этом исходные данные я сохранила, поскольку стандартизация изменяет масштаб значений, но не делает распределение нормальным.</p>\n</div></details></section>')
    return

@app.cell
def _(mo):
    mo.Html("""
    <section class="cl cl-section" id="sampling">
       <div class="cl-head"><h2>Выборки и точность</h2></div>
       <p class="cl-sub">Я сравнила отбор с возвращением и без него. Для каждого размера выборки от 50 до 5000 фотографий повторила эксперимент 300 раз. На графиках ниже показана средняя ошибка оценок (RMSE).</p>
    </section>""")
    return




@app.cell
def _(mo):
    mo.Html('<section class="cl cl-section cl-conclusions-inset"><details class="cl-verbatim"><summary><span>Вывод по исследованию</span><strong>Сравнение выборок</strong><span class="cl-expand-icon" aria-hidden="true">+</span></summary><div class="cl-verbatim-body"><p>В качестве ориентиров взяла характеристики всех 10 000 изображений: среднюю яркость <mark class="cl-key cl-key-yellow">0,5427</mark> и среднюю насыщенность <mark class="cl-key cl-key-green">0,2725</mark>.</p>\n<p>По таблице видно, что полученные выборочные средние в целом близки к характеристикам всей совокупности. Особенно небольшие отклонения получились для выборок по 1000 изображений.</p>\n<p>Однако я заметила, что при увеличении размера выборки результат не всегда становится точнее. Например, средняя яркость для 500 изображений с возвращением оказалась дальше от среднего, чем для 100 изображений.</p>\n<p>Это объясняется случайностью отбора. Поэтому по одному эксперименту нельзя уверенно определить, какой способ лучше и как меняется точность оценок. Чтобы проверить это, дальше я проведу многократный отбор выборок и сравню средние ошибки оценивания.</p>\n</div></details></section>')
    return

@app.cell
def _(np, plt, plot_png, table, mo):
    _population = table[["brightness","saturation"]].to_numpy()
    _sizes = [50,100,250,500,1000,2000,5000]
    _truth_mean = _population.mean(axis=0)
    _truth_var = _population.var(axis=0,ddof=0)
    _errors = np.zeros((2,2,2,len(_sizes)))
    _rng = np.random.default_rng(42)
    for _method, _replace in enumerate((False,True)):
        for _index,_size in enumerate(_sizes):
            _sample_means=[]
            _sample_vars=[]
            for _iteration in range(300):
                _chosen = _rng.choice(len(_population),size=_size,replace=_replace)
                _v = _population[_chosen]
                _sample_means.append(_v.mean(axis=0))
                _sample_vars.append(_v.var(axis=0,ddof=1))
            _errors[0,_method,:,_index] = np.sqrt(np.mean((np.asarray(_sample_means)-_truth_mean)**2,axis=0))
            _errors[1,_method,:,_index] = np.sqrt(np.mean((np.asarray(_sample_vars)-_truth_var)**2,axis=0))
    _fig,_axs = plt.subplots(1,2,figsize=(11.5,3.6),facecolor="white")
    for _metric,_ax in enumerate(_axs):
        for _feature,_color in ((0,"#d4b441"),(1,"#6ca478")):
            for _method,_style in ((0,"-"),(1,"--")):
                _ax.plot(_sizes,_errors[_metric,_method,_feature,:],_style,marker="o",markersize=3,
                         color=_color,linewidth=1.8,label=("Яркость" if _feature==0 else "Насыщенность")+(", без возвращения" if _method==0 else ", с возвращением"))
        _ax.set(title="RMSE среднего" if _metric==0 else "RMSE дисперсии",xlabel="Размер выборки",ylabel="Ошибка")
        _ax.spines[["top","right"]].set_visible(False)
        _ax.grid(alpha=.13)
        _ax.legend(fontsize=7,frameon=False)
    _fig.tight_layout()
    _plot = plot_png(_fig)
    mo.Html(f"""
    <section class="cl cl-section" style="padding-top:4px">
      <div class="cl-box"><img class="cl-chart" src="data:image/png;base64,{_plot}" alt="RMSE среднего и дисперсии при росте выборок"></div>
      <p class="cl-grid-note">RMSE рассчитана для выборочных средних и дисперсий: 300 повторений на каждый размер и способ отбора.</p>
    </section>""")
    return




@app.cell
def _(mo):
    mo.Html('<section class="cl cl-section cl-conclusions-inset"><details class="cl-verbatim"><summary><span>Вывод по исследованию</span><strong>Состоятельность оценок</strong><span class="cl-expand-icon" aria-hidden="true">+</span></summary><div class="cl-verbatim-body"><p>Я провела по 300 случайных экспериментов для каждого размера выборки и сравнила их.</p>\n<p>Первый график-ошибка оценки среднего. При увеличении выборки с 50 до 5000 изображений RMSE уменьшается как для яркости, так и для насыщенности. Значит, при большем количестве наблюдений выборочные средние обычно оказываются ближе к средним всей совокупности.</p>\n<p>Второй график-ошибка оценки дисперсии. Здесь наблюдаем такую же закономерность. Чем больше изображений берём, тем точнее оцениваем разброс яркости и насыщенности.</p>\n<p>Также на больших выборках сплошные линии чаще расположены ниже пунктирных. Это показывает преимущество отбора без возвращения. При небольших выборках разница может быть совсем маленькой.</p>\n<p>Таким образом, эксперимент показывает, что <mark class="cl-key cl-key-green">увеличение размера выборки повышает точность оценок</mark> среднего и дисперсии. Полученные результаты согласуются с теоретическим свойством состоятельности этих оценок.</p>\n</div></details></section>')
    return



@app.cell
def _(mo):
    mo.Html("""
    <section class="cl cl-section" id="experiment-relation">
      <div class="cl-head"><h2>Попробуй сам: зависимость</h2></div>
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
               mo.hstack([relation_view, relation_count], gap=4, justify="start")], gap=0).style(
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
    generator_refresh = mo.ui.button(label="↻ Сгенерировать заново", value=0,
                                     on_click=lambda value: value + 1)
    mo.vstack([
        mo.Html('<span class="cl-interactive-surface" aria-hidden="true"></span>'),
        mo.hstack([generator_method, generator_rng], gap=3, justify="start"),
        mo.hstack([generator_count, generator_refresh], gap=3, justify="start")
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


@app.cell
def _(mo, flower):
    mo.Html(f"""
    <section class="cl cl-section" id="conclusion">
       <div class="cl-head"><h2>Вывод</h2></div>
       <div style="display:grid;grid-template-columns:100px 1fr;gap:22px;align-items:start">
          <img src="data:image/svg+xml;base64,{flower}" alt="" style="width:100px;filter:brightness(0) invert(1);opacity:.7">
          <div class="cl-full-conclusion">
<p>В этой работе я исследовала две характеристики цифровых изображений: среднюю яркость и среднюю насыщенность. Для анализа использовала 10 000 изображений из датасета CIFAR-10. Обе величины рассчитывались по цветовой модели HSV.</p>
<p>Сначала я провела разведочный анализ данных. Средняя яркость изображений составила 0,5427, а средняя насыщенность 0,2725. По гистограммам было видно, что яркость имеет почти симметричное распределение, а насыщенность чаще принимает небольшие значения.</p>
<p>Затем я проверила, существует ли связь между этими характеристиками. Коэффициент корреляции Пирсона составил −0,1889, а Спирмена −0,1904. Оба значения указывают на слабую отрицательную связь. Перестановочный тест дал p-value около 0,0005, поэтому на уровне значимости 0,05 я опровергла гипотезу о независимости величин. Получается, что в исследуемом наборе более яркие изображения имеют небольшую тенденцию быть менее насыщенными, хотя сама связь выражена слабо.</p>
<p>Для описания распределений я рассмотрела несколько математических моделей. Яркость удалось достаточно хорошо приблизить нормальным распределением. Для насыщенности я использовала смешанную модель, поскольку у 106 изображений насыщенность оказалась равна нулю. Для остальных 9 894 изображений было подобрано бета-распределение с параметрами <i>a</i> = 2,6313 и <i>b</i> = 6,8900.</p>
<p>Проверка с помощью Q–Q графиков и статистики Колмогорова и Смирнова показала, что выбранные модели близко описывают наблюдаемые распределения, хотя полностью с ними не совпадают.</p>
<p>Также я сравнила случайные выборки разного размера. При многократном отборе получилось, что с увеличением количества изображений ошибки оценивания среднего и дисперсии уменьшаются. Это согласуется с теоретическим свойством состоятельности оценок. При больших выборках отбор без возвращения обычно показывал меньшую ошибку.</p>
<p>С точки зрения дизайна исследование показало, что яркость и насыщенность стоит рассматривать как две разные характеристики изображения. Между ними есть статистическая связь, но она недостаточно сильная, чтобы по одной характеристике точно определять другую.</p>
<p>При этом результаты относятся к изображениям CIFAR-10, а не ко всем существующим фотографиям. Кроме того, из-за небольшого разрешения изображений исследование не позволяет оценивать качество профессиональной фотографии или её нишевость и эстетику.</p>
</div>
       </div>


<div class="cl-footer-links">
    <div>
        Исходный анализ:
        <a href="https://colab.research.google.com/drive/17_NhhSs_E5tIDFuaY3CTjjgJWv2oJ3hE?usp=sharing"
           target="_blank"
           rel="noopener noreferrer">Открыть Colab</a>
    </div>
</div>

<div class="cl-footer-sources">
    Источники: CIFAR-10, В. Е. Гмурман, Leemis и McQueston (2008), SciPy, NumPy, Matplotlib
</div>

    </section>""")
    return


if __name__ == "__main__":
    app.run()

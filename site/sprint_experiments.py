# %%
from pathlib import Path as SprintPath
import json as sprint_json

populations = {
    name: np.asarray(values)
    for name, values in sprint_json.loads(
        SprintPath(photos_path).with_name("combustion-populations.json").read_text(encoding="utf-8")
    ).items()
}
population_names = {
    "Температура, °C": "temperature",
    "Задержка, мс": "delay",
    "Скорость, мм/с": "speed",
}

# %%
population_choice = mo.ui.dropdown(
    list(population_names), value="Температура, °C", label="Величина"
)
mo.hstack([population_choice], justify="start")

# %%
population_values = populations[population_names[population_choice.value]]
sample_volume = mo.ui.slider(
    5, len(population_values), value=20, step=1,
    label="Объём выборки", show_value=True,
)
sample_repeat = mo.ui.button(label="Повторить отбор", value=0, on_click=lambda value: value + 1)
mo.hstack([sample_volume, sample_repeat], justify="start", gap=1, wrap=True)

# %%
_sampling_rng = np.random.default_rng(42 + sample_repeat.value)
_volume = sample_volume.value
_true_mean = population_values.mean()
_ordinary = _sampling_rng.choice(population_values, (_volume, 500)).mean(axis=0)
_unique = np.array([
    _sampling_rng.choice(population_values, _volume, replace=False).mean()
    for _ in range(500)
])
_sampling_chart = go.Figure()
for _data, _label, _color in [
    (_ordinary, "С возвращением", "#525764"),
    (_unique, "Без возвращения", "#b75435"),
]:
    _sampling_chart.add_histogram(x=_data, name=_label, marker_color=_color, opacity=.62)
_sampling_chart.add_vline(x=_true_mean, line_dash="dash", line_color="#223c50")
_sampling_chart.update_layout(
    template="plotly_white", barmode="overlay", height=305,
    margin=dict(t=10, b=44, l=48, r=12),
    xaxis_title=f"Среднее по выборке · {population_choice.value}",
    yaxis_title="Число выборок", legend=dict(orientation="h", y=1.16),
)
_rmse_with = np.sqrt(np.mean((_ordinary - _true_mean) ** 2))
_rmse_without = np.sqrt(np.mean((_unique - _true_mean) ** 2))
mo.vstack([
    mo.ui.plotly(_sampling_chart, config={"displaylogo": False}),
    mo.md(f"**Среднее совокупности** {num(_true_mean, 3)} · **RMSE с возвращением** {num(_rmse_with, 3)} · **без возвращения** {num(_rmse_without, 3)}"),
])

# %%
simulation_size = mo.ui.slider(100, 5000, value=1000, step=100, label="Размер генерации", show_value=True)
simulation_repeat = mo.ui.button(label="Новая генерация", value=0, on_click=lambda value: value + 1)
mo.hstack([simulation_size, simulation_repeat], justify="start", gap=1, wrap=True)

# %%
# The two delay generators follow the definitions in the submitted Colab.
_measured = populations["delay"]
_count = simulation_size.value
_seed = 42 + simulation_repeat.value
_rng = np.random.default_rng(_seed)
_sorted = np.sort(_measured)
_cumulative = np.arange(1, len(_sorted) + 1) / len(_sorted)
_inverse = _sorted[np.searchsorted(_cumulative, 1 - _rng.random(_count), side="left")]
_rng = np.random.default_rng(_seed)
_pairs = (_count + 1) // 2
_radius = np.sqrt(-2 * np.log(1 - _rng.random(_pairs)))
_angle = 2 * np.pi * _rng.random(_pairs)
_z = np.column_stack((_radius * np.cos(_angle), _radius * np.sin(_angle))).ravel()[:_count]
_normal = _measured.mean() + _measured.std(ddof=0) * _z
_generator_chart = go.Figure()
for _data, _label, _color in [
    (_measured, "Измерения", "#203f55"),
    (_inverse, "Обратная ИФР", "#525764"),
    (_normal, "Бокс-Мюллер", "#b75435"),
]:
    _xs, _freq = np.unique(_data, return_counts=True)
    _generator_chart.add_scatter(
        x=_xs, y=np.cumsum(_freq) / len(_data), name=_label, mode="lines",
        line=dict(color=_color, shape="hv"),
    )
_generator_chart.update_layout(
    template="plotly_white", height=305, margin=dict(t=10, b=44, l=48, r=12),
    xaxis_title="Задержка воспламенения, мс", yaxis_title="Эмпирическая ИФР",
    legend=dict(orientation="h", y=1.16),
)
_ks_inverse = stats.ks_2samp(_measured, _inverse).statistic
_ks_normal = stats.ks_2samp(_measured, _normal).statistic
mo.vstack([
    mo.ui.plotly(_generator_chart, config={"displaylogo": False}),
    mo.md(f"**Расстояние KS до измерений** {num(_ks_inverse, 3)} (обратная ИФР) · {num(_ks_normal, 3)} (Бокс-Мюллер). **Отрицательных значений в нормальной модели** {int((_normal < 0).sum())}."),
])


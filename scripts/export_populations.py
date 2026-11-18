"""Export the three finite populations used by the original Colab analyses."""
from pathlib import Path
import json
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
workbook = load_workbook(ROOT / "data/20260104Combustion_Data.xlsx", read_only=True, data_only=True)

def rows(sheet):
    return workbook[sheet].iter_rows(min_row=3, values_only=True)

temperature_sheet = workbook["Ignition temperature"]
symbols = next(temperature_sheet.iter_rows(min_row=2, max_row=2, values_only=True))
magnesium = symbols.index("Mg")
temperature = [r[41] for r in rows("Ignition temperature")
               if r[42] == "bulk" and isinstance(r[magnesium], (int, float)) and r[magnesium] > 50]

delay_rows = dict.fromkeys(rows("Ignition delay time"))
delay_sheet = workbook["Ignition delay time"]
elements = next(delay_sheet.iter_rows(min_row=2, max_row=2, values_only=True))
aluminum = elements.index("Al")
magnesium = elements.index("Mg")
delay = [r[18] for r in delay_rows
         if r[16] == "particle" and r[aluminum] == 100 and r[magnesium] == 0 and r[25] == "[30]"]

alloys = {"Ti-2Cu", "Ti-7Cu", "Ti-12Cu", "Ti-17Cu", "Ti-22Cu"}
speed = [r[14] for r in rows("Combustion rate(volume)") if r[0] in alloys and r[14] is not None]

populations = {"temperature": temperature, "delay": delay, "speed": speed}
for values, expected in zip(populations.values(), (95, 55, 80), strict=True):
    assert len(values) == expected and all(isinstance(x, (int, float)) for x in values)
path = ROOT / "ktvd/ColorLab/interactive/public/data/combustion-populations.json"
path.write_text(json.dumps(populations, indent=2) + "\n", encoding="utf-8")


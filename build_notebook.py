"""Builds and executes the narrative notebook so it ships with outputs embedded.
Run once: `python build_notebook.py`. Safe to delete; kept for reproducibility.
"""

from pathlib import Path
import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parent
md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

cells = [
    md(
        "# Forecast vs. Actual - export shipment adherence\n\n"
        "How well did each export market's **forecast** match what was actually "
        "**loaded**? This notebook ingests three messy source files, applies the "
        "business rules, and measures forecast accuracy per market and per month.\n\n"
        "*Anonymized portfolio project - fictional markets and figures, reproducible "
        "synthetic data.*"
    ),
    md(
        "## 1. Setup\n"
        "Make the `src` package importable and work from the project root so the "
        "`data/` and `output/` paths resolve whether you run this from the repo "
        "root or from `notebooks/`."
    ),
    code(
        "import os, sys\n"
        "from pathlib import Path\n"
        "if Path.cwd().name == 'notebooks':\n"
        "    os.chdir('..')\n"
        "sys.path.insert(0, os.getcwd())\n"
        "import pandas as pd\n"
        "from IPython.display import Image\n"
        "from src import sample_data, ingest, transform, analysis, report\n"
        "pd.set_option('display.max_rows', 15)"
    ),
    md(
        "## 2. The raw sources\n"
        "Three Excel files with different layouts: an early-months workbook (one "
        "sheet per month, values offset under title rows), later months as separate "
        "files (header on row 5, a dynamically named month column), and a "
        "per-vehicle loading log with **hand-typed market names** (aliases, typos, "
        "hub members under their own name)."
    ),
    code(
        "data_dir = sample_data.generate_all('data')\n"
        "forecast_long = ingest.read_all_forecast(data_dir)\n"
        "loading_long = ingest.read_loading_log(data_dir / 'loading_log.xlsx')\n"
        "print('forecast rows:', len(forecast_long), '| loading rows:', len(loading_long))\n"
        "loading_long.head(8)  # note the messy, hand-typed market names"
    ),
    md(
        "## 3. Business rules\n"
        "Normalise market names to codes, drop road-freight lanes (sea only), "
        "consolidate the low-volume hub members into a single `HUB` lane, and "
        "convert forecast pallets to containers (pallets / 22) so they compare with "
        "the real vehicle count. The result is one tidy comparison table."
    ),
    code(
        "forecast_df = transform.prepare_forecast(forecast_long)\n"
        "loading_df = transform.prepare_loading(loading_long)\n"
        "comp = transform.build_comparison(forecast_df, loading_df)\n"
        "comp.head(12)"
    ),
    md(
        "## 4. Accuracy KPIs\n"
        "**Bias** = systematic over/under-planning. **MAPE** = typical error size. "
        "**Hit rate** = share of lanes within +/-20% of forecast."
    ),
    code("analysis.monthly_kpis(comp)"),
    code("analysis.overall_kpis(comp)"),
    md(
        "## 5. Visuals\n"
        "Forecast vs. actual per market, with the target line - and the accuracy "
        "trend across months."
    ),
    code(
        "charts = report.save_charts(comp, 'output/charts')\n"
        "Image('output/charts/comparison_january.png')"
    ),
    code("Image('output/charts/accuracy_trend.png')"),
    md(
        "## 6. Where the plan missed most\n"
        "The largest gaps tell planners which lanes to revisit - and which markets "
        "are structurally hard to forecast."
    ),
    code("analysis.top_deviations(comp, 8)"),
    code("analysis.market_accuracy(comp)"),
    md(
        "## 7. Deliverable\n"
        "The same analysis is exported as the formatted Excel workbook operators "
        "use (one comparison sheet per month, combo charts, a KPI summary)."
    ),
    code(
        "path = report.write_excel(comp, 'output/forecast_vs_actual.xlsx')\n"
        "print('Wrote', path)"
    ),
]

nb = nbf.v4.new_notebook()
nb.cells = cells
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}

print("Executing notebook...")
ep = ExecutePreprocessor(timeout=300, kernel_name="python3")
ep.preprocess(nb, {"metadata": {"path": str(ROOT)}})

out = ROOT / "notebooks" / "forecast_vs_actual.ipynb"
nbf.write(nb, out)
print("Wrote", out)

[English](README.md) | [Português](README.pt-BR.md)

# Forecast vs. Actual — export shipment adherence

A data pipeline that answers a recurring supply-chain question: **how well did
each export market's forecast match what was actually shipped?** It ingests three
messy spreadsheet sources, cleans and reconciles them, applies the business
rules, and produces forecast-accuracy KPIs, charts, and a formatted Excel report.

> **Context.** This is a sanitized, self-contained distillation of a monthly
> analysis I built for a real export operation. The original is a set of Python
> scripts that read the team's actual forecast and loading spreadsheets; this
> repo reproduces the **logic and the data challenges** with fictional markets and
> reproducible synthetic data — no real destinations, customers, or figures.

📓 **The narrative walkthrough is in [`notebooks/forecast_vs_actual.ipynb`](notebooks/forecast_vs_actual.ipynb)** — it renders with charts and tables directly on GitHub.

## The problem

Each month, planners forecast how much will ship to each market (in pallets),
and separately a loading log records what actually went out (in vehicles). To
judge adherence you have to reconcile two sources that don't line up:

- **Different units** — forecast is in pallets, actuals are in vehicles. A
  container holds 22 pallets, so forecast pallets convert to a comparable
  container count.
- **Different layouts** — early months live in one workbook (a sheet each, values
  offset under title rows); later months arrive as separate files with the header
  on row 5 and a *dynamically named* month column; the loading log is one row per
  vehicle.
- **Messy keys** — the loading log is hand-typed, so the same market appears under
  aliases and typos, and several low-volume markets must be consolidated into one
  "HUB" lane. Road-freight lanes have to be excluded entirely.

Doing this by hand every month is slow and error-prone. This pipeline makes it
one command.

## Pipeline

```
 3 source files            ingest                transform               analysis            report
 ┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌───────────────┐   ┌──────────────┐
 │ general xlsx │   │ read each layout │   │ normalise names  │   │ bias / MAPE / │   │ Excel (combo │
 │ monthly xlsx │──▶│ into tidy long   │──▶│ drop road lanes  │──▶│ hit rate /    │──▶│ charts) +    │
 │ loading log  │   │ DataFrames       │   │ group HUB        │   │ deviations    │   │ PNG charts   │
 └──────────────┘   └──────────────────┘   │ pallets → cont.  │   └───────────────┘   └──────────────┘
                                            └──────────────────┘
```

Each step is its own module (`src/ingest.py`, `src/transform.py`,
`src/analysis.py`, `src/report.py`) orchestrated by `pipeline.py` — the same
shape a production ETL job would take.

## Business rules

- **Container = pallets / 22** — forecast pallets become a comparable container count.
- **Difference = actual − forecast**; **Target (BID)** is the per-market monthly goal.
- **HUB consolidation** — low-volume lanes are summed into a single `HUB` market.
- **Road-freight excluded** — sea lanes only.
- **Name normalisation** — hand-typed loading names map back to canonical codes.

## KPIs

| KPI | Meaning |
| --- | --- |
| **Bias %** | systematic over- or under-planning (Σactual − Σforecast) |
| **MAPE %** | mean absolute percentage error — typical miss size |
| **Hit rate %** | share of lanes that landed within ±20% of forecast |

## Results (bundled synthetic run)

```
Month       Forecast   Actual   Bias%   MAPE%    Hit%
January        145.4      154     5.9    21.3    60.0
February       121.8      138    13.3    23.9    60.0
March          123.2      134     8.7    22.6    50.0
April          124.7      123    -1.3    17.3    60.0
May            119.6      133    11.2    17.6    70.0
June           123.0      134     8.9    21.5    70.0
OVERALL        757.6      816     7.7    20.7    61.7
```

The operation **ships ~8% more than it forecasts** on average, and two markets
(AVL, TRN) are the persistent over-shippers driving most of the gap — exactly the
kind of finding that lets planners correct the next forecast.

**Forecast vs. actual per market (January):**

![Forecast vs. actual — January](output/charts/comparison_january.png)

**Accuracy over time:**

![Accuracy trend](output/charts/accuracy_trend.png)

## Run it

```bash
pip install -r requirements.txt
python pipeline.py          # generates data, runs the analysis, writes output/
```

Outputs land in `output/`: `forecast_vs_actual.xlsx` (one comparison sheet per
month with combo charts, plus a KPI summary) and `output/charts/*.png`.

To explore interactively, open `notebooks/forecast_vs_actual.ipynb` (or rebuild
it headless with `python build_notebook.py`).

## Project layout

```
src/config.py        Markets, hub grouping, road exclusion, targets, name aliases
src/sample_data.py   Reproducible synthetic source files (the 3 real layouts)
src/ingest.py        Read each layout into tidy long DataFrames
src/transform.py     Business rules + the comparison table
src/analysis.py      Accuracy KPIs (bias, MAPE, hit rate, deviations)
src/report.py        Formatted Excel (openpyxl) + matplotlib charts
pipeline.py          End-to-end CLI
notebooks/           Narrative analysis (executed, with outputs)
```

## Tech & concepts

Python · pandas / numpy · multi-source ETL (heterogeneous Excel layouts, dynamic
column detection, fuzzy key normalisation) · forecast-accuracy metrics (bias,
MAPE, hit rate) · matplotlib visualisation · openpyxl report generation · Jupyter.

## Possible extensions

- A rolling forecast-bias correction suggestion per market.
- Confidence bands / control limits on the accuracy trend.
- Swap the synthetic generator for a real database or API source.

## License

MIT

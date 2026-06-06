"""End-to-end pipeline.

Generates synthetic source files, ingests and cleans them, applies the business
rules, computes the forecast-accuracy KPIs, and writes the Excel report and PNG
charts. Run with: `python pipeline.py`
"""

from pathlib import Path

from src import sample_data, ingest, transform, analysis, report


def run(data_dir="data", output_dir="output"):
    # 1. Generate synthetic sources (the three real-shaped Excel files).
    data_dir = sample_data.generate_all(data_dir)

    # 2. Ingest the heterogeneous sources into tidy frames.
    forecast_long = ingest.read_all_forecast(data_dir)
    loading_long = ingest.read_loading_log(Path(data_dir) / "loading_log.xlsx")

    # 3. Apply business rules and build the comparison table.
    forecast_df = transform.prepare_forecast(forecast_long)
    loading_df = transform.prepare_loading(loading_long)
    comp = transform.build_comparison(forecast_df, loading_df)

    # 4. KPIs.
    monthly = analysis.monthly_kpis(comp)
    overall = analysis.overall_kpis(comp)
    top = analysis.top_deviations(comp, 8)

    # 5. Deliverables.
    xlsx = report.write_excel(comp, Path(output_dir) / "forecast_vs_actual.xlsx")
    charts = report.save_charts(comp, Path(output_dir) / "charts")

    return comp, monthly, overall, top, xlsx, charts


def main():
    comp, monthly, overall, top, xlsx, charts = run()

    bar = "=" * 68
    print("Forecast vs. Actual - pipeline run")
    print(bar)
    print(f"Lanes analysed:   {overall['lanes']} (road lanes excluded, hub consolidated)")
    print(f"Months:           {overall['months']}")
    print()

    print("Monthly KPIs")
    print("-" * 68)
    print(f"{'Month':<10}{'Forecast':>10}{'Actual':>9}{'Bias%':>8}{'MAPE%':>8}{'Hit%':>8}")
    for r in monthly.itertuples(index=False):
        print(f"{r.month:<10}{r.forecast_containers:>10.1f}{r.real_vehicles:>9}{r.bias_pct:>8.1f}{r.mape_pct:>8.1f}{r.hit_rate_pct:>8.1f}")
    print("-" * 68)
    print(f"{'OVERALL':<10}{overall['forecast_containers']:>10.1f}{overall['real_vehicles']:>9}"
          f"{overall['bias_pct']:>8.1f}{overall['mape_pct']:>8.1f}{overall['hit_rate_pct']:>8.1f}")
    print()

    print("Largest deviations (forecast vs. actual)")
    print("-" * 68)
    print(top.to_string(index=False))
    print()

    print(f"Excel report: {xlsx}")
    print(f"Charts:       {len(charts)} PNG(s) in {charts[0].parent}")


if __name__ == "__main__":
    main()

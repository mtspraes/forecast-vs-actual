"""Analysis - forecast-accuracy KPIs on top of the comparison table.

Definitions (forecast in containers, actual in vehicles, treated as comparable):
  difference  = actual - forecast        (positive = shipped more than planned)
  abs_error   = |difference|
  ape         = abs_error / forecast      (absolute percentage error, forecast>0)
  bias        = sum(actual) - sum(forecast)   (systematic over/under-planning)
  MAPE        = mean(ape)                  (typical error magnitude)
  hit rate    = share of lanes within +/- tolerance of forecast
"""

import numpy as np
import pandas as pd

from . import config

DEFAULT_TOLERANCE = 0.20  # +/- 20% counts as "on target"


def add_error_columns(comp, tolerance=DEFAULT_TOLERANCE):
    df = comp.copy()
    df["abs_error"] = df["difference"].abs()
    with np.errstate(divide="ignore", invalid="ignore"):
        df["ape"] = np.where(df["forecast_containers"] > 0,
                             df["abs_error"] / df["forecast_containers"], np.nan)
    df["on_target"] = df["ape"] <= tolerance
    return df


def monthly_kpis(comp, tolerance=DEFAULT_TOLERANCE):
    df = add_error_columns(comp, tolerance)
    rows = []
    for month in config.MONTH_ORDER:
        m = df[df["month"] == month]
        if m.empty:
            continue
        scored = m[m["forecast_containers"] > 0]
        fc = m["forecast_containers"].sum()
        real = m["real_vehicles"].sum()
        rows.append({
            "month": month,
            "forecast_containers": round(fc, 1),
            "real_vehicles": int(real),
            "bias": round(real - fc, 1),
            "bias_pct": round((real - fc) / fc * 100, 1) if fc else 0.0,
            "mape_pct": round(scored["ape"].mean() * 100, 1) if not scored.empty else np.nan,
            "hit_rate_pct": round(scored["on_target"].mean() * 100, 1) if not scored.empty else np.nan,
            "lanes": int((m[["forecast_containers", "real_vehicles"]].sum(axis=1) > 0).sum()),
        })
    return pd.DataFrame(rows)


def overall_kpis(comp, tolerance=DEFAULT_TOLERANCE):
    df = add_error_columns(comp, tolerance)
    scored = df[df["forecast_containers"] > 0]
    fc = df["forecast_containers"].sum()
    real = df["real_vehicles"].sum()
    return {
        "forecast_containers": round(fc, 1),
        "real_vehicles": int(real),
        "bias": round(real - fc, 1),
        "bias_pct": round((real - fc) / fc * 100, 1) if fc else 0.0,
        "mape_pct": round(scored["ape"].mean() * 100, 1) if not scored.empty else np.nan,
        "hit_rate_pct": round(scored["on_target"].mean() * 100, 1) if not scored.empty else np.nan,
        "lanes": int(df["market"].nunique()),
        "months": int(df["month"].nunique()),
    }


def top_deviations(comp, n=10):
    df = add_error_columns(comp)
    out = df.reindex(df["abs_error"].sort_values(ascending=False).index).head(n)
    out = out.assign(
        direction=np.where(out["difference"] >= 0, "over", "under"),
        forecast_containers=out["forecast_containers"].round(1),
        difference=out["difference"].round(1),
        ape_pct=(out["ape"] * 100).round(1),
    )
    return out[["month", "market", "forecast_containers", "real_vehicles",
               "difference", "ape_pct", "direction"]].reset_index(drop=True)


def market_accuracy(comp, tolerance=DEFAULT_TOLERANCE):
    """Per-market accuracy across all months - which lanes are hardest to plan."""
    df = add_error_columns(comp, tolerance)
    scored = df[df["forecast_containers"] > 0]
    g = scored.groupby("market").agg(
        forecast_containers=("forecast_containers", "sum"),
        real_vehicles=("real_vehicles", "sum"),
        mape_pct=("ape", lambda s: round(s.mean() * 100, 1)),
        hit_rate_pct=("on_target", lambda s: round(s.mean() * 100, 1)),
    ).reset_index()
    g["bias"] = (g["real_vehicles"] - g["forecast_containers"]).round(1)
    return g.sort_values("mape_pct", ascending=False).reset_index(drop=True)

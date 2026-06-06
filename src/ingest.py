"""Ingestion - read the heterogeneous source files into tidy DataFrames.

The three sources have different layouts (title-row offsets, a header buried on
row 5, a dynamically named month column, a per-vehicle log). This module hides
all of that and returns two clean long-format frames:

  forecast_long : month | market | pallets     (market is already a code)
  loading_long  : month | market_raw | vehicles (market is a hand-typed name)
"""

import re
from pathlib import Path
import pandas as pd

from . import config

_PAL_COL_RE = re.compile(r"\d{2}/\d{4} \(Pal\)")


def read_forecast_general(path):
    """Early months: one sheet per month; market in column E, pallets in column
    N, data starting on row 3 (two title rows above)."""
    path = Path(path)
    frames = []
    for sheet in pd.ExcelFile(path).sheet_names:
        df = pd.read_excel(
            path, sheet_name=sheet, header=None,
            skiprows=2, usecols=[4, 13], names=["market", "pallets"],
        )
        df = df.dropna(subset=["market", "pallets"])
        df["month"] = sheet
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else _empty_forecast()


def read_forecast_monthly(folder):
    """Later months: separate files, sheet 'Forecast', header on row 5, with a
    dynamically named '<MM>/<YYYY> (Pal)' column to locate."""
    folder = Path(folder)
    frames = []
    for path in sorted(folder.glob("[0-9][0-9]_forecast_*.xlsx")):
        month = _month_from_filename(path.name)
        if month is None:
            continue
        df = pd.read_excel(path, sheet_name="Forecast", header=4)
        pal_cols = [c for c in df.columns if _PAL_COL_RE.fullmatch(str(c))]
        if "Pais" not in df.columns or not pal_cols:
            continue
        sub = df[["Pais", pal_cols[0]]].rename(columns={"Pais": "market", pal_cols[0]: "pallets"})
        sub = sub.dropna(subset=["market", "pallets"])
        sub["month"] = month
        frames.append(sub)
    return pd.concat(frames, ignore_index=True) if frames else _empty_forecast()


def read_loading_log(path):
    """Per-vehicle loading log: date, hand-typed market name, vehicle count."""
    path = Path(path)
    df = pd.read_excel(path, sheet_name="Loading", header=0)
    df = df.dropna(subset=["Date", "Market"])
    df["Date"] = pd.to_datetime(df["Date"])
    df["month"] = df["Date"].apply(lambda d: config.YM_TO_MONTH.get((d.year, d.month)))
    df = df.dropna(subset=["month"])
    df["vehicles"] = pd.to_numeric(df["Vehicles"], errors="coerce").fillna(0)
    return df.rename(columns={"Market": "market_raw"})[["month", "market_raw", "vehicles", "Date"]]


def read_all_forecast(data_dir):
    """Combine both forecast formats into one long frame, newest format winning
    if a month appears in both."""
    data_dir = Path(data_dir)
    general = read_forecast_general(data_dir / "forecast_general.xlsx")
    monthly = read_forecast_monthly(data_dir)
    combined = pd.concat([general, monthly], ignore_index=True)
    # A month should not be double-counted; keep the first source seen per month.
    seen_general = set(general["month"].unique())
    monthly_extra = monthly[~monthly["month"].isin(seen_general)]
    return pd.concat([general, monthly_extra], ignore_index=True)


def _month_from_filename(name):
    low = name.lower()
    for month in config.MONTH_ORDER:
        if month.lower() in low:
            return month
    return None


def _empty_forecast():
    return pd.DataFrame(columns=["market", "pallets", "month"])

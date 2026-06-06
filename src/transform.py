"""Transformation - apply the business rules and build the comparison table.

Rules (shared by both sides):
  * normalise hand-typed market names to canonical codes
  * group the low-volume hub members into a single HUB lane
  * drop road-freight lanes (sea lanes only)
  * convert forecast pallets to containers (pallets / 22) so they are comparable
    with the real vehicle count
"""

import pandas as pd

from . import config


def normalize_code(value):
    """Map a raw market value (code or hand-typed name) to a canonical code,
    then collapse hub members into HUB. Returns None for road lanes."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    raw = str(value).strip()
    code = config.NAME_TO_CODE.get(raw.lower(), raw.upper() if len(raw) <= 4 else raw)
    if code in config.ROAD_MARKETS:
        return None
    if code in config.HUB_MEMBERS:
        return config.HUB_CODE
    return code


def prepare_forecast(forecast_long):
    """Long forecast (month, market code, pallets) -> per (month, market)
    containers, with road lanes dropped and hub members grouped."""
    df = forecast_long.copy()
    df["market"] = df["market"].apply(normalize_code)
    df = df.dropna(subset=["market"])
    df["pallets"] = pd.to_numeric(df["pallets"], errors="coerce").fillna(0)
    grouped = df.groupby(["month", "market"], as_index=False)["pallets"].sum()
    grouped["forecast_containers"] = grouped["pallets"] / config.PALLETS_PER_CONTAINER
    return grouped.rename(columns={"pallets": "forecast_pallets"})


def prepare_loading(loading_long):
    """Long loading log (month, raw name, vehicles) -> per (month, market)
    real vehicle count, with the same normalisation rules."""
    df = loading_long.copy()
    df["market"] = df["market_raw"].apply(normalize_code)
    df = df.dropna(subset=["market"])
    df["vehicles"] = pd.to_numeric(df["vehicles"], errors="coerce").fillna(0)
    return df.groupby(["month", "market"], as_index=False)["vehicles"].sum().rename(
        columns={"vehicles": "real_vehicles"}
    )


def build_comparison(forecast_df, loading_df):
    """Outer-join forecast and real per (month, market) across every month/market
    that appears in either side, filling gaps with zero and adding diff + BID."""
    comp = pd.merge(forecast_df, loading_df, on=["month", "market"], how="outer")
    comp[["forecast_pallets", "forecast_containers", "real_vehicles"]] = comp[
        ["forecast_pallets", "forecast_containers", "real_vehicles"]
    ].fillna(0)

    comp["difference"] = comp["real_vehicles"] - comp["forecast_containers"]
    comp["bid"] = comp["market"].map(config.BID_TARGETS).fillna(config.BID_DEFAULT)

    # Order rows by calendar month, then market.
    month_rank = {m: i for i, m in enumerate(config.MONTH_ORDER)}
    comp["_m"] = comp["month"].map(month_rank)
    comp = comp.sort_values(["_m", "market"]).drop(columns="_m").reset_index(drop=True)
    return comp

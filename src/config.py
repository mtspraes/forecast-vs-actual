"""Configuration and business rules for the forecast-vs-actual analysis.

All market codes and names here are fictional. The structure mirrors a real
export operation (sea lanes vs. road lanes, a consolidation hub, per-market
targets) without exposing any real destination, customer, or figure.
"""

# A forecast is expressed in pallets; loadings are counted in vehicles/containers.
# One container holds this many pallets, so forecast pallets convert to an
# equivalent container count that is comparable with the real vehicle count.
PALLETS_PER_CONTAINER = 22

# Maritime markets that ship in containers and are analysed individually.
# (code -> display name)
MARITIME_MARKETS = {
    "AVL": "Avalon",
    "BRG": "Bramor",
    "CDR": "Cendar",
    "DLT": "Delvia",
    "ELM": "Elmara",
    "FRN": "Faron",
    "GLD": "Golding",
    "JZR": "Jazira",
    "TRN": "Torin",
}

# Low-volume markets consolidated and reported as a single "HUB" lane.
HUB_MEMBERS = {"KST", "LRA", "MNT", "NVA"}
HUB_MEMBER_NAMES = {
    "KST": "Kestrel",
    "LRA": "Lira",
    "MNT": "Montera",
    "NVA": "Novara",
}
HUB_CODE = "HUB"

# Road-freight markets - excluded from this analysis (sea lanes only).
ROAD_MARKETS = {"OST", "PRD", "QNT", "RVN", "STL"}
ROAD_MARKET_NAMES = {
    "OST": "Oster",
    "PRD": "Prado",
    "QNT": "Quenta",
    "RVN": "Raven",
    "STL": "Stela",
}

# Per-market monthly target (BID), in containers. The benchmark line on charts.
BID_TARGETS = {
    "AVL": 25,
    "BRG": 20,
    "CDR": 15,
    "DLT": 10,
    "ELM": 8,
    "FRN": 6,
    "GLD": 4,
    "JZR": 2,
    "TRN": 12,
    "HUB": 20,
}
BID_DEFAULT = 0

# Loading logs are typed by hand, so the same market shows up under several
# spellings. This normalises the mess back to a canonical code. Built from the
# display names plus realistic aliases/typos and the multi-name hub members.
def _build_name_to_code():
    mapping = {}
    for code, name in {**MARITIME_MARKETS, **HUB_MEMBER_NAMES, **ROAD_MARKET_NAMES}.items():
        mapping[name.strip().lower()] = code
    # Hub members may be logged by their own name; map them to the hub.
    for code in HUB_MEMBERS:
        mapping[HUB_MEMBER_NAMES[code].strip().lower()] = code
    # Realistic aliases and typos seen in hand-typed logs.
    aliases = {
        "avalon port": "AVL",
        "bramor city": "BRG",
        "cendar is.": "CDR",
        "delvia (dl)": "DLT",
        "torin & co": "TRN",
        "kestrl": "KST",  # typo
        "novara island": "NVA",
    }
    mapping.update(aliases)
    return mapping


NAME_TO_CODE = _build_name_to_code()

# Spanish/Portuguese month names in calendar order, with their (year, month).
MONTHS = [
    ("January", 2026, 1),
    ("February", 2026, 2),
    ("March", 2026, 3),
    ("April", 2026, 4),
    ("May", 2026, 5),
    ("June", 2026, 6),
]
MONTH_ORDER = [m[0] for m in MONTHS]
YM_TO_MONTH = {(y, m): name for name, y, m in MONTHS}


def market_display_name(code):
    """Human-readable name for a market code (falls back to the code)."""
    if code == HUB_CODE:
        return "Hub (consolidated)"
    return (
        MARITIME_MARKETS.get(code)
        or HUB_MEMBER_NAMES.get(code)
        or ROAD_MARKET_NAMES.get(code)
        or code
    )

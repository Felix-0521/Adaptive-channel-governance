"""Canonical mapping tables for external business data normalization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CountryCode(str, Enum):
    """ISO 3166-1 alpha-2 country codes used by the PartnerRecord contract."""
    PL = "PL"
    DE = "DE"
    FR = "FR"
    ES = "ES"
    SE = "SE"


# ──────────────────────────────────────────────────────────────────────────────
# Country normalization
# ──────────────────────────────────────────────────────────────────────────────
# Bidirectional: English name → ISO code AND ISO code → English name (for display)
COUNTRY_TO_CODE: dict[str, str] = {
    # Canonical lowercase English names
    "poland": "PL",
    "germany": "DE",
    "france": "FR",
    "spain": "ES",
    "sweden": "SE",
}

# Reverse map for validation / display
CODE_TO_COUNTRY: dict[str, str] = {v: k.title() for k, v in COUNTRY_TO_CODE.items()}

VALID_COUNTRY_NAMES: frozenset[str] = frozenset(COUNTRY_TO_CODE.keys())
VALID_COUNTRY_CODES: frozenset[str] = frozenset(COUNTRY_TO_CODE.values())


def normalize_country(raw: str | None) -> str | None:
    """Convert a raw country string to a canonical ISO alpha-2 code.

    Handles three input forms:
      - English name  ("Poland")
      - ISO code     ("PL")
      - Mixed case   ("PlAnD" / "POLAND", etc.)

    Returns None for None / empty input.
    Raises ValueError for unrecognized country strings.
    """
    if raw is None:
        return None
    raw = str(raw).strip()
    if not raw:
        return None

    # Try lowercase English name first (handles mixed-case like "PlAnD")
    # Strip spaces too so "Pl AnD" → "pland" still resolves
    lower = raw.lower().replace(" ", "")
    if lower in COUNTRY_TO_CODE:
        return COUNTRY_TO_CODE[lower]

    # Try as ISO code (case-insensitive)
    upper = raw.upper()
    if len(upper) == 2 and upper in VALID_COUNTRY_CODES:
        return upper

    raise ValueError(f"Unrecognized country value: '{raw}'. Expected ISO 3166-1 alpha-2 code "
                     f"(e.g. 'PL') or English name from: {sorted(VALID_COUNTRY_NAMES)}.")


# ──────────────────────────────────────────────────────────────────────────────
# Market Tier normalization
# ──────────────────────────────────────────────────────────────────────────────
# Excel template uses "MID_VALUE"; existing MarketTier enum has HIGH/GROWTH/DEVELOPING.
# We canonicalise to the existing enum values AND handle the Excel variant.
MARKET_TIER_CANONICAL: dict[str, str] = {
    # Canonical names (case-insensitive)
    "high_value": "HIGH_VALUE",
    "growth_value": "GROWTH_VALUE",
    "developing": "DEVELOPING",
    # Excel "MID_VALUE" variant
    "mid_value": "MID_VALUE",
    "mid": "MID_VALUE",
    # Legacy / alternate spellings
    "hv": "HIGH_VALUE",
}

# Only the three tiers defined in the PartnerRecord MarketTier enum
# are accepted as final canonical values. MID_VALUE requires a separate
# extension and is marked NEW_REQUIRED_FIELD until models.py is updated.
MARKET_TIER_ENUM_VALUES: frozenset[str] = frozenset({"HIGH_VALUE", "GROWTH_VALUE", "DEVELOPING"})
MARKET_TIER_EXTENDED: frozenset[str] = MARKET_TIER_ENUM_VALUES | {"MID_VALUE"}


def normalize_market_tier(raw: str | None) -> str | None:
    """Convert a raw market tier string to a canonical enum value.

    Accepts the three standard enum values plus the Excel variant 'MID_VALUE'.
    Raises ValueError for unrecognised tier strings.
    """
    if raw is None:
        return None
    raw = str(raw).strip()
    if not raw:
        return None

    key = raw.lower()
    if key in MARKET_TIER_CANONICAL:
        canonical = MARKET_TIER_CANONICAL[key]
        if canonical not in MARKET_TIER_EXTENDED:
            raise ValueError(f"Unrecognised market tier canonical value: '{canonical}'.")
        return canonical

    raise ValueError(f"Unrecognised market tier value: '{raw}'. "
                     f"Expected one of: {sorted(MARKET_TIER_EXTENDED)}.")


# ──────────────────────────────────────────────────────────────────────────────
# Lifecycle Stage normalization
# ──────────────────────────────────────────────────────────────────────────────
LIFECYCLE_STAGE_MAP: dict[str, str] = {
    "entry": "ENTRY",
    "build": "BUILD",
    "emerging": "EMERGING",
    "growth": "GROWTH",
    "mature": "MATURE",
    "maintenance": "MAINTENANCE",
    "decline": "DECLINE",
}
LIFECYCLE_STAGE_VALUES: frozenset[str] = frozenset(LIFECYCLE_STAGE_MAP.values())


def normalize_lifecycle_stage(raw: str | None) -> str | None:
    """Convert a raw lifecycle stage string to a canonical enum value."""
    if raw is None:
        return None
    raw = str(raw).strip()
    if not raw:
        return None

    key = raw.lower()
    if key in LIFECYCLE_STAGE_MAP:
        return LIFECYCLE_STAGE_MAP[key]

    raise ValueError(f"Unrecognised lifecycle stage value: '{raw}'. "
                     f"Expected one of: {sorted(LIFECYCLE_STAGE_VALUES)}.")


# ──────────────────────────────────────────────────────────────────────────────
# Partner Type normalization
# ──────────────────────────────────────────────────────────────────────────────
PARTNER_TYPE_MAP: dict[str, str] = {
    "distributor": "DISTRIBUTOR",
    "dealer": "DEALER",
}
PARTNER_TYPE_VALUES: frozenset[str] = frozenset(PARTNER_TYPE_MAP.values())


def normalize_partner_type(raw: str | None) -> str | None:
    """Convert a raw partner type string to a canonical enum value."""
    if raw is None:
        return None
    raw = str(raw).strip()
    if not raw:
        return None

    key = raw.lower()
    if key in PARTNER_TYPE_MAP:
        return PARTNER_TYPE_MAP[key]

    raise ValueError(f"Unrecognised partner type value: '{raw}'. "
                     f"Expected one of: {sorted(PARTNER_TYPE_VALUES)}.")


# ──────────────────────────────────────────────────────────────────────────────
# Resource Commitment normalization
# ──────────────────────────────────────────────────────────────────────────────
# Excel uses strings like "Engineer Support", "MDF", "Training", "None".
# TargetRationaleInput.resource_commitment is bool | None.
RESOURCE_COMMITMENT_MAP: dict[str, bool] = {
    "engineer support": True,
    "engineer_support": True,
    "engineer-support": True,
    "mdf": True,
    "training": True,
    "sales support": True,
    "marketing support": True,
    "none": False,
    "no commitment": False,
    "pending": None,
    "": None,
}


def normalize_resource_commitment(raw: str | None) -> bool | None:
    """Convert a raw resource commitment string to bool | None.

    True  = resource committed (Engineer Support / MDF / Training / etc.)
    False = explicitly no commitment (None)
    None  = unknown / pending
    """
    if raw is None:
        return None
    raw = str(raw).strip()
    if not raw:
        return None

    key = raw.lower()
    if key in RESOURCE_COMMITMENT_MAP:
        return RESOURCE_COMMITMENT_MAP[key]

    raise ValueError(f"Unrecognised resource commitment value: '{raw}'. "
                     f"Expected one of: Engineer Support, MDF, Training, None.")


# ──────────────────────────────────────────────────────────────────────────────
# New Product Plan normalization
# ──────────────────────────────────────────────────────────────────────────────
# Excel uses "High", "Medium", "Low", "None".
# TargetRationaleInput.new_product_potential_pct is float 0-100.
NEW_PRODUCT_PLAN_MAP: dict[str, float | None] = {
    "high": 80.0,
    "medium": 50.0,
    "low": 20.0,
    "none": 0.0,
    "": None,
}


def normalize_new_product_plan(raw: str | None) -> float | None:
    """Convert a raw new product plan string to a percent float.

    Maps qualitative plan levels to quantitative scores:
      High   → 80%
      Medium → 50%
      Low    → 20%
      None   → 0%
    """
    if raw is None:
        return None
    raw = str(raw).strip()
    if not raw:
        return None

    key = raw.lower()
    if key in NEW_PRODUCT_PLAN_MAP:
        return NEW_PRODUCT_PLAN_MAP[key]

    raise ValueError(f"Unrecognised new product plan value: '{raw}'. "
                     f"Expected one of: High, Medium, Low, None.")


# ──────────────────────────────────────────────────────────────────────────────
# Boolean normalization
# ──────────────────────────────────────────────────────────────────────────────
TRUE_VALUES: frozenset[str] = frozenset({"true", "yes", "1", "on", "y"})
FALSE_VALUES: frozenset[str] = frozenset({"false", "no", "0", "off", "n", ""})


def normalize_bool(raw: str | bool | int | float | None) -> bool | None:
    """Convert a raw value to bool | None.

    Handles Python bool, int (0/1), and string representations.
    Empty string → None.
    Unknown string raises ValueError.
    """
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    raw_str = str(raw).strip()
    if not raw_str:
        return None
    lower = raw_str.lower()
    if lower in TRUE_VALUES:
        return True
    if lower in FALSE_VALUES:
        return False
    raise ValueError(f"Unrecognised boolean value: '{raw}'. "
                     f"Expected: true/false, yes/no, 1/0, on/off.")


# ──────────────────────────────────────────────────────────────────────────────
# Percentage normalization
# ──────────────────────────────────────────────────────────────────────────────
def normalize_percent(raw: str | float | int | None) -> float | None:
    """Convert a raw percent value to float in the 0-100 range.

    Accepts:
      - String with % suffix  ("85%")
      - Plain float           (85.0)
      - Plain int             (85)
      - Decimal float         (0.85)  → auto-detected and scaled to 85.0

    Returns None for None / empty string.
    Raises ValueError for out-of-range or unparseable values.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        value = float(raw)
    else:
        raw_str = str(raw).strip()
        if not raw_str:
            return None
        # Strip trailing %
        if raw_str.endswith("%"):
            raw_str = raw_str[:-1].strip()
        try:
            value = float(raw_str)
        except ValueError:
            raise ValueError(f"Unrecognised percentage value: '{raw}'.")

    # Auto-detect decimal fraction: 0-1 range → scale to percent
    if 0.0 <= value <= 1.0:
        value *= 100.0

    # Allow negative values for growth metrics (YoY_Growth_Percent)
    if not (-100.0 <= value <= 500.0):
        raise ValueError(
            f"Percentage value {value} out of reasonable range (-100 to 500). "
            f"Original input: '{raw}'."
        )
    return round(value, 4)


# ──────────────────────────────────────────────────────────────────────────────
# Summary dataclass for all mappings
# ──────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class MappingCatalog:
    """Read-only catalog of all mapping tables for inspection / testing."""

    country_to_code: dict[str, str] = field(default_factory=lambda: COUNTRY_TO_CODE.copy())
    market_tier_canonical: dict[str, str] = field(default_factory=lambda: MARKET_TIER_CANONICAL.copy())
    lifecycle_stage_map: dict[str, str] = field(default_factory=lambda: LIFECYCLE_STAGE_MAP.copy())
    partner_type_map: dict[str, str] = field(default_factory=lambda: PARTNER_TYPE_MAP.copy())
    resource_commitment_map: dict[str, bool] = field(default_factory=lambda: RESOURCE_COMMITMENT_MAP.copy())
    new_product_plan_map: dict[str, float | None] = field(default_factory=lambda: NEW_PRODUCT_PLAN_MAP.copy())
    true_values: frozenset[str] = field(default_factory=lambda: TRUE_VALUES)
    false_values: frozenset[str] = field(default_factory=lambda: FALSE_VALUES)
    valid_country_names: frozenset[str] = field(default_factory=lambda: VALID_COUNTRY_NAMES)
    valid_country_codes: frozenset[str] = field(default_factory=lambda: VALID_COUNTRY_CODES)
    market_tier_extended: frozenset[str] = field(default_factory=lambda: MARKET_TIER_EXTENDED)
    lifecycle_stage_values: frozenset[str] = field(default_factory=lambda: LIFECYCLE_STAGE_VALUES)
    partner_type_values: frozenset[str] = field(default_factory=lambda: PARTNER_TYPE_VALUES)


MAPPINGS = MappingCatalog()

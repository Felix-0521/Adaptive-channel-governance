"""Create and validate locally managed Partner records without changing scoring."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pandas as pd

from .models import LifecycleStage, MarketTier, PartnerRecord, PartnerType
from .storage import SQLitePartnerStore
from .validation import ValidationIssue, validate_dataframe


MANAGEMENT_FIELDS = {
    "partner_name",
    "country_code",
    "region",
    "business_line",
    "partner_type",
    "lifecycle_stage",
    "market_tier",
}
CONTEXT_FIELDS = MANAGEMENT_FIELDS | {"partner_id"}


@dataclass(frozen=True)
class PartnerImportAnalysis:
    preview: pd.DataFrame
    records: list[PartnerRecord]
    issues: list[ValidationIssue]
    warnings: list[str]

    @property
    def can_import(self) -> bool:
        return bool(self.records) and not self.issues


def generate_partner_id() -> str:
    return f"P-{uuid4().hex[:8].upper()}"


def create_partner(
    store: SQLitePartnerStore,
    *,
    partner_name: str,
    country_code: str,
    region: str,
    business_line: str,
    partner_type: PartnerType,
    lifecycle_stage: LifecycleStage,
    market_tier: MarketTier,
) -> PartnerRecord:
    if not region.strip():
        raise ValueError("区域为必填项 · Region is required.")
    partner = PartnerRecord(
        partner_id=generate_partner_id(),
        partner_name=partner_name,
        country_code=country_code,
        region=region.strip(),
        business_line=business_line,
        partner_type=partner_type,
        lifecycle_stage=lifecycle_stage,
        market_tier=market_tier,
    )
    store.save_partners([partner], source="CREATE_FORM")
    return partner


def analyze_partner_import(
    frame: pd.DataFrame, existing: list[PartnerRecord]
) -> PartnerImportAnalysis:
    preview = frame.copy()
    preview.columns = [str(column).strip().lower() for column in preview.columns]
    issues: list[ValidationIssue] = []
    missing = sorted(MANAGEMENT_FIELDS - set(preview.columns))
    if missing:
        issues.extend(
            ValidationIssue(-1, field, "缺少必填导入字段 · required import field is missing")
            for field in missing
        )
        return PartnerImportAnalysis(preview, [], issues, [])

    if "partner_id" not in preview.columns:
        preview.insert(0, "partner_id", [generate_partner_id() for _ in range(len(preview))])
    else:
        preview["partner_id"] = [
            generate_partner_id() if pd.isna(value) or not str(value).strip() else str(value).strip()
            for value in preview["partner_id"]
        ]

    records, contract_issues = validate_dataframe(preview)
    issues.extend(contract_issues)
    existing_ids = {partner.partner_id for partner in existing}
    existing_keys = {
        (partner.partner_name.casefold(), partner.country_code) for partner in existing
    }
    seen_keys: set[tuple[str, str]] = set()
    for row, record in enumerate(records, start=2):
        key = (record.partner_name.casefold(), record.country_code)
        if record.partner_id in existing_ids:
            issues.append(ValidationIssue(row, "partner_id", "Partner 已存在 · duplicate Partner"))
        if key in existing_keys or key in seen_keys:
            issues.append(
                ValidationIssue(row, "partner_name", "Partner Name + Country 重复 · duplicate")
            )
        seen_keys.add(key)

    optional_fields = set(PartnerRecord.model_fields) - CONTEXT_FIELDS
    warnings = []
    for record in records:
        missing_count = sum(getattr(record, field) is None for field in optional_fields)
        if missing_count:
            warnings.append(
                f"{record.partner_name}：缺少 {missing_count} 个可选观测值；"
                "Confidence 将相应降低。"
            )
    return PartnerImportAnalysis(preview, records, issues, warnings)


def import_partners(
    store: SQLitePartnerStore, analysis: PartnerImportAnalysis
) -> int:
    if not analysis.can_import:
        raise ValueError("确认前必须通过 Validation · Import must pass validation.")
    store.save_partners(analysis.records, source="CSV_IMPORT")
    return len(analysis.records)

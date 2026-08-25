"""DataFrame validation with row-level, actionable errors."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd
from pydantic import ValidationError

from .models import PartnerRecord


@dataclass(frozen=True)
class ValidationIssue:
    row: int
    field: str
    message: str


def _null_to_none(value: Any) -> Any:
    return None if value is None or (isinstance(value, float) and math.isnan(value)) else value


def validate_dataframe(frame: pd.DataFrame) -> tuple[list[PartnerRecord], list[ValidationIssue]]:
    records: list[PartnerRecord] = []
    issues: list[ValidationIssue] = []
    contract_fields = set(PartnerRecord.model_fields)
    required = {
        name for name, field in PartnerRecord.model_fields.items() if field.is_required()
    }
    missing_columns = sorted(required - set(frame.columns))
    if missing_columns:
        return [], [ValidationIssue(-1, name, "required column is missing") for name in missing_columns]
    unknown_columns = sorted(set(frame.columns) - contract_fields)
    if unknown_columns:
        return [], [ValidationIssue(-1, name, "column is not part of the data contract") for name in unknown_columns]

    for position, (_, row) in enumerate(frame.iterrows(), start=2):
        payload = {
            key: _null_to_none(row[key]) if key in frame.columns else None
            for key in contract_fields
        }
        try:
            records.append(PartnerRecord.model_validate(payload))
        except ValidationError as exc:
            for error in exc.errors():
                issues.append(ValidationIssue(position, str(error["loc"][0]), error["msg"]))
    seen: dict[str, int] = {}
    for position, record in enumerate(records, start=2):
        if record.partner_id in seen:
            issues.append(
                ValidationIssue(
                    position,
                    "partner_id",
                    f"duplicate partner_id; first seen on row {seen[record.partner_id]}",
                )
            )
        else:
            seen[record.partner_id] = position
    return records, issues


def require_valid_dataframe(frame: pd.DataFrame) -> list[PartnerRecord]:
    records, issues = validate_dataframe(frame)
    if issues:
        detail = "; ".join(f"row {i.row}, {i.field}: {i.message}" for i in issues[:10])
        raise ValueError(f"Partner data failed validation: {detail}")
    return records

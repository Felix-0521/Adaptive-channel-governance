"""Schema definitions for the 7 business Excel templates.

This module defines the canonical shape of each template so that the normalizer
knows:
  - which columns exist
  - whether they are required
  - what type / format they use
  - how they map to PartnerRecord / TargetRationaleInput fields
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Literal


# ──────────────────────────────────────────────────────────────────────────────
# Template identifiers
# ──────────────────────────────────────────────────────────────────────────────
class TemplateId(str, Enum):
    PARTNER_MASTER = "01_Partner_Master"
    COMMERCIAL_PERFORMANCE = "02_Commercial_Performance"
    OPERATIONAL_HEALTH = "03_Operational_Health"
    FINANCIAL_HEALTH = "04_Financial_Health"
    SERVICE_CAPABILITY = "05_Service_Capability"
    COMPLIANCE_GOVERNANCE = "06_Compliance_Governance"
    TARGET_RATIONALE = "07_Target_Rationale"


# ──────────────────────────────────────────────────────────────────────────────
# Field type descriptors
# ──────────────────────────────────────────────────────────────────────────────
class FieldType(str, Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    PERCENT = "percent"   # stored as "85%" or 85.0
    BOOL = "bool"         # stored as "TRUE"/"FALSE"
    DATE = "date"         # stored as "YYYY-MM-DD"
    ENUM = "enum"         # stored as "ACTIVE" / "Completed" etc.
    PERIOD = "period"     # stored as "2026Q2"


# ──────────────────────────────────────────────────────────────────────────────
# Individual field definition
# ──────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class TemplateField:
    """One column inside a template."""

    excel_name: str                 # exact column header in the Excel file
    field_type: FieldType           # how to parse the raw cell value
    required: bool = False          # True = must be present (not necessarily non-null)
    enum_values: frozenset[str] | None = None  # allowed values for ENUM type
    min_value: float | None = None  # inclusive lower bound
    max_value: float | None = None  # inclusive upper bound

    def parse(self, raw: Any) -> Any:
        """Parse a raw cell value to the expected Python type."""
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return None

        match self.field_type:
            case FieldType.STRING:
                return str(raw).strip()
            case FieldType.INT:
                return int(float(str(raw)))
            case FieldType.FLOAT | FieldType.PERCENT:
                return float(str(raw))
            case FieldType.BOOL:
                from .mappings import normalize_bool
                return normalize_bool(raw)
            case FieldType.DATE:
                return str(raw).strip()
            case FieldType.ENUM:
                val = str(raw).strip()
                if self.enum_values and val not in self.enum_values:
                    raise ValueError(
                        f"Invalid enum value '{val}' for field '{self.excel_name}'. "
                        f"Expected one of: {sorted(self.enum_values)}."
                    )
                return val
            case FieldType.PERIOD:
                val = str(raw).strip()
                # Accept YYYYQN format
                return val
            case _:
                return str(raw).strip()


# ──────────────────────────────────────────────────────────────────────────────
# Template definition
# ──────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class TemplateSchema:
    """Full schema for one Excel template."""

    template_id: TemplateId
    sheet_name: str = "Template"
    # Rows to skip: (title_row, header_row) — 0-indexed
    skip_rows: tuple[int, int] = (0, 1)
    fields: tuple[TemplateField, ...] = field(default_factory=tuple)
    join_key: str = "Partner_ID"          # the column used to join across templates

    def get_field(self, name: str) -> TemplateField | None:
        return next((f for f in self.fields if f.excel_name == name), None)

    def required_fields(self) -> tuple[TemplateField, ...]:
        return tuple(f for f in self.fields if f.required)

    def all_column_names(self) -> tuple[str, ...]:
        return tuple(f.excel_name for f in self.fields)


# ──────────────────────────────────────────────────────────────────────────────
# Schema instances
# ──────────────────────────────────────────────────────────────────────────────

T01_FIELDS = (
    TemplateField("Partner_ID",              FieldType.STRING,    required=True),
    TemplateField("Partner_Name",           FieldType.STRING,    required=True),
    TemplateField("Country",                FieldType.STRING,    required=True),   # "Poland" → "PL"
    TemplateField("Region",                 FieldType.STRING,    required=True),
    TemplateField("Business_Line",           FieldType.STRING,    required=True),
    TemplateField("Partner_Type",           FieldType.ENUM,      required=True,
                  enum_values=frozenset({"DISTRIBUTOR", "DEALER"})),
    TemplateField("Lifecycle_Stage",         FieldType.STRING,    required=True),   # normalized separately
    TemplateField("Market_Tier",            FieldType.STRING,    required=True),   # normalized separately
    TemplateField("Cooperation_Start_Date", FieldType.DATE,      required=True),
    TemplateField("Employee_Count",         FieldType.INT,       required=False),
    TemplateField("Secondary_Dealer_Count", FieldType.INT,       required=False),
    TemplateField("Strategic_Flag",         FieldType.BOOL,      required=False),
)

T02_FIELDS = (
    TemplateField("Partner_ID",               FieldType.STRING,  required=True),
    TemplateField("Evaluation_Period",        FieldType.PERIOD, required=True),
    TemplateField("Annual_Revenue_USD",       FieldType.INT,    required=False),
    TemplateField("Sales_Target_USD",         FieldType.INT,    required=False),
    TemplateField("Sell_In_Units",            FieldType.INT,    required=False),
    TemplateField("Sell_Out_Units",          FieldType.INT,    required=False),
    TemplateField("YoY_Growth_Percent",       FieldType.PERCENT, required=False),
    TemplateField("Gross_Margin_Percent",     FieldType.PERCENT, required=False),
    TemplateField("New_Product_Revenue_Percent", FieldType.PERCENT, required=False),
    TemplateField("Active_Customer_Count",    FieldType.INT,    required=False),
    TemplateField("Pipeline_Value_USD",       FieldType.INT,    required=False),
)

T03_FIELDS = (
    TemplateField("Partner_ID",                FieldType.STRING,  required=True),
    TemplateField("Evaluation_Period",          FieldType.PERIOD, required=True),
    TemplateField("Inventory_Value_USD",        FieldType.INT,    required=False),
    TemplateField("Inventory_Units",            FieldType.INT,    required=False),
    TemplateField("Inventory_Days",             FieldType.INT,    required=False),
    TemplateField("Sell_Out_Last_3M",          FieldType.INT,    required=False),
    TemplateField("Forecast_Accuracy_Percent",  FieldType.PERCENT, required=False),
    TemplateField("Stock_Aging_90_Days_Percent", FieldType.PERCENT, required=False),
    TemplateField("Reporting_Timeliness_Percent", FieldType.PERCENT, required=False),
    TemplateField("Order_Fulfillment_Rate",    FieldType.PERCENT, required=False),
)

T04_FIELDS = (
    TemplateField("Partner_ID",                FieldType.STRING,  required=True),
    TemplateField("Credit_Limit_USD",          FieldType.INT,    required=False),
    TemplateField("Credit_Used_USD",           FieldType.INT,    required=False),
    TemplateField("Outstanding_AR_USD",        FieldType.INT,    required=False),
    TemplateField("Overdue_AR_USD",           FieldType.INT,    required=False),
    TemplateField("DSO_Days",                 FieldType.INT,    required=False),
    TemplateField("Payment_On_Time_Percent",   FieldType.PERCENT, required=False),
    TemplateField("Credit_Rating",             FieldType.STRING,  required=False),
)

T05_FIELDS = (
    TemplateField("Partner_ID",                  FieldType.STRING,  required=True),
    TemplateField("Certified_Engineer_Count",    FieldType.INT,    required=False),
    TemplateField("Training_Completion_Percent",  FieldType.PERCENT, required=False),
    TemplateField("Service_Center_Count",       FieldType.INT,    required=False),
    TemplateField("Spare_Part_Availability_Percent", FieldType.PERCENT, required=False),
    TemplateField("Average_Response_Time_Hours", FieldType.INT,    required=False),
    TemplateField("SLA_Compliance_Percent",     FieldType.PERCENT, required=False),
    TemplateField("Demo_Machine_Count",          FieldType.INT,    required=False),
    TemplateField("Demo_Conversion_Percent",     FieldType.PERCENT, required=False),
    TemplateField("Reference_Project_Count",     FieldType.INT,    required=False),
)

T06_FIELDS = (
    TemplateField("Partner_ID",                    FieldType.STRING, required=True),
    TemplateField("Contract_Status",               FieldType.STRING, required=False),
    TemplateField("Contract_Expiration_Date",      FieldType.DATE,  required=False),
    TemplateField("Compliance_Training_Status",     FieldType.STRING, required=False),
    TemplateField("Reporting_Compliance_Percent",  FieldType.PERCENT, required=False),
    TemplateField("Confirmed_Compliance_Incident",  FieldType.INT,   required=False),
    TemplateField("Unauthorized_Sales_Signal",     FieldType.INT,   required=False),
    TemplateField("Data_Fraud_Flag",              FieldType.BOOL,  required=False),
    TemplateField("Audit_Result",                 FieldType.STRING, required=False),
)

T07_FIELDS = (
    TemplateField("Partner_ID",               FieldType.STRING,  required=True),
    TemplateField("Current_Revenue_USD",       FieldType.INT,    required=False),
    TemplateField("Proposed_Target_USD",        FieldType.INT,    required=False),
    TemplateField("Historical_Growth_Percent",  FieldType.PERCENT, required=False),
    TemplateField("Pipeline_Value_USD",         FieldType.INT,    required=False),
    TemplateField("New_Customer_Plan",         FieldType.INT,    required=False),
    TemplateField("Coverage_Expansion_Plan",   FieldType.INT,    required=False),
    TemplateField("Resource_Commitment",        FieldType.STRING, required=False),
    TemplateField("New_Product_Plan",          FieldType.STRING, required=False),
)


# ──────────────────────────────────────────────────────────────────────────────
# Schema registry
# ──────────────────────────────────────────────────────────────────────────────
TEMPLATES: dict[TemplateId, TemplateSchema] = {
    TemplateId.PARTNER_MASTER:          TemplateSchema(TemplateId.PARTNER_MASTER,          fields=T01_FIELDS),
    TemplateId.COMMERCIAL_PERFORMANCE:  TemplateSchema(TemplateId.COMMERCIAL_PERFORMANCE,  fields=T02_FIELDS),
    TemplateId.OPERATIONAL_HEALTH:      TemplateSchema(TemplateId.OPERATIONAL_HEALTH,      fields=T03_FIELDS),
    TemplateId.FINANCIAL_HEALTH:        TemplateSchema(TemplateId.FINANCIAL_HEALTH,        fields=T04_FIELDS),
    TemplateId.SERVICE_CAPABILITY:      TemplateSchema(TemplateId.SERVICE_CAPABILITY,      fields=T05_FIELDS),
    TemplateId.COMPLIANCE_GOVERNANCE:  TemplateSchema(TemplateId.COMPLIANCE_GOVERNANCE,  fields=T06_FIELDS),
    TemplateId.TARGET_RATIONALE:        TemplateSchema(TemplateId.TARGET_RATIONALE,        fields=T07_FIELDS),
}


def get_schema(template_id: TemplateId) -> TemplateSchema:
    return TEMPLATES[template_id]

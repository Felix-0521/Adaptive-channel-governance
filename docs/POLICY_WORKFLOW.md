# Adaptive Policy Workflow

## Data structure

Each versioned Policy contains:

- `policy_id`, `version`, `status`, `scenario_tested`, `base_version`
- explicit `match` context
- six `pillar_weights`
- Metric rules containing Pillar, normalization method, thresholds, and
  within-Pillar `weight`
- risk thresholds
- tier thresholds
- UI-only resolution metadata (`source_label`, `selection_level`)

## Isolation model

`PolicyLifecycleManager` owns mutable versions. Dashboards receive a new
read-only `PolicyRepository` containing only Active versions. Saving a Draft
adds a new version but does not alter that repository.

Scenario builds another temporary repository in which the selected Draft
replaces only the Active Policy with the same exact context. The manager's
Active versions remain unchanged. Activation is a separate explicit command
that requires `scenario_tested = true`.

## Country inheritance

Resolver rank is based on a closed set of allowed match shapes. It cannot rank
an arbitrary partial match, which prevents accidental silent fallback. The UI
always receives a source label such as `Country Override: PL` or
`Inherited from Lifecycle Policy`.

## Scenario result

Every selected Partner is evaluated twice against identical observations:

1. Active baseline repository
2. Temporary Draft scenario repository

The comparison includes score, tier, risk, and governance status. Weight-only
changes therefore affect weighted scores while risk and gates remain stable.

## Activation audit

Activation archives the previous Active version for the same exact context,
activates the tested Draft, and appends:

```text
timestamp
policy_id
old_version
new_version
actor
change_reason
```

When a new Country Override is activated, its inherited parent remains Active
for countries without that Override.

## Verification

Run:

```powershell
python -m pytest
python -m streamlit run app.py
```

Verified on Python 3.12 with **45 passing tests**, successful compilation,
dependency consistency, and a local Streamlit HTTP smoke test.

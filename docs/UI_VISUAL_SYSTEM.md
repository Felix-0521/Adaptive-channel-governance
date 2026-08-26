# Refined Enterprise UI System

## Positioning

The presentation layer uses a **clean, restrained, enterprise-grade visual system** designed for decision-support software. The goal is to make dense governance information easier to scan without turning the interface into a consumer-style showcase.

The visual system prioritizes:

- clear information hierarchy;
- comfortable reading density;
- generous but controlled whitespace;
- restrained surfaces and borders;
- consistent component sizing;
- minimal accent color;
- bilingual readability for Chinese and English labels.

No third-party brand identity, logo, proprietary visual asset, or bundled font file is used.

## Typography

Font stack: `Inter → SF Pro Display → Segoe UI → PingFang SC → Microsoft YaHei → Arial`.

| Layer | Size | Weight | Use |
|---|---:|---:|---|
| Product title | 31–39 px | 650 | Page identity |
| Section title | 24 px | 620 | Major section |
| Subsection | 18 px | 620 | Local hierarchy |
| Body | 14 px | 400–500 | Main content |
| Label / KPI label | 12.5–13 px | 520 | Supporting information |
| KPI value | 27 px | 650 | Decision signal |

## Layout

- Maximum content width: **1480 px**
- Desktop side padding: **20–52 px responsive**
- Top padding: **34 px**
- Bottom padding: **64 px**
- Primary spacing rhythm: **8 / 12 / 16 / 24 / 32 px**

## Surfaces

- Background `#F7F7F7`
- Primary surface `#FFFFFF`
- Selected surface `#F2F2F2`
- Main text `#191919`
- Secondary text `#5F5F5F`
- Muted text `#8A8A8A`
- Border `#E8E8E8`
- Accent `#FF6900`, used sparingly for focus and hierarchy rather than decoration

## Components

- Cards: 16–20 px radius, thin border, almost no shadow
- Buttons: pill shape, 42 px minimum height
- Inputs: 44 px minimum height, 12 px radius, subtle accent focus ring
- Tabs: white segmented surface with a light selected state
- Tables and charts: white surface, thin border, 16 px radius
- File uploader: dashed neutral border and light surface
- Empty states: explicit and informative rather than silently showing demo data

## Product Rule

Visual polish must not obscure system state. In particular, the interface should always make it clear whether the current analysis is based on:

- no active dataset;
- explicitly loaded synthetic demo data; or
- validated user-uploaded data.

## Guardrail

This system governs **presentation only**. It does not change scoring, policy resolution, risk, governance, target rationale, persistence, or AI decision boundaries.

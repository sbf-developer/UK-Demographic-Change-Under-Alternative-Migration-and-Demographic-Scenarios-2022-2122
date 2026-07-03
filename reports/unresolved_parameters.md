# Unresolved Empirical Parameters

This document lists parameters that cannot yet be estimated from available official data.
Each entry specifies what is needed, why it matters, and the planned resolution phase.

## Critical (blocking historical validation)

| Parameter | Model component | Why needed | Planned resolution |
|-----------|----------------|------------|------------------|
| Single-year-of-age ethnicity distribution | Base population | Cohort-component model requires age 0–100+ | Disaggregate Nomis broad age bands using MYE age structure; Phase 2 |
| Migrant generation classification | Generation state | Five-category generation scheme not directly observed in census ethnicity tables | Link Census country-of-birth and parental COB tables; Phase 2 |
| Age-specific fertility by ethnic group | Fertility | Birth model requires maternal ASFR by group | ONS births by age of mother + APS/Census ethnicity; Phase 4 |
| Historical census harmonisation (2001, 2011) | Validation | Hindcast requires consistent time series | Extend harmonisation mapping to 2001 and 2011 categories; Phase 4 |

## High priority (blocking probabilistic mode)

| Parameter | Model component | Why needed | Planned resolution |
|-----------|----------------|------------|------------------|
| Partnership distribution P(e_p, g_p \| e_m, g_m) | Births | Mixed-parent births | Census household/parental ethnicity tables; Phase 7 |
| Child ethnicity assignment P(e \| e_m, e_p, g_m, g_p) | Identity | Children not automatically assigned mother's ethnicity | Census linked tables; Phase 7 |
| Ethnic identity transition matrix Q | Identity | Self-identification changes across censuses | Estimate from 2001→2011→2021 transitions; Phase 7 |
| Emigration hazard by origin and duration | Migration | Separate I and O required | LTIM/IPS emigration by country of birth; Phase 5 |
| Parameter uncertainty distributions | Uncertainty | Probabilistic mode requires p(θ) | Bayesian calibration with posterior draws; Phase 5 |

## Moderate priority (blocking full UK coverage)

| Parameter | Model component | Why needed | Planned resolution |
|-----------|----------------|------------|------------------|
| Scotland Census 2022 ethnicity by age by sex | Base population | Scotland uses 2022 census | SPARQL or Flexible Table Builder; Phase 6 |
| Northern Ireland DT-0035 processing | Base population | NI census categories differ from England/Wales | NISRA download adapter + harmonisation; Phase 6 |
| Internal migration flows between UK nations | Internal migration | Nation-specific projections | ONS/NRS internal migration estimates; Phase 6 |
| Mid-2022 population adjustment factors | Base population | Census dates differ from mid-year base | ONS MYE 2022; Phase 2 |

## Lower priority (enhancing scenario richness)

| Parameter | Model component | Why needed | Planned resolution |
|-----------|----------------|------------|------------------|
| Migration route-specific composition | Migration | Policy scenarios require measurable parameters | Home Office visa statistics; Phase 8 |
| Ethnic mortality differentials | Mortality | Sensitivity variant only | Literature review + ONS where available; Phase 5 |
| Fertility convergence κ by group | Fertility | Six convergence specifications | APS duration analysis; Phase 4 |
| ONS 2024-based projection alignment | Benchmark validation | Coherence with official totals | ONS NPP download; Phase 4 |

## Data access status (as of project initiation)

- **ONS API (RM032)**: Metadata confirmed available; JSON endpoint accessible
- **Nomis API (C2021RM032)**: Dataset NM_2132; dimension parameter names `c2021_eth_20`, `c2021_age_6`, `c_sex`; sex-disaggregated fetch requires separate queries (Phase 2)
- **Scotland SPARQL**: Endpoint available; ethnicity cross-tabulations may require Flexible Table Builder
- **NISRA DT-0035**: XLSX download URL identified; no stable public API
- **Census 2001/2011 ethnicity**: Available via Nomis but harmonisation to 2021 categories non-trivial

## What this study can and cannot say (at Phase 1)

**Can say:**
- The projection system architecture is specified and auditable
- Under clearly labelled placeholder assumptions, the model produces internally consistent demographic trajectories
- Official data sources have been identified with documented access paths

**Cannot yet say:**
- How the UK's ethnic composition will change by 2122 (no calibrated parameters exist)
- Which assumptions contribute most to uncertainty (probabilistic mode not implemented)
- Whether the model would have accurately projected Census 2011 or 2021 (validation not yet run)
- Nation-specific projections for Scotland and Northern Ireland (Phase 6)

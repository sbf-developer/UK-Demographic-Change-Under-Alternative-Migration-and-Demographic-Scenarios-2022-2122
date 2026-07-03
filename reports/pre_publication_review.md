# Pre-Publication Academic Review

**Author:** Scott Brodie Forsyth  
**Review date:** July 2026 (updated after empirical calibration)  
**Purpose:** Journal submission readiness assessment

---

## Verdict

**Suitable for submission as a conditional-projection / methods paper** describing an open, reproducible ethnic cohort-component system calibrated to Census 2021 and ONS/Nomis official statistics for England and Wales—provided limitations are stated prominently (no hindcast, E&W only, static mortality, rule-based partnership/child ethnicity, not benchmarked to ONS aggregate NPP totals).

**Not suitable** for submission as a validated forecasting paper to *Population Studies* or *Demography* until historical hindcasts (2001→2011→2021) and fuller UK coverage are completed.

**Not suitable** for policy claims about specific immigration reforms (scenarios vary measurable demographic inputs, not legislation).

---

## What is empirically grounded (verified July 2026)

| Component | Source | Status |
|-----------|--------|--------|
| Base population mid-2022 (~60.28M E&W) | Census 2021 RM032 + Nomis MYE NM_2002_1 | Calibrated |
| Ethnic shares at base (e.g. England White 81.0%) | RM032 harmonisation | Matches processed base |
| Mortality | ONS National Life Tables 2020–2022 | Calibrated |
| Fertility ASFR + ethnic scalars | Nomis NM_203_1 (2022) + RM032 proxy | Calibrated (proxy documented) |
| Migration volumes | ONS 2022-based NPP variants | Scenario-specified |
| Migration age/ethnic profiles | Census RM011 / RM010 | Calibrated |
| Scenario tables to 2122 | Engine output | Reproduced in manuscript |
| Automated tests | pytest | 32 passing |

All manuscript table values (population and White share at 2030, 2040, 2050, 2075, 2100, 2122) match `outputs/*/projection_summary.md` within rounding.

---

## Honest limitations (must remain in manuscript)

| Limitation | Impact |
|-----------|--------|
| No historical hindcast | Century-scale trajectories unvalidated |
| England & Wales only | UK research question; incomplete geography |
| Static mortality (2020–2022, no improvement) | Long-run totals diverge from ONS NPP |
| ONS migration ramp 2022–2028 not modelled | Long-term volumes applied from year 1 |
| Fertility convergence not applied | Static ethnic ASFR after calibration |
| Rule-based partnership / child ethnicity | Not census household tables |
| Fixed ethnic identity (diagonal Q) | No census identity switching |
| Emigration capped at available stock | Realized outflow can fall below assumed level |
| Aggregate totals not benchmarked to ONS NPP | Uses ONS migration *volumes*, not full NPP system |
| RM032 age-band fertility proxy | 0–4 children approximated within under-25 band |

---

## Recommended submission framing

**Title:** *UK Ethnic Demographic Change Under Alternative Migration and Demographic Scenarios, 2022–2122: Conditional Projections for England and Wales from Census 2021 and ONS 2022-Based Assumptions*

**Abstract emphasis:** Conditional trajectories under specified assumptions; open-source pipeline; official data calibration; scenario comparison—not predictions or ONS total-population forecasts.

**Target outlets:**
1. *Demographic Research* — Methods and Data section
2. arXiv (stat.AP / demography) — methods + conditional scenarios preprint
3. *Journal of Open Source Software* — if positioned primarily as software

---

## Pre-push checklist

- [x] 32 tests pass
- [x] References fact-checked
- [x] Data claims match cached official tables (SHA-256 manifests)
- [x] LaTeX PDF compiles with empirical figures (16 pages)
- [x] Watermark on all projection outputs
- [x] Manuscript claims aligned with implementation (migration timing, ONS scope)
- [x] Comparison figures generated (`outputs/comparison/`)
- [ ] ORCID added (author to provide)
- [ ] Historical hindcast completed (required before forecast framing)
- [ ] Preregistration on OSF (recommended)

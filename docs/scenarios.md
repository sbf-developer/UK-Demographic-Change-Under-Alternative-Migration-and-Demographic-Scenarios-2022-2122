# Scenarios and model — plain-language guide

This document explains what each scenario means, what the model does, and how to read the figures.

## Why 2122, not 2050?

The research design targets **2022–2122** (100 years). Every empirical scenario YAML file sets `end_year: 2122`.

Earlier figures stopped at **2050** because the CLI used to default `--end-year 2050` when running `simulate`. That was a convenience default for quick runs, not a model limit. The engine supports the full horizon.

**Now:** `simulate` defaults to each scenario's YAML `end_year` (2122). Use `--end-year 2050` only if you want a shorter run.

```bash
# Full horizon (2122) — default
python -m ukethnicproj simulate --scenario scenarios/census_2021_mid2022_baseline.yml

# Short horizon (optional)
python -m ukethnicproj simulate --scenario scenarios/census_2021_mid2022_baseline.yml --end-year 2050

# Run all four ONS migration scenarios + comparison charts
python -m ukethnicproj simulate-all
```

---

## What is a "scenario"?

A **scenario** is a fully specified set of assumptions. It answers: *"If fertility, mortality, and migration followed these rules every year, what would the population look like?"*

Scenarios are **not predictions**. They are conditional "what if" exercises. The same model with different migration assumptions produces different trajectories.

Each scenario is defined in a YAML file under `scenarios/` and includes:

| Component | What it controls |
|-----------|------------------|
| **Base population** | Who is in the population at mid-2022 (Census 2021 + ONS MYE) |
| **Mortality** | Age/sex survival probabilities (ONS National Life Tables 2020–2022) |
| **Fertility** | Age-specific birth rates by ethnic group (Nomis 2022 births + Census differentials) |
| **Migration** | Annual immigration and emigration volumes and profiles (ONS 2022-based NPP variants) |
| **Identity** | Whether ethnic self-identification can change over time (currently fixed) |

---

## The four empirical migration scenarios

All four use the **same** Census 2021 base, fertility (principal, TFR 1.45), and mortality. **Only migration differs.**

| Scenario file | ONS variant | UK net migration (long-term ONS volumes) | Purpose |
|---------------|-------------|------------------------------------------|---------|
| `migration_zero.yml` | Zero | 0 / year | Counterfactual: natural change only (births − deaths) |
| `migration_low_2022npp.yml` | Low | +120,000 / year | Lower immigration envelope |
| `census_2021_mid2022_baseline.yml` | Principal | +340,000 / year | ONS central assumption |
| `migration_high_2022npp.yml` | High | +525,000 / year | Higher immigration envelope |

**Implementation note:** These long-term volumes are applied as constant annual flows from the first projection year. The ONS phased transition to long-term assumptions over 2022–2028 is not yet modelled. Mortality is fixed at 2020–2022 with no improvement; aggregate totals are not benchmarked to ONS principal NPP population outputs.

Immigration **age profile** comes from Census country-of-birth by age (RM011). Immigration **ethnic composition** comes from Census ethnicity × country-of-birth (RM010). Emigration is proportional to the existing population stock.

---

## What is the model?

**Model A** (`A-deterministic-v0.1`) is a **deterministic multistate cohort-component** projection:

1. **Age** existing cohorts one year
2. **Apply mortality** (survival probabilities)
3. **Add births** from maternal age-specific fertility
4. **Add immigrants** and **subtract emigrants** (separate flows)
5. **Check accounting** (population = previous + births − deaths + net migration)

The population state tracks:

- **Nation:** England, Wales (Scotland/NI planned)
- **Ethnic group:** White, Mixed, Asian, Black, Other (5 broad groups from Census 2021)
- **Generation:** Foreign-born adult/child; UK-born with 0/1/2 foreign-born parents; UK-born with two UK-born parents
- **Sex and age:** Female/male, ages 0–100+

**Deterministic** means one fixed set of parameters produces one trajectory. There is no random sampling or confidence interval (probabilistic mode is planned).

**Not yet implemented:** fertility convergence by duration of residence; partnership-based two-sex fertility; ethnic identity switching; Scotland/NI.

---

## How to read the figures

### Single-scenario (`outputs/<scenario>/ethnic_shares_trajectory.png`)

- **Top panel:** Ethnic **shares** (%) in England over time
- **Bottom panel:** Ethnic **counts** (millions) over time
- Dotted vertical lines: report years (2030, 2040, 2050, 2075, 2100, 2122)
- Red footer: conditional projection disclaimer

### Comparison charts (`outputs/comparison/`)

| File | Shows |
|------|-------|
| `comparison_total_population.png` | Total England & Wales population under all four migration scenarios |
| `comparison_white_share_england.png` | White share in England — direct scenario contrast |
| `comparison_ethnic_shares_panel.png` | Small multiples: all five ethnic groups, one panel per scenario |
| `comparison_white_share_report_years.png` | Bar chart of White share at 2030, 2040, 2050, 2075, 2100, 2122 |

---

## Geographic scope

Results are for **England and Wales** (~60.3M at mid-2022). The paper title refers to the UK research question; Scotland and Northern Ireland are not yet in the base population.

---

## Illustrative scenario (do not use for research)

`scenarios/illustrative_demonstration.yml` uses a 1M placeholder population for engine testing only. It is not calibrated to official data.

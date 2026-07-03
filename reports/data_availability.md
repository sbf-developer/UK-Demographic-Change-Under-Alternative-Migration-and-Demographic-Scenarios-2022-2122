# Data Availability Report

**Project:** UK Ethnic Demographic Change Under Alternative Migration and Demographic Scenarios, 2022–2122  
**Author:** Scott Brodie Forsyth  
**Generated:** Phase 1 initiation  
**Status:** Pre-modelling audit

---

## Purpose

This report classifies the evidence status for every parameter required by the projection model. No modelling proceeds on fabricated data. Where data cannot be obtained, the pipeline fails clearly and the gap is documented here.

## Evidence classification

| Code | Meaning |
|------|---------|
| **DO** | Directly observed in official data |
| **CO** | Calculated from official data |
| **SE** | Statistically estimated from official data |
| **BL** | Borrowed from academic literature |
| **SA** | Scenario assumption (no empirical basis) |
| **UA** | Unavailable |

---

## 1. Base population

| Parameter | Nation | Evidence | Source | Status | Notes |
|-----------|--------|----------|--------|--------|-------|
| Ethnic group × age × sex | England | DO | Nomis C2021RM032 (NM_2132) | Retrieved via API | Age in six broad bands only |
| Ethnic group × age × sex | Wales | DO | Nomis C2021RM032 (NM_2132) | Retrieved via API | Regional geography (TYPE480) |
| Ethnic group × age × sex | Scotland | UA | NRS Census 2022 | Not retrieved (Phase 6) | Census year 2022 |
| Ethnic group × age × sex | Northern Ireland | UA | NISRA DT-0035 | Not retrieved (Phase 6) | Different category wording |
| Mid-year population 2022 | All | CO | ONS MYE 2022 | ONS API / download | Adjustment from census date required |
| Generation classification | All | SE | Census COB + parental COB | Phase 2 | Not in ethnicity tables alone |

## 2. Fertility

| Parameter | Evidence | Source | Status | Notes |
|-----------|----------|--------|--------|-------|
| National ASFR by age | DO | ONS births by age of mother | Download required | Annual time series available |
| Ethnic group ASFR | SE | APS / Census + births linkage | UA | Requires statistical estimation |
| Fertility convergence κ | BL | Academic literature (Wohland et al. 2010) | UA | Needs UK-specific estimation |
| TFR by ethnic group | SE | Derived from ASFR | UA | Phase 4 calibration |

## 3. Mortality

| Parameter | Evidence | Source | Status | Notes |
|-----------|----------|--------|--------|-------|
| National life tables (age × sex) | DO | ONS National Life Tables | Download required | Annual publication |
| Ethnic mortality differentials | BL | ONS Health Index; academic studies | UA | Evidence limited; sensitivity only |
| Mortality improvement factors | CO | ONS NPP mortality assumptions | Download required | For projection forward |

## 4. Migration

| Parameter | Evidence | Source | Status | Notes |
|-----------|----------|--------|--------|-------|
| International immigration (total) | DO | ONS ABME / historical LTIM | Download required | ABME from 2020; LTIM pre-2020 with comparability break |
| International emigration (total) | DO | ONS ABME / historical LTIM | Download required | Modelled separately from immigration |
| Immigration age × sex distribution | CO | LTIM / Home Office | Phase 4 | |
| Immigration ethnic composition | SE | LTIM country of birth + ethnicity mapping | UA | Proxy requires explicit documentation |
| Emigration by origin / duration | SE | LTIM | UA | Phase 5 |
| Migration route shares | DO | Home Office visa statistics | Download required | Work, study, family, asylum |
| Internal UK migration | CO | ONS/NRS internal migration estimates | Phase 6 | Flows between nations |

## 5. Partnership and child identification

| Parameter | Evidence | Source | Status | Notes |
|-----------|----------|--------|--------|-------|
| Partnership distribution P(e_p \| e_m) | SE | Census household tables | UA | Phase 7 |
| Child ethnicity P(e_child \| e_m, e_p) | SE | Census parental ethnicity tables | UA | Phase 7; critical for mixed groups |
| Ethnic identity transition Q | SE | Census 2001→2011→2021 | UA | Phase 7 |

## 6. Historical validation data

| Dataset | Census year | Evidence | Source | Status |
|---------|-------------|----------|--------|--------|
| Ethnic group population | 2001 | DO | Nomis / UK Data Service | Download required |
| Ethnic group population | 2011 | DO | Nomis / ONS | Download required |
| Ethnic group population | 2021/2022 | DO | Nomis / NRS / NISRA | Partially retrieved (Phase 1) |
| Intercensal births and deaths | 2001–2022 | DO | ONS Vital Statistics | Download required |

## 7. Benchmark data

| Dataset | Evidence | Source | Status |
|---------|----------|--------|--------|
| ONS 2024-based national population projections | DO | ONS NPP | Download required |
| APS ethnicity estimates (annual) | DO | Nomis APS tables | Download required |

---

## API access verification

### ONS Beta API (`https://api.beta.ons.gov.uk/v1`)

| Endpoint | Tested | Result |
|----------|--------|--------|
| `/datasets` | Yes | Returns dataset list |
| `/datasets/RM032` | Yes | Metadata accessible |
| `/datasets/RM032/editions/2021/versions/1/json` | Yes | Observations retrievable with area-type filter |

**Limitation:** Nomis NM_2132 provides age in six broad bands. Single-year-of-age requires statistical disaggregation using mid-year population estimates (Phase 2). Nomis API codes (1–19) differ from Census output codes (10001–50002).

### Nomis API (`https://www.nomisweb.co.uk/api/v01`)

| Endpoint | Tested | Result |
|----------|--------|--------|
| `/dataset/NM_2132.def.sdmx.json` | Yes | C2021RM032 definition accessible |
| `/dataset/NM_2132.data.json` | Yes | 10,450 observations retrieved (10 regions) |

**Limitation:** Nomis internal geography codes (not GSS codes). Age in 6 broad bands.

### Scotland SPARQL (`https://statistics.gov.scot/sparql.json`)

| Query | Tested | Result |
|-------|--------|--------|
| Ethnicity cross-tabulation | Phase 6 | Endpoint available; query construction pending |

### NISRA (Northern Ireland)

| Table | Tested | Result |
|-------|--------|--------|
| DT-0035 (Ethnic Group by Age by Sex) | Phase 6 | XLSX download URL identified |

---

## Data directory structure

```
data/
  raw/          # Unmodified downloaded files (never edited)
  interim/      # Partially processed files
  processed/    # Analysis-ready datasets
  metadata/     # Variable definitions and documentation
  manifests/    # Provenance records with SHA-256 checksums
```

Every downloaded file includes: source organisation, dataset title, identifier, URL, retrieval timestamp, reference period, geographical coverage, variable definitions, licence, SHA-256 checksum, processing script, and known limitations.

---

## Summary assessment

| Category | DO | CO | SE | BL | SA | UA |
|----------|----|----|----|----|----|----|
| Base population | 4 | 1 | 1 | 0 | 0 | 0 |
| Fertility | 1 | 0 | 2 | 1 | 0 | 2 |
| Mortality | 1 | 1 | 0 | 1 | 0 | 0 |
| Migration | 3 | 2 | 3 | 0 | 0 | 2 |
| Partnership/identity | 0 | 0 | 3 | 0 | 0 | 3 |
| Validation | 4 | 0 | 0 | 0 | 0 | 0 |
| Benchmark | 2 | 0 | 0 | 0 | 0 | 0 |

**Conclusion:** Sufficient official data exists to build the base population for England and Wales (Phase 2) and to calibrate fertility and migration (Phase 4). Partnership, child-identification, and ethnic identity transition parameters require statistical estimation from census tables not yet processed. The illustrative Phase 1 scenario uses placeholder parameters and produces no empirical results.

---

## References

- Office for National Statistics. (2023). *Census 2021: Ethnic group by sex by age*. Dataset RM032. https://www.ons.gov.uk/datasets/RM032
- Nomis. (2023). *C2021RM032: Ethnic group by sex by age*. https://www.nomisweb.co.uk/datasets/c2021rm032
- Office for National Statistics. (2024). *Population estimates for the UK, England, Wales, Scotland and Northern Ireland: mid-2022*. https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates
- National Records of Scotland. (2023). *Scotland's Census 2022*. https://www.scotlandscensus.gov.uk
- Northern Ireland Statistics and Research Agency. (2022). *Census 2021 Main Statistics for Northern Ireland*. https://www.nisra.gov.uk/statistics/census

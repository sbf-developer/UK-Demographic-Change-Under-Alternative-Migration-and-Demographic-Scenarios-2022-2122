# Pre-Publication Academic Review

**Author:** Scott Brodie Forsyth  
**Review date:** July 2026  
**Purpose:** Journal submission readiness assessment after Phase 1 corrections

---

## Verdict

**Suitable for submission as a methods/software design paper** to outlets such as *Demographic Research* (software/methods note), *Journal of Open Source Software*, or as an arXiv methods preprint—**after** the corrections listed below (now implemented in this revision).

**Not suitable** for submission as an empirical demography paper to *Population Studies* or *Demography* until Phase 4 historical validation and calibrated parameters exist.

---

## Corrections implemented (this revision)

### References (CRITICAL — fixed)
- Coleman (2010): corrected to *Population and Development Review* 36(3), 441–486
- Rees et al. (2017): corrected to Swanson (Ed.), *The Frontiers of Applied Demography*, pp. 383–408; Norman, P. (not G.)
- Wohland et al. (2010): corrected to University of Leeds Working Paper 10/02
- Added: Haskey (2002), Rees et al. (2011), NEWETHPOP, ONS ABME, GSS ethnicity guidance
- Removed incorrect Simpson (2007) as primary projection citation; reframed prior work

### Mathematical notation (MAJOR — fixed)
- Internal migration now $M^{int}$ throughout; deaths $D$ reserved for accounting identity only
- Migration equation includes nation subscript $n$
- Phase 1 implementation status table added to manuscript

### Projection engine (CRITICAL — fixed)
- Birth sex double-counting corrected (sex ratio at birth applied)
- Child generation assigned from parent nativity rules
- Population accounting identity verified each projection year
- Emigration capped at cell population (prevents negative counts from fixed flows)

### Data documentation (CRITICAL — fixed)
- Nomis dataset ID corrected: NM_2132 (not NM_1694)
- Scotland and Northern Ireland reclassified as not yet retrieved
- Age band limitation documented: six broad bands, not single-year-of-age
- ABME replaces LTIM for post-2020 migration calibration

### Harmonisation (MAJOR — fixed)
- Added `nomis_api_code` column (API codes 1–19 distinct from output codes 10001–50002)
- Scope limited to England/Wales Census 2021 in mapping table

### Visualisation (MINOR — fixed)
- Age pyramid watermark added
- Count axis formatted with thousands separators

### Testing (MAJOR — fixed)
- Added tests: birth sex split, accounting identity
- API tests marked `@pytest.mark.integration`
- 16 unit tests passing (12 projection + 4 integration when run)

---

## Remaining limitations (document honestly)

| Limitation | Impact | Resolution phase |
|-----------|--------|------------------|
| Placeholder parameters only | No empirical projections | Phase 4 calibration |
| Fertility convergence not applied | Static ASFR in engine | Phase 4 |
| Partnership weights without male stock | Simplified fertility input | Phase 7 |
| Nomis sex=All persons only | No sex-disaggregated census base | Phase 2 |
| No Scotland/NI base population | UK-wide totals incomplete | Phase 6 |
| No historical hindcast | Cannot assess forecast accuracy | Phase 4 |
| Illustrative horizon 2022–2050 only | Not yet 2122 | Phase 8 (after validation) |

---

## Recommended submission framing

**Title (methods paper):**  
*A Reproducible Multistate Cohort-Component Framework for Conditional Ethnic Population Projections in the United Kingdom*

**Abstract emphasis:**  
Conditional trajectories under specified assumptions; open-source pipeline; Census 2021 data ingestion; preregistered scenario design—not forecasts.

**Target outlets:**
1. *Demographic Research* — Methods and Data section
2. *Journal of Open Source Software* — if positioned as software
3. arXiv (stat.AP or demography) — methods preprint

---

## Pre-push checklist

- [x] All 20 tests pass (including ONS/Nomis parser validation)
- [x] References fact-checked and corrected
- [x] Data claims match retrieved files (manifests with SHA-256)
- [x] LaTeX PDF compiles with figure
- [x] Watermark on all illustrative outputs
- [x] No politicised terminology
- [x] Limitations section complete
- [ ] ORCID added (author to provide)
- [ ] Repository URL verified (author to confirm GitHub remote)
- [ ] Preregistration on OSF (recommended before Phase 8 scenarios)

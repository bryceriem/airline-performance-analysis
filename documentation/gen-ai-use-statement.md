# Generative AI Use Statement

**Project:** MIST 4610 Group Project 2  
**Team:** 61608 Group 4  
**Tool Used:** Claude (Anthropic)  
**Scope:** Used throughout the full project — dataset exploration, SQL development, Streamlit app construction, and documentation writing.

---

## Overview

Claude was used as a development and documentation assistant across every phase of this project. All analytical decisions, question framing, and final judgment calls were made by the team. The AI did not have direct access to Snowflake — every query was copied, run, and verified by a team member before being accepted. Errors introduced by the AI were caught through testing and corrected, sometimes requiring multiple iterations.

---

## Phase 1 — Dataset Exploration

**What was prompted:**  
Asked Claude to read the USDOT Snowflake documentation and explain the structure of the dataset — what tables existed, how they related, and what variables were available.

**What it produced:**  
Claude identified the EAV (Entity-Attribute-Value) format of the `US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES` table, explained that calculating any ratio metric (like load factor) would require pivoting from long to wide format using conditional aggregation, and mapped the key join between the timeseries table and `AIRCRAFT_CARRIER_INDEX`. This framing shaped the structure of every SQL query written for the project.

**What was modified:**  
Claude initially referred to the table as `US_DEPARTENT_OF_TRANSPORTATION_TIMESERIES` (misspelled). The team caught this when queries failed in Snowflake and corrected it to `US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES` across all files.

---

## Phase 2 — Analytical Question Development

**What was prompted:**  
Asked Claude to propose strong analytical questions suited to the dataset and project requirements. Asked for options before committing to any.

**What it produced:**  
Claude offered five question directions across load factor efficiency, departure reliability, route diversity, fleet utilization, and revenue-per-seat trends. The team selected load factor efficiency and departure reliability. Claude then wrote the final question statements used in the README, including the qualifying criteria (100M+ passengers since 2020) and the "why it's meaningful" explanations covering social, economic, and operational significance.

**What was rejected:**  
Three of the five proposed question directions — route diversity, fleet utilization, and revenue-per-seat — were not pursued. A second iteration proposed "cancelled departures" as the framing for Question 2; this was implemented, tested, and rejected by the team in favor of the reliability ratio approach.

---

## Phase 3 — Carrier Filtering

**What was prompted:**  
Asked Claude to help identify which carriers to include and write a SQL filter that would scope the dataset to current, recognizable, mainline passenger carriers without hardcoding names.

**What it produced:**  
Multiple filter combinations were proposed and tested iteratively. Claude wrote queries using `OAI_CARRIER_TYPE`, `SERVICE_CLASS`, passenger thresholds, and date ranges in various combinations. The qualifying carriers CTE (`DATE >= '2020-01-01'` + `PASSENGERS_TRANSPORTED` + `HAVING SUM > 100,000,000`) was the final version accepted after several rounds of testing.

**What was rejected / iterated:**  
- Filtering by `OAI_CARRIER_TYPE = 'Large Regional'` — too broad, included freight carriers  
- Filtering by `SERVICE_CLASS` — caused SQL compilation errors; the column did not exist on the table Claude assumed it was on  
- Revenue threshold of $1B+ — pulled in too many carriers  
- Passenger threshold of 10M — pulled in too many carriers  
- Passenger threshold of 5B — threshold was misread; corrected by the team  
- Several intermediate combinations that returned 13, 37, or 49 carriers before the team settled on the 9-carrier result

---

## Phase 4 — SQL Query Development

**What was prompted:**  
Asked Claude to write all five dashboard queries once the analytical questions and carrier filter were finalized.

**What it produced:**  
Claude authored:
- The shared `qualifying_carriers` CTE used in every query
- Conditional aggregation pivot (`CASE WHEN ts.VARIABLE = '...' THEN ts.VALUE ELSE 0 END`) to convert long-format EAV rows into side-by-side columns
- Load factor calculation: `ROUND(total_passengers / NULLIF(total_seats, 0) * 100, 2)`
- Reliability score calculation: `ROUND(total_performed / NULLIF(total_scheduled, 0) * 100, 2)`
- `NULLIF` division-by-zero protection on all ratio calculations
- `DATE_TRUNC('year', ts.DATE)` + `YEAR()` pattern for annual aggregation
- `YEAR(ts.DATE) % 5 = 0` filter to sample every 5th year for the heatmap
- `LEAST(..., 100)` cap on reliability score so carriers above 100% are displayed at 100 rather than excluded
- `LIMIT 1000` on all queries per Snowflake dashboard requirements

**What was modified:**  
- The original reliability score query used `WHERE reliability_score <= 100` to exclude carriers above 100%. This caused 2 of the 9 carriers to disappear from Figure 2.1. The team identified the issue; Claude replaced the filter with `LEAST(..., 100)` to cap rather than exclude.
- Date range filters were added and removed across iterations as the team decided whether to include a year range slider in the app.

---

## Phase 5 — Snowflake Dashboard Configuration

**What was prompted:**  
Asked Claude to provide chart type, axis, and configuration instructions for all five figures to be built inside Snowflake Dashboards.

**What it produced:**  
Chart type selections, axis mappings, series/color-by settings, and titles for all five figures. Recommended replacing a planned scorecard chart with a heatgrid to better answer the analytical question.

**What was rejected:**  
The scorecard chart originally proposed for Dashboard 1 was rejected by the team as redundant with the line chart. The heatgrid recommendation was accepted.

---

## Phase 6 — Streamlit App

**What was prompted:**  
Snowflake's "Export to Streamlit" feature generated a base app. The auto-generated code was pasted into the conversation and Claude was asked to fix issues and enhance the app.

**What it produced (fixes to auto-generated code):**  
- Replaced the unsupported heatgrid chart type with a Plotly `go.Heatmap`, including a DataFrame pivot and annotated cell values
- Fixed Figure 2.3 scatter where the auto-generated code grouped by `CARRIER_SIZE` before rendering, which dropped `CARRIER_NAME` and broke the color-by-carrier feature
- Switched Figures 2.2 and 2.3 from `st.line_chart` / `st.scatter_chart` to Plotly Express to enable y-axis range cuts
- Fixed indentation errors in Figure 2.2 and 2.3 where `if/else` and `except` blocks were outside `try:` scope
- Corrected swapped axis labels on Figure 1.1
- Added `plotly` to `requirements.txt`

**What it produced (enhancements):**  
- Replaced all emoji characters with Streamlit Material icons (`:material/icon_name:`)
- Implemented `st.tabs` to separate the two dashboards
- Designed and implemented the Compare Carriers multiselect with carrier filtering and an always-on Industry Average benchmark overlaid on every chart
- Implemented the Reset to All button using an `on_click` callback

**What was modified or rejected across iterations:**  

| Iteration | Outcome |
|---|---|
| Y-axis cut for Fig 2.3 set to `[98, 103]` | Adjusted to `[97, 104]` by team for visual margin |
| Figure 2.3 text labels added on dots | Removed — labels were clipping on all sides. `cliponaxis=False` tried and rejected by team (caused overlap between two close dots). Replaced with `hover_name` + larger markers |
| Year range slider added as interactive element | Implemented, then removed by team — judged to add complexity without enough focused analytical value |
| Carrier multiselect + separate spotlight control | Two controls merged into one by team direction |
| Spotlight behavior (fade to 10% opacity) | Rejected by team — changed to hide unselected carriers entirely |
| Hide behavior without benchmark | Rejected by team — requested always-on industry average benchmark to preserve context |
| Reset button using `st.session_state["key"] = []` after widget instantiation | Failed with `StreamlitAPIException`; fixed by moving the clear logic to an `on_click` callback |
| `default=[]` on keyed multiselect | Caused widget/session state conflict; removed and replaced with pre-initialization via `if key not in st.session_state` |

---

## Phase 7 — Documentation

**What was prompted:**  
Asked Claude to write all supplementary markdown files and README sections.

**What it produced:**  
- `schema_notes.md` — full schema reference for all 7 tables
- `methodology.md` — carrier filtering rationale, qualifying carrier list, derived metric definitions
- `data_manipulations.md` — all 9 SQL transformations explained with code
- `dashboards.md` — all 5 queries with chart configs and written interpretations
- `streamlit.md` — app structure, tech stack, interactive element documentation, chart implementation notes, known fixes log
- README sections: dataset description, analytical questions, interactive elements, AI use statement

**What was modified:**  
All documentation was reviewed by the team against actual Snowflake query output and app behavior. Several sections were revised after bugs were caught and fixed — for example, the reliability score documentation was updated when the `WHERE <= 100` filter was replaced with `LEAST()`, and the interactive elements section was rewritten multiple times as the design of the Compare Carriers control evolved.

# Data Manipulations

All SQL transformations, filters, aggregations, and calculated fields used across both dashboards — with explanations of what each does and why.

---

## 1. Qualifying Carriers CTE

**What it does:** Identifies the 9 carriers used across all dashboard queries by filtering the timeseries table to carriers with over 100 million passengers transported since January 2020.

**Why:** The raw dataset contains 955 carriers including defunct airlines, regional feeders, and cargo operators. This CTE scopes all downstream analysis to current, mainline passenger carriers without hardcoding any carrier names, making the filter data-driven and reproducible.

```sql
WITH qualifying_carriers AS (
    SELECT DISTINCT carrier.AIRCRAFT_CARRIER_ID
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES ts
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRCRAFT_CARRIER_INDEX carrier
        ON ts.AIRCRAFT_CARRIER_ID = carrier.AIRCRAFT_CARRIER_ID
    WHERE ts.DATE >= '2020-01-01'
      AND ts.VARIABLE = 'PASSENGERS_TRANSPORTED'
    GROUP BY carrier.AIRCRAFT_CARRIER_ID
    HAVING SUM(ts.VALUE) > 100000000
)
```

---

## 2. Long-to-Wide Pivot (Conditional Aggregation)

**What it does:** The timeseries table stores one row per variable per segment per month. To compute derived metrics like load factor, two variables (`PASSENGERS_TRANSPORTED` and `AVAILABLE_SEATS`) must appear as separate columns in the same row. This is achieved using `CASE WHEN` inside `SUM()` to pivot the data without a native `PIVOT` clause.

**Why:** Snowflake's EAV-formatted timeseries table cannot be directly used for ratio calculations across variables. This transformation is required for any multi-variable metric.

```sql
SUM(CASE WHEN ts.VARIABLE = 'PASSENGERS_TRANSPORTED' THEN ts.VALUE ELSE 0 END) AS total_passengers,
SUM(CASE WHEN ts.VARIABLE = 'AVAILABLE_SEATS'        THEN ts.VALUE ELSE 0 END) AS total_seats
```

---

## 3. Load Factor Calculation

**What it does:** Divides total passengers transported by total available seats and multiplies by 100 to express as a percentage. `NULLIF` prevents division-by-zero errors by returning NULL instead of crashing when `total_seats` is 0. `ROUND(..., 2)` limits output to 2 decimal places.

**Why:** Load factor is a standard aviation efficiency metric not stored in the dataset — it must be derived. A result of 85% means 85 out of every 100 available seats were filled.

```sql
ROUND(total_passengers / NULLIF(total_seats, 0) * 100, 2) AS load_factor_pct
```

---

## 4. Reliability Score Calculation

**What it does:** Divides total departures performed by total departures scheduled and multiplies by 100. Results are capped at 100% in Figure 2.1 using `LEAST(..., 100)` so that carriers who performed more flights than scheduled are shown at 100% rather than excluded from the ranking entirely.

**Why:** Reliability score is a derived metric measuring scheduling accuracy. Scores above 100% occur when airlines add unplanned flights not captured in the original schedule — valid data, but misleading in a ranking context. Using `LEAST()` instead of a `WHERE` filter keeps all 9 carriers visible in the bar chart while still bounding the scale at 100%.

```sql
-- Figure 2.2, 2.3 — raw ratio:
ROUND(total_performed / NULLIF(total_scheduled, 0) * 100, 2) AS reliability_score

-- Figure 2.1 — capped at 100 to keep all carriers in the ranking:
LEAST(ROUND(total_performed / NULLIF(total_scheduled, 0) * 100, 2), 100) AS reliability_score
```

---

## 5. Year-Level Aggregation

**What it does:** `DATE_TRUNC('year', ts.DATE)` collapses monthly records into annual totals by truncating each date to the first day of its year. `YEAR()` is then applied in the outer SELECT to return a clean integer year for display.

**Why:** The raw data is monthly, which produces too much noise for trend charts. Aggregating to annual totals smooths the data and makes multi-year trends legible.

```sql
DATE_TRUNC('year', ts.DATE) AS year  -- in CTE
YEAR(year) AS year                    -- in outer SELECT for clean integer display
```

---

## 6. Every-5th-Year Filter (Figure 1.2 Only)

**What it does:** Filters the heatmap query to only include years divisible by 5 (1990, 1995, 2000... 2020, 2025).

**Why:** The heatmap spans the full dataset history from 1990 to present. Showing every year would produce 35+ columns, making the chart unreadable. Sampling every 5 years preserves the long-term trend while keeping the visualization clean.

```sql
AND YEAR(ts.DATE) % 5 = 0
```

---

## 7. HAVING Clause for Threshold Filtering

**What it does:** Applied in the qualifying carriers CTE, `HAVING SUM(ts.VALUE) > 100000000` filters carrier groups after aggregation — only carriers whose total passenger count exceeds 100 million since 2020 are retained.

**Why:** `WHERE` filters rows before aggregation; `HAVING` filters after. Since the 100M threshold applies to a summed value, it must use `HAVING` rather than `WHERE`.

```sql
GROUP BY carrier.AIRCRAFT_CARRIER_ID
HAVING SUM(ts.VALUE) > 100000000
```

---

## 8. Y-Axis Cuts (Streamlit/Plotly)

**What it does:** Applied in the Streamlit app via `fig.update_yaxes(range=[min, max])` to constrain the visible y-axis range on two charts.

**Why:** All 9 carriers cluster in a narrow reliability score band (roughly 90–103%). Without a y-axis cut, the full 0–100% range compresses all lines/dots into an unreadable sliver at the top of the chart. Cutting the axis zooms into the meaningful range and makes carrier differences visible.

| Chart | Y-axis range | Reason |
|---|---|---|
| Figure 2.2 (line) | 90–120 | Captures full post-pandemic dip and recovery range |
| Figure 2.3 (scatter) | 97–104 | Zooms into the tight band where carrier dots actually cluster, with margin on each side |

```python
fig.update_yaxes(range=[90, 120])   # Figure 2.2
fig.update_yaxes(range=[97, 104])   # Figure 2.3
```

---

## 9. LIMIT 1000

**What it does:** Caps all query results at 1,000 rows.

**Why:** Required by Snowflake's dashboard query environment. In practice, all queries return far fewer rows than this limit given the level of aggregation applied.

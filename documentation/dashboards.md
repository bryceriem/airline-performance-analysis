# Dashboard Queries, Chart Configs & Interpretations

All queries use a qualifying carriers CTE to scope results to the 9 major U.S. mainline passenger carriers. See [`methodology.md`](methodology.md) for full filtering rationale.

---

## Dashboard 1 — Load Factor Efficiency

**Analytical Question:** Among U.S. mainline passenger carriers with over 100 million passengers transported since 2020, which operate most efficiently as measured by load factor (passengers transported ÷ available seats), and how has that efficiency trended over time?

---

### Figure 1.1 — "U.S. Major Passenger Carrier Load Factor Over Time"

**Chart type:** Line
**X axis:** `YEAR` — "Year"
**Y axis:** `LOAD_FACTOR_PCT` — "Load Factor (%)"
**Series/color by:** `CARRIER_NAME` — "Carrier"
**Benchmark:** Grey dashed "Industry Avg" line — per-year mean across all 9 carriers
**Implemented with:** `plotly.express.line` via `st.plotly_chart`

**Interpretation:**
The COVID-19 pandemic caused a near-collapse in load factors across all carriers in 2020, but the speed and strength of recovery varied significantly — suggesting that some airlines managed capacity more strategically than others during the rebound. Carriers that returned to pre-pandemic load factors quickly demonstrate stronger demand forecasting and capacity discipline, while those that lagged indicate a mismatch between seats offered and actual passenger demand. This divergence has real revenue implications: a carrier consistently 10 percentage points below its peers is leaving significant income on the table per flight.

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
),
aggregated AS (
    SELECT
        carrier.CARRIER_NAME,
        DATE_TRUNC('year', ts.DATE) AS year,
        SUM(CASE WHEN ts.VARIABLE = 'PASSENGERS_TRANSPORTED' THEN ts.VALUE ELSE 0 END) AS total_passengers,
        SUM(CASE WHEN ts.VARIABLE = 'AVAILABLE_SEATS'        THEN ts.VALUE ELSE 0 END) AS total_seats
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES ts
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRCRAFT_CARRIER_INDEX carrier
        ON ts.AIRCRAFT_CARRIER_ID = carrier.AIRCRAFT_CARRIER_ID
    JOIN qualifying_carriers qc ON carrier.AIRCRAFT_CARRIER_ID = qc.AIRCRAFT_CARRIER_ID
    WHERE ts.VARIABLE IN ('PASSENGERS_TRANSPORTED', 'AVAILABLE_SEATS')
    GROUP BY 1, 2
)
SELECT
    CARRIER_NAME,
    YEAR(year) AS year,
    ROUND(total_passengers / NULLIF(total_seats, 0) * 100, 2) AS load_factor_pct
FROM aggregated
WHERE total_seats > 0
ORDER BY year, CARRIER_NAME
LIMIT 1000;
```

---

### Figure 1.2 — "Load Factor Efficiency by Major Carrier and Year"

**Chart type:** Heatmap (Plotly `go.Heatmap`)
**Rows:** `CARRIER_NAME` — "Carrier"
**Columns:** `YEAR` — "Year"
**Values:** `LOAD_FACTOR_PCT` — "Load Factor (%)"
**Color scale:** Blues (darker = higher load factor)
**Benchmark:** "Industry Avg" row appended at the bottom of the heatmap, computed from all 9 carriers per year
**Implemented with:** `st.plotly_chart`

> Filtered to every 5th year (`YEAR % 5 = 0`) to keep columns readable. Snowflake's native heatgrid chart type is not supported in Streamlit — replaced with a Plotly heatmap.

**Interpretation:**
The heatgrid reveals which carriers have been structurally efficient over decades versus which are situationally efficient, exposing patterns that a single year's snapshot would miss. A carrier that shows consistently dark cells across all years is not just having a good recent run — it has built an operationally lean model that fills planes reliably regardless of market conditions. Carriers with patchy or light cells signal chronic overcapacity, which pressures margins and often leads to fare discounting to fill seats.

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
),
aggregated AS (
    SELECT
        carrier.CARRIER_NAME,
        DATE_TRUNC('year', ts.DATE) AS year,
        SUM(CASE WHEN ts.VARIABLE = 'PASSENGERS_TRANSPORTED' THEN ts.VALUE ELSE 0 END) AS total_passengers,
        SUM(CASE WHEN ts.VARIABLE = 'AVAILABLE_SEATS'        THEN ts.VALUE ELSE 0 END) AS total_seats
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES ts
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRCRAFT_CARRIER_INDEX carrier
        ON ts.AIRCRAFT_CARRIER_ID = carrier.AIRCRAFT_CARRIER_ID
    JOIN qualifying_carriers qc ON carrier.AIRCRAFT_CARRIER_ID = qc.AIRCRAFT_CARRIER_ID
    WHERE ts.VARIABLE IN ('PASSENGERS_TRANSPORTED', 'AVAILABLE_SEATS')
      AND YEAR(ts.DATE) % 5 = 0
    GROUP BY 1, 2
)
SELECT
    CARRIER_NAME,
    YEAR(year) AS year,
    ROUND(total_passengers / NULLIF(total_seats, 0) * 100, 2) AS load_factor_pct
FROM aggregated
WHERE total_seats > 0
ORDER BY year, CARRIER_NAME
LIMIT 1000;
```

---
---

## Dashboard 2 — Departure Reliability

**Analytical Question:** Among U.S. mainline passenger carriers with over 100 million passengers transported since 2020, which have the largest gap between scheduled and performed departures, and does reliability correlate with carrier size?

---

### Figure 2.1 — "Major Passenger Carrier Reliability Score Rankings"

**Chart type:** Bar (horizontal)
**X axis:** `RELIABILITY_SCORE` — "Reliability Score (%)"
**Y axis:** `CARRIER_NAME` — "Carrier"
**Color scale:** Continuous RdYlGn on `RELIABILITY_SCORE` — red = low, green = high
**Benchmark:** Grey dashed vertical line at the average reliability score across all 9 carriers, labeled with the value
**Implemented with:** `plotly.express.bar` via `st.plotly_chart`

> Reliability score capped at 100% using `LEAST(..., 100)` so all 9 carriers appear in the ranking. Carriers that performed more flights than scheduled are displayed at 100% rather than being excluded.

**Interpretation:**
The ranking exposes meaningful operational differences between carriers that passengers rarely see aggregated in one place — a carrier near the bottom of this chart has systematically failed to operate a material portion of its scheduled flights, meaning thousands of travelers faced cancellations over this period. This is not just an inconvenience metric; carriers with low reliability scores face higher rebooking costs, compensation liabilities, and long-term reputational damage. The spread between the best and worst performers quantifies how much operational discipline varies across the industry.

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
),
aggregated AS (
    SELECT
        carrier.CARRIER_NAME,
        SUM(CASE WHEN ts.VARIABLE = 'DEPARTURES_PERFORMED' THEN ts.VALUE ELSE 0 END) AS total_performed,
        SUM(CASE WHEN ts.VARIABLE = 'DEPARTURES_SCHEDULED' THEN ts.VALUE ELSE 0 END) AS total_scheduled
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES ts
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRCRAFT_CARRIER_INDEX carrier
        ON ts.AIRCRAFT_CARRIER_ID = carrier.AIRCRAFT_CARRIER_ID
    JOIN qualifying_carriers qc ON carrier.AIRCRAFT_CARRIER_ID = qc.AIRCRAFT_CARRIER_ID
    WHERE ts.VARIABLE IN ('DEPARTURES_PERFORMED', 'DEPARTURES_SCHEDULED')
    GROUP BY 1
)
SELECT
    CARRIER_NAME,
    LEAST(ROUND(total_performed / NULLIF(total_scheduled, 0) * 100, 2), 100) AS reliability_score
FROM aggregated
WHERE total_scheduled > 0
ORDER BY reliability_score DESC
LIMIT 1000;
```

---

### Figure 2.2 — "Major Passenger Carrier Departure Reliability Over Time"

**Chart type:** Line
**X axis:** `YEAR` — "Year"
**Y axis:** `RELIABILITY_SCORE` — "Reliability Score (%)"
**Series/color by:** `CARRIER_NAME` — "Carrier"
**Y axis range:** 90–120 (cut to focus on meaningful variation)
**Benchmark:** Grey dashed "Industry Avg" line — per-year mean across all 9 carriers
**Implemented with:** `plotly.express.line` via `st.plotly_chart`

> Y axis cut at 90–120 to eliminate whitespace and highlight variation between carriers. Full range would compress all lines into a narrow band at the top of the chart.

**Interpretation:**
The 2020 dip visible across carriers reflects pandemic-era mass cancellations, but the more telling story is what happened after — carriers that snapped back quickly had leaner, more adaptable operations, while those that continued to struggle post-2021 signal deeper structural issues in staffing, scheduling, or fleet management. A carrier whose reliability score declined after 2022 despite recovering passenger demand is particularly concerning, as it suggests the airline expanded its schedule faster than its operational capacity could support. These trends directly explain headlines about summer travel meltdowns at specific carriers in recent years.

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
),
aggregated AS (
    SELECT
        carrier.CARRIER_NAME,
        DATE_TRUNC('year', ts.DATE) AS year,
        SUM(CASE WHEN ts.VARIABLE = 'DEPARTURES_PERFORMED' THEN ts.VALUE ELSE 0 END) AS total_performed,
        SUM(CASE WHEN ts.VARIABLE = 'DEPARTURES_SCHEDULED' THEN ts.VALUE ELSE 0 END) AS total_scheduled
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES ts
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRCRAFT_CARRIER_INDEX carrier
        ON ts.AIRCRAFT_CARRIER_ID = carrier.AIRCRAFT_CARRIER_ID
    JOIN qualifying_carriers qc ON carrier.AIRCRAFT_CARRIER_ID = qc.AIRCRAFT_CARRIER_ID
    WHERE ts.VARIABLE IN ('DEPARTURES_PERFORMED', 'DEPARTURES_SCHEDULED')
    GROUP BY 1, 2
)
SELECT
    CARRIER_NAME,
    YEAR(year) AS year,
    ROUND(total_performed / NULLIF(total_scheduled, 0) * 100, 2) AS reliability_score
FROM aggregated
WHERE total_scheduled > 0
ORDER BY year, CARRIER_NAME
LIMIT 1000;
```

---

### Figure 2.3 — "Reliability Score vs. Carrier Size"

**Chart type:** Scatter
**X axis:** `CARRIER_SIZE` — "Total Scheduled Departures (Size Proxy)"
**Y axis:** `RELIABILITY_SCORE` — "Reliability Score (%)"
**Series/color by:** `CARRIER_NAME` — "Carrier"
**Y axis range:** 97–104 (cut to zoom into the tight cluster with margin)
**Benchmark:** Grey dashed horizontal line at the average reliability score across all 9 carriers, labeled with the value
**Implemented with:** `plotly.express.scatter` via `st.plotly_chart`

> Each dot represents one carrier. Y axis cut at 97–104 to zoom into the range where all carriers cluster and make differences visible. `CARRIER_SIZE` = total scheduled departures, used as a proxy for operational scale. Carrier name surfaced via hover tooltip (`hover_name`) rather than on-chart labels to avoid overlap.

**Interpretation:**
If the dots cluster with larger carriers scoring lower, it confirms that operational scale introduces complexity that degrades reliability — a finding with real policy and consumer implications. Conversely, if large carriers score as well or better than small ones, it suggests that resources and infrastructure at scale actually support more consistent operations. The distribution of dots tells a story about whether the industry's biggest players are earning their market dominance through operational excellence or simply through network lock-in despite inferior reliability.

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
),
aggregated AS (
    SELECT
        carrier.CARRIER_NAME,
        SUM(CASE WHEN ts.VARIABLE = 'DEPARTURES_PERFORMED' THEN ts.VALUE ELSE 0 END) AS total_performed,
        SUM(CASE WHEN ts.VARIABLE = 'DEPARTURES_SCHEDULED' THEN ts.VALUE ELSE 0 END) AS total_scheduled
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES ts
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRCRAFT_CARRIER_INDEX carrier
        ON ts.AIRCRAFT_CARRIER_ID = carrier.AIRCRAFT_CARRIER_ID
    JOIN qualifying_carriers qc ON carrier.AIRCRAFT_CARRIER_ID = qc.AIRCRAFT_CARRIER_ID
    WHERE ts.VARIABLE IN ('DEPARTURES_PERFORMED', 'DEPARTURES_SCHEDULED')
    GROUP BY 1
)
SELECT
    CARRIER_NAME,
    total_scheduled AS carrier_size,
    ROUND(total_performed / NULLIF(total_scheduled, 0) * 100, 2) AS reliability_score
FROM aggregated
WHERE total_scheduled > 0
ORDER BY total_scheduled DESC
LIMIT 1000;
```

# Methodology

## Analytical Questions

**Question 1 — Load Factor Efficiency**
Among U.S. mainline passenger carriers with over 100 million passengers transported since 2020, which operate most efficiently as measured by load factor (passengers transported ÷ available seats), and how has that efficiency trended over time?

**Question 2 — Departure Reliability**
Among U.S. mainline passenger carriers with over 100 million passengers transported since 2020, which have the largest gap between scheduled and performed departures, and does reliability correlate with carrier size?

---

## Carrier Filtering

All dashboards are scoped to a consistent set of 9 qualifying carriers, identified using the following criteria:

### Qualifying Filters
| Filter | Value | Rationale |
|---|---|---|
| Date range | `DATE >= '2020-01-01'` | Excludes defunct carriers that ceased operations before 2020 (e.g. Continental, Northwest, ATA, US Airways). Ensures analysis reflects the current competitive landscape. |
| Variable | `PASSENGERS_TRANSPORTED` | Scopes qualification to passenger activity only, excluding pure cargo operators like FedEx and UPS. |
| Passenger threshold | `SUM(VALUE) > 100,000,000` | Limits to carriers with sufficient data density for reliable trend analysis. Naturally excludes regional feeders (SkyWest, Envoy, Republic, Mesa) that operate under contract for mainline brands and do not represent independent strategic operators. |

### Qualifying Carrier Query
```sql
WITH pivoted AS (
    SELECT
        carrier.CARRIER_NAME,
        SUM(CASE WHEN ts.VARIABLE = 'PASSENGERS_TRANSPORTED' THEN ts.VALUE ELSE 0 END) AS total_passengers
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES ts
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRCRAFT_CARRIER_INDEX carrier
        ON ts.AIRCRAFT_CARRIER_ID = carrier.AIRCRAFT_CARRIER_ID
    WHERE ts.DATE >= '2020-01-01'
      AND ts.VARIABLE = 'PASSENGERS_TRANSPORTED'
    GROUP BY 1
)
SELECT
    CARRIER_NAME,
    total_passengers
FROM pivoted
WHERE total_passengers > 100000000
ORDER BY total_passengers DESC;
```

### Qualifying Carriers (9 total)
1. Southwest Airlines Co.
2. American Airlines Inc.
3. Delta Air Lines Inc.
4. United Air Lines Inc.
5. SkyWest Airlines Inc.
6. Spirit Air Lines
7. Alaska Airlines Inc.
8. JetBlue Airways
9. Frontier Airlines Inc.

---

## Derived Metrics

**Load Factor (%)**
> `PASSENGERS_TRANSPORTED / AVAILABLE_SEATS * 100`
>
> Measures what percentage of available seats were filled. A higher load factor indicates greater efficiency. Requires pivoting the long-format timeseries table on two variables using conditional aggregation.

**Reliability Score (%)**
> `DEPARTURES_PERFORMED / DEPARTURES_SCHEDULED * 100`
>
> Measures what percentage of scheduled departures were actually completed. Capped at 100% in the rankings bar chart using `LEAST(..., 100)` — carriers that performed more flights than scheduled are displayed at 100% rather than excluded, ensuring all 9 carriers appear in the ranking. A higher score indicates greater reliability.

---

## Data Structure Notes

The `US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES` table uses a long/narrow EAV format — one row per flight segment per variable per month. To compare two variables (e.g. passengers vs. seats), the data must be pivoted using `CASE WHEN` conditional aggregation inside a CTE. All dashboard queries follow this pattern.

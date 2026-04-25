# airline-performance-analysis

Group 4 | MIST4610: Data Management & Analytics w/ Dr. Nikhil Srinivasan | Group Project 2: Snowflake Analytics Dashboard

# I. Team Name & Members
### Team Name: 
61608 Group 4
### Team Members:
1. Jacob Witucki [@jacobwitucki](https://github.com/jacobWitucki)
2. Ashleigh Serafin [@ashleighserafin](https://github.com/ashleighserafin)
3. Bryce Riemersma [@bryceriem](https://github.com/bryceriem)
4. Lily Shaw  [@lilyshaw714](https://github.com/lilyshaw714)
5. Matt Miller  [@matthewroanmiller](https://github.com/matthewroanmiller)
6. Shruti Alladi  [@salladi13](https://github.com/salladi13)

# II. Dataset Description:

### Description of Data Model:

The **USDOT dataset** available through Snowflake’s Data Foundations is a structured, aviation-focused dataset that provides detailed information on airline operations within the United States. It is designed to support analysis of air travel activity, carrier performance, and transportation trends.  

At a high level, the dataset contains **monthly records of domestic, non-stop flight segments** reported by both U.S. and international air carriers. These records capture operational details such as routes, carriers, and activity levels, making it useful for analyzing airline networks, traffic patterns, and industry performance over time.  

The dataset is organized using Snowflake’s standardized schema, which separates data into **entities and time series**. Entity tables provide reference information about core components of the aviation system—such as airlines, aircraft, and airports—while time series tables store measurable activity (e.g., flight volumes) across time periods.
<br><br>

(Database: SNOWFLAKE_PUBLIC_DATA_FREE Schema: PUBLIC_DATA_FREE)  

(EX: SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRCRAFT_CARRIER_INDEX)
<br><br>

## Tables included in the USDOT dataset are:

#### 1. AIRCRAFT_CARRIER_INDEX (955 Rows)
 
<img width="849" height="591" alt="Screenshot 2026-04-15 at 12 39 11 PM" src="https://github.com/user-attachments/assets/2d92ee06-1e53-445f-b8c8-b1a8b2f58e3b" />
<br><br>
 
#### 2. AIRCRAFT_INDEX (697 Rows)

<img width="847" height="325" alt="Screenshot 2026-04-15 at 12 40 08 PM" src="https://github.com/user-attachments/assets/980af716-8de8-41f8-a056-9bb8ae099619" />  
<br><br>

#### 3. AIRPORT_INDEX (5,107 Rows)  

<img width="765" height="644" alt="Screenshot 2026-04-15 at 12 40 57 PM" src="https://github.com/user-attachments/assets/8d20b697-736b-4fe7-945f-6e228fc5753c" />  
<br><br>

#### 4. US_DEPARTENT_OF_TRANSPORTATION_ATTRIBUTES (10 Rows) 

<img width="764" height="287" alt="Screenshot 2026-04-15 at 12 42 13 PM" src="https://github.com/user-attachments/assets/1dd3477f-c93a-4d31-bf31-c474e49d9b54" />  
<br><br>

#### 5. US_DEPARTENT_OF_TRANSPORTATION_ATTRIBUTES_PIT (10 Rows)

<img width="765" height="446" alt="Screenshot 2026-04-15 at 12 44 28 PM" src="https://github.com/user-attachments/assets/56173aea-a4dc-4346-88f0-f74a53b12f27" />
<br><br>

#### 6. US_DEPARTENT_OF_TRANSPORTATION_TIMESERIES (123,250,510 Rows)

<img width="680" height="700" alt="Screenshot 2026-04-15 at 12 45 16 PM" src="https://github.com/user-attachments/assets/bce1d72c-41fa-4fc3-971d-38b8feaa5860" />
<br><br>

#### 7. US_DEPARTENT_OF_TRANSPORTATION_TIMESERIES_PIT (336,370,033 Rows)

<img width="567" height="709" alt="Screenshot 2026-04-15 at 12 45 50 PM" src="https://github.com/user-attachments/assets/d22511cd-3576-452d-9390-a3bf83a8119e" />
<br><br>

Overall, this dataset is structured to enable **consistent, time-based analysis of U.S. air transportation**, supporting use cases such as trend analysis, route optimization, and performance benchmarking. It is particularly valuable for analysts, data scientists, and businesses interested in aviation, logistics, and transportation economics because it combines standardized reference data with regularly updated operational metrics.

# III. Questions & Justification:  

### 1. Load Factor Efficiency:

- #### Among U.S. mainline passenger carriers with over 100 million passengers transported since 2020, which operate most efficiently as measured by load factor (passengers transported / available seats), and how has that efficiency trended over time?

#### Why it's meaningful:
- Load factor is one of the most important metrics in aviation economics. Airlines that consistently fill more of their seats generate more revenue per flight without adding operational costs, directly impacting profitability and ticket pricing. Socially, carriers with higher load factors can justify more routes and frequencies, improving connectivity for travelers. Operationally, tracking load factor over time reveals how well each airline manages capacity relative to demand, exposing carriers that are over-scheduling or under-filling flights.

#### Tables used:
- **US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES** – provides the PASSENGERS_TRANSPORTED and AVAILABLE_SEATS values from their respective tables
- **AIRCRAFT_CARRIER_INDEX** – provides CARRIER_NAME for labeling and filtering qualifying carriers

#### Columns used:
AIRCRAFT_CARRIER_ID, CARRIER_NAME, VARIABLE, VALUE, DATE
<br><br>

### 2. Departure Reliability:

- #### Among U.S. mainline passenger carriers with over 100 million passengers transported since 2020, which have the largest gap between scheduled and performed departures, and does reliability correlate with carrier size?**

#### Why it's meaningful:
- Departure reliability directly affects millions of travelers; missed connections, rebooking costs, and lost productivity all stem from cancelled or unperformed flights. Economically, chronic under-performance relative to schedule signals operational inefficiency and can erode consumer trust, affecting an airline's long-term market share. The correlation with carrier size adds a strategic layer: if larger carriers are less reliable, it suggests that operational complexity at scale is a genuine industry challenge rather than an individual carrier problem.

#### Tables used:
- **US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES** – provides the DEPARTURES_PERFORMED and DEPARTURES_SCHEDULED values
- **AIRCRAFT_CARRIER_INDEX** – provides CARRIER_NAME for labeling and filtering qualifying carriers

#### Columns used:
AIRCRAFT_CARRIER_ID, CARRIER_NAME, VARIABLE, VALUE, DATE
<br><br>

# IV. Data Manipulations

### 1. Qualifying Carriers WITH Clause
- #### What it does:
  Identifies the 9 carriers used across all dashboard queries by filtering the timeseries table to carriers with over 100 million passengers transported since January 2020.

- #### Why:
  The raw dataset contains 955 carriers, including defunct airlines, regional feeders, and cargo operators. This CTE scopes all downstream analysis to current, mainline passenger carriers without hardcoding any carrier names, making the filter data-driven and reproducible.

<img width="749" height="204" alt="qualifying carriers" src="https://github.com/user-attachments/assets/355515c8-4369-438f-93c7-498fac1a6cc5" />
<br>

### 2. Long-to-Wide Pivot (Conditional Aggregation)
- #### What it does:
  The timeseries table stores one row per variable per segment per month. To compute derived metrics like load factor, two variables (PASSENGERS_TRANSPORTED and AVAILABLE_SEATS) must appear as separate columns in the same row. This is achieved using CASE WHEN inside SUM() to pivot the data without a native PIVOT clause.

- #### Why:
  Snowflake's EAV-formatted timeseries table cannot be directly used for ratio calculations across variables. This transformation is required for any multi-variable metric.

<img width="764" height="90" alt="conditional aggregation" src="https://github.com/user-attachments/assets/7acd8f48-7806-466c-a206-ec02611b3ed8" />
<br>

### 3. Load Factor Calculation
- #### What it does:
  Divides total passengers transported by total available seats and multiplies by 100 to express as a percentage. NULLIF prevents division-by-zero errors by returning NULL instead of crashing when total_seats is 0.

- #### Why:
  Load factor is a standard aviation efficiency metric not stored in the dataset. It must be derived. A result of 85% means 85 out of every 100 available seats were filled.

<img width="592" height="56" alt="load factor calculation" src="https://github.com/user-attachments/assets/80c15ebe-d0b9-40cd-b408-4edf59f5c7f2" />
<br>

### 4. Reliability Score Calculation
- #### What it does:
  Divides total departures performed by total departures scheduled and multiplies by 100. Results are capped at 100% in Chart 1 using a WHERE filter to exclude carriers that flew more than scheduled.

- #### Why:
  Reliability score is a derived metric measuring scheduling accuracy. Scores above 100% occur when airlines add unplanned flights not captured in the original schedule — valid data, but misleading in a ranking context. The cap ensures the bar chart is interpretable as a reliability measure rather than a volume measure.

<img width="629" height="110" alt="reliability score calculation" src="https://github.com/user-attachments/assets/7e93c203-4ca9-417e-b7f6-ec5fbc01f9c6" />
<br>

### 5. Year-Level Aggregation
- #### What it does:
  DATE_TRUNC('year', ts.DATE) collapses monthly records into annual totals by truncating each date to the first day of its year. YEAR() is then applied in the outer SELECT to return a clean integer year for display.

- #### Why:
  The raw data is monthly, which produces too much noise for trend charts. Aggregating to annual totals smooths the data and makes multi-year trends legible.

<img width="589" height="95" alt="year-level aggregation" src="https://github.com/user-attachments/assets/905d8979-819b-481d-abec-f539932b9511" />
<br>

### 6. Every-5th-Year Filter (Heatgrid Only)
- #### What it does:
  Filters the heatgrid query to only include years divisible by 5 (1990, 1995, 2000... 2020, 2025).

- #### Why:
  The heatgrid spans the full dataset history from 1990 to present. Showing every year would produce 35+ columns, making the chart unreadable. Sampling every 5 years preserves the long-term trend while keeping the visualization clean.

<img width="232" height="62" alt="every-5th-year filter" src="https://github.com/user-attachments/assets/787103e6-e765-481e-9442-4de172ab1f5d" />
<br>

### 7. HAVING Clause for Threshold Filtering
- #### What it does:
  Applied in the qualifying carriers CTE, HAVING SUM(ts.VALUE) > 100000000 filters carrier groups after aggregation — only carriers whose total passenger count exceeds 100 million since 2020 are retained.

- #### Why:
  WHERE filters rows before aggregation; HAVING filters after. Since the 100M threshold applies to a summed value, it must use HAVING rather than WHERE.

<img width="320" height="88" alt="threshold filtering" src="https://github.com/user-attachments/assets/589f7eaa-0a0a-41fc-876b-2ee1e78d541f" />
<br>

### 8. HAVING Clause for Threshold Filtering
- #### What it does:
  Caps all query results at 1,000 rows.

- #### Why:
  Saves token usage.
<br>

# V. Analysis & Results

## Load Factor Efficiency 

### Figure 1.1: U.S. Major Passenger Carrier Load Factor Over Time

<img width="1136" height="508" alt="figure1 1" src="https://github.com/user-attachments/assets/9a5fe938-b48b-4ebe-b8d6-531cdd290256" />
<br>
The COVID-19 pandemic caused a near-collapse in load factors across all carriers in 2020, but the speed and strength of recovery varied significantly — suggesting that some airlines managed capacity more strategically than others during the rebound. Carriers that returned to pre-pandemic load factors quickly demonstrate stronger demand forecasting and capacity discipline, while those that lagged indicate a mismatch between seats offered and actual passenger demand. This divergence has real revenue implications: a carrier consistently 10 percentage points below its peers is leaving significant income on the table per flight.
<br><br>

### Figure 1.2: Load Factor Efficiency by Major Carrier and Year

<img width="1160" height="523" alt="figure1 2" src="https://github.com/user-attachments/assets/7fca9af2-51d8-41ac-9fe0-633654f3a55b" />
<br>
The heatgrid reveals which carriers have been structurally efficient over decades versus which are situationally efficient, exposing patterns that a single year's snapshot would miss. A carrier that shows consistently dark cells across all years is not just having a good recent run — it has built an operationally lean model that fills planes reliably regardless of market conditions. Carriers with patchy or light cells signal chronic overcapacity, which pressures margins and often leads to fare discounting to fill seats.
<br><br>

## Departure Reliability

### Figure 2.1: Major Passenger Carrier Reliability Score Rankings (2015-Present)

<img width="1142" height="320" alt="figure2 1" src="https://github.com/user-attachments/assets/1a868dfb-0b70-4b72-9fdb-fb04d87abda3" />
<br>
The ranking exposes meaningful operational differences between carriers that passengers rarely see aggregated in one place — a carrier near the bottom of this chart has systematically failed to operate a material portion of its scheduled flights, meaning thousands of travelers faced cancellations over this period. This is not just an inconvenience metric; carriers with low reliability scores face higher rebooking costs, compensation liabilities, and long-term reputational damage. The spread between the best and worst performers quantifies how much operational discipline varies across the industry.
<br><br>

### Figure 2.2: Major Passenger Carrier Departure Reliability Over Time

<img width="1146" height="513" alt="figure2 2" src="https://github.com/user-attachments/assets/7339956a-c2c2-4db5-b2dc-f9e47e717104" />
<br>
The 2020 dip visible across carriers reflects pandemic-era mass cancellations, but the more telling story is what happened after. Carriers that snapped back quickly had leaner, more adaptable operations, while those that continued to struggle post-2021 signal deeper structural issues in staffing, scheduling, or fleet management. A carrier whose reliability score declined after 2022 despite recovering passenger demand is particularly concerning, as it suggests the airline expanded its schedule faster than its operational capacity could support. These trends directly explain headlines about summer travel meltdowns at specific carriers in recent years.
<br><br>

### Figure 2.3: Reliability Score vs. Carrier Size (2015-Present

<img width="1144" height="508" alt="figure2 3" src="https://github.com/user-attachments/assets/e87cfd47-50e4-45c1-851a-ebb933304e81" />
<br>
If the dots cluster with larger carriers scoring lower, it confirms that operational scale introduces complexity that degrades reliability; a finding with real policy and consumer implications. Conversely, if large carriers score as well or better than small ones, it suggests that resources and infrastructure at scale actually support more consistent operations. The distribution of dots tells a story about whether the industry's biggest players are earning their market dominance through operational excellence or simply through network lock-in despite inferior reliability.
<br><br>

# VI. Streamlit App

The Snowflake dashboards were exported and rebuilt as a live Streamlit web application connected directly to Snowflake. The app renders all five figures interactively, organized into two tabs — one per analytical question — with a sidebar Compare Carriers control that lets users isolate specific airlines across every chart simultaneously. An industry average benchmark is always visible in each chart as a reference point. All data is queried live from Snowflake on load and cached for the session.

<img width="1432" height="762" alt="streamlit 1" src="https://github.com/user-attachments/assets/23796ba7-5671-4617-a1f0-4f0c2e52b94c" />
<br>

<img width="1431" height="762" alt="streamlit 2" src="https://github.com/user-attachments/assets/754a7352-3407-47bd-9ef8-ae2ab2ba79c2" />
<br>

<img width="1430" height="761" alt="streamlit 3" src="https://github.com/user-attachments/assets/c8cac033-6da0-48e3-9f32-946c17757a08" />
<br>

<img width="1430" height="762" alt="streamlit 4" src="https://github.com/user-attachments/assets/2008b91f-d9fb-4e99-b6f4-e24e3ff3e45b" />
<br>

<img width="1431" height="761" alt="streamlit 5" src="https://github.com/user-attachments/assets/6d9e29a9-e054-4b71-9e9b-6bba1479724a" />
<br><br>

### Interactive Element 1: Dashboard Tabs

The app is split into two tabs — one per analytical question — keeping the load factor and reliability dashboards visually separate. Switching tabs does not reset any filters, so a carrier selection made in one dashboard carries over immediately to the other. This interaction is built for more of a quality and user-experience aspect than a significant analytical value feature. 

<img width="1432" height="762" alt="functionality 1 1" src="https://github.com/user-attachments/assets/00c5984d-5cd3-44f9-945d-ee97fb45a290" />
<br>

<img width="1430" height="761" alt="functionality 1 2" src="https://github.com/user-attachments/assets/49676155-b069-4655-98fa-64829ad55ce3" />
<br><br>

### Interactive Element 2: Compare Carriers

The sidebar Compare Carriers multiselect allows users to isolate any subset of the 9 carriers across all five charts simultaneously. When a selection is made, unselected carriers are removed from every chart — and the Industry Average benchmark remains visible in every chart regardless of what is selected, always computed from all 9 carriers as a fixed reference point. Selecting none restores the full view; a Reset to All button clears the selection in one click.

This interaction is directly connected to the underlying data: filtering happens at the DataFrame level after each Snowflake query, and the benchmark never changes with the selection. Shown here filtered to Delta Air Lines and American Airlines — the comparison immediately surfaces how two of the largest U.S. carriers stack up against each other and against the industry average across load factor history, reliability ranking, reliability over time, and size-to-reliability position, across both dashboards at once without re-entering any parameters.

<img width="1432" height="762" alt="functionality 2 1" src="https://github.com/user-attachments/assets/0cf67947-7d81-4c3c-987e-08b1e6390964" />
<br>

<img width="1430" height="760" alt="functionality 2 2" src="https://github.com/user-attachments/assets/21003093-6628-4fef-bc19-cdc2e8c1c9d3" />
<br>

<img width="1427" height="760" alt="functionality 2 3" src="https://github.com/user-attachments/assets/633d8cfb-f67f-4da6-a804-434f1c7fca3f" />
<br>

<img width="1431" height="762" alt="functionality 2 4" src="https://github.com/user-attachments/assets/bf6c323b-1d5a-4cdd-8bf9-2549720ca531" />
<br>

<img width="1429" height="762" alt="functionality 2 5" src="https://github.com/user-attachments/assets/8fae7113-0a06-4612-b173-a037fadaebc5" />
<br>

<img width="1429" height="760" alt="functionality 2 6" src="https://github.com/user-attachments/assets/01c69de0-916e-4a8a-b3e3-9547a8daab94" />
<br>

<img width="1428" height="761" alt="functionality 2 7" src="https://github.com/user-attachments/assets/02c6de93-b6c0-4c39-a6c9-b44c8d3328b0" />
<br>

<img width="1427" height="760" alt="functionality 2 8" src="https://github.com/user-attachments/assets/8bdde5d8-3130-45eb-8663-d06ff601e5b7" />
<br>

# VII. AI Use Statement

Claude (Anthropic) was used throughout this project for dataset exploration, SQL query development, Streamlit app construction, and documentation writing. All queries were tested and verified in Snowflake by the team. Analytical decisions, question selection, and design judgments were made by the team — AI-generated output was reviewed, iterated on, and in several cases rejected or significantly revised before being accepted.

For a full account of what was prompted, what changed, and what was modified or rejected at each phase, see gen-ai-use-statement.md.


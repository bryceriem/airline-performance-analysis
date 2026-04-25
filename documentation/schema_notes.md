# USDOT Snowflake Schema Reference

**Database:** `SNOWFLAKE_PUBLIC_DATA_FREE`  
**Schema:** `PUBLIC_DATA_FREE`  
**Source:** BTS T-100 Domestic Segment Data — monthly non-stop domestic flight segments  
**History:** 1990–present | **Granularity:** Monthly | **Lag:** ~2.5 months

---

## Tables Overview

| Table | Rows | Type |
|---|---|---|
| `AIRCRAFT_CARRIER_INDEX` | 955 | Entity — carrier reference |
| `AIRCRAFT_INDEX` | 697 | Entity — aircraft reference |
| `AIRPORT_INDEX` | 5,107 | Entity — airport reference |
| `US_DEPARTMENT_OF_TRANSPORTATION_ATTRIBUTES` | 10 | Variable definitions |
| `US_DEPARTMENT_OF_TRANSPORTATION_ATTRIBUTES_PIT` | 10 | Attributes + validity timestamps |
| `US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES` | 123,250,510 | Fact — monthly measurements |
| `US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES_PIT` | 336,370,033 | Timeseries + validity timestamps |

---

## AIRCRAFT_CARRIER_INDEX

List of airline carriers with identification codes and operational details.

| Column | Type | Description | Example |
|---|---|---|---|
| `AIRCRAFT_CARRIER_ID` | VARCHAR | **PK.** Unique carrier ID. | `06700_61` |
| `CARRIER_NAME` | VARCHAR | Carrier name. | `SkyWest Airlines Inc. (Domestic)` |
| `CARRIER_WORLD_AREA_CODE` | NUMBER | DOT geographic area code for carrier's base. | `10` |
| `CARRIER_TYPE` | VARCHAR | Primary operational type. | `Domestic Carrier` |
| `OAI_CARRIER_TYPE` | VARCHAR | Detailed OAC classification (revenue-based). | `Commuter Carrier` |
| `STATE_GEO_ID` | VARCHAR | State identifier, joinable to GEOGRAPHY_INDEX. | `geoId/36` |
| `COUNTRY_GEO_ID` | VARCHAR | Country identifier, joinable to GEOGRAPHY_INDEX. | `country/USA` |

**OAI_CARRIER_TYPE values seen:** Major Carrier ($1B+), National Carrier ($100M–$1B), Large Regional ($20–100M), Medium Regional (under $20M), Commuter Carrier

---

## AIRCRAFT_INDEX

Aircraft type reference with manufacturer and configuration details.

| Column | Type | Description | Example |
|---|---|---|---|
| `AIRCRAFT_ID` | VARCHAR | **PK.** Unique aircraft type ID. | `15013` |
| `AIRCRAFT_NAME` | VARCHAR | Manufacturer and model name. | `Gulfstream G450` |
| `AIRCRAFT_GROUP` | VARCHAR | Size/engine classification. | `Jet, 2-Engine` |
| `CABIN_CONFIGURATION` | VARCHAR | Cabin layout type. | `Passenger` |

**CABIN_CONFIGURATION values:** `Passenger`, `Cargo`, `Combination Passenger/Cargo`  
**AIRCRAFT_GROUP values:** `Jet, 2-Engine`, `Jet, 3-Engine`, `Turbo-Prop, 1-Engine/2-Engine`, `Piston, 2-Engine`, `Piston, 3-Engine/4-Engine`, `Helicopter/Stol`

---

## AIRPORT_INDEX

All airports tracked in the DOT domestic segment data.

| Column | Type | Description | Example |
|---|---|---|---|
| `AIRPORT_ID` | VARCHAR | **PK.** DOT code + IATA code concatenated. | `36494NC6` |
| `AIRPORT_DOT_CODE` | NUMBER | DOT unique numeric identifier. | `36494` |
| `AIRPORT_NAME` | VARCHAR | Full airport name. | `Henderson Oxford` |
| `AIRPORT_ALPHA_CODE` | VARCHAR | IATA 3-letter code. | `DFW` |
| `AIRPORT_WORLD_AREA_CODE` | NUMBER | DOT geographic area code. | `36` |
| `LOCATION` | VARCHAR | City, State: Airport Name string. | `Denver, CO: Denver International` |
| `AIRPORT_CITY_NAME` | VARCHAR | City name. | `Dallas/Fort Worth` |
| `STATE_GEO_ID` | VARCHAR | State identifier, joinable to GEOGRAPHY_INDEX. | `geoId/48` |
| `COUNTRY_GEO_ID` | VARCHAR | Country identifier, joinable to GEOGRAPHY_INDEX. | `country/USA` |

---

## US_DEPARTMENT_OF_TRANSPORTATION_ATTRIBUTES

Defines the 10 measurable variables available in the timeseries table.

| Column | Type | Description |
|---|---|---|
| `VARIABLE` | VARCHAR | **PK.** Machine-readable variable identifier. |
| `VARIABLE_NAME` | VARCHAR | Human-readable name. |
| `MEASURE` | VARCHAR | Category of what is being measured. |
| `UNIT` | VARCHAR | Unit of measurement. |
| `FREQUENCY` | VARCHAR | Aggregation frequency (always `Monthly`). |

**All 10 variables:**

| VARIABLE | VARIABLE_NAME | MEASURE | UNIT |
|---|---|---|---|
| `PASSENGERS_TRANSPORTED` | Non-Stop Segment Passengers Transported | Cargo | Count |
| `AVAILABLE_SEATS` | Available Seats | Capacity | Count |
| `AVAILABLE_CAPACITY_PAYLOAD_POUNDS` | Available Payload | Capacity | Pounds |
| `AIRBORNE_IN_MINUTES` | Airborne Time | Flight Duration | Minutes |
| `MAIL_TRANSPORTED` | Non-Stop Segment Mail Transported | Cargo | Pounds |
| `DEPARTURES_PERFORMED` | Departures Performed | Departures | Count |
| `DEPARTURES_SCHEDULED` | Departures Scheduled | Departures | Count |
| `FREIGHT_TRANSPORTED` | Non-Stop Segment Freight Transported | Cargo | Pounds |
| `DISTANCE` | Distance Between Airports | Distance | Miles |
| `RAMP_IN_MINUTES` | Ramp to Ramp Time | Flight Duration | Minutes |

---

## US_DEPARTMENT_OF_TRANSPORTATION_ATTRIBUTES_PIT

Same as ATTRIBUTES but with validity timestamps for tracking historical changes.

Adds two columns to the ATTRIBUTES schema:

| Column | Type | Description |
|---|---|---|
| `_EFFECTIVE_START_TIMESTAMP` | TIMESTAMP_TZ | When this row became valid (ET). |
| `_EFFECTIVE_END_TIMESTAMP` | TIMESTAMP_TZ | When this row expired; NULL = currently active. |

---

## US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES

**Main fact table — 123M+ rows.** One row per unique flight segment + variable + month.

| Column | Type | Description | Example |
|---|---|---|---|
| `FLIGHT_TYPE_ID` | VARCHAR | **PK.** MD5 hash of carrier + aircraft + origin + destination. | `9772cfa436...` |
| `AIRCRAFT_CARRIER_ID` | VARCHAR | **FK → AIRCRAFT_CARRIER_INDEX** | `06700_31` |
| `AIRCRAFT_ID` | VARCHAR | **FK → AIRCRAFT_INDEX** | `62961` |
| `ORIGIN_AIRPORT_ID` | VARCHAR | **FK → AIRPORT_INDEX.AIRPORT_ID** | `30325DEN` |
| `DESTINATION_AIRPORT_ID` | VARCHAR | **FK → AIRPORT_INDEX.AIRPORT_ID** | `34794SGU` |
| `SERVICE_CLASS` | VARCHAR | Type of service (scheduled vs. non-scheduled). | `Scheduled Passenger/Cargo Service` |
| `VARIABLE` | VARCHAR | **FK → ATTRIBUTES.VARIABLE** | `DEPARTURES_PERFORMED` |
| `VARIABLE_NAME` | VARCHAR | Human-readable variable name. | `Departures Performed` |
| `DATE` | DATE | Month-end date for the record. | `2020-11-30` |
| `VALUE` | FLOAT | Measured value for the variable. | `61.0` |
| `UNIT` | VARCHAR | Unit of the value. | `Count` |

**SERVICE_CLASS values seen:** `Scheduled Passenger/Cargo Service`, `Scheduled All Cargo Service`, `Non-Scheduled Civilian Passenger Service`

> This table is in **long/narrow format** — each row is one variable for one segment in one month. To compare multiple variables for the same route, use `PIVOT` or self-joins on `FLIGHT_TYPE_ID + DATE`.

---

## US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES_PIT

Same as TIMESERIES but tracks row-level history. Adds two columns:

| Column | Type | Description |
|---|---|---|
| `_EFFECTIVE_START_TIMESTAMP` | TIMESTAMP_TZ | When this row became valid. |
| `_EFFECTIVE_END_TIMESTAMP` | TIMESTAMP_TZ | When this row expired; NULL = currently active. |

---

## Key Join Patterns

```sql
-- Standard join: timeseries → all reference tables
SELECT
    carrier.CARRIER_NAME,
    aircraft.AIRCRAFT_NAME,
    origin.AIRPORT_ALPHA_CODE    AS origin_iata,
    dest.AIRPORT_ALPHA_CODE      AS dest_iata,
    ts.VARIABLE_NAME,
    ts.DATE,
    ts.VALUE,
    ts.UNIT
FROM US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES ts
JOIN AIRCRAFT_CARRIER_INDEX carrier  ON ts.AIRCRAFT_CARRIER_ID    = carrier.AIRCRAFT_CARRIER_ID
JOIN AIRCRAFT_INDEX aircraft         ON ts.AIRCRAFT_ID             = aircraft.AIRCRAFT_ID
JOIN AIRPORT_INDEX origin            ON ts.ORIGIN_AIRPORT_ID       = origin.AIRPORT_ID
JOIN AIRPORT_INDEX dest              ON ts.DESTINATION_AIRPORT_ID  = dest.AIRPORT_ID
WHERE ts.VARIABLE = 'PASSENGERS_TRANSPORTED';
```

---

## Notes

- The `TIMESERIES` table uses an **EAV (Entity-Attribute-Value)** structure — filter on `VARIABLE` or `VARIABLE_NAME` to isolate a metric.
- `FLIGHT_TYPE_ID` is stable across time; the same route/carrier/aircraft combo always hashes to the same ID.
- `_PIT` tables are point-in-time snapshots useful for auditing data corrections (DOT updates past months retroactively).
- `STATE_GEO_ID` / `COUNTRY_GEO_ID` in carrier and airport tables are joinable to Snowflake's built-in `GEOGRAPHY_INDEX` for geospatial analysis.

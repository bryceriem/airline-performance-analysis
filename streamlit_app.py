import datetime as dt
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="U.S. Airline Performance Analysis", layout="wide")

# ── Snowflake session ─────────────────────────────────────────────────────────
session = st.connection("snowflake").session()

@st.cache_data(ttl="23h50m")
def execute_query(query: str) -> str:
    return session.sql(query).collect_nowait().query_id

def run(query: str) -> pd.DataFrame:
    return session.create_async_job(execute_query(query)).result("pandas")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("U.S. Airline Performance Analysis")
st.markdown(
    "Analyzing **load factor efficiency** and **departure reliability** across 9 major U.S. "
    "passenger carriers using USDOT T-100 domestic segment data."
)
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
ALL_CARRIERS = [
    "Southwest Airlines Co.",
    "American Airlines Inc.",
    "Delta Air Lines Inc.",
    "United Air Lines Inc.",
    "SkyWest Airlines Inc.",
    "Spirit Air Lines",
    "Alaska Airlines Inc.",
    "JetBlue Airways",
    "Frontier Airlines Inc."
]

if "comparison_selection" not in st.session_state:
    st.session_state["comparison_selection"] = []

def _reset_comparison():
    st.session_state["comparison_selection"] = []

with st.sidebar:
    st.markdown("### :material/search: Compare Carriers")
    st.caption("Select carriers to isolate them. All others are hidden. Industry average always shown.")

    comparison = st.multiselect(
        "Carriers",
        options=ALL_CARRIERS,
        key="comparison_selection",
        help="Select 2 or more carriers to focus on across all charts. "
             "Unselected carriers are hidden. Leave empty to show all 9."
    )

    if comparison:
        st.button(
            ":material/restart_alt: Reset to All",
            on_click=_reset_comparison,
            use_container_width=True
        )

    st.divider()
    st.caption("**Data source:** USDOT T-100 Domestic Segment via Snowflake Public Data")
    st.caption("**Qualifying filter:** Carriers with 100M+ passengers since 2020")

# ── Qualifying carriers CTE (shared across all queries) ───────────────────────
QUALIFYING_CTE = """
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
"""

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs([
    ":material/bar_chart: Dashboard 1 — Load Factor Efficiency",
    ":material/flight_takeoff: Dashboard 2 — Departure Reliability"
])

# ════════════════════════════════════════════════════════════════════════════
# DASHBOARD 1 — Load Factor Efficiency
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown(
        "_Among U.S. mainline passenger carriers with over 100 million passengers transported since 2020, "
        "which operate most efficiently as measured by load factor (passengers transported ÷ available seats), "
        "and how has that efficiency trended over time?_"
    )

    # Figure 1.1 — Line chart
    @st.cache_data(ttl="23h50m")
    def get_fig1_1():
        sql = f"""
        {QUALIFYING_CTE},
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
        """
        return session.create_async_job(execute_query(sql)).result("pandas")

    with st.container(border=True):
        st.markdown("#### Figure 1.1: U.S. Major Passenger Carrier Load Factor Over Time")
        try:
            df = get_fig1_1()
            if len(df) > 0:
                # Industry average benchmark (always computed from all 9)
                avg_df = df.groupby("YEAR")["LOAD_FACTOR_PCT"].mean().reset_index()

                # Filter to selected carriers if a comparison is active
                df_plot = df[df["CARRIER_NAME"].isin(comparison)] if comparison else df

                fig = px.line(
                    df_plot, x="YEAR", y="LOAD_FACTOR_PCT", color="CARRIER_NAME",
                    labels={"YEAR": "Year", "LOAD_FACTOR_PCT": "Load Factor (%)", "CARRIER_NAME": "Carrier"},
                    height=420
                )
                fig.add_scatter(
                    x=avg_df["YEAR"], y=avg_df["LOAD_FACTOR_PCT"],
                    mode="lines", name="Industry Avg",
                    line=dict(color="grey", dash="dash", width=2)
                )
                fig.update_layout(legend_title_text="Carrier", hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
        st.caption(
            "The COVID-19 pandemic caused a near-collapse in load factors in 2020, but recovery speeds varied. "
            "Carriers returning to pre-pandemic levels quickly demonstrate stronger capacity discipline. "
            "A carrier consistently 10 points below peers is leaving significant revenue on the table per flight."
        )

    # Figure 1.2 — Heatmap
    @st.cache_data(ttl="23h50m")
    def get_fig1_2():
        sql = f"""
        {QUALIFYING_CTE},
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
        """
        return session.create_async_job(execute_query(sql)).result("pandas")

    with st.container(border=True):
        st.markdown("#### Figure 1.2: Load Factor Efficiency by Major Carrier and Year")
        try:
            df = get_fig1_2()
            if len(df) > 0:
                full_pivot = df.pivot(index="CARRIER_NAME", columns="YEAR", values="LOAD_FACTOR_PCT")

                # Average row (always included, computed from all 9)
                avg_row = df.groupby("YEAR")["LOAD_FACTOR_PCT"].mean().rename("Industry Avg")
                avg_pivot = pd.DataFrame(avg_row).T

                # Filter carrier rows if comparison active
                pivot_df = full_pivot.loc[full_pivot.index.isin(comparison)] if comparison else full_pivot
                pivot_df = pd.concat([pivot_df, avg_pivot])

                fig = go.Figure(data=go.Heatmap(
                    z=pivot_df.values,
                    x=pivot_df.columns.tolist(),
                    y=pivot_df.index.tolist(),
                    colorscale="Blues",
                    text=pivot_df.values,
                    texttemplate="%{text:.1f}%",
                    colorbar=dict(title="Load Factor (%)"),
                    hovertemplate="Carrier: %{y}<br>Year: %{x}<br>Load Factor: %{z:.1f}%<extra></extra>"
                ))
                fig.update_layout(
                    xaxis_title="Year", yaxis_title="Carrier",
                    height=420, margin=dict(l=20, r=20, t=20, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
        st.caption(
            "Darker cells indicate higher load factors. Consistently dark rows reveal structurally lean carriers "
            "that fill planes reliably across all market conditions. Light or patchy rows signal chronic overcapacity, "
            "which pressures margins and often leads to fare discounting."
        )

# ════════════════════════════════════════════════════════════════════════════
# DASHBOARD 2 — Departure Reliability
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(
        "_Among U.S. mainline passenger carriers with over 100 million passengers transported since 2020, "
        "which have the largest gap between scheduled and performed departures, "
        "and does reliability correlate with carrier size?_"
    )

    # Figure 2.1 — Bar chart
    @st.cache_data(ttl="23h50m")
    def get_fig2_1():
        sql = f"""
        {QUALIFYING_CTE},
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
        """
        return session.create_async_job(execute_query(sql)).result("pandas")

    with st.container(border=True):
        st.markdown("#### Figure 2.1: Major Passenger Carrier Reliability Score Rankings")
        try:
            df = get_fig2_1()
            if len(df) > 0:
                avg_score = df["RELIABILITY_SCORE"].mean()
                df_plot = df[df["CARRIER_NAME"].isin(comparison)] if comparison else df

                fig = px.bar(
                    df_plot, x="RELIABILITY_SCORE", y="CARRIER_NAME", orientation="h",
                    color="RELIABILITY_SCORE", color_continuous_scale="RdYlGn",
                    labels={"RELIABILITY_SCORE": "Reliability Score (%)", "CARRIER_NAME": "Carrier"},
                    height=420
                )
                fig.add_vline(
                    x=avg_score, line_dash="dash", line_color="grey", line_width=2,
                    annotation_text=f"Industry Avg: {avg_score:.1f}%",
                    annotation_position="top"
                )
                fig.update_layout(yaxis=dict(categoryorder="total ascending"), coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
        st.caption(
            "A carrier near the bottom has systematically failed to operate a material portion of its scheduled flights. "
            "Low reliability drives higher rebooking costs, compensation liabilities, and long-term reputational damage. "
            "The spread between best and worst quantifies how much operational discipline varies across the industry."
        )

    # Figure 2.2 — Line chart
    @st.cache_data(ttl="23h50m")
    def get_fig2_2():
        sql = f"""
        {QUALIFYING_CTE},
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
        """
        return session.create_async_job(execute_query(sql)).result("pandas")

    with st.container(border=True):
        st.markdown("#### Figure 2.2: Major Passenger Carrier Departure Reliability Over Time")
        try:
            df = get_fig2_2()
            if len(df) > 0:
                avg_df = df.groupby("YEAR")["RELIABILITY_SCORE"].mean().reset_index()
                df_plot = df[df["CARRIER_NAME"].isin(comparison)] if comparison else df

                fig = px.line(
                    df_plot, x="YEAR", y="RELIABILITY_SCORE", color="CARRIER_NAME",
                    labels={"YEAR": "Year", "RELIABILITY_SCORE": "Reliability Score (%)", "CARRIER_NAME": "Carrier"},
                    height=420
                )
                fig.add_scatter(
                    x=avg_df["YEAR"], y=avg_df["RELIABILITY_SCORE"],
                    mode="lines", name="Industry Avg",
                    line=dict(color="grey", dash="dash", width=2)
                )
                fig.update_yaxes(range=[90, 120])
                fig.update_layout(legend_title_text="Carrier", hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
        st.caption(
            "The 2020 dip reflects pandemic-era mass cancellations. Carriers that snapped back quickly had leaner, "
            "more adaptable operations. A carrier whose score declined post-2022 despite recovering demand suggests "
            "it expanded its schedule faster than its operational capacity could support."
        )

    # Figure 2.3 — Scatter chart
    @st.cache_data(ttl="23h50m")
    def get_fig2_3():
        sql = f"""
        {QUALIFYING_CTE},
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
        """
        return session.create_async_job(execute_query(sql)).result("pandas")

    with st.container(border=True):
        st.markdown("#### Figure 2.3: Reliability Score vs. Carrier Size")
        try:
            df = get_fig2_3()
            if len(df) > 0:
                avg_reliability = df["RELIABILITY_SCORE"].mean()
                df_plot = df[df["CARRIER_NAME"].isin(comparison)] if comparison else df

                fig = px.scatter(
                    df_plot, x="CARRIER_SIZE", y="RELIABILITY_SCORE", color="CARRIER_NAME",
                    hover_name="CARRIER_NAME",
                    labels={
                        "CARRIER_SIZE": "Total Scheduled Departures (Size Proxy)",
                        "RELIABILITY_SCORE": "Reliability Score (%)",
                        "CARRIER_NAME": "Carrier"
                    },
                    height=420
                )
                fig.add_hline(
                    y=avg_reliability, line_dash="dash", line_color="grey", line_width=2,
                    annotation_text=f"Industry Avg: {avg_reliability:.1f}%",
                    annotation_position="top right"
                )
                fig.update_traces(marker=dict(size=14))
                fig.update_yaxes(range=[97, 104])
                fig.update_layout(legend_title_text="Carrier")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
        st.caption(
            "Each dot is one carrier. If larger carriers (right side) cluster lower, scale degrades reliability. "
            "If they score equally or better, infrastructure at scale supports consistent operations. "
            "The distribution reveals whether dominance reflects operational excellence or just network lock-in."
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f":material/database: Data: USDOT T-100 Domestic Segment via Snowflake Public Data  ·  "
    f":material/schedule: Loaded: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

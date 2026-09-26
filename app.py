import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import traceback

# ============================================================
# MARKETLENS — MARKETING INTELLIGENCE
# ============================================================

st.set_page_config(
    page_title="MarketLens | Marketing Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PATHS
# ============================================================

def find_project_root(start, marker="analysis", max_up=4):
    """
    Walk upward from `start` looking for a folder that contains `marker`
    as a subfolder. This makes the app work no matter how deep app.py
    is nested, instead of hardcoding a fixed number of parent hops
    (which is what silently broke the paths before).
    """
    current = start
    for _ in range(max_up + 1):
        if (current / marker).exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    # Fall back to the script's own folder if nothing was found
    return start


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = find_project_root(SCRIPT_DIR, marker="analysis")

TABLES = ROOT / "analysis" / "outputs" / "tables"
AB_TEST = ROOT / "ab_testing" / "reports"
GA4 = ROOT / "g4 case study"

# ============================================================
# CUSTOM CSS
# ============================================================

# Colorblind-safe categorical palette (Okabe–Ito), reordered so the
# calmer blue/teal tones lead. Safe for deuteranopia, protanopia and
# tritanopia — never relies on red/green alone to distinguish series.
CHART_COLORWAY = [
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # bluish green
    "#CC79A7",  # reddish purple
    "#56B4E9",  # sky blue
    "#D55E00",  # vermillion
    "#F0E442",  # yellow
]

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #0e1117;
        --bg-panel: #161a23;
        --bg-panel-2: #1c212c;
        --border: #2a3040;
        --text-primary: #f5f7fb;    /* near-white, for headings/values */
        --text-secondary: #d3d9e6;  /* light gray-blue, for body copy — must stay light */
        --text-muted: #a7aec2;      /* only for small labels, never for body text */
        --accent: #7cc4f0;          /* sky blue - colorblind safe */
        --accent-2: #3ccaa8;        /* bluish green - colorblind safe */
        --warn-bg: #3a2f14;
        --warn-border: #6b5620;
        --warn-text: #f0d488;
    }

    html { font-size: 17px; }

    html, body, .stApp, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .stApp { background-color: var(--bg); }

    /* ---------- Base text: force light, readable color everywhere ---------- */
    body, .stApp, .stMarkdown, [data-testid="stMarkdownContainer"],
    [data-testid="stText"], [data-testid="stCaptionContainer"],
    .stApp p, .stApp li, .stApp span, .stApp div {
        color: var(--text-secondary) !important;
        font-size: 1rem;
        line-height: 1.65;
    }

    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {
        color: var(--text-primary) !important;
    }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] { background-color: var(--bg-panel); border-right: 1px solid var(--border); }
    [data-testid="stSidebar"] * { color: var(--text-primary) !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] li {
        color: var(--text-secondary) !important;
        font-size: 1rem !important;
    }
    [data-testid="stSidebar"] label {
        color: var(--text-primary) !important;
        font-weight: 500;
        font-size: 1rem !important;
    }
    [data-testid="stSidebar"] h2 { font-size: 1.4rem !important; }

    label, .stSelectbox label, .stRadio label {
        color: var(--text-primary) !important;
        font-size: 1rem !important;
    }

    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 0;
        color: var(--text-primary) !important;
    }

    .subtitle {
        color: var(--accent) !important;
        font-size: 1.15rem;
        font-weight: 600;
        margin-top: 6px;
        margin-bottom: 26px;
    }

    .kpi-card {
        background: var(--bg-panel-2);
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent);
        border-radius: 12px;
        padding: 18px 20px;
        min-height: 110px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    }

    .kpi-label {
        color: var(--text-muted) !important;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .kpi-value {
        color: var(--text-primary) !important;
        font-size: 1.75rem;
        font-weight: 700;
        margin-top: 8px;
    }

    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 32px;
        margin-bottom: 14px;
        color: var(--text-primary) !important;
        border-bottom: 1px solid var(--border);
        padding-bottom: 8px;
    }

    .info-box {
        background-color: var(--bg-panel-2);
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent-2);
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 15px;
        color: var(--text-secondary) !important;
        font-size: 1rem;
        line-height: 1.7;
    }

    .info-box b { color: var(--text-primary) !important; }

    .small-text { color: var(--text-muted) !important; font-size: 0.85rem; }

    /* ---------- Streamlit's own info/warning/success/error boxes ---------- */
    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] span,
    div[data-testid="stAlertContent"] p {
        color: var(--text-primary) !important;
        font-size: 1rem !important;
    }
    div[data-testid="stAlertContentInfo"] { background-color: #123a52 !important; }
    div[data-testid="stAlertContentWarning"] { background-color: var(--warn-bg) !important; }
    div[data-testid="stAlertContentSuccess"] { background-color: #123a30 !important; }
    div[data-testid="stAlertContentError"] { background-color: #3a1414 !important; }

    /* ---------- Tabs ---------- */
    button[data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        font-size: 1rem !important;
        font-weight: 500;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--accent) !important;
        font-weight: 700;
    }

    /* ---------- Dataframes / tables ---------- */
    [data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 8px; }
    [data-testid="stDataFrame"] * { color: var(--text-secondary) !important; }

    /* ---------- Expander ---------- */
    [data-testid="stExpander"] summary {
        color: var(--text-primary) !important;
        font-size: 1rem !important;
        font-weight: 600;
    }

    /* ---------- Selectbox current value / dropdown ---------- */
    [data-baseweb="select"] * { color: var(--text-primary) !important; }

    /* ---------- Code blocks (tracebacks) ---------- */
    pre, code { color: #f0d488 !important; }

    /* ---------- Footer text ---------- */
    .footer-text, .footer-text * { color: var(--text-muted) !important; }
    </style>
    """,
    unsafe_allow_html=True
)


def style_chart(fig, title=None):
    """Apply the app's calm, colorblind-safe theme to a plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#f5f7fb", size=14),
        title_font=dict(size=18, color="#f5f7fb"),
        colorway=CHART_COLORWAY,
        margin=dict(t=50, l=10, r=10, b=10),
        legend=dict(font=dict(color="#d3d9e6", size=13)),
    )
    fig.update_xaxes(gridcolor="#2a3040", color="#d3d9e6", title_font=dict(color="#d3d9e6", size=13),
                      tickfont=dict(size=12))
    fig.update_yaxes(gridcolor="#2a3040", color="#d3d9e6", title_font=dict(color="#d3d9e6", size=13),
                      tickfont=dict(size=12))
    if title:
        fig.update_layout(title=title)
    return fig

# ============================================================
# ALWAYS RENDER SOMETHING FIRST
# ============================================================
# The header renders immediately, before any file loading, so even if
# data files are missing or a path is wrong, the page is never blank.

st.markdown('<div class="main-title">MARKETLENS</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Marketing Intelligence & Performance Analytics</div>',
    unsafe_allow_html=True
)

# ============================================================
# HELPERS
# ============================================================


def load_csv(filename, folder=TABLES):
    """Load a CSV safely, never raising."""
    try:
        path = folder / filename
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path)
    except Exception as e:
        st.warning(f"Could not load {filename}: {e}")
        return pd.DataFrame()


def normalize_columns(df):
    if df.empty:
        return df
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
        .str.replace("/", "_", regex=False)
    )
    return df


def find_column(df, possible_names):
    if df.empty:
        return None
    cols = {str(c).lower(): c for c in df.columns}
    for name in possible_names:
        if name.lower() in cols:
            return cols[name.lower()]
    for name in possible_names:
        for col in df.columns:
            if name.lower() in str(col).lower():
                return col
    return None


def numeric_value(df, possible_names, default=0):
    col = find_column(df, possible_names)
    if col is None or df.empty:
        return default
    try:
        return float(pd.to_numeric(df[col], errors="coerce").iloc[0])
    except Exception:
        return default


def long_format_value(df, possible_metric_names, default=0):
    """
    Handle a 'tall' KPI table shaped like:
        metric          | value
        total_spend     | 33500
        total_revenue   | 101760
    instead of one row with each metric as its own column. Returns the
    first matching row's value, or `default` if the shape doesn't match
    or nothing is found.
    """
    if df.empty:
        return default

    key_col = find_column(df, ["metric", "kpi", "name", "label"])
    val_col = find_column(df, ["value", "amount", "result"])

    if key_col is None or val_col is None:
        return default

    keys = df[key_col].astype(str).str.strip().str.lower()

    for name in possible_metric_names:
        match = df[keys == name.lower()]
        if not match.empty:
            try:
                return float(pd.to_numeric(match[val_col], errors="coerce").iloc[0])
            except Exception:
                continue
        # partial match fallback
        match = df[keys.str.contains(name.lower(), na=False)]
        if not match.empty:
            try:
                return float(pd.to_numeric(match[val_col], errors="coerce").iloc[0])
            except Exception:
                continue

    return default


def get_overall_kpi(df, possible_names, fallback_df=None, fallback_names=None,
                     fallback_agg="sum", default=0):
    """
    Robustly pull one KPI value, trying in order:
      1. Wide format: a column named like the metric, first row.
      2. Long format: a metric/value pair of columns.
      3. A fallback dataframe (e.g. campaign-level data), aggregated.
    This means the Executive Overview KPIs still populate even if
    global_ads_overall_kpis.csv isn't shaped exactly as expected.
    """
    value = numeric_value(df, possible_names, default=None)
    if value not in (None, 0):
        return value

    value = long_format_value(df, possible_names, default=None)
    if value not in (None, 0):
        return value

    if fallback_df is not None and not fallback_df.empty and fallback_names:
        col = find_column(fallback_df, fallback_names)
        if col:
            try:
                series = pd.to_numeric(fallback_df[col], errors="coerce")
                if fallback_agg == "sum":
                    return float(series.sum())
                elif fallback_agg == "mean":
                    return float(series.mean())
            except Exception:
                pass

    return default if value is None else value


def format_number(value):
    if value is None or pd.isna(value):
        return "—"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def format_currency(value):
    if value is None or pd.isna(value):
        return "—"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.2f}"


def format_percent(value):
    if value is None or pd.isna(value):
        return "—"
    if value <= 1:
        value = value * 100
    return f"{value:.2f}%"


def format_ratio(value):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.2f}x"


def kpi_card(title, value):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def safe_section(section_name, func):
    """Run a page section; show the error instead of crashing the whole app."""
    try:
        func()
    except Exception:
        st.error(f"Something went wrong while rendering '{section_name}'. See details below.")
        st.code(traceback.format_exc())


# ============================================================
# LOAD DATA
# ============================================================

overall = normalize_columns(load_csv("global_ads_overall_kpis.csv"))
platform = normalize_columns(load_csv("global_ads_platform_performance.csv"))
campaign = normalize_columns(load_csv("global_ads_campaign_performance.csv"))
country = normalize_columns(load_csv("global_ads_country_performance.csv"))
industry = normalize_columns(load_csv("global_ads_industry_performance.csv"))
kag_funnel = normalize_columns(load_csv("kag_overall_funnel.csv"))
kag_campaign = normalize_columns(load_csv("kag_campaign_performance.csv"))
kag_age = normalize_columns(load_csv("kag_age_performance.csv"))
kag_gender = normalize_columns(load_csv("kag_gender_performance.csv"))
kag_interest = normalize_columns(load_csv("kag_interest_performance.csv"))
ab_test = normalize_columns(load_csv("ab_test_group_metrics.csv", AB_TEST))

with st.expander("🔧 Diagnostics (click if the dashboard looks empty)"):
    st.write("**Script location (`__file__`):**", str(Path(__file__).resolve()))
    st.write("**Script's own folder:**", str(SCRIPT_DIR))
    st.write("**Auto-detected ROOT:**", str(ROOT))
    st.write("**Looking for tables in:**", str(TABLES), "→ exists:", TABLES.exists())
    st.write("**Looking for A/B reports in:**", str(AB_TEST), "→ exists:", AB_TEST.exists())
    st.write("**Looking for GA4 folder in:**", str(GA4), "→ exists:", GA4.exists())
    if TABLES.exists():
        st.write("CSV files found in TABLES:", [p.name for p in TABLES.glob("*.csv")])
    else:
        st.error(
            "ROOT auto-detection didn't find an 'analysis' folder anywhere in the "
            "parent directories of this script. Double-check that app.py truly sits "
            "next to the 'analysis', 'ab_testing' and 'g4 case study' folders."
        )

    st.markdown("---")
    st.write("**global_ads_overall_kpis.csv — loaded shape** (drives Executive Overview KPIs):")
    if overall.empty:
        st.write("This file loaded empty or wasn't found — KPIs will fall back to campaign-level totals.")
    else:
        st.write("Columns after normalization:", list(overall.columns))
        st.dataframe(overall, width='stretch')

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <h2>📊 MARKETLENS</h2>
    <p style="color:#9298a6;">Marketing Intelligence</p>
    """,
    unsafe_allow_html=True
)
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Overview",
        "Campaign Analysis",
        "Audience Analysis",
        "A/B Testing",
        "GA4 Case Study"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Project Coverage**

    • Marketing Analytics  
    • Performance Marketing  
    • Audience Segmentation  
    • A/B Testing  
    • GA4 Analytics  
    • Business Intelligence
    """
)

# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

def render_executive_overview():
    st.markdown(
        """
        This dashboard brings together campaign performance,
        audience analytics and experimental results into a single
        marketing intelligence view.
        """
    )

    spend = get_overall_kpi(
        overall, ["total_spend", "spend", "ad_spend"],
        fallback_df=campaign, fallback_names=["spend", "ad_spend", "total_spend"]
    )
    revenue = get_overall_kpi(
        overall, ["total_revenue", "revenue", "sales"],
        fallback_df=campaign, fallback_names=["revenue", "total_revenue", "sales"]
    )
    conversions = get_overall_kpi(
        overall, ["total_conversions", "conversions", "conversion"],
        fallback_df=campaign, fallback_names=["conversions", "total_conversions"]
    )
    ctr = get_overall_kpi(
        overall, ["ctr", "average_ctr", "click_through_rate"],
        fallback_df=campaign, fallback_names=["ctr", "click_through_rate"], fallback_agg="mean"
    )
    cpa = get_overall_kpi(
        overall, ["cpa", "cost_per_acquisition"],
        fallback_df=campaign, fallback_names=["cpa", "cost_per_acquisition"], fallback_agg="mean"
    )
    roas = get_overall_kpi(
        overall, ["roas", "return_on_ad_spend"],
        fallback_df=campaign, fallback_names=["roas", "return_on_ad_spend"], fallback_agg="mean"
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Total Spend", format_currency(spend))
    with c2:
        kpi_card("Total Revenue", format_currency(revenue))
    with c3:
        kpi_card("Conversions", format_number(conversions))

    c4, c5, c6 = st.columns(3)
    with c4:
        kpi_card("CTR", format_percent(ctr))
    with c5:
        kpi_card("CPA", format_currency(cpa))
    with c6:
        kpi_card("ROAS", format_ratio(roas))

    st.markdown('<div class="section-title">Platform Performance</div>', unsafe_allow_html=True)

    if not platform.empty:
        platform_name = find_column(platform, ["platform", "channel", "source"])
        revenue_col = find_column(platform, ["revenue", "total_revenue", "sales"])
        roas_col = find_column(platform, ["roas", "return_on_ad_spend"])

        if platform_name and revenue_col:
            chart = px.bar(platform, x=platform_name, y=revenue_col, color=platform_name,
                            color_discrete_sequence=CHART_COLORWAY)
            style_chart(chart, title="Revenue by Platform")
            chart.update_layout(showlegend=False)
            st.plotly_chart(chart, width='stretch')

        if roas_col and platform_name:
            chart2 = px.bar(platform, x=platform_name, y=roas_col, color=platform_name,
                             color_discrete_sequence=CHART_COLORWAY)
            style_chart(chart2, title="ROAS by Platform")
            chart2.update_layout(showlegend=False)
            st.plotly_chart(chart2, width='stretch')
    else:
        st.info("Platform performance data was not found.")

    st.markdown('<div class="section-title">Campaign Performance</div>', unsafe_allow_html=True)

    if not campaign.empty:
        campaign_name = find_column(campaign, ["campaign", "campaign_name", "campaign_type"])
        revenue_col = find_column(campaign, ["revenue", "total_revenue", "sales"])

        if campaign_name and revenue_col:
            top_campaigns = campaign.sort_values(revenue_col, ascending=False).head(10)
            chart = px.bar(top_campaigns, x=campaign_name, y=revenue_col, color=campaign_name,
                            color_discrete_sequence=CHART_COLORWAY)
            style_chart(chart, title="Top Campaigns by Revenue")
            chart.update_layout(showlegend=False)
            st.plotly_chart(chart, width='stretch')
    else:
        st.info("Campaign performance data was not found.")


def render_campaign_analysis():
    if campaign.empty:
        st.warning("Campaign performance file was not found.")
        return

    campaign_name = find_column(campaign, ["campaign", "campaign_name", "campaign_type"])
    spend_col = find_column(campaign, ["spend", "ad_spend", "total_spend"])
    revenue_col = find_column(campaign, ["revenue", "total_revenue", "sales"])
    roas_col = find_column(campaign, ["roas", "return_on_ad_spend"])
    ctr_col = find_column(campaign, ["ctr", "click_through_rate"])
    cpa_col = find_column(campaign, ["cpa", "cost_per_acquisition"])

    if campaign_name:
        selected_campaign = st.selectbox(
            "Select Campaign",
            sorted(campaign[campaign_name].dropna().astype(str).unique())
        )
        filtered = campaign[campaign[campaign_name].astype(str) == selected_campaign]

        if not filtered.empty:
            row = filtered.iloc[0]
            cols = st.columns(5)
            metrics = [
                ("Spend", spend_col, format_currency),
                ("Revenue", revenue_col, format_currency),
                ("ROAS", roas_col, format_ratio),
                ("CTR", ctr_col, format_percent),
                ("CPA", cpa_col, format_currency)
            ]
            for col, (label, field, formatter) in zip(cols, metrics):
                with col:
                    value = row[field] if field else None
                    kpi_card(label, formatter(value))

    st.markdown('<div class="section-title">Campaign Performance Table</div>', unsafe_allow_html=True)
    st.dataframe(campaign, width='stretch', hide_index=True)

    if campaign_name and revenue_col:
        top15 = campaign.sort_values(revenue_col, ascending=False).head(15)
        fig = px.bar(top15, x=campaign_name, y=revenue_col, color=campaign_name,
                     color_discrete_sequence=CHART_COLORWAY)
        style_chart(fig, title="Campaign Revenue")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')


def render_audience_analysis():
    tabs = st.tabs(["Age", "Gender", "Interest", "Campaign"])

    with tabs[0]:
        if not kag_age.empty:
            st.dataframe(kag_age, width='stretch', hide_index=True)
            age_col = find_column(kag_age, ["age", "age_group"])
            conv_col = find_column(kag_age, ["conversion_rate", "conversion", "conversions"])
            if age_col and conv_col:
                fig = px.bar(kag_age, x=age_col, y=conv_col, color=age_col,
                             color_discrete_sequence=CHART_COLORWAY)
                style_chart(fig, title="Conversion Performance by Age")
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, width='stretch')
        else:
            st.info("Age analysis data not available.")

    with tabs[1]:
        if not kag_gender.empty:
            st.dataframe(kag_gender, width='stretch', hide_index=True)
            gender_col = find_column(kag_gender, ["gender", "sex"])
            conv_col = find_column(kag_gender, ["conversion_rate", "conversion", "conversions"])
            if gender_col and conv_col:
                fig = px.bar(kag_gender, x=gender_col, y=conv_col, color=gender_col,
                             color_discrete_sequence=CHART_COLORWAY)
                style_chart(fig, title="Conversion Performance by Gender")
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, width='stretch')
        else:
            st.info("Gender analysis data not available.")

    with tabs[2]:
        if not kag_interest.empty:
            st.dataframe(kag_interest, width='stretch', hide_index=True)
            interest_col = find_column(kag_interest, ["interest", "interest_category"])
            conv_col = find_column(kag_interest, ["conversion_rate", "conversion", "conversions"])
            if interest_col and conv_col:
                top_interest = kag_interest.sort_values(conv_col, ascending=False).head(15)
                fig = px.bar(top_interest, x=interest_col, y=conv_col, color=interest_col,
                             color_discrete_sequence=CHART_COLORWAY)
                style_chart(fig, title="Top Interest Segments")
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, width='stretch')
        else:
            st.info("Interest analysis data not available.")

    with tabs[3]:
        if not kag_campaign.empty:
            st.dataframe(kag_campaign, width='stretch', hide_index=True)
        else:
            st.info("KAG campaign analysis data not available.")


def render_ab_testing():
    control_rate = 0.01785410644448223
    treatment_rate = 0.025546559636683747
    absolute_lift = treatment_rate - control_rate
    relative_lift = absolute_lift / control_rate

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Control Rate", f"{control_rate * 100:.2f}%")
    with c2:
        kpi_card("Treatment Rate", f"{treatment_rate * 100:.2f}%")
    with c3:
        kpi_card("Absolute Lift", f"{absolute_lift * 100:.2f} pp")
    with c4:
        kpi_card("Relative Lift", f"{relative_lift * 100:.2f}%")

    ab_chart = pd.DataFrame({
        "Group": ["Control", "Treatment"],
        "Conversion Rate": [control_rate * 100, treatment_rate * 100]
    })

    fig = px.bar(ab_chart, x="Group", y="Conversion Rate", text="Conversion Rate",
                 color="Group", color_discrete_sequence=["#56B4E9", "#E69F00"])
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    style_chart(fig, title="Control vs Treatment Conversion Rate")
    fig.update_layout(yaxis_title="Conversion Rate (%)", showlegend=False)
    st.plotly_chart(fig, width='stretch')

    st.markdown('<div class="section-title">Statistical Test</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    with s1:
        kpi_card("Z-Statistic", "7.3701")
    with s2:
        kpi_card("P-Value", "< 0.001")
    with s3:
        kpi_card("95% CI", "0.60% – 0.94%")

    st.markdown(
        """
        <div class="info-box">
        <b>Statistical Interpretation</b><br><br>
        The two-proportion Z-test produced a statistically significant
        difference between the control and treatment conversion rates
        at α = 0.05.
        <br><br>
        The treatment group recorded the higher observed conversion rate
        in the analyzed experiment.
        </div>
        """,
        unsafe_allow_html=True
    )

    if not ab_test.empty:
        st.markdown('<div class="section-title">A/B Test Group Metrics</div>', unsafe_allow_html=True)
        st.dataframe(ab_test, width='stretch', hide_index=True)

    st.markdown('<div class="section-title">Business Interpretation</div>', unsafe_allow_html=True)
    st.markdown(
        """
        The treatment group achieved a higher observed conversion rate
        than the control group.

        The observed difference is statistically significant based on
        the two-proportion Z-test. However, statistical significance
        does not by itself establish profitability or long-term business
        impact.

        Additional analysis should consider campaign cost, incremental
        revenue, customer value and experiment quality before making a
        scaling decision.
        """
    )


def render_ga4_case_study():
    st.markdown(
        """
        This section presents the GA4 Demo Account case study conducted
        using the Google Merchandise Store demonstration property.
        """
    )
    st.markdown("---")

    report_file = GA4 / "GA4_CASE_STUDY.md"

    if report_file.exists():
        st.success("GA4 case study report found in the project.")
        report_text = None
        # Try common encodings in order; Windows-saved .md files are
        # frequently cp1252/latin-1, not UTF-8, which caused the crash.
        for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
            try:
                with open(report_file, "r", encoding=encoding) as f:
                    report_text = f.read()
                break
            except UnicodeDecodeError:
                continue
        if report_text is None:
            # Last resort: read as bytes and drop anything undecodable
            with open(report_file, "rb") as f:
                report_text = f.read().decode("utf-8", errors="ignore")
        st.markdown(report_text)
    else:
        st.warning("GA4_CASE_STUDY.md was not found.")

    st.markdown('<div class="section-title">GA4 Screenshots</div>', unsafe_allow_html=True)

    screenshot_files = [
        "g4 home 01.png",
        "acquisition overview 02.png",
        "engagement overview 03.png",
        "engagement events 04.png",
        "conversions event 05.png",
        "ecommerce purchase 06.png",
        "purchase journe7.png"
    ]

    found_any = False
    for filename in screenshot_files:
        image_path = GA4 / filename
        if image_path.exists():
            found_any = True
            st.image(str(image_path), caption=filename, width='stretch')

    if not found_any:
        st.info("No GA4 screenshots were found in the expected folder.")


# ============================================================
# PAGE ROUTER — each page runs inside safe_section so one bad
# section can never blank out the whole app
# ============================================================

if page == "Executive Overview":
    st.markdown('<div class="section-title">Executive Overview</div>', unsafe_allow_html=True)
    safe_section("Executive Overview", render_executive_overview)

elif page == "Campaign Analysis":
    st.markdown('<div class="section-title">Campaign Analysis</div>', unsafe_allow_html=True)
    safe_section("Campaign Analysis", render_campaign_analysis)

elif page == "Audience Analysis":
    st.markdown('<div class="section-title">Audience Analysis</div>', unsafe_allow_html=True)
    safe_section("Audience Analysis", render_audience_analysis)

elif page == "A/B Testing":
    st.markdown('<div class="section-title">A/B Testing</div>', unsafe_allow_html=True)
    safe_section("A/B Testing", render_ab_testing)

elif page == "GA4 Case Study":
    st.markdown('<div class="section-title">GA4 Case Study</div>', unsafe_allow_html=True)
    safe_section("GA4 Case Study", render_ga4_case_study)

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.markdown(
    """
    <div class="footer-text" style="text-align:center;padding:20px;font-size:0.95rem;">
        <b style="color:#d3d9e6;">MarketLens</b> · Marketing Analytics · A/B Testing · GA4 · Business Intelligence
        <br>
        <small>Built by Pranoti Ashok Munjankar</small>
    </div>
    """,
    unsafe_allow_html=True
)
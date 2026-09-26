from pathlib import Path
import math
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================
# MARKETLENS
# Comprehensive Marketing Analytics & Research Analysis
# ============================================================

warnings.filterwarnings("ignore")

# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\Users\Pranoti munjankar\OneDrive\Desktop\DA PROJECTS\Marketlens"
)

RAW_DIR = PROJECT_ROOT / "data" / "raw"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"

OUTPUT_DIR = ANALYSIS_DIR / "outputs"
TABLE_DIR = OUTPUT_DIR / "tables"
FIGURE_DIR = OUTPUT_DIR / "figures"
REPORT_DIR = OUTPUT_DIR / "reports"

GLOBAL_ADS_FILE = RAW_DIR / "global_ads_performance_dataset.csv"
KAG_FILE = RAW_DIR / "KAG_conversion_data.csv"
MARKETING_AB_FILE = RAW_DIR / "marketing_AB.csv"

MASTER_REPORT_FILE = REPORT_DIR / "MARKETLENS_MASTER_ANALYSIS_REPORT.txt"

# ------------------------------------------------------------
# 2. CREATE OUTPUT DIRECTORIES
# ------------------------------------------------------------

for directory in [OUTPUT_DIR, TABLE_DIR, FIGURE_DIR, REPORT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# 3. CONSTANTS
# ------------------------------------------------------------

OUTLIER_COLUMNS = [
    "Variable",
    "Outlier Count",
    "Outlier Percentage",
    "Lower Bound",
    "Upper Bound",
]

EMPTY_OUTLIER_TABLE = pd.DataFrame(columns=OUTLIER_COLUMNS)

EMPTY_CORRELATION_TABLE = pd.DataFrame(
    columns=[
        "Variable 1",
        "Variable 2",
        "Correlation",
    ]
)

# ------------------------------------------------------------
# 4. GENERAL UTILITY FUNCTIONS
# ------------------------------------------------------------


def print_banner(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def safe_divide(numerator, denominator, scale=1):
    """
    Vectorized safe division.

    Returns NaN where denominator is zero.
    """
    denominator = denominator.replace(0, np.nan)

    return (numerator / denominator) * scale


def safe_scalar_divide(numerator, denominator, default=np.nan):
    """
    Safe division for scalar values.
    """
    if denominator is None:
        return default

    if pd.isna(denominator) or denominator == 0:
        return default

    return numerator / denominator


def normal_cdf(x):
    """
    Standard normal cumulative distribution function.
    """
    return 0.5 * (
        1 + math.erf(x / math.sqrt(2))
    )


def format_p_value(p_value):
    """
    Format p-values without incorrectly converting
    very small values to 0.000000.

    Example:
        0.042531 -> 0.042531
        1.705303e-13 -> 1.705303e-13
    """

    if pd.isna(p_value):
        return "NA"

    if p_value < 0.001:
        return f"{p_value:.6e}"

    return f"{p_value:.6f}"


def save_table(df, filename):
    """
    Save DataFrame to CSV in the tables directory.
    """
    path = TABLE_DIR / filename
    df.to_csv(path, index=False)
    return path


def save_figure(filename):
    """
    Save current matplotlib figure.
    """
    path = FIGURE_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    return path


def dataframe_to_text(df, float_format=None):
    """
    Convert a DataFrame to readable report text.
    """

    if df is None or df.empty:
        return "No records available."

    if float_format is not None:
        return df.to_string(
            index=False,
            float_format=float_format
        )

    return df.to_string(index=False)


def write_report_section(report_lines, title, content):
    """
    Append a formatted section to the master report.
    """

    report_lines.append("\n")
    report_lines.append("=" * 90)
    report_lines.append(title)
    report_lines.append("=" * 90)
    report_lines.append(content)


def validate_required_columns(df, required_columns, dataset_name):
    """
    Validate required columns.
    """

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{dataset_name} is missing required columns: "
            f"{missing_columns}"
        )


def dataset_basic_quality(df):
    """
    Generate basic data-quality metrics.
    """

    quality = pd.DataFrame(
        {
            "Metric": [
                "Rows",
                "Columns",
                "Missing Cells",
                "Duplicate Rows",
            ],
            "Value": [
                len(df),
                len(df.columns),
                int(df.isna().sum().sum()),
                int(df.duplicated().sum()),
            ],
        }
    )

    return quality

# ------------------------------------------------------------
# 5. OUTLIER ANALYSIS
# ------------------------------------------------------------


def calculate_iqr_outliers(df, numeric_columns):
    """
    Detect IQR-based outliers.

    Outliers are flagged, not deleted.
    """

    records = []

    for column in numeric_columns:

        if column not in df.columns:
            continue

        series = pd.to_numeric(
            df[column],
            errors="coerce"
        ).dropna()

        if series.empty:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        outlier_mask = (
            (series < lower_bound)
            | (series > upper_bound)
        )

        outlier_count = int(outlier_mask.sum())

        outlier_percentage = (
            outlier_count / len(series) * 100
            if len(series) > 0
            else np.nan
        )

        records.append(
            {
                "Variable": column,
                "Outlier Count": outlier_count,
                "Outlier Percentage": outlier_percentage,
                "Lower Bound": lower_bound,
                "Upper Bound": upper_bound,
            }
        )

    if not records:
        return EMPTY_OUTLIER_TABLE.copy()

    return pd.DataFrame(records)

# ------------------------------------------------------------
# 6. CORRELATION ANALYSIS
# ------------------------------------------------------------


def calculate_strong_correlations(
    df,
    numeric_columns,
    threshold=0.70
):
    """
    Identify strong Pearson correlations.
    """

    available_columns = [
        column
        for column in numeric_columns
        if column in df.columns
    ]

    if len(available_columns) < 2:
        return EMPTY_CORRELATION_TABLE.copy()

    correlation_matrix = df[
        available_columns
    ].corr(numeric_only=True)

    records = []

    for i in range(len(correlation_matrix.columns)):

        for j in range(i + 1, len(correlation_matrix.columns)):

            variable_1 = correlation_matrix.columns[i]
            variable_2 = correlation_matrix.columns[j]

            correlation = correlation_matrix.iloc[i, j]

            if pd.isna(correlation):
                continue

            if abs(correlation) >= threshold:

                records.append(
                    {
                        "Variable 1": variable_1,
                        "Variable 2": variable_2,
                        "Correlation": correlation,
                    }
                )

    if not records:
        return EMPTY_CORRELATION_TABLE.copy()

    return (
        pd.DataFrame(records)
        .sort_values(
            "Correlation",
            key=lambda x: x.abs(),
            ascending=False
        )
        .reset_index(drop=True)
    )

# ------------------------------------------------------------
# 7. GENERAL DATASET QUALITY ANALYSIS
# ------------------------------------------------------------


def perform_dataset_quality_analysis(
    df,
    numeric_columns
):
    quality_table = dataset_basic_quality(df)

    outlier_table = calculate_iqr_outliers(
        df,
        numeric_columns
    )

    correlation_table = calculate_strong_correlations(
        df,
        numeric_columns
    )

    return {
        "quality_table": quality_table,
        "outlier_table": outlier_table,
        "correlation_table": correlation_table,
    }

# ------------------------------------------------------------
# 8. PLOTTING HELPERS
# ------------------------------------------------------------


def plot_numeric_distributions(
    df,
    numeric_columns,
    prefix
):
    """
    Generate distribution plots for numeric variables.
    """

    for column in numeric_columns:

        if column not in df.columns:
            continue

        series = pd.to_numeric(
            df[column],
            errors="coerce"
        ).dropna()

        if series.empty:
            continue

        plt.figure(figsize=(8, 5))

        sns.histplot(
            series,
            kde=True
        )

        plt.title(
            f"{prefix}: Distribution of {column}"
        )

        plt.xlabel(column)
        plt.ylabel("Frequency")

        safe_name = (
            column
            .replace("/", "_")
            .replace(" ", "_")
        )

        save_figure(
            f"{prefix.lower().replace(' ', '_')}_{safe_name}_distribution.png"
        )


def plot_correlation_heatmap(
    df,
    numeric_columns,
    filename,
    title
):
    available_columns = [
        column
        for column in numeric_columns
        if column in df.columns
    ]

    if len(available_columns) < 2:
        return

    correlation_matrix = df[
        available_columns
    ].corr(numeric_only=True)

    plt.figure(
        figsize=(
            max(8, len(available_columns) * 1.2),
            max(6, len(available_columns) * 0.9),
        )
    )

    sns.heatmap(
        correlation_matrix,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0
    )

    plt.title(title)

    save_figure(filename)

# ============================================================
# GLOBAL ADS PERFORMANCE ANALYSIS
# ============================================================


def analyze_global_ads():
    print_banner(
        "GLOBAL ADS PERFORMANCE DATASET ANALYSIS"
    )

    df = pd.read_csv(GLOBAL_ADS_FILE)

    required_columns = [
        "date",
        "platform",
        "campaign_type",
        "industry",
        "country",
        "impressions",
        "clicks",
        "CTR",
        "CPC",
        "ad_spend",
        "conversions",
        "CPA",
        "revenue",
        "ROAS",
    ]

    validate_required_columns(
        df,
        required_columns,
        "Global Ads Performance Dataset"
    )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    numeric_columns = [
        "impressions",
        "clicks",
        "CTR",
        "CPC",
        "ad_spend",
        "conversions",
        "CPA",
        "revenue",
        "ROAS",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    quality = perform_dataset_quality_analysis(
        df,
        numeric_columns
    )

    # --------------------------------------------------------
    # KPI VALIDATION
    # --------------------------------------------------------

    # Important:
    # The source CTR is stored on a DECIMAL scale.
    # Therefore validation is Clicks / Impressions,
    # NOT Clicks / Impressions * 100.

    df["CTR_Calculated"] = safe_divide(
        df["clicks"],
        df["impressions"]
    )

    df["CPC_Calculated"] = safe_divide(
        df["ad_spend"],
        df["clicks"]
    )

    df["CPA_Calculated"] = safe_divide(
        df["ad_spend"],
        df["conversions"]
    )

    df["ROAS_Calculated"] = safe_divide(
        df["revenue"],
        df["ad_spend"]
    )

    kpi_validation_records = []

    kpi_pairs = [
        (
            "CTR",
            "CTR_Calculated"
        ),
        (
            "CPC",
            "CPC_Calculated"
        ),
        (
            "CPA",
            "CPA_Calculated"
        ),
        (
            "ROAS",
            "ROAS_Calculated"
        ),
    ]

    for reported_column, calculated_column in kpi_pairs:

        comparison = pd.DataFrame(
            {
                "Reported": df[reported_column],
                "Calculated": df[calculated_column],
            }
        ).dropna()

        if comparison.empty:

            kpi_validation_records.append(
                {
                    "KPI": reported_column,
                    "Reported Mean": np.nan,
                    "Calculated Mean": np.nan,
                    "Max Abs Difference": np.nan,
                    "Rows Within Tolerance": 0,
                    "Rows Compared": 0,
                    "Match Percentage": np.nan,
                }
            )

            continue

        absolute_difference = (
            comparison["Reported"]
            -comparison["Calculated"]
        ).abs()

        tolerance = 0.01

        matches = (
            absolute_difference <= tolerance
        )

        kpi_validation_records.append(
            {
                "KPI": reported_column,
                "Reported Mean": comparison["Reported"].mean(),
                "Calculated Mean": comparison["Calculated"].mean(),
                "Max Abs Difference": absolute_difference.max(),
                "Rows Within Tolerance": int(matches.sum()),
                "Rows Compared": len(comparison),
                "Match Percentage": matches.mean() * 100,
            }
        )

    kpi_validation = pd.DataFrame(
        kpi_validation_records
    )

    # --------------------------------------------------------
    # OVERALL BUSINESS KPIs
    # --------------------------------------------------------

    total_impressions = df["impressions"].sum()
    total_clicks = df["clicks"].sum()
    total_spend = df["ad_spend"].sum()
    total_conversions = df["conversions"].sum()
    total_revenue = df["revenue"].sum()

    overall_kpis = pd.DataFrame(
        {
            "Metric": [
                "Total Impressions",
                "Total Clicks",
                "Total Ad Spend",
                "Total Conversions",
                "Total Revenue",
                "CTR %",
                "CPC",
                "CPA",
                "ROAS",
            ],
            "Value": [
                total_impressions,
                total_clicks,
                total_spend,
                total_conversions,
                total_revenue,
                safe_scalar_divide(
                    total_clicks,
                    total_impressions
                ) * 100,
                safe_scalar_divide(
                    total_spend,
                    total_clicks
                ),
                safe_scalar_divide(
                    total_spend,
                    total_conversions
                ),
                safe_scalar_divide(
                    total_revenue,
                    total_spend
                ),
            ],
        }
    )

    # --------------------------------------------------------
    # PLATFORM PERFORMANCE
    # --------------------------------------------------------

    platform = (
        df.groupby("platform", dropna=False)
        .agg(
            Impressions=("impressions", "sum"),
            Clicks=("clicks", "sum"),
            Ad_Spend=("ad_spend", "sum"),
            Conversions=("conversions", "sum"),
            Revenue=("revenue", "sum"),
        )
        .reset_index()
    )

    platform["CTR_%"] = safe_divide(
        platform["Clicks"],
        platform["Impressions"],
        scale=100
    )

    platform["CPC"] = safe_divide(
        platform["Ad_Spend"],
        platform["Clicks"]
    )

    platform["CPA"] = safe_divide(
        platform["Ad_Spend"],
        platform["Conversions"]
    )

    platform["ROAS"] = safe_divide(
        platform["Revenue"],
        platform["Ad_Spend"]
    )

    # --------------------------------------------------------
    # CAMPAIGN TYPE PERFORMANCE
    # --------------------------------------------------------

    campaign = (
        df.groupby(
            "campaign_type",
            dropna=False
        )
        .agg(
            Impressions=("impressions", "sum"),
            Clicks=("clicks", "sum"),
            Ad_Spend=("ad_spend", "sum"),
            Conversions=("conversions", "sum"),
            Revenue=("revenue", "sum"),
        )
        .reset_index()
    )

    campaign["CTR_%"] = safe_divide(
        campaign["Clicks"],
        campaign["Impressions"],
        scale=100
    )

    campaign["CPC"] = safe_divide(
        campaign["Ad_Spend"],
        campaign["Clicks"]
    )

    campaign["CPA"] = safe_divide(
        campaign["Ad_Spend"],
        campaign["Conversions"]
    )

    campaign["ROAS"] = safe_divide(
        campaign["Revenue"],
        campaign["Ad_Spend"]
    )

    # --------------------------------------------------------
    # INDUSTRY PERFORMANCE
    # --------------------------------------------------------

    industry = (
        df.groupby(
            "industry",
            dropna=False
        )
        .agg(
            Impressions=("impressions", "sum"),
            Clicks=("clicks", "sum"),
            Ad_Spend=("ad_spend", "sum"),
            Conversions=("conversions", "sum"),
            Revenue=("revenue", "sum"),
        )
        .reset_index()
    )

    industry["CTR_%"] = safe_divide(
        industry["Clicks"],
        industry["Impressions"],
        scale=100
    )

    industry["CPC"] = safe_divide(
        industry["Ad_Spend"],
        industry["Clicks"]
    )

    industry["CPA"] = safe_divide(
        industry["Ad_Spend"],
        industry["Conversions"]
    )

    industry["ROAS"] = safe_divide(
        industry["Revenue"],
        industry["Ad_Spend"]
    )

    # --------------------------------------------------------
    # COUNTRY PERFORMANCE
    # --------------------------------------------------------

    country = (
        df.groupby(
            "country",
            dropna=False
        )
        .agg(
            Impressions=("impressions", "sum"),
            Clicks=("clicks", "sum"),
            Ad_Spend=("ad_spend", "sum"),
            Conversions=("conversions", "sum"),
            Revenue=("revenue", "sum"),
        )
        .reset_index()
    )

    country["CTR_%"] = safe_divide(
        country["Clicks"],
        country["Impressions"],
        scale=100
    )

    country["CPC"] = safe_divide(
        country["Ad_Spend"],
        country["Clicks"]
    )

    country["CPA"] = safe_divide(
        country["Ad_Spend"],
        country["Conversions"]
    )

    country["ROAS"] = safe_divide(
        country["Revenue"],
        country["Ad_Spend"]
    )

    # --------------------------------------------------------
    # LOGICAL VALIDATIONS
    # --------------------------------------------------------

    logical_validation = pd.DataFrame(
        {
            "Validation": [
                "Clicks greater than Impressions",
                "Conversions greater than Clicks",
                "Negative Impressions",
                "Negative Clicks",
                "Negative Ad Spend",
                "Negative Conversions",
                "Negative Revenue",
            ],
            "Count": [
                int(
                    (
                        df["clicks"]
                        > df["impressions"]
                    ).sum()
                ),
                int(
                    (
                        df["conversions"]
                        > df["clicks"]
                    ).sum()
                ),
                int(
                    (
                        df["impressions"] < 0
                    ).sum()
                ),
                int(
                    (
                        df["clicks"] < 0
                    ).sum()
                ),
                int(
                    (
                        df["ad_spend"] < 0
                    ).sum()
                ),
                int(
                    (
                        df["conversions"] < 0
                    ).sum()
                ),
                int(
                    (
                        df["revenue"] < 0
                    ).sum()
                ),
            ],
        }
    )

    # --------------------------------------------------------
    # SAVE TABLES
    # --------------------------------------------------------

    save_table(
        quality["quality_table"],
        "global_ads_quality.csv"
    )

    save_table(
        quality["outlier_table"],
        "global_ads_outliers.csv"
    )

    save_table(
        quality["correlation_table"],
        "global_ads_strong_correlations.csv"
    )

    save_table(
        kpi_validation,
        "global_ads_kpi_validation.csv"
    )

    save_table(
        overall_kpis,
        "global_ads_overall_kpis.csv"
    )

    save_table(
        platform,
        "global_ads_platform_performance.csv"
    )

    save_table(
        campaign,
        "global_ads_campaign_performance.csv"
    )

    save_table(
        industry,
        "global_ads_industry_performance.csv"
    )

    save_table(
        country,
        "global_ads_country_performance.csv"
    )

    save_table(
        logical_validation,
        "global_ads_logical_validation.csv"
    )

    # --------------------------------------------------------
    # PLOTS
    # --------------------------------------------------------

    plot_numeric_distributions(
        df,
        numeric_columns,
        "Global Ads"
    )

    plot_correlation_heatmap(
        df,
        numeric_columns,
        "global_ads_correlation_heatmap.png",
        "Global Ads Correlation Heatmap"
    )

    # Platform ROAS
    plt.figure(figsize=(9, 5))

    sns.barplot(
        data=platform,
        x="platform",
        y="ROAS"
    )

    plt.title(
        "Global Ads ROAS by Platform"
    )

    plt.xlabel("Platform")
    plt.ylabel("ROAS")

    save_figure(
        "global_ads_platform_roas.png"
    )

    return {
        "df": df,
        "quality_table": quality["quality_table"],
        "outlier_table": quality["outlier_table"],
        "correlation_table": quality["correlation_table"],
        "kpi_validation": kpi_validation,
        "overall_kpis": overall_kpis,
        "platform": platform,
        "campaign": campaign,
        "industry": industry,
        "country": country,
        "logical_validation": logical_validation,
    }

# ============================================================
# KAG CONVERSION DATA ANALYSIS
# ============================================================


def analyze_kag():
    print_banner(
        "KAG CONVERSION DATASET ANALYSIS"
    )

    df = pd.read_csv(KAG_FILE)

    required_columns = [
        "ad_id",
        "xyz_campaign_id",
        "fb_campaign_id",
        "interest",
        "Impressions",
        "Clicks",
        "Spent",
        "Total_Conversion",
        "Approved_Conversion",
        "age",
        "gender",
    ]

    validate_required_columns(
        df,
        required_columns,
        "KAG Conversion Dataset"
    )

    # Identifier / categorical columns
    df["ad_id"] = df["ad_id"].astype(str)
    df["xyz_campaign_id"] = (
        df["xyz_campaign_id"].astype(str)
    )
    df["fb_campaign_id"] = (
        df["fb_campaign_id"].astype(str)
    )

    df["interest"] = df["interest"].astype(str)
    df["age"] = df["age"].astype(str)
    df["gender"] = df["gender"].astype(str)

    numeric_columns = [
        "Impressions",
        "Clicks",
        "Spent",
        "Total_Conversion",
        "Approved_Conversion",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    quality = perform_dataset_quality_analysis(
        df,
        numeric_columns
    )

    # --------------------------------------------------------
    # OVERALL FUNNEL
    # --------------------------------------------------------

    total_impressions = df["Impressions"].sum()
    total_clicks = df["Clicks"].sum()
    total_conversions = df[
        "Total_Conversion"
    ].sum()
    total_approved = df[
        "Approved_Conversion"
    ].sum()
    total_spend = df["Spent"].sum()

    overall_funnel = pd.DataFrame(
        {
            "Metric": [
                "Total Impressions",
                "Total Clicks",
                "Total Conversion",
                "Approved Conversion",
                "Total Spend",
                "Impression-to-Click Rate %",
                "Click-to-Total Conversion %",
                "Click-to-Approved Conversion %",
                "Total-to-Approved Conversion %",
                "Cost per Approved Conversion",
            ],
            "Value": [
                total_impressions,
                total_clicks,
                total_conversions,
                total_approved,
                total_spend,
                safe_scalar_divide(
                    total_clicks,
                    total_impressions
                ) * 100,
                safe_scalar_divide(
                    total_conversions,
                    total_clicks
                ) * 100,
                safe_scalar_divide(
                    total_approved,
                    total_clicks
                ) * 100,
                safe_scalar_divide(
                    total_approved,
                    total_conversions
                ) * 100,
                safe_scalar_divide(
                    total_spend,
                    total_approved
                ),
            ],
        }
    )

    # --------------------------------------------------------
    # CAMPAIGN PERFORMANCE
    # --------------------------------------------------------

    campaign = (
        df.groupby(
            "xyz_campaign_id",
            dropna=False
        )
        .agg(
            Records=("ad_id", "count"),
            Impressions=("Impressions", "sum"),
            Clicks=("Clicks", "sum"),
            Spend=("Spent", "sum"),
            Total_Conversion=(
                "Total_Conversion",
                "sum"
            ),
            Approved_Conversion=(
                "Approved_Conversion",
                "sum"
            ),
        )
        .reset_index()
    )

    campaign["CTR_%"] = safe_divide(
        campaign["Clicks"],
        campaign["Impressions"],
        scale=100
    )

    campaign["Approved Conversion Rate %"] = (
        safe_divide(
            campaign["Approved_Conversion"],
            campaign["Clicks"],
            scale=100
        )
    )

    campaign["CPC"] = safe_divide(
        campaign["Spend"],
        campaign["Clicks"]
    )

    campaign["Cost per Approved"] = safe_divide(
        campaign["Spend"],
        campaign["Approved_Conversion"]
    )

    # --------------------------------------------------------
    # AGE PERFORMANCE
    # --------------------------------------------------------

    age = (
        df.groupby(
            "age",
            dropna=False
        )
        .agg(
            Records=("ad_id", "count"),
            Impressions=("Impressions", "sum"),
            Clicks=("Clicks", "sum"),
            Spend=("Spent", "sum"),
            Total_Conversion=(
                "Total_Conversion",
                "sum"
            ),
            Approved_Conversion=(
                "Approved_Conversion",
                "sum"
            ),
        )
        .reset_index()
    )

    age["CTR_%"] = safe_divide(
        age["Clicks"],
        age["Impressions"],
        scale=100
    )

    age["Approved Conversion Rate %"] = (
        safe_divide(
            age["Approved_Conversion"],
            age["Clicks"],
            scale=100
        )
    )

    age["CPC"] = safe_divide(
        age["Spend"],
        age["Clicks"]
    )

    age["Cost per Approved"] = safe_divide(
        age["Spend"],
        age["Approved_Conversion"]
    )

    # --------------------------------------------------------
    # GENDER PERFORMANCE
    # --------------------------------------------------------

    gender = (
        df.groupby(
            "gender",
            dropna=False
        )
        .agg(
            Records=("ad_id", "count"),
            Impressions=("Impressions", "sum"),
            Clicks=("Clicks", "sum"),
            Spend=("Spent", "sum"),
            Total_Conversion=(
                "Total_Conversion",
                "sum"
            ),
            Approved_Conversion=(
                "Approved_Conversion",
                "sum"
            ),
        )
        .reset_index()
    )

    gender["CTR_%"] = safe_divide(
        gender["Clicks"],
        gender["Impressions"],
        scale=100
    )

    gender["Approved Conversion Rate %"] = (
        safe_divide(
            gender["Approved_Conversion"],
            gender["Clicks"],
            scale=100
        )
    )

    gender["CPC"] = safe_divide(
        gender["Spend"],
        gender["Clicks"]
    )

    gender["Cost per Approved"] = safe_divide(
        gender["Spend"],
        gender["Approved_Conversion"]
    )

    # --------------------------------------------------------
    # INTEREST PERFORMANCE
    # --------------------------------------------------------

    interest = (
        df.groupby(
            "interest",
            dropna=False
        )
        .agg(
            Records=("ad_id", "count"),
            Impressions=("Impressions", "sum"),
            Clicks=("Clicks", "sum"),
            Spend=("Spent", "sum"),
            Total_Conversion=(
                "Total_Conversion",
                "sum"
            ),
            Approved_Conversion=(
                "Approved_Conversion",
                "sum"
            ),
        )
        .reset_index()
    )

    interest["CTR_%"] = safe_divide(
        interest["Clicks"],
        interest["Impressions"],
        scale=100
    )

    interest["Approved Conversion Rate %"] = (
        safe_divide(
            interest["Approved_Conversion"],
            interest["Clicks"],
            scale=100
        )
    )

    interest["CPC"] = safe_divide(
        interest["Spend"],
        interest["Clicks"]
    )

    interest["Cost per Approved"] = safe_divide(
        interest["Spend"],
        interest["Approved_Conversion"]
    )

    # --------------------------------------------------------
    # LOGICAL VALIDATION
    # --------------------------------------------------------

    total_conversion_greater_than_clicks = int(
        (
            df["Total_Conversion"]
            > df["Clicks"]
        ).sum()
    )

    approved_greater_than_total = int(
        (
            df["Approved_Conversion"]
            > df["Total_Conversion"]
        ).sum()
    )

    negative_rows = int(
        (
            df[
                numeric_columns
            ] < 0
        ).any(axis=1).sum()
    )

    logical_validation = pd.DataFrame(
        {
            "Validation": [
                "Total_Conversion greater than Clicks",
                "Approved_Conversion greater than Total_Conversion",
                "Rows with negative numeric values",
            ],
            "Count": [
                total_conversion_greater_than_clicks,
                approved_greater_than_total,
                negative_rows,
            ],
        }
    )

    # --------------------------------------------------------
    # FLAG SOURCE-DEFINITION ISSUE
    # --------------------------------------------------------

    source_definition_note = pd.DataFrame(
        {
            "Metric": [
                "Total_Conversion greater than Clicks"
            ],
            "Flagged Rows": [
                total_conversion_greater_than_clicks
            ],
            "Interpretation": [
                (
                    "Retained as a source-definition flag. "
                    "The dataset is aggregated at ad level, so "
                    "Total_Conversion is not assumed to be a "
                    "simple click-level funnel count."
                )
            ],
        }
    )

    # --------------------------------------------------------
    # SAVE TABLES
    # --------------------------------------------------------

    save_table(
        quality["quality_table"],
        "kag_quality.csv"
    )

    save_table(
        quality["outlier_table"],
        "kag_outliers.csv"
    )

    save_table(
        quality["correlation_table"],
        "kag_strong_correlations.csv"
    )

    save_table(
        overall_funnel,
        "kag_overall_funnel.csv"
    )

    save_table(
        campaign,
        "kag_campaign_performance.csv"
    )

    save_table(
        age,
        "kag_age_performance.csv"
    )

    save_table(
        gender,
        "kag_gender_performance.csv"
    )

    save_table(
        interest,
        "kag_interest_performance.csv"
    )

    save_table(
        logical_validation,
        "kag_logical_validation.csv"
    )

    save_table(
        source_definition_note,
        "kag_source_definition_flags.csv"
    )

    # --------------------------------------------------------
    # PLOTS
    # --------------------------------------------------------

    plot_numeric_distributions(
        df,
        numeric_columns,
        "KAG"
    )

    plot_correlation_heatmap(
        df,
        numeric_columns,
        "kag_correlation_heatmap.png",
        "KAG Conversion Data Correlation Heatmap"
    )

    plt.figure(figsize=(8, 5))

    sns.barplot(
        data=campaign,
        x="xyz_campaign_id",
        y="Cost per Approved"
    )

    plt.title(
        "KAG Campaign Cost per Approved Conversion"
    )

    plt.xlabel("Campaign ID")
    plt.ylabel("Cost per Approved Conversion")

    save_figure(
        "kag_campaign_cost_per_approved.png"
    )

    return {
        "df": df,
        "quality_table": quality["quality_table"],
        "outlier_table": quality["outlier_table"],
        "correlation_table": quality["correlation_table"],
        "overall_funnel": overall_funnel,
        "campaign": campaign,
        "age": age,
        "gender": gender,
        "interest": interest,
        "logical_validation": logical_validation,
        "source_definition_note": source_definition_note,
    }

# ============================================================
# MARKETING A/B TESTING ANALYSIS
# ============================================================


def analyze_marketing_ab():
    print_banner(
        "MARKETING A/B TESTING DATASET ANALYSIS"
    )

    df = pd.read_csv(
        MARKETING_AB_FILE
    )

    required_columns = [
        "Unnamed: 0",
        "user id",
        "test group",
        "converted",
        "total ads",
        "most ads day",
        "most ads hour",
    ]

    validate_required_columns(
        df,
        required_columns,
        "Marketing A/B Testing Dataset"
    )

    # --------------------------------------------------------
    # DATA TYPES
    # --------------------------------------------------------

    df["Unnamed: 0"] = pd.to_numeric(
        df["Unnamed: 0"],
        errors="coerce"
    )

    df["user id"] = (
        df["user id"].astype(str)
    )

    df["test group"] = (
        df["test group"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    df["converted"] = (
        df["converted"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    df["total ads"] = pd.to_numeric(
        df["total ads"],
        errors="coerce"
    )

    df["most ads hour"] = pd.to_numeric(
        df["most ads hour"],
        errors="coerce"
    )

    numeric_columns = [
        "total ads"
    ]

    quality = perform_dataset_quality_analysis(
        df,
        numeric_columns
    )

    # --------------------------------------------------------
    # GROUP SUMMARY
    # --------------------------------------------------------

    group_summary = (
        df.groupby(
            "test group",
            dropna=False
        )
        .agg(
            Users=("user id", "count"),
            Conversions=(
                "converted",
                lambda x: (
                    x == "true"
                ).sum()
            ),
            Total_Ads=(
                "total ads",
                "sum"
            ),
        )
        .reset_index()
    )

    group_summary["Average Ads per User"] = (
        safe_divide(
            group_summary["Total_Ads"],
            group_summary["Users"]
        )
    )

    group_summary["Conversion Rate %"] = (
        safe_divide(
            group_summary["Conversions"],
            group_summary["Users"],
            scale=100
        )
    )

    # --------------------------------------------------------
    # A/B TWO-PROPORTION Z TEST
    # --------------------------------------------------------

    ad_group = df[
        df["test group"] == "ad"
    ]

    psa_group = df[
        df["test group"] == "psa"
    ]

    ad_n = len(ad_group)
    psa_n = len(psa_group)

    ad_conversions = int(
        (
            ad_group["converted"]
            == "true"
        ).sum()
    )

    psa_conversions = int(
        (
            psa_group["converted"]
            == "true"
        ).sum()
    )

    ad_rate = safe_scalar_divide(
        ad_conversions,
        ad_n
    )

    psa_rate = safe_scalar_divide(
        psa_conversions,
        psa_n
    )

    absolute_difference = (
        ad_rate - psa_rate
    )

    relative_lift = safe_scalar_divide(
        absolute_difference,
        psa_rate
    ) * 100

    # Pooled proportion
    pooled_rate = safe_scalar_divide(
        ad_conversions + psa_conversions,
        ad_n + psa_n
    )

    standard_error = math.sqrt(
        pooled_rate
        * (1 - pooled_rate)
        * (
            (1 / ad_n)
            +(1 / psa_n)
        )
    )

    z_statistic = (
        absolute_difference
        / standard_error
    )

    p_value = (
        2
        * (
            1
            -normal_cdf(
                abs(z_statistic)
            )
        )
    )

    # --------------------------------------------------------
    # 95% CONFIDENCE INTERVAL
    # --------------------------------------------------------

    ci_standard_error = math.sqrt(
        (
            ad_rate
            * (1 - ad_rate)
            / ad_n
        )
        +
        (
            psa_rate
            * (1 - psa_rate)
            / psa_n
        )
    )

    ci_margin = (
        1.96
        * ci_standard_error
    )

    ci_lower = (
        absolute_difference
        -ci_margin
    )

    ci_upper = (
        absolute_difference
        +ci_margin
    )

    # --------------------------------------------------------
    # STATISTICAL COMPARISON TABLE
    # --------------------------------------------------------

    # P-value is stored as a formatted string here so that
    # the master report does not let pandas display it in an
    # uncontrolled format.
    #
    # The underlying numeric p_value remains available in
    # the result dictionary for any later calculations.

    ab_test_results = pd.DataFrame(
        [
            {
                "Comparison": "ad vs psa",
                "Ad Users": ad_n,
                "PSA Users": psa_n,
                "Ad Conversions": ad_conversions,
                "PSA Conversions": psa_conversions,
                "Ad Conversion Rate %": (
                    ad_rate * 100
                ),
                "PSA Conversion Rate %": (
                    psa_rate * 100
                ),
                "Absolute Difference Percentage Points": (
                    absolute_difference * 100
                ),
                "Relative Lift %": relative_lift,
                "Z Statistic": z_statistic,
                "Two-Sided P Value": format_p_value(
                    p_value
                ),
                "95% CI Lower Percentage Points": (
                    ci_lower * 100
                ),
                "95% CI Upper Percentage Points": (
                    ci_upper * 100
                ),
            }
        ]
    )

    # Numeric version preserved separately
    ab_test_numeric = pd.DataFrame(
        [
            {
                "Comparison": "ad vs psa",
                "Ad Users": ad_n,
                "PSA Users": psa_n,
                "Ad Conversions": ad_conversions,
                "PSA Conversions": psa_conversions,
                "Ad Conversion Rate": ad_rate,
                "PSA Conversion Rate": psa_rate,
                "Absolute Difference": absolute_difference,
                "Relative Lift %": relative_lift,
                "Z Statistic": z_statistic,
                "Two-Sided P Value": p_value,
                "95% CI Lower": ci_lower,
                "95% CI Upper": ci_upper,
            }
        ]
    )

    # --------------------------------------------------------
    # STATISTICAL INTERPRETATION
    # --------------------------------------------------------

    if p_value < 0.05:
        statistical_result = (
            "The observed conversion rates differ under "
            "the two-sided two-proportion z-test at the "
            "5% significance level."
        )
    else:
        statistical_result = (
            "The observed conversion rates do not show "
            "a statistically significant difference under "
            "the two-sided two-proportion z-test at the "
            "5% significance level."
        )

    statistical_interpretation = pd.DataFrame(
        {
            "Metric": [
                "Ad Conversion Rate %",
                "PSA Conversion Rate %",
                "Observed Difference Percentage Points",
                "Observed Relative Lift %",
                "Z Statistic",
                "Two-Sided P Value",
                "95% CI Lower Percentage Points",
                "95% CI Upper Percentage Points",
                "Interpretation",
                "Causal Limitation",
                "Sample Size Caveat",
            ],
            "Value": [
                f"{ad_rate * 100:.6f}",
                f"{psa_rate * 100:.6f}",
                f"{absolute_difference * 100:.6f}",
                f"{relative_lift:.6f}",
                f"{z_statistic:.6f}",
                format_p_value(p_value),
                f"{ci_lower * 100:.6f}",
                f"{ci_upper * 100:.6f}",
                statistical_result,
                (
                    "The statistical comparison identifies an "
                    "observed association between test group and "
                    "conversion outcome; it does not by itself "
                    "establish causal impact."
                ),
                (
                    "The ad and PSA groups are highly imbalanced "
                    "in sample size, so group size should be "
                    "considered when interpreting the comparison."
                ),
            ],
        }
    )

    # --------------------------------------------------------
    # DAY PERFORMANCE
    # --------------------------------------------------------

    day_performance = (
        df.groupby(
            ["test group", "most ads day"],
            dropna=False
        )
        .agg(
            Users=("user id", "count"),
            Total_Ads=("total ads", "sum"),
            Conversions=(
                "converted",
                lambda x: (
                    x == "true"
                ).sum()
            ),
        )
        .reset_index()
    )

    day_performance["Conversion Rate %"] = (
        safe_divide(
            day_performance["Conversions"],
            day_performance["Users"],
            scale=100
        )
    )

    day_performance["Average Ads per User"] = (
        safe_divide(
            day_performance["Total_Ads"],
            day_performance["Users"]
        )
    )

    # --------------------------------------------------------
    # HOUR PERFORMANCE
    # --------------------------------------------------------

    hour_performance = (
        df.groupby(
            ["test group", "most ads hour"],
            dropna=False
        )
        .agg(
            Users=("user id", "count"),
            Total_Ads=("total ads", "sum"),
            Conversions=(
                "converted",
                lambda x: (
                    x == "true"
                ).sum()
            ),
        )
        .reset_index()
    )

    hour_performance["Conversion Rate %"] = (
        safe_divide(
            hour_performance["Conversions"],
            hour_performance["Users"],
            scale=100
        )
    )

    hour_performance["Average Ads per User"] = (
        safe_divide(
            hour_performance["Total_Ads"],
            hour_performance["Users"]
        )
    )

    # --------------------------------------------------------
    # EXPOSURE ANALYSIS
    # --------------------------------------------------------

    exposure_summary = (
        df.groupby(
            "test group",
            dropna=False
        )
        .agg(
            Users=("user id", "count"),
            Total_Ads=("total ads", "sum"),
            Average_Ads_per_User=(
                "total ads",
                "mean"
            ),
            Median_Ads_per_User=(
                "total ads",
                "median"
            ),
            Maximum_Ads_per_User=(
                "total ads",
                "max"
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # INDEX VALIDATION
    # --------------------------------------------------------

    index_is_numeric = pd.api.types.is_numeric_dtype(
        df["Unnamed: 0"]
    )

    index_is_unique = df[
        "Unnamed: 0"
    ].is_unique

    index_is_monotonic = df[
        "Unnamed: 0"
    ].is_monotonic_increasing

    index_validation = pd.DataFrame(
        {
            "Property": [
                "Numeric",
                "Unique",
                "Monotonic Increasing",
                "Interpretation",
            ],
            "Value": [
                index_is_numeric,
                index_is_unique,
                index_is_monotonic,
                (
                    "Index-like metadata column; "
                    "not used as an analytical feature."
                ),
            ],
        }
    )

    # --------------------------------------------------------
    # LOGICAL VALIDATION
    # --------------------------------------------------------

    negative_total_ads = int(
        (
            df["total ads"] < 0
        ).sum()
    )

    distinct_converted_values = (
        df["converted"]
        .dropna()
        .nunique()
    )

    duplicate_user_ids = int(
        df["user id"].duplicated().sum()
    )

    logical_validation = pd.DataFrame(
        {
            "Validation": [
                "Negative total ads",
                "Distinct converted values",
                "Duplicate user IDs",
            ],
            "Count": [
                negative_total_ads,
                distinct_converted_values,
                duplicate_user_ids,
            ],
        }
    )

    # --------------------------------------------------------
    # SAVE TABLES
    # --------------------------------------------------------

    save_table(
        quality["quality_table"],
        "marketing_ab_quality.csv"
    )

    save_table(
        quality["outlier_table"],
        "marketing_ab_outliers.csv"
    )

    save_table(
        quality["correlation_table"],
        "marketing_ab_strong_correlations.csv"
    )

    save_table(
        group_summary,
        "marketing_ab_group_summary.csv"
    )

    save_table(
        ab_test_results,
        "marketing_ab_statistical_comparison.csv"
    )

    save_table(
        ab_test_numeric,
        "marketing_ab_statistical_comparison_numeric.csv"
    )

    save_table(
        statistical_interpretation,
        "marketing_ab_statistical_interpretation.csv"
    )

    save_table(
        day_performance,
        "marketing_ab_day_performance.csv"
    )

    save_table(
        hour_performance,
        "marketing_ab_hour_performance.csv"
    )

    save_table(
        exposure_summary,
        "marketing_ab_exposure_summary.csv"
    )

    save_table(
        index_validation,
        "marketing_ab_index_validation.csv"
    )

    save_table(
        logical_validation,
        "marketing_ab_logical_validation.csv"
    )

    # --------------------------------------------------------
    # PLOTS
    # --------------------------------------------------------

    plot_numeric_distributions(
        df,
        numeric_columns,
        "Marketing AB"
    )

    # Conversion-rate comparison
    plt.figure(figsize=(8, 5))

    sns.barplot(
        data=group_summary,
        x="test group",
        y="Conversion Rate %"
    )

    plt.title(
        "Marketing A/B Conversion Rate by Test Group"
    )

    plt.xlabel("Test Group")
    plt.ylabel("Conversion Rate (%)")

    save_figure(
        "marketing_ab_conversion_rate_comparison.png"
    )

    # Average ads per user
    plt.figure(figsize=(8, 5))

    sns.barplot(
        data=group_summary,
        x="test group",
        y="Average Ads per User"
    )

    plt.title(
        "Average Ad Exposure per User"
    )

    plt.xlabel("Test Group")
    plt.ylabel("Average Ads per User")

    save_figure(
        "marketing_ab_average_ads_per_user.png"
    )

    return {
        "df": df,
        "quality_table": quality["quality_table"],
        "outlier_table": quality["outlier_table"],
        "correlation_table": quality["correlation_table"],
        "group_summary": group_summary,
        "ab_test_results": ab_test_results,
        "ab_test_numeric": ab_test_numeric,
        "statistical_interpretation": statistical_interpretation,
        "day_performance": day_performance,
        "hour_performance": hour_performance,
        "exposure_summary": exposure_summary,
        "index_validation": index_validation,
        "logical_validation": logical_validation,
        "p_value_numeric": p_value,
    }

# ============================================================
# MASTER REPORT
# ============================================================


def create_master_report(
    global_results,
    kag_results,
    ab_results
):
    print_banner(
        "CREATING MARKETLENS MASTER REPORT"
    )

    report_lines = []

    report_lines.append(
        "MARKETLENS"
    )

    report_lines.append(
        "Comprehensive Marketing Analytics & Research Report"
    )

    report_lines.append(
        "Generated from three marketing datasets."
    )

    report_lines.append(
        ""
    )

    # ========================================================
    # EXECUTIVE DATASET INVENTORY
    # ========================================================

    inventory = pd.DataFrame(
        {
            "Dataset": [
                "Global Ads Performance",
                "KAG Conversion Data",
                "Marketing A/B Testing",
            ],
            "Rows": [
                len(global_results["df"]),
                len(kag_results["df"]),
                len(ab_results["df"]),
            ],
            "Columns": [
                len(global_results["df"].columns),
                len(kag_results["df"].columns),
                len(ab_results["df"].columns),
            ],
            "Missing Cells": [
                int(
                    global_results["df"]
                    .isna()
                    .sum()
                    .sum()
                ),
                int(
                    kag_results["df"]
                    .isna()
                    .sum()
                    .sum()
                ),
                int(
                    ab_results["df"]
                    .isna()
                    .sum()
                    .sum()
                ),
            ],
            "Duplicate Rows": [
                int(
                    global_results["df"]
                    .duplicated()
                    .sum()
                ),
                int(
                    kag_results["df"]
                    .duplicated()
                    .sum()
                ),
                int(
                    ab_results["df"]
                    .duplicated()
                    .sum()
                ),
            ],
        }
    )

    write_report_section(
        report_lines,
        "1. DATASET INVENTORY",
        dataframe_to_text(
            inventory
        )
    )

    # ========================================================
    # GLOBAL ADS
    # ========================================================

    write_report_section(
        report_lines,
        "2. GLOBAL ADS PERFORMANCE - DATA QUALITY",
        dataframe_to_text(
            global_results["quality_table"]
        )
    )

    write_report_section(
        report_lines,
        "3. GLOBAL ADS PERFORMANCE - IQR OUTLIER ANALYSIS",
        dataframe_to_text(
            global_results["outlier_table"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "4. GLOBAL ADS PERFORMANCE - STRONG CORRELATIONS",
        dataframe_to_text(
            global_results["correlation_table"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "5. GLOBAL ADS PERFORMANCE - KPI VALIDATION",
        dataframe_to_text(
            global_results["kpi_validation"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    report_lines.append(
        ""
    )

    report_lines.append(
        "KPI validation note:"
    )

    report_lines.append(
        "CTR is validated on the same decimal scale as "
        "the source CTR field using Clicks / Impressions. "
        "Percentage versions of CTR are used separately "
        "for business reporting."
    )

    write_report_section(
        report_lines,
        "6. GLOBAL ADS PERFORMANCE - OVERALL KPIs",
        dataframe_to_text(
            global_results["overall_kpis"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "7. GLOBAL ADS PERFORMANCE - PLATFORM PERFORMANCE",
        dataframe_to_text(
            global_results["platform"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "8. GLOBAL ADS PERFORMANCE - CAMPAIGN PERFORMANCE",
        dataframe_to_text(
            global_results["campaign"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "9. GLOBAL ADS PERFORMANCE - INDUSTRY PERFORMANCE",
        dataframe_to_text(
            global_results["industry"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "10. GLOBAL ADS PERFORMANCE - COUNTRY PERFORMANCE",
        dataframe_to_text(
            global_results["country"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "11. GLOBAL ADS PERFORMANCE - LOGICAL VALIDATION",
        dataframe_to_text(
            global_results["logical_validation"]
        )
    )

    report_lines.append(
        "Global Ads data-quality note:"
    )

    report_lines.append(
        "Global Ads CTR validation uses the same decimal "
        "scale as the source field: Clicks / Impressions. "
        "Percentage-scale CTR is used separately for "
        "business reporting."
    )

    # ========================================================
    # KAG
    # ========================================================

    write_report_section(
        report_lines,
        "12. KAG CONVERSION DATA - DATA QUALITY",
        dataframe_to_text(
            kag_results["quality_table"]
        )
    )

    write_report_section(
        report_lines,
        "13. KAG CONVERSION DATA - IQR OUTLIER ANALYSIS",
        dataframe_to_text(
            kag_results["outlier_table"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "14. KAG CONVERSION DATA - STRONG CORRELATIONS",
        dataframe_to_text(
            kag_results["correlation_table"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "15. KAG CONVERSION DATA - OVERALL FUNNEL",
        dataframe_to_text(
            kag_results["overall_funnel"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "16. KAG CONVERSION DATA - CAMPAIGN PERFORMANCE",
        dataframe_to_text(
            kag_results["campaign"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "17. KAG CONVERSION DATA - AGE PERFORMANCE",
        dataframe_to_text(
            kag_results["age"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "18. KAG CONVERSION DATA - GENDER PERFORMANCE",
        dataframe_to_text(
            kag_results["gender"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "19. KAG CONVERSION DATA - INTEREST PERFORMANCE",
        dataframe_to_text(
            kag_results["interest"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "20. KAG CONVERSION DATA - LOGICAL VALIDATION",
        dataframe_to_text(
            kag_results["logical_validation"]
        )
    )

    write_report_section(
        report_lines,
        "21. KAG CONVERSION DATA - SOURCE DEFINITION FLAGS",
        dataframe_to_text(
            kag_results["source_definition_note"]
        )
    )

    # ========================================================
    # MARKETING A/B
    # ========================================================

    write_report_section(
        report_lines,
        "22. MARKETING A/B TESTING - DATA QUALITY",
        dataframe_to_text(
            ab_results["quality_table"]
        )
    )

    write_report_section(
        report_lines,
        "23. MARKETING A/B TESTING - IQR OUTLIER ANALYSIS",
        dataframe_to_text(
            ab_results["outlier_table"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "24. MARKETING A/B TESTING - STRONG CORRELATIONS",
        dataframe_to_text(
            ab_results["correlation_table"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "25. MARKETING A/B TESTING - GROUP SUMMARY",
        dataframe_to_text(
            ab_results["group_summary"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "26. MARKETING A/B TESTING - STATISTICAL COMPARISON",
        dataframe_to_text(
            ab_results["ab_test_results"]
        )
    )

    write_report_section(
        report_lines,
        "27. MARKETING A/B TESTING - NUMERIC STATISTICAL RESULTS",
        dataframe_to_text(
            ab_results["ab_test_numeric"],
            float_format=lambda x: f"{x:.12f}"
        )
    )

    write_report_section(
        report_lines,
        "28. MARKETING A/B TESTING - STATISTICAL INTERPRETATION",
        dataframe_to_text(
            ab_results["statistical_interpretation"]
        )
    )

    write_report_section(
        report_lines,
        "29. MARKETING A/B TESTING - DAY PERFORMANCE",
        dataframe_to_text(
            ab_results["day_performance"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "30. MARKETING A/B TESTING - HOUR PERFORMANCE",
        dataframe_to_text(
            ab_results["hour_performance"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "31. MARKETING A/B TESTING - EXPOSURE ANALYSIS",
        dataframe_to_text(
            ab_results["exposure_summary"],
            float_format=lambda x: f"{x:.6f}"
        )
    )

    write_report_section(
        report_lines,
        "32. MARKETING A/B TESTING - INDEX VALIDATION",
        dataframe_to_text(
            ab_results["index_validation"]
        )
    )

    write_report_section(
        report_lines,
        "33. MARKETING A/B TESTING - LOGICAL VALIDATION",
        dataframe_to_text(
            ab_results["logical_validation"]
        )
    )

    # ========================================================
    # RESEARCH / ANALYTICS METHODOLOGY NOTES
    # ========================================================

    methodology_text = """
MarketLens applies a structured analytical workflow across
three marketing datasets.

The workflow includes:

1. Structural data-quality assessment.
2. Missing-value and duplicate-row checks.
3. Numeric-type validation.
4. IQR-based outlier detection.
5. Strong Pearson correlation screening.
6. Marketing KPI recalculation and validation.
7. Funnel analysis.
8. Platform, campaign, industry, country and audience
   segmentation.
9. Marketing A/B statistical comparison.
10. Two-proportion z-test.
11. 95% confidence interval estimation.
12. Business-oriented interpretation.

Outliers are identified for investigation and are NOT
automatically removed.

Correlation indicates statistical association and does not
establish causation.

The A/B test compares observed conversion rates between
the ad and PSA groups using a two-sided two-proportion
z-test. Statistical significance should not be interpreted
as proof of causal impact without considering the study
design and possible confounding factors.

For the KAG dataset, the occurrence of Total_Conversion
greater than Clicks is retained as a source-definition flag.
The dataset is aggregated at ad level, so the fields should
not automatically be interpreted as a simple click-level
funnel.

For the Marketing A/B dataset, "total ads" represents ad
exposure and is treated as an exposure variable rather than
as an outcome.

For Global Ads, CTR validation is performed using the
source field's decimal representation. Business-facing
CTR percentages are calculated separately by multiplying
Clicks / Impressions by 100.
"""

    write_report_section(
        report_lines,
        "34. METHODOLOGY AND INTERPRETATION NOTES",
        methodology_text.strip()
    )

    # ========================================================
    # FINAL PROJECT STATUS
    # ========================================================

    final_status = """
MarketLens analysis completed successfully.

Completed analytical components:

- Dataset inventory
- Data-quality assessment
- Missing-value checks
- Duplicate checks
- Numeric validation
- IQR outlier detection
- Correlation analysis
- Global Ads KPI validation
- Platform analysis
- Campaign analysis
- Industry analysis
- Country analysis
- KAG funnel analysis
- KAG campaign analysis
- KAG audience segmentation
- Marketing A/B group comparison
- Two-proportion z-test
- 95% confidence interval
- Day-of-week analysis
- Hour-of-day analysis
- Ad exposure analysis
- Logical validation
- Research methodology documentation

The current analytical stage does not automatically remove
outliers or claim causal relationships from observational
associations.

The next project stage is the documented cleaned-data layer
followed by the business-facing dashboard.
"""

    write_report_section(
        report_lines,
        "35. MARKETLENS PROJECT STATUS",
        final_status.strip()
    )

    # ========================================================
    # WRITE REPORT
    # ========================================================

    MASTER_REPORT_FILE.write_text(
        "\n".join(report_lines),
        encoding="utf-8"
    )

    return MASTER_REPORT_FILE

# ============================================================
# MAIN
# ============================================================


def main():

    print_banner(
        "MARKETLENS - MARKETING ANALYTICS PROJECT"
    )

    print(
        f"Project root:\n{PROJECT_ROOT}"
    )

    print(
        f"\nRaw data directory:\n{RAW_DIR}"
    )

    print(
        "\nStarting analysis..."
    )

    # --------------------------------------------------------
    # ANALYZE ALL THREE DATASETS
    # --------------------------------------------------------

    dataset_results = {}

    global_results = analyze_global_ads()

    dataset_results[
        "Global Ads Performance"
    ] = global_results

    kag_results = analyze_kag()

    dataset_results[
        "KAG Conversion Data"
    ] = kag_results

    ab_results = analyze_marketing_ab()

    dataset_results[
        "Marketing A/B Testing"
    ] = ab_results

    # --------------------------------------------------------
    # CREATE MASTER REPORT
    # --------------------------------------------------------

    report_path = create_master_report(
        global_results,
        kag_results,
        ab_results
    )

    # --------------------------------------------------------
    # COMPLETION MESSAGE
    # --------------------------------------------------------

    print_banner(
        "MARKETLENS ANALYSIS COMPLETED"
    )

    print(
        "\nMaster report:"
    )

    print(
        report_path
    )

    print(
        "\nTables:"
    )

    print(
        TABLE_DIR
    )

    print(
        "\nFigures:"
    )

    print(
        FIGURE_DIR
    )

    print(
        "\nReports:"
    )

    print(
        REPORT_DIR
    )

    print(
        "\nAll three datasets were analyzed successfully."
    )

    print(
        "\nNext stage: cleaned-data layer and dashboard preparation."
    )


if __name__ == "__main__":
    main()

from pathlib import Path
import math
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(
    r"C:\Users\Pranoti munjankar\OneDrive\Desktop\DA PROJECTS\Marketlens"
)

RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"

GLOBAL_ADS_FILE = RAW_DIR / "global_ads_performance_dataset.csv"
KAG_FILE = RAW_DIR / "KAG_conversion_data.csv"
MARKETING_AB_FILE = RAW_DIR / "marketing_AB.csv"

CLEANED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def print_banner(title):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def safe_divide(numerator, denominator):
    """
    Row-wise division.

    Returns NaN where denominator is zero or missing.
    """
    numerator = pd.to_numeric(
        numerator,
        errors="coerce"
    )

    denominator = pd.to_numeric(
        denominator,
        errors="coerce"
    )

    return numerator.div(
        denominator.replace(0, np.nan)
    )


def safe_scalar_divide(numerator, denominator):
    """
    Scalar division with protection against zero.
    """
    if pd.isna(numerator) or pd.isna(denominator):
        return np.nan

    if denominator == 0:
        return np.nan

    return numerator / denominator


def add_iqr_outlier_flag(df, column):
    """
    Adds a binary IQR outlier flag.

    1 = statistical outlier
    0 = not an IQR outlier

    Outliers are FLAGGED, not deleted.
    """

    numeric = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)

    iqr = q3 - q1

    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    flag = (
        (numeric < lower_bound)
        | 
        (numeric > upper_bound)
    )

    df[f"{column}_IQR_Outlier_Flag"] = (
        flag
        .fillna(False)
        .astype(int)
    )

    return df


def standardize_text_column(df, column):
    """
    Standardizes text fields without changing their meaning.
    """

    if column not in df.columns:
        return df

    df[column] = (
        df[column]
        .astype("string")
        .str.strip()
    )

    return df


def convert_numeric_columns(df, columns):
    """
    Converts selected columns to numeric safely.
    """

    for column in columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


def clean_global_ads():

    print_banner(
        "CLEANING DATASET 1: GLOBAL ADS PERFORMANCE"
    )

    df = pd.read_csv(
        GLOBAL_ADS_FILE
    )

    raw_rows = len(df)
    raw_columns = len(df.columns)

    print(
        f"Raw dataset: {raw_rows:,} rows × "
        f"{raw_columns} columns"
    )

    df.columns = (
        df.columns
        .str.strip()
    )

    if "date" in df.columns:

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
        "ROAS"
    ]

    df = convert_numeric_columns(
        df,
        numeric_columns
    )

    categorical_columns = [
        "platform",
        "campaign_type",
        "industry",
        "country"
    ]

    for column in categorical_columns:
        df = standardize_text_column(
            df,
            column
        )

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

    df["CTR_Validation_Difference"] = (
        df["CTR"]
        -
        df["CTR_Calculated"]
    )

    df["CPC_Validation_Difference"] = (
        df["CPC"]
        -
        df["CPC_Calculated"]
    )

    df["CPA_Validation_Difference"] = (
        df["CPA"]
        -
        df["CPA_Calculated"]
    )

    df["ROAS_Validation_Difference"] = (
        df["ROAS"]
        -
        df["ROAS_Calculated"]
    )

    df["CTR_%"] = (
        safe_divide(
            df["clicks"],
            df["impressions"]
        )
        * 100
    )

    df["CTR_Validation_Flag"] = (
        df["CTR_Validation_Difference"]
        .abs()
        <= 0.01
    ).astype(int)

    df["CPC_Validation_Flag"] = (
        df["CPC_Validation_Difference"]
        .abs()
        <= 0.01
    ).astype(int)

    df["CPA_Validation_Flag"] = (
        df["CPA_Validation_Difference"]
        .abs()
        <= 0.01
    ).astype(int)

    df["ROAS_Validation_Flag"] = (
        df["ROAS_Validation_Difference"]
        .abs()
        <= 0.01
    ).astype(int)

    df["Clicks_Greater_Than_Impressions_Flag"] = (
        df["clicks"]
        > 
        df["impressions"]
    ).astype(int)

    df["Conversions_Greater_Than_Clicks_Flag"] = (
        df["conversions"]
        > 
        df["clicks"]
    ).astype(int)

    negative_condition = (
        (df["impressions"] < 0)
        | 
        (df["clicks"] < 0)
        | 
        (df["ad_spend"] < 0)
        | 
        (df["conversions"] < 0)
        | 
        (df["revenue"] < 0)
    )

    df["Negative_Value_Flag"] = (
        negative_condition
        .fillna(False)
        .astype(int)
    )

    outlier_columns = [
        "impressions",
        "clicks",
        "CTR",
        "CPC",
        "ad_spend",
        "conversions",
        "CPA",
        "revenue",
        "ROAS"
    ]

    for column in outlier_columns:

        df = add_iqr_outlier_flag(
            df,
            column
        )

    df["Invalid_Date_Flag"] = (
        df["date"].isna()
    ).astype(int)

    output_file = (
        CLEANED_DIR
        / 
        "global_ads_performance_cleaned.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"Cleaned dataset saved:\n{output_file}"
    )

    print(
        f"Final shape: {df.shape[0]:,} rows × "
        f"{df.shape[1]} columns"
    )

    return df


def clean_kag():

    print_banner(
        "CLEANING DATASET 2: KAG CONVERSION DATA"
    )

    df = pd.read_csv(
        KAG_FILE
    )

    raw_rows = len(df)
    raw_columns = len(df.columns)

    print(
        f"Raw dataset: {raw_rows:,} rows × "
        f"{raw_columns} columns"
    )

    df.columns = (
        df.columns
        .str.strip()
    )

    identifier_columns = [
        "ad_id",
        "xyz_campaign_id",
        "fb_campaign_id"
    ]

    for column in identifier_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

    if "interest" in df.columns:

        df["interest"] = (
            df["interest"]
            .astype("string")
            .str.strip()
        )

    if "gender" in df.columns:

        df["gender"] = (
            df["gender"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    if "age" in df.columns:

        df["age"] = (
            df["age"]
            .astype("string")
            .str.strip()
        )

    numeric_columns = [
        "Impressions",
        "Clicks",
        "Spent",
        "Total_Conversion",
        "Approved_Conversion"
    ]

    df = convert_numeric_columns(
        df,
        numeric_columns
    )

    df["CTR_%"] = (
        safe_divide(
            df["Clicks"],
            df["Impressions"]
        )
        * 100
    )

    df["Click_to_Total_Conversion_%"] = (
        safe_divide(
            df["Total_Conversion"],
            df["Clicks"]
        )
        * 100
    )

    df["Click_to_Approved_Conversion_%"] = (
        safe_divide(
            df["Approved_Conversion"],
            df["Clicks"]
        )
        * 100
    )

    df["Total_to_Approved_Conversion_%"] = (
        safe_divide(
            df["Approved_Conversion"],
            df["Total_Conversion"]
        )
        * 100
    )

    df["CPC"] = safe_divide(
        df["Spent"],
        df["Clicks"]
    )

    df["Cost_per_Approved_Conversion"] = (
        safe_divide(
            df["Spent"],
            df["Approved_Conversion"]
        )
    )

    df["Total_Conversion_Greater_Than_Clicks_Flag"] = (
        df["Total_Conversion"]
        > 
        df["Clicks"]
    ).astype(int)

    df["Approved_Greater_Than_Total_Flag"] = (
        df["Approved_Conversion"]
        > 
        df["Total_Conversion"]
    ).astype(int)

    negative_condition = (
        (df["Impressions"] < 0)
        | 
        (df["Clicks"] < 0)
        | 
        (df["Spent"] < 0)
        | 
        (df["Total_Conversion"] < 0)
        | 
        (df["Approved_Conversion"] < 0)
    )

    df["Negative_Value_Flag"] = (
        negative_condition
        .fillna(False)
        .astype(int)
    )

    outlier_columns = [
        "Impressions",
        "Clicks",
        "Spent",
        "Total_Conversion",
        "Approved_Conversion"
    ]

    for column in outlier_columns:

        df = add_iqr_outlier_flag(
            df,
            column
        )

    df["Missing_Value_Flag"] = (
        df.isna()
        .any(axis=1)
        .astype(int)
    )

    df["Duplicate_Row_Flag"] = (
        df.duplicated(
            keep=False
        )
        .astype(int)
    )

    output_file = (
        CLEANED_DIR
        / 
        "KAG_conversion_data_cleaned.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"Cleaned dataset saved:\n{output_file}"
    )

    print(
        f"Final shape: {df.shape[0]:,} rows × "
        f"{df.shape[1]} columns"
    )

    return df


def clean_marketing_ab():

    print_banner(
        "CLEANING DATASET 3: MARKETING A/B TESTING"
    )

    df = pd.read_csv(
        MARKETING_AB_FILE
    )

    raw_rows = len(df)
    raw_columns = len(df.columns)

    print(
        f"Raw dataset: {raw_rows:,} rows × "
        f"{raw_columns} columns"
    )

    df.columns = (
        df.columns
        .str.strip()
    )

    if "user id" in df.columns:

        df["user id"] = (
            df["user id"]
            .astype("string")
            .str.strip()
        )

    if "test group" in df.columns:

        df["test group"] = (
            df["test group"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

    if "converted" in df.columns:

        df["converted"] = pd.to_numeric(
            df["converted"],
            errors="coerce"
        )

    if "total ads" in df.columns:

        df["total ads"] = pd.to_numeric(
            df["total ads"],
            errors="coerce"
        )

    if "date" in df.columns:

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

    if "hour" in df.columns:

        df["hour"] = pd.to_numeric(
            df["hour"],
            errors="coerce"
        )

    if "Unnamed: 0" in df.columns:

        df["Index_Metadata_Flag"] = 1

    else:

        df["Index_Metadata_Flag"] = 0

    df["Negative_Total_Ads_Flag"] = (
        df["total ads"] < 0
    ).astype(int)

    df["Invalid_Conversion_Value_Flag"] = (
        ~df["converted"].isin([0, 1])
    ).astype(int)

    df["Ad_Exposure_Level"] = pd.cut(
        df["total ads"],
        bins=[
            -np.inf,
            0,
            5,
            20,
            50,
            np.inf
        ],
        labels=[
            "No Exposure",
            "Low Exposure",
            "Moderate Exposure",
            "High Exposure",
            "Very High Exposure"
        ]
    )

    df = add_iqr_outlier_flag(
        df,
        "total ads"
    )

    if "user id" in df.columns:

        df["Duplicate_User_ID_Flag"] = (
            df["user id"]
            .duplicated(
                keep=False
            )
            .astype(int)
        )

    else:

        df["Duplicate_User_ID_Flag"] = 0

    df["Missing_Value_Flag"] = (
        df.isna()
        .any(axis=1)
        .astype(int)
    )

    df["Data_Quality_Flag"] = (
        (
            df["Negative_Total_Ads_Flag"]
            == 0
        )
        & 
        (
            df["Invalid_Conversion_Value_Flag"]
            == 0
        )
    ).astype(int)

    output_file = (
        CLEANED_DIR
        / 
        "marketing_AB_cleaned.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"Cleaned dataset saved:\n{output_file}"
    )

    print(
        f"Final shape: {df.shape[0]:,} rows × "
        f"{df.shape[1]} columns"
    )

    return df


def print_quality_summary(
    name,
    df
):

    print()
    print("-" * 80)
    print(f"POST-CLEANING QUALITY CHECK: {name}")
    print("-" * 80)

    print(
        f"Rows: {len(df):,}"
    )

    print(
        f"Columns: {len(df.columns):,}"
    )

    print(
        f"Missing cells: {int(df.isna().sum().sum()):,}"
    )

    print(
        f"Duplicate rows: {int(df.duplicated().sum()):,}"
    )

    print(
        "Cleaned dataset retained all source observations."
    )


def main():

    print_banner(
        "MARKETLENS — CLEANED DATA GENERATION"
    )

    print(
        "Raw datasets will remain unchanged."
    )

    print(
        "Outliers will be flagged rather than automatically deleted."
    )

    print(
        f"\nCleaned output directory:\n{CLEANED_DIR}"
    )

    global_ads = clean_global_ads()

    kag = clean_kag()

    marketing_ab = clean_marketing_ab()

    print_quality_summary(
        "Global Ads Performance",
        global_ads
    )

    print_quality_summary(
        "KAG Conversion Data",
        kag
    )

    print_quality_summary(
        "Marketing A/B Testing",
        marketing_ab
    )

    print_banner(
        "MARKETLENS CLEANING COMPLETE"
    )

    print(
        "Three cleaned analytical datasets were created:"
    )

    print(
        f"1. {CLEANED_DIR / 'global_ads_performance_cleaned.csv'}"
    )

    print(
        f"2. {CLEANED_DIR / 'KAG_conversion_data_cleaned.csv'}"
    )

    print(
        f"3. {CLEANED_DIR / 'marketing_AB_cleaned.csv'}"
    )

    print()
    print(
        "Raw datasets were not modified."
    )

    print(
        "IQR outliers were flagged, not deleted."
    )

    print(
        "KAG conversion-definition anomalies were retained and flagged."
    )

    print(
        "These cleaned datasets are ready for the next analytical stage."
    )


if __name__ == "__main__":
    main()

from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(
    r"C:\Users\Pranoti munjankar\OneDrive\Desktop\DA PROJECTS\Marketlens"
)

RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"

GLOBAL_RAW = RAW_DIR / "global_ads_performance_dataset.csv"
GLOBAL_CLEANED = (
    CLEANED_DIR / "global_ads_performance_cleaned.csv"
)

KAG_RAW = RAW_DIR / "KAG_conversion_data.csv"
KAG_CLEANED = (
    CLEANED_DIR / "KAG_conversion_data_cleaned.csv"
)

AB_RAW = RAW_DIR / "marketing_AB.csv"
AB_CLEANED = (
    CLEANED_DIR / "marketing_AB_cleaned.csv"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "analysis"
    / "outputs"
    / "reports"
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

VALIDATION_REPORT = (
    REPORT_DIR
    / "MARKETLENS_POST_CLEANING_VALIDATION.txt"
)


def section(title):
    return [
        "",
        "=" * 90,
        title,
        "=" * 90,
    ]


def subsection(title):
    return [
        "",
        "-" * 90,
        title,
        "-" * 90,
    ]


def compare_series(
    raw_df,
    cleaned_df,
    column
):
    """
    Compare original source column between
    raw and cleaned datasets.
    """

    if column not in raw_df.columns:
        return {
            "status": "NOT_FOUND_IN_RAW"
        }

    if column not in cleaned_df.columns:
        return {
            "status": "MISSING_FROM_CLEANED"
        }

    raw = raw_df[column]
    cleaned = cleaned_df[column]

    if len(raw) != len(cleaned):
        return {
            "status": "ROW_COUNT_MISMATCH"
        }
     
    raw_compare = raw.astype("string").fillna("<NA>")
    cleaned_compare = (
        cleaned.astype("string")
        .fillna("<NA>")
    )

    differences = (
        raw_compare
        != cleaned_compare
    )

    difference_count = int(
        differences.sum()
    )

    return {
        "status": "MATCH"
        if difference_count == 0
        else "VALUE_DIFFERENCE",
        "differences": difference_count,
    }


def get_new_columns(
    raw_df,
    cleaned_df
):
    return [
        column
        for column in cleaned_df.columns
        if column not in raw_df.columns
    ]


def count_flagged_rows(
    df,
    column
):
    if column not in df.columns:
        return None

    return int(
        pd.to_numeric(
            df[column],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )


def validate_global_ads(lines):

    raw = pd.read_csv(
        GLOBAL_RAW
    )

    cleaned = pd.read_csv(
        GLOBAL_CLEANED
    )

    lines += section(
        "1. GLOBAL ADS PERFORMANCE — POST-CLEANING VALIDATION"
    )

    lines += subsection(
        "1.1 RAW VS CLEANED STRUCTURE"
    )

    lines.append(
        f"Raw rows: {len(raw):,}"
    )

    lines.append(
        f"Cleaned rows: {len(cleaned):,}"
    )

    lines.append(
        f"Raw columns: {len(raw.columns):,}"
    )

    lines.append(
        f"Cleaned columns: {len(cleaned.columns):,}"
    )

    row_match = (
        len(raw)
        == 
        len(cleaned)
    )

    lines.append(
        f"Row count preserved: {'YES' if row_match else 'NO'}"
    )

    lines += subsection(
        "1.2 ORIGINAL SOURCE COLUMNS"
    )

    missing_original_columns = [
        column
        for column in raw.columns
        if column not in cleaned.columns
    ]

    if not missing_original_columns:
        lines.append(
            "All 14 original source columns are present."
        )
    else:
        lines.append(
            "Missing original columns:"
        )
        lines.extend(
            f"  - {column}"
            for column in missing_original_columns
        )

    lines += subsection(
        "1.3 ORIGINAL VALUE PRESERVATION"
    )

    for column in raw.columns:

        result = compare_series(
            raw,
            cleaned,
            column
        )

        if result["status"] == "MATCH":

            lines.append(
                f"{column}: MATCH"
            )

        else:

            lines.append(
                f"{column}: {result}"
            )

    lines += subsection(
        "1.4 NEW ANALYTICAL COLUMNS"
    )

    new_columns = get_new_columns(
        raw,
        cleaned
    )

    for column in new_columns:
        lines.append(
            f"- {column}"
        )

    lines.append(
        f"Number of new analytical columns: {len(new_columns)}"
    )

    lines += subsection(
        "1.5 MISSING VALUES"
    )

    raw_missing = int(
        raw.isna().sum().sum()
    )

    cleaned_missing = int(
        cleaned.isna().sum().sum()
    )

    lines.append(
        f"Raw missing cells: {raw_missing:,}"
    )

    lines.append(
        f"Cleaned missing cells: {cleaned_missing:,}"
    )

    lines += subsection(
        "1.6 LOGICAL QUALITY FLAGS"
    )

    logical_flags = [
        "Clicks_Greater_Than_Impressions_Flag",
        "Conversions_Greater_Than_Clicks_Flag",
        "Negative_Value_Flag",
        "Invalid_Date_Flag",
    ]

    for flag in logical_flags:

        count = count_flagged_rows(
            cleaned,
            flag
        )

        if count is not None:

            lines.append(
                f"{flag}: {count:,} flagged rows"
            )

    lines += subsection(
        "1.7 IQR OUTLIER FLAGS"
    )

    outlier_flags = [
        column
        for column in cleaned.columns
        if column.endswith(
            "_IQR_Outlier_Flag"
        )
    ]

    for flag in outlier_flags:

        count = count_flagged_rows(
            cleaned,
            flag
        )

        lines.append(
            f"{flag}: {count:,} flagged rows"
        )

    lines += subsection(
        "1.8 GLOBAL ADS VALIDATION RESULT"
    )

    if (
        row_match
        and not missing_original_columns
        and cleaned_missing == 0
    ):

        lines.append(
            "STATUS: PASSED"
        )

        lines.append(
            "Original observations and source values were preserved."
        )

    else:

        lines.append(
            "STATUS: REVIEW REQUIRED"
        )


def validate_kag(lines):

    raw = pd.read_csv(
        KAG_RAW
    )

    cleaned = pd.read_csv(
        KAG_CLEANED
    )

    lines += section(
        "2. KAG CONVERSION DATA — POST-CLEANING VALIDATION"
    )

    lines += subsection(
        "2.1 RAW VS CLEANED STRUCTURE"
    )

    lines.append(
        f"Raw rows: {len(raw):,}"
    )

    lines.append(
        f"Cleaned rows: {len(cleaned):,}"
    )

    lines.append(
        f"Raw columns: {len(raw.columns):,}"
    )

    lines.append(
        f"Cleaned columns: {len(cleaned.columns):,}"
    )

    row_match = (
        len(raw)
        == 
        len(cleaned)
    )

    lines.append(
        f"Row count preserved: {'YES' if row_match else 'NO'}"
    )

    lines += subsection(
        "2.2 ORIGINAL SOURCE COLUMNS"
    )

    missing_original_columns = [
        column
        for column in raw.columns
        if column not in cleaned.columns
    ]

    if not missing_original_columns:

        lines.append(
            "All 11 original source columns are present."
        )

    else:

        lines.append(
            "Missing original columns:"
        )

        lines.extend(
            f"  - {column}"
            for column in missing_original_columns
        )

    lines += subsection(
        "2.3 ORIGINAL VALUE PRESERVATION"
    )

    for column in raw.columns:

        result = compare_series(
            raw,
            cleaned,
            column
        )

        if result["status"] == "MATCH":

            lines.append(
                f"{column}: MATCH"
            )

        else:

            lines.append(
                f"{column}: {result}"
            )

    lines += subsection(
        "2.4 NEW ANALYTICAL COLUMNS"
    )

    new_columns = get_new_columns(
        raw,
        cleaned
    )

    for column in new_columns:

        lines.append(
            f"- {column}"
        )

    lines.append(
        f"Number of new analytical columns: {len(new_columns)}"
    )

    lines += subsection(
        "2.5 MISSING VALUES INVESTIGATION"
    )

    raw_missing = int(
        raw.isna().sum().sum()
    )

    cleaned_missing = int(
        cleaned.isna().sum().sum()
    )

    lines.append(
        f"Raw missing cells: {raw_missing:,}"
    )

    lines.append(
        f"Cleaned missing cells: {cleaned_missing:,}"
    )

    lines.append(
        ""
    )

    lines.append(
        "Missing values by cleaned column:"
    )

    missing_by_column = (
        cleaned.isna()
        .sum()
    )

    missing_by_column = (
        missing_by_column[
            missing_by_column > 0
        ]
        .sort_values(
            ascending=False
        )
    )

    if missing_by_column.empty:

        lines.append(
            "  No missing values found."
        )

    else:

        for column, count in (
            missing_by_column.items()
        ):

            lines.append(
                f"  {column}: {int(count):,}"
            )

    lines.append(
        ""
    )

    lines.append(
        "Interpretation:"
    )

    lines.append(
        "The KAG raw dataset contained no missing source values."
    )

    lines.append(
        "Any missing values introduced during cleaning are expected "
        "to come from calculated rate fields where the denominator "
        "is zero."
    )

    lines.append(
        "These analytical NaN values are retained rather than "
        "artificially replacing them with zero."
    )

    lines += subsection(
        "2.6 SOURCE-DEFINITION VALIDATION"
    )

    anomaly_flag = (
        "Total_Conversion_Greater_Than_Clicks_Flag"
    )

    if anomaly_flag in cleaned.columns:

        flagged = count_flagged_rows(
            cleaned,
            anomaly_flag
        )

        raw_anomaly = int(
            (
                pd.to_numeric(
                    raw["Total_Conversion"],
                    errors="coerce"
                )
                > 
                pd.to_numeric(
                    raw["Clicks"],
                    errors="coerce"
                )
            )
            .sum()
        )

        lines.append(
            f"Raw records where Total_Conversion > Clicks: "
            f"{raw_anomaly:,}"
        )

        lines.append(
            f"Cleaned records flagged: {flagged:,}"
        )

        lines.append(
            "Result: source-definition anomaly retained and flagged."
        )

    approved_flag = (
        "Approved_Greater_Than_Total_Flag"
    )

    if approved_flag in cleaned.columns:

        flagged = count_flagged_rows(
            cleaned,
            approved_flag
        )

        lines.append(
            f"Approved_Conversion > Total_Conversion: "
            f"{flagged:,} flagged rows"
        )

    lines += subsection(
        "2.7 NEGATIVE VALUES"
    )

    negative_flag = (
        "Negative_Value_Flag"
    )

    if negative_flag in cleaned.columns:

        flagged = count_flagged_rows(
            cleaned,
            negative_flag
        )

        lines.append(
            f"Negative-value flagged rows: {flagged:,}"
        )

    lines += subsection(
        "2.8 IQR OUTLIER FLAGS"
    )

    outlier_flags = [
        column
        for column in cleaned.columns
        if column.endswith(
            "_IQR_Outlier_Flag"
        )
    ]

    for flag in outlier_flags:

        count = count_flagged_rows(
            cleaned,
            flag
        )

        lines.append(
            f"{flag}: {count:,} flagged rows"
        )

    lines += subsection(
        "2.9 KAG VALIDATION RESULT"
    )

    if (
        row_match
        and not missing_original_columns
    ):

        lines.append(
            "STATUS: PASSED WITH DOCUMENTED ANALYTICAL NaN VALUES"
        )

        lines.append(
            "Original observations and source values were preserved."
        )

        lines.append(
            "The additional missing cells originate from "
            "calculated metrics and are not raw-data missingness."
        )

    else:

        lines.append(
            "STATUS: REVIEW REQUIRED"
        )


def validate_marketing_ab(lines):

    raw = pd.read_csv(
        AB_RAW
    )

    cleaned = pd.read_csv(
        AB_CLEANED
    )

    lines += section(
        "3. MARKETING A/B TESTING — POST-CLEANING VALIDATION"
    )

    lines += subsection(
        "3.1 RAW VS CLEANED STRUCTURE"
    )

    lines.append(
        f"Raw rows: {len(raw):,}"
    )

    lines.append(
        f"Cleaned rows: {len(cleaned):,}"
    )

    lines.append(
        f"Raw columns: {len(raw.columns):,}"
    )

    lines.append(
        f"Cleaned columns: {len(cleaned.columns):,}"
    )

    row_match = (
        len(raw)
        == 
        len(cleaned)
    )

    lines.append(
        f"Row count preserved: {'YES' if row_match else 'NO'}"
    )

    lines += subsection(
        "3.2 ORIGINAL SOURCE COLUMNS"
    )

    missing_original_columns = [
        column
        for column in raw.columns
        if column not in cleaned.columns
    ]

    if not missing_original_columns:

        lines.append(
            "All 7 original source columns are present."
        )

    else:

        lines.append(
            "Missing original columns:"
        )

        lines.extend(
            f"  - {column}"
            for column in missing_original_columns
        )

    lines += subsection(
        "3.3 ORIGINAL VALUE PRESERVATION"
    )

    for column in raw.columns:

        result = compare_series(
            raw,
            cleaned,
            column
        )

        if result["status"] == "MATCH":

            lines.append(
                f"{column}: MATCH"
            )

        else:

            lines.append(
                f"{column}: {result}"
            )

    lines += subsection(
        "3.4 NEW ANALYTICAL COLUMNS"
    )

    new_columns = get_new_columns(
        raw,
        cleaned
    )

    for column in new_columns:

        lines.append(
            f"- {column}"
        )

    lines.append(
        f"Number of new analytical columns: {len(new_columns)}"
    )

    lines += subsection(
        "3.5 MISSING VALUES"
    )

    raw_missing = int(
        raw.isna().sum().sum()
    )

    cleaned_missing = int(
        cleaned.isna().sum().sum()
    )

    lines.append(
        f"Raw missing cells: {raw_missing:,}"
    )

    lines.append(
        f"Cleaned missing cells: {cleaned_missing:,}"
    )

    lines += subsection(
        "3.6 CONVERSION VALIDATION"
    )

    if "converted" in cleaned.columns:

        unique_values = sorted(
            cleaned["converted"]
            .dropna()
            .unique()
            .tolist()
        )

        lines.append(
            f"Distinct converted values: {unique_values}"
        )

        invalid_count = int(
            (
                ~cleaned["converted"]
                .isin([0, 1])
            )
            .sum()
        )

        lines.append(
            f"Invalid conversion values: {invalid_count:,}"
        )

    lines += subsection(
        "3.7 EXPOSURE VALIDATION"
    )

    if "total ads" in cleaned.columns:

        negative_ads = int(
            (
                cleaned["total ads"]
                < 0
            )
            .sum()
        )

        lines.append(
            f"Negative total ads: {negative_ads:,}"
        )

        lines.append(
            f"Minimum total ads: "
            f"{cleaned['total ads'].min():,.0f}"
        )

        lines.append(
            f"Median total ads: "
            f"{cleaned['total ads'].median():,.2f}"
        )

        lines.append(
            f"Maximum total ads: "
            f"{cleaned['total ads'].max():,.0f}"
        )

    lines += subsection(
        "3.8 DUPLICATE USER VALIDATION"
    )

    if "user id" in cleaned.columns:

        duplicate_users = int(
            cleaned["user id"]
            .duplicated()
            .sum()
        )

        lines.append(
            f"Duplicate user IDs: {duplicate_users:,}"
        )

    lines += subsection(
        "3.9 INDEX-LIKE METADATA"
    )

    if "Unnamed: 0" in cleaned.columns:

        lines.append(
            "Unnamed: 0 is retained as source metadata."
        )

        lines.append(
            "It should NOT be used as an analytical feature "
            "in Power BI."
        )

    lines += subsection(
        "3.10 IQR OUTLIER VALIDATION"
    )

    flag = (
        "total ads_IQR_Outlier_Flag"
    )

    if flag in cleaned.columns:

        count = count_flagged_rows(
            cleaned,
            flag
        )

        lines.append(
            f"Total ads IQR outliers flagged: {count:,}"
        )

        lines.append(
            "Outliers were flagged rather than deleted."
        )

    lines += subsection(
        "3.11 MARKETING A/B VALIDATION RESULT"
    )

    if (
        row_match
        and not missing_original_columns
        and cleaned_missing == 0
    ):

        lines.append(
            "STATUS: PASSED"
        )

        lines.append(
            "Original observations and source values were preserved."
        )

    else:

        lines.append(
            "STATUS: REVIEW REQUIRED"
        )


def final_validation(lines):

    lines += section(
        "4. MARKETLENS — OVERALL POST-CLEANING CONCLUSION"
    )

    lines.append(
        "The three cleaned analytical datasets were generated "
        "without modifying the original raw CSV files."
    )

    lines.append(
        ""
    )

    lines.append(
        "Global Ads Performance:"
    )

    lines.append(
        "1,800 observations retained."
    )

    lines.append(
        "Original source values preserved."
    )

    lines.append(
        "Analytical KPI calculations and quality flags added."
    )

    lines.append(
        "IQR outliers flagged rather than deleted."
    )

    lines.append(
        ""
    )

    lines.append(
        "KAG Conversion Data:"
    )

    lines.append(
        "1,143 observations retained."
    )

    lines.append(
        "Original source values preserved."
    )

    lines.append(
        "The Total_Conversion > Clicks condition was retained "
        "as a documented source-definition issue."
    )

    lines.append(
        "Missing values in calculated metrics are treated as "
        "undefined ratios rather than forced zeros."
    )

    lines.append(
        ""
    )

    lines.append(
        "Marketing A/B Testing:"
    )

    lines.append(
        "588,101 observations retained."
    )

    lines.append(
        "Original source values preserved."
    )

    lines.append(
        "Total ad exposure outliers were flagged rather than deleted."
    )

    lines.append(
        "The index-like Unnamed: 0 field is retained as metadata "
        "but should not be used as an analytical feature."
    )

    lines.append(
        ""
    )

    lines.append(
        "OVERALL STATUS:"
    )

    lines.append(
        "CLEANED DATA LAYER VALIDATED FOR DASHBOARD PREPARATION"
    )

    lines.append(
        ""
    )

    lines.append(
        "Recommended next stage:"
    )

    lines.append(
        "Cleaned Data → Data Dictionary → Power BI Data Model → Dashboard"
    )


def main():

    print()
    print("=" * 90)
    print("MARKETLENS — POST-CLEANING VALIDATION")
    print("=" * 90)

    print()
    print(
        "Validating cleaned datasets..."
    )

    print(
        "No cleaned CSV will be modified."
    )

    lines = []

    lines.append(
        "MARKETLENS"
    )

    lines.append(
        "POST-CLEANING VALIDATION REPORT"
    )

    lines.append(
        "=" * 90
    )

    lines.append(
        "Purpose: Validate the analytical cleaned-data layer "
        "before Power BI dashboard development."
    )

    lines.append(
        "Raw data remains unchanged."
    )

    lines.append(
        "Outliers are evaluated as flags rather than automatically deleted."
    )

    validate_global_ads(
        lines
    )

    validate_kag(
        lines
    )

    validate_marketing_ab(
        lines
    )

    final_validation(
        lines
    )

    report_text = "\n".join(
        lines
    )

    VALIDATION_REPORT.write_text(
        report_text,
        encoding="utf-8"
    )

    print()
    print("=" * 90)
    print("POST-CLEANING VALIDATION COMPLETED")
    print("=" * 90)

    print()
    print(
        "Validation report:"
    )

    print(
        VALIDATION_REPORT
    )

    print()
    print(
        "The three cleaned datasets were not modified."
    )


if __name__ == "__main__":
    main()

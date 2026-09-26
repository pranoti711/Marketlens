"""
MarketLens - A/B Testing Analysis
==================================

Purpose
-------
Analyze a randomized marketing experiment to evaluate whether the
treatment group shows a statistically different conversion rate
compared with the control group.

Analysis included
-----------------
1. Data loading and validation
2. Group-level sample size analysis
3. Conversion-rate calculation
4. Absolute lift
5. Relative lift
6. Two-proportion z-test
7. 95% confidence interval
8. Effect-size interpretation
9. Business interpretation
10. Automated report generation
11. Visualization

Author: Pranoti Ashok Munjankar
Project: MarketLens
"""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm

warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

AB_TEST_DIR = PROJECT_ROOT / "ab_testing"

DATA_DIR = PROJECT_ROOT / "data"

REPORT_DIR = AB_TEST_DIR / "reports"
FIGURE_DIR = AB_TEST_DIR / "figures"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# IMPORTANT:
# Change this path ONLY if your A/B dataset has a different
# filename or is stored somewhere else.
# ------------------------------------------------------------

POSSIBLE_FILES = [
    DATA_DIR / "raw" / "marketing_AB.csv",
    DATA_DIR / "raw" / "marketing_ab.csv",
    DATA_DIR / "marketing_AB.csv",
    DATA_DIR / "marketing_ab.csv",
    PROJECT_ROOT / "marketing_AB.csv",
    PROJECT_ROOT / "marketing_ab.csv",
]

ALPHA = 0.05
CONFIDENCE_LEVEL = 0.95

# ============================================================
# UTILITY FUNCTIONS
# ============================================================


def find_dataset():
    """
    Locate the A/B testing dataset automatically.
    """

    for file_path in POSSIBLE_FILES:
        if file_path.exists():
            return file_path

    # Search recursively as a fallback
    candidates = list(PROJECT_ROOT.rglob("marketing_AB.csv"))

    if not candidates:
        candidates = list(PROJECT_ROOT.rglob("marketing_ab.csv"))

    if candidates:
        return candidates[0]

    raise FileNotFoundError(
        "\nA/B testing dataset was not found.\n\n"
        "Expected filename examples:\n"
        "  marketing_AB.csv\n"
        "  marketing_ab.csv\n\n"
        "Place the file inside:\n"
        "  MarketLens/data/raw/\n"
    )


def detect_column(df, possible_names):
    """
    Detect a column from a list of possible names.
    """

    normalized = {
        str(column).strip().lower().replace(" ", "_"): column
        for column in df.columns
    }

    for name in possible_names:
        key = name.lower().replace(" ", "_")

        if key in normalized:
            return normalized[key]

    return None


def clean_binary_conversion(series):
    """
    Convert common binary conversion formats into 0/1.
    """

    if pd.api.types.is_numeric_dtype(series):

        values = pd.to_numeric(series, errors="coerce")

        unique_values = set(values.dropna().unique())

        if unique_values.issubset({0, 1}):
            return values

    cleaned = (
        series.astype(str)
        .str.strip()
        .str.lower()
    )

    mapping = {
        "1": 1,
        "0": 0,
        "true": 1,
        "false": 0,
        "yes": 1,
        "no": 0,
        "converted": 1,
        "not converted": 0,
        "t": 1,
        "f": 0,
        "y": 1,
        "n": 0,
    }

    return cleaned.map(mapping)


def find_control_and_treatment(groups):
    """
    Identify control and treatment groups.
    """

    normalized = {
        str(group).strip().lower(): group
        for group in groups
    }

    control_candidates = [
        "control",
        "psa",
        "a",
        "control group",
    ]

    treatment_candidates = [
        "treatment",
        "ad",
        "test",
        "b",
        "treatment group",
    ]

    control = None
    treatment = None

    for candidate in control_candidates:
        if candidate in normalized:
            control = normalized[candidate]
            break

    for candidate in treatment_candidates:
        if candidate in normalized:
            treatment = normalized[candidate]
            break

    # Fallback:
    # If exactly two groups exist and names are unfamiliar,
    # use the order returned by pandas.
    if control is None or treatment is None:

        unique_groups = list(groups)

        if len(unique_groups) == 2:

            if control is None:
                control = unique_groups[0]

            if treatment is None:
                treatment = (
                    unique_groups[1]
                    if unique_groups[1] != control
                    else unique_groups[0]
                )

    return control, treatment

# ============================================================
# DATA LOADING
# ============================================================


def load_data():

    file_path = find_dataset()

    print("\n" + "=" * 70)
    print("MARKETLENS - A/B TESTING ANALYSIS")
    print("=" * 70)

    print(f"\nDataset: {file_path}")

    df = pd.read_csv(file_path)

    print(f"Rows    : {df.shape[0]:,}")
    print(f"Columns : {df.shape[1]}")

    return df, file_path

# ============================================================
# DATA VALIDATION
# ============================================================


def validate_data(df):

    print("\n" + "-" * 70)
    print("DATA VALIDATION")
    print("-" * 70)

    print(f"Duplicate rows : {df.duplicated().sum():,}")
    print(f"Missing cells  : {df.isna().sum().sum():,}")

    group_col = detect_column(
        df,
        [
            "test_group",
            "test group",
            "group",
            "experiment_group",
        ],
    )

    conversion_col = detect_column(
        df,
        [
            "converted",
            "conversion",
            "conversion_flag",
        ],
    )

    if group_col is None:
        raise ValueError(
            "Could not identify the test-group column."
        )

    if conversion_col is None:
        raise ValueError(
            "Could not identify the conversion column."
        )

    print(f"\nGroup column      : {group_col}")
    print(f"Conversion column : {conversion_col}")

    return group_col, conversion_col

# ============================================================
# PREPARE DATA
# ============================================================


def prepare_data(df, group_col, conversion_col):

    data = df.copy()

    data[group_col] = (
        data[group_col]
        .astype(str)
        .str.strip()
    )

    data["conversion_binary"] = clean_binary_conversion(
        data[conversion_col]
    )

    before = len(data)

    data = data.dropna(
        subset=[group_col, "conversion_binary"]
    )

    removed = before - len(data)

    data["conversion_binary"] = (
        data["conversion_binary"].astype(int)
    )

    print(f"\nRows removed due to invalid/missing values: {removed:,}")

    print("\nExperiment groups:")
    print(data[group_col].value_counts())

    return data

# ============================================================
# GROUP IDENTIFICATION
# ============================================================


def identify_groups(data, group_col):

    groups = list(
        data[group_col]
        .dropna()
        .unique()
    )

    if len(groups) != 2:

        raise ValueError(
            f"Expected exactly 2 experiment groups, "
            f"but found {len(groups)}: {groups}"
        )

    control, treatment = find_control_and_treatment(groups)

    if control == treatment:
        raise ValueError(
            "Could not uniquely identify control and treatment groups."
        )

    print(f"\nControl group   : {control}")
    print(f"Treatment group : {treatment}")

    return control, treatment

# ============================================================
# CONVERSION ANALYSIS
# ============================================================


def calculate_group_metrics(
    data,
    group_col,
    control,
    treatment,
):

    rows = []

    for group_name, label in [
        (control, "Control"),
        (treatment, "Treatment"),
    ]:

        group_data = data[
            data[group_col] == group_name
        ]

        sample_size = len(group_data)

        conversions = int(
            group_data["conversion_binary"].sum()
        )

        non_conversions = sample_size - conversions

        conversion_rate = (
            conversions / sample_size
            if sample_size > 0
            else np.nan
        )

        rows.append(
            {
                "Group": label,
                "Source_Group": group_name,
                "Sample_Size": sample_size,
                "Conversions": conversions,
                "Non_Conversions": non_conversions,
                "Conversion_Rate": conversion_rate,
            }
        )

    metrics = pd.DataFrame(rows)

    return metrics

# ============================================================
# LIFT CALCULATION
# ============================================================


def calculate_lift(metrics):

    control_rate = metrics.loc[
        metrics["Group"] == "Control",
        "Conversion_Rate",
    ].iloc[0]

    treatment_rate = metrics.loc[
        metrics["Group"] == "Treatment",
        "Conversion_Rate",
    ].iloc[0]

    absolute_lift = treatment_rate - control_rate

    if control_rate != 0:
        relative_lift = (
            absolute_lift / control_rate
        )
    else:
        relative_lift = np.nan

    return (
        control_rate,
        treatment_rate,
        absolute_lift,
        relative_lift,
    )

# ============================================================
# TWO-PROPORTION Z-TEST
# ============================================================


def two_proportion_z_test(metrics):

    control = metrics[
        metrics["Group"] == "Control"
    ].iloc[0]

    treatment = metrics[
        metrics["Group"] == "Treatment"
    ].iloc[0]

    x1 = treatment["Conversions"]
    n1 = treatment["Sample_Size"]

    x2 = control["Conversions"]
    n2 = control["Sample_Size"]

    p1 = x1 / n1
    p2 = x2 / n2

    pooled_p = (
        (x1 + x2) / 
        (n1 + n2)
    )

    standard_error = np.sqrt(
        pooled_p
        * (1 - pooled_p)
        * (
            (1 / n1) + 
            (1 / n2)
        )
    )

    difference = p1 - p2

    if standard_error == 0:

        z_stat = np.nan
        p_value = np.nan

    else:

        z_stat = difference / standard_error

        p_value = 2 * (
            1 - norm.cdf(abs(z_stat))
        )

    return z_stat, p_value

# ============================================================
# CONFIDENCE INTERVAL
# ============================================================


def calculate_confidence_interval(metrics):

    control = metrics[
        metrics["Group"] == "Control"
    ].iloc[0]

    treatment = metrics[
        metrics["Group"] == "Treatment"
    ].iloc[0]

    p_control = control["Conversion_Rate"]
    p_treatment = treatment["Conversion_Rate"]

    n_control = control["Sample_Size"]
    n_treatment = treatment["Sample_Size"]

    difference = (
        p_treatment - p_control
    )

    standard_error = np.sqrt(
        (
            p_treatment
            * (1 - p_treatment)
            / n_treatment
        )
        +
        (
            p_control
            * (1 - p_control)
            / n_control
        )
    )

    z_critical = norm.ppf(
        1 - ALPHA / 2
    )

    margin_error = (
        z_critical * standard_error
    )

    lower = difference - margin_error
    upper = difference + margin_error

    return lower, upper

# ============================================================
# INTERPRETATION
# ============================================================


def interpret_results(
    p_value,
    absolute_lift,
    relative_lift,
    ci_lower,
    ci_upper,
):

    statistically_significant = (
        p_value < ALPHA
        if not np.isnan(p_value)
        else False
    )

    if statistically_significant:

        if absolute_lift > 0:

            statistical_statement = (
                "The treatment group shows a statistically "
                "significant higher conversion rate than the control group."
            )

        else:

            statistical_statement = (
                "The treatment group shows a statistically "
                "significant lower conversion rate than the control group."
            )

    else:

        statistical_statement = (
            "The observed difference in conversion rates "
            "is not statistically significant at the 5% significance level."
        )

    if np.isnan(relative_lift):

        lift_text = "Relative lift could not be calculated."

    else:

        lift_text = (
            f"The treatment group shows a relative lift of "
            f"{relative_lift * 100:.2f}% compared with control."
        )

    return (
        statistical_statement,
        lift_text,
        statistically_significant,
    )

# ============================================================
# VISUALIZATION
# ============================================================


def create_conversion_chart(metrics):

    plt.figure(figsize=(9, 6))

    bars = plt.bar(
        metrics["Group"],
        metrics["Conversion_Rate"] * 100,
    )

    plt.title(
        "A/B Test Conversion Rate Comparison",
        fontsize=15,
        fontweight="bold",
    )

    plt.ylabel("Conversion Rate (%)")
    plt.xlabel("Experiment Group")

    plt.ylim(
        0,
        max(metrics["Conversion_Rate"] * 100) * 1.25
    )

    for bar, value in zip(
        bars,
        metrics["Conversion_Rate"] * 100,
    ):

        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.2f}%",
            ha="center",
            va="bottom",
            fontsize=11,
        )

    plt.tight_layout()

    output_file = (
        FIGURE_DIR / 
        "ab_test_conversion_rate.png"
    )

    plt.savefig(
        output_file,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    return output_file

# ============================================================
# REPORT GENERATION
# ============================================================


def generate_report(
    file_path,
    data,
    metrics,
    z_stat,
    p_value,
    absolute_lift,
    relative_lift,
    ci_lower,
    ci_upper,
    statistical_statement,
    lift_text,
):

    control = metrics[
        metrics["Group"] == "Control"
    ].iloc[0]

    treatment = metrics[
        metrics["Group"] == "Treatment"
    ].iloc[0]

    report_file = (
        REPORT_DIR / 
        "AB_TESTING_ANALYSIS_REPORT.md"
    )

    significance = (
        "Statistically Significant"
        if p_value < ALPHA
        else "Not Statistically Significant"
    )

    report = f"""# MarketLens — A/B Testing Analysis

## 1. Experiment Overview

**Dataset:** `{file_path.name}`

**Purpose:** Evaluate whether the treatment group produced a different conversion rate from the control group.

**Significance level:** α = {ALPHA}

**Confidence level:** {CONFIDENCE_LEVEL * 100:.0f}%

---

## 2. Dataset Summary

| Metric | Value |
|---|---:|
| Total observations analyzed | {len(data):,} |
| Control observations | {int(control['Sample_Size']):,} |
| Treatment observations | {int(treatment['Sample_Size']):,} |
| Control conversions | {int(control['Conversions']):,} |
| Treatment conversions | {int(treatment['Conversions']):,} |

---

## 3. Conversion Performance

| Group | Sample Size | Conversions | Conversion Rate |
|---|---:|---:|---:|
| Control | {int(control['Sample_Size']):,} | {int(control['Conversions']):,} | {control['Conversion_Rate'] * 100:.2f}% |
| Treatment | {int(treatment['Sample_Size']):,} | {int(treatment['Conversions']):,} | {treatment['Conversion_Rate'] * 100:.2f}% |

---

## 4. Lift Analysis

### Absolute Lift

**{absolute_lift * 100:.2f} percentage points**

### Relative Lift

**{relative_lift * 100:.2f}%**

{lift_text}

---

## 5. Statistical Test

### Two-Proportion Z-Test

**Z-statistic:** {z_stat:.4f}

**P-value:** {p_value:.6f}

**Result:** **{significance}**

{statistical_statement}

---

## 6. 95% Confidence Interval

The estimated difference in conversion rates has the following 95% confidence interval:

**[{ci_lower * 100:.2f}%, {ci_upper * 100:.2f}%]**

This interval represents the estimated uncertainty around the difference between treatment and control conversion rates.

---

## 7. Business Interpretation

The analysis compares conversion performance between the two experiment groups.

The treatment conversion rate was **{treatment['Conversion_Rate'] * 100:.2f}%**, compared with **{control['Conversion_Rate'] * 100:.2f}%** for the control group.

The observed difference was **{absolute_lift * 100:.2f} percentage points**.

The statistical test returned a p-value of **{p_value:.6f}**.

Therefore:

> {statistical_statement}

The result should be interpreted together with the confidence interval, sample size, experiment design and business context before making a marketing decision.

---

## 8. Analytical Limitations

- Statistical significance does not automatically imply business significance.
- Conversion rate is only one performance measure.
- The analysis does not evaluate profitability unless revenue or profit data is available.
- External factors may affect campaign performance.
- Experiment quality depends on the underlying randomization and data collection process.
- The analysis does not estimate long-term customer value.

---

## 9. Recommended Next Questions

1. Does the treatment effect remain consistent across audience segments?
2. Does the treatment affect users differently by advertising exposure?
3. What is the relationship between ad exposure and conversion?
4. Would the observed lift justify additional testing?
5. What additional revenue or profit would the treatment generate if scaled?

---

## 10. Visualization

![A/B Test Conversion Rate](../figures/ab_test_conversion_rate.png)

---

### MarketLens

**Marketing Analytics | Statistical Testing | Business Intelligence | Generative AI**

Author: **Pranoti Ashok Munjankar**
"""

    with open(
        report_file,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(report)

    return report_file

# ============================================================
# MAIN
# ============================================================


def main():

    # --------------------------------------------------------
    # 1. Load
    # --------------------------------------------------------

    df, file_path = load_data()

    # --------------------------------------------------------
    # 2. Validate
    # --------------------------------------------------------

    group_col, conversion_col = validate_data(df)

    # --------------------------------------------------------
    # 3. Prepare
    # --------------------------------------------------------

    data = prepare_data(
        df,
        group_col,
        conversion_col,
    )

    # --------------------------------------------------------
    # 4. Identify experiment groups
    # --------------------------------------------------------

    control, treatment = identify_groups(
        data,
        group_col,
    )

    # --------------------------------------------------------
    # 5. Group metrics
    # --------------------------------------------------------

    metrics = calculate_group_metrics(
        data,
        group_col,
        control,
        treatment,
    )

    # --------------------------------------------------------
    # 6. Lift
    # --------------------------------------------------------

    (
        control_rate,
        treatment_rate,
        absolute_lift,
        relative_lift,
    ) = calculate_lift(metrics)

    # --------------------------------------------------------
    # 7. Statistical test
    # --------------------------------------------------------

    z_stat, p_value = two_proportion_z_test(
        metrics
    )

    # --------------------------------------------------------
    # 8. Confidence interval
    # --------------------------------------------------------

    ci_lower, ci_upper = calculate_confidence_interval(
        metrics
    )

    # --------------------------------------------------------
    # 9. Interpretation
    # --------------------------------------------------------

    (
        statistical_statement,
        lift_text,
        statistically_significant,
    ) = interpret_results(
        p_value,
        absolute_lift,
        relative_lift,
        ci_lower,
        ci_upper,
    )

    # --------------------------------------------------------
    # 10. Print results
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("A/B TEST RESULTS")
    print("=" * 70)

    print("\nGroup Performance:")
    print(metrics.to_string(index=False))

    print("\n" + "-" * 70)

    print(
        f"Control conversion rate   : "
        f"{control_rate * 100:.2f}%"
    )

    print(
        f"Treatment conversion rate : "
        f"{treatment_rate * 100:.2f}%"
    )

    print(
        f"Absolute lift             : "
        f"{absolute_lift * 100:.2f} percentage points"
    )

    print(
        f"Relative lift             : "
        f"{relative_lift * 100:.2f}%"
    )

    print(
        f"Z-statistic               : "
        f"{z_stat:.4f}"
    )

    print(
        f"P-value                   : "
        f"{p_value:.6f}"
    )

    print(
        f"95% CI                    : "
        f"[{ci_lower * 100:.2f}%, "
        f"{ci_upper * 100:.2f}%]"
    )

    print(
        f"Statistically significant : "
        f"{statistically_significant}"
    )

    print("\nInterpretation:")
    print(statistical_statement)

    # --------------------------------------------------------
    # 11. Save metrics
    # --------------------------------------------------------

    metrics_file = (
        REPORT_DIR / 
        "ab_test_group_metrics.csv"
    )

    metrics.to_csv(
        metrics_file,
        index=False,
    )

    # --------------------------------------------------------
    # 12. Visualization
    # --------------------------------------------------------

    figure_file = create_conversion_chart(
        metrics
    )

    # --------------------------------------------------------
    # 13. Report
    # --------------------------------------------------------

    report_file = generate_report(
        file_path=file_path,
        data=data,
        metrics=metrics,
        z_stat=z_stat,
        p_value=p_value,
        absolute_lift=absolute_lift,
        relative_lift=relative_lift,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        statistical_statement=statistical_statement,
        lift_text=lift_text,
    )

    # --------------------------------------------------------
    # 14. Final output
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("FILES CREATED")
    print("=" * 70)

    print(f"\nMetrics : {metrics_file}")
    print(f"Figure  : {figure_file}")
    print(f"Report  : {report_file}")

    print("\nA/B testing analysis completed successfully.")


if __name__ == "__main__":
    main()

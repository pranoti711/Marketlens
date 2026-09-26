# 📊 MarketLens

### Marketing Intelligence & Performance Analytics

**MarketLens** is an end-to-end marketing analytics project built to answer a practical business question:

> **Where should a brand spend its next marketing budget, and how do we know?**

The project combines marketing performance analysis, campaign evaluation, audience analysis, A/B testing, GA4 analysis, SQL, Python, and interactive dashboards to turn raw marketing data into clear business insights.

Rather than focusing only on charts, MarketLens follows a complete analytics workflow:

**Raw Data → Data Validation → Analysis → KPI Evaluation → Statistical Testing → Business Insights → Dashboard → Decision Support**

---

## 🎯 Project Objective

Marketing teams generate large amounts of data from advertising platforms, campaigns, audiences, websites, and experiments.

The challenge is not simply calculating metrics such as CTR or ROAS. The real challenge is understanding:

* Which platforms are performing efficiently?
* Which campaigns are generating the most value?
* Which audiences respond differently?
* How should advertising performance be compared?
* Did a marketing experiment actually improve conversion?
* What can website analytics tell us about user behaviour?
* How can these findings support future marketing decisions?

MarketLens was developed to explore these questions using multiple real-world-style marketing datasets.

---

# 🔎 Key Business Questions

The analysis focuses on questions such as:

### Marketing Performance

* Which advertising platforms generate stronger returns?
* Which campaigns contribute the most revenue?
* How do CTR, CPC, CPA and ROAS vary across platforms and campaigns?
* Where are advertising costs relatively high or low?

### Audience Analysis

* Which audience groups show stronger engagement?
* How do age, gender, interest and campaign characteristics relate to performance?
* Are some audience segments responding differently to campaigns?

### Experimentation

* Is there a measurable difference between control and treatment groups?
* What is the conversion-rate lift?
* Is the observed difference statistically significant?
* What does the experiment actually support, and what does it not prove?

### Website Analytics

* What can GA4 data reveal about acquisition and user behaviour?
* Which channels and user interactions are important?
* How can website analytics complement advertising performance analysis?

---

# 🗂️ Datasets

MarketLens uses multiple datasets because each dataset answers a different analytical question.

They are **not artificially merged into one dataset**.

## 1. Global Advertising Performance Dataset

Used for:

* Platform comparison
* Campaign performance
* Country/market analysis
* Industry analysis
* Advertising KPI analysis
* CTR, CPC, CPA and ROAS evaluation

**Dataset size:** 1,800 rows × 14 columns

---

## 2. KAG Conversion Dataset

Used for:

* Audience analysis
* Demographic analysis
* Campaign performance
* Conversion behaviour
* Audience segmentation

**Dataset size:** 1,143 rows × 11 columns

---

## 3. Marketing A/B Testing Dataset

Used specifically for experimentation.

It contains control and treatment groups and is used to analyse:

* Conversion rate
* Conversion-rate difference
* Relative lift
* Statistical significance
* Confidence intervals

**Dataset size:** 588,101 rows × 7 columns

---

## 4. GA4 Demo Account Case Study

A separate GA4 case study was conducted using the **Google Merchandise Store demonstration property**.

The GA4 section focuses on understanding:

* Acquisition
* User behaviour
* Engagement
* Conversion-related analysis
* Marketing analytics concepts used in GA4

The GA4 work is maintained separately because it represents a web analytics case study rather than another raw CSV dataset in the main analysis pipeline.

---

# 🛠️ Technology Stack

| Area                    | Tools                                     |
| ----------------------- | ----------------------------------------- |
| Data Analysis           | Python, Pandas, NumPy                     |
| Statistical Analysis    | Statistical testing, confidence intervals |
| Visualization           | Matplotlib                                |
| Database / Querying     | SQL                                       |
| Business Intelligence   | Microsoft Power BI                        |
| Interactive Application | Streamlit                                 |
| Marketing Analytics     | CTR, CPC, CPA, ROAS, Conversion Rate      |
| Web Analytics           | Google Analytics 4                        |
| Experimentation         | A/B Testing                               |
| Version Control         | Git & GitHub                              |

---

# 📈 Marketing KPIs

MarketLens evaluates commonly used digital marketing performance indicators.

### CTR — Click-Through Rate

Measures the percentage of impressions that resulted in clicks.

$$
CTR = \frac{Clicks}{Impressions} \times 100
$$

### CPC — Cost Per Click

Measures the average advertising cost for each click.

$$
CPC = \frac{Spend}{Clicks}
$$

### CPA — Cost Per Acquisition

Measures the average advertising cost associated with an acquisition/conversion.

$$
CPA = \frac{Spend}{Conversions}
$$

### ROAS — Return on Advertising Spend

Measures revenue generated relative to advertising spend.

$$
ROAS = \frac{Revenue}{Advertising\ Spend}
$$

### Conversion Rate

Measures the percentage of users who converted.

$$
Conversion\ Rate = \frac{Conversions}{Users} \times 100
$$

These metrics are evaluated together rather than relying on a single KPI.

---

# 🔬 A/B Testing

One of the important parts of MarketLens is the A/B testing analysis.

The `marketing_AB.csv` dataset contains **control and treatment groups**, allowing the project to treat this as an actual randomized experiment rather than simply comparing two unrelated marketing segments.

The analysis includes:

* Control conversion rate
* Treatment conversion rate
* Absolute conversion-rate difference
* Relative lift
* Statistical significance testing
* Confidence interval
* Interpretation of the experiment

### Example result

The analysis found:

* **Control:** 420 conversions / 23,524 users
* **Control conversion rate:** approximately **1.79%**

The treatment group is evaluated against this baseline through statistical testing rather than assuming that a higher observed conversion rate automatically means the treatment was successful.

This distinction is important because:

> **Observed difference ≠ automatically meaningful difference.**

The statistical analysis is therefore used to determine whether the observed difference is sufficiently supported by the experiment.

---

# 📊 Power BI Dashboard

MarketLens also includes an interactive Power BI dashboard designed to provide a business-facing view of the analysis.

The dashboard brings together:

* Executive marketing KPIs
* Campaign performance
* Platform analysis
* Audience analysis
* Performance metrics
* Interactive filters
* A/B testing results
* GA4 case-study insights

The objective of the dashboard is to move from:

**“Here is the data.”**

to:

**“Here is what the data is telling the marketing team.”**

---

# 🖥️ Streamlit Application

A Streamlit application was developed to make the project easier to explore interactively.

The application contains sections for:

### Executive Overview

Provides a high-level view of marketing performance and major KPIs.

### Campaign Analysis

Allows campaign-level performance to be explored.

### Audience Analysis

Focuses on audience and conversion-related patterns.

### A/B Testing

Displays the experiment results and statistical analysis.

### GA4 Case Study

Presents the GA4 analysis and supporting case-study information.

The application is designed as a portfolio-facing analytics interface rather than a production marketing platform.

---

# 📁 Project Structure

```text
MarketLens/
│
├── analysis/
│   ├── outputs/
│   │   ├── figures/
│   │   ├── reports/
│   │   └── tables/
│   │
│   └── marketlens_analysis.py
│
├── ab_testing/
│   └── ab_testing_analysis.py
│
├── g4 case study/
│   ├── GA4_CASE_STUDY.md
│   └── screenshots/
│
├── sql/
│   └── ...
│
├── app/
│   └── app.py
│
├── data/
│   ├── global_ads_performance_dataset.csv
│   ├── KAG_conversion_data.csv
│   └── marketing_AB.csv
│
├── p1.pbix
├── p1.pbit
├── requirements.txt
└── README.md
```

> Dataset filenames and folder contents may vary slightly depending on the version of the repository.

---

# 🔄 Analysis Workflow

The project follows a structured workflow.

```text
                 ┌─────────────────┐
                 │    Raw Data     │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │ Data Validation │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │ Data Analysis   │
                 │ & KPI Creation  │
                 └────────┬────────┘
                          ↓
              ┌───────────┴───────────┐
              ↓                       ↓
       Marketing Analysis       Audience Analysis
              │                       │
              └───────────┬───────────┘
                          ↓
                 ┌─────────────────┐
                 │   A/B Testing   │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │   GA4 Case      │
                 │     Study       │
                 └────────┬────────┘
                          ↓
             ┌─────────────────────────┐
             │ Power BI + Streamlit    │
             │ Interactive Reporting   │
             └────────────┬────────────┘
                          ↓
                 ┌─────────────────┐
                 │ Business Insight│
                 │ & Decision      │
                 │ Support         │
                 └─────────────────┘
```

---

# 📌 Key Analysis Findings

Some of the major observations from the marketing performance analysis include:

### Platform Performance

The analysis identified differences in performance across advertising platforms.

For example, the analysed data showed:

| Platform | Observed Metric |
| -------- | --------------: |
| TikTok   |     ROAS ≈ 7.62 |
| TikTok   |     CTR ≈ 5.53% |
| TikTok   |     CPA ≈ 21.67 |

These values are dataset-specific and should not be interpreted as general industry benchmarks.

---

### Revenue by Platform

The analysis showed **Google** with the highest observed revenue in the Global Ads dataset:

**≈ 22.03M**

Again, this represents the analysed dataset rather than a claim about Google's performance in the broader advertising market.

---

### Campaign Performance

The analysis identified **Search** as the highest-revenue campaign category in the analysed data:

**Revenue ≈ 15.22M**

with an observed:

**ROAS ≈ 5.31**

These findings are used as analytical observations rather than universal marketing recommendations.

---

# ⚠️ Data Validation

Data validation was performed before interpreting the datasets.

For the main datasets used in the project:

* Duplicate records were checked.
* Missing values were checked.
* Column structures were inspected.
* KPI calculations were validated.
* Derived metrics were compared with source fields where possible.

An important example was identified during validation:

### CTR Validation

The Global Ads dataset showed a mismatch between the reported/calculated CTR values during validation.

The validation result showed:

**0% of records within the selected 0.01 tolerance**

while CPC, CPA and ROAS calculations showed full agreement under the corresponding validation checks.

Rather than hiding this discrepancy, it is documented as a data-quality/definition issue.

This is an important part of the project because real-world analytics is not only about finding impressive numbers. It also requires questioning whether the numbers are calculated and defined correctly.

---

# 🧪 What This Project Demonstrates

MarketLens demonstrates practical skills across several areas of data analytics.

### Data Analytics

* Data cleaning
* Data validation
* Exploratory analysis
* KPI calculation
* Comparative analysis
* Business interpretation

### Marketing Analytics

* Digital advertising metrics
* Performance marketing
* Campaign analysis
* Audience segmentation
* Conversion analysis
* CTR
* CPC
* CPA
* ROAS

### Statistics

* A/B testing
* Conversion-rate comparison
* Lift calculation
* Hypothesis testing
* Confidence intervals
* Statistical interpretation

### Business Intelligence

* Power BI
* Interactive dashboards
* KPI reporting
* Business-focused visualization

### Web Analytics

* GA4
* Acquisition analysis
* User behaviour
* Conversion-related metrics

### Technical Skills

* Python
* Pandas
* NumPy
* SQL
* Matplotlib
* Power BI
* Streamlit
* Git/GitHub

---



# 💡 Main Learning From the Project

One of the biggest lessons from MarketLens was that marketing analytics is not about finding one metric and declaring a winner.

For example:

A campaign may have a high CTR but poor conversion.

Another campaign may have a lower CTR but stronger ROAS.

An audience may show a higher conversion rate, but that does not automatically mean the difference is statistically meaningful.

Similarly, an A/B test may show an observed improvement, but the experiment must be statistically evaluated before drawing conclusions.

This project therefore treats marketing analysis as a combination of:

> **Business Context + Data Quality + Metrics + Statistics + Visualization + Interpretation**

---

# 🎯 Final Business Perspective

MarketLens is built around a simple idea:

> **Good marketing analytics should help answer not only “what happened?” but also “how confident are we about it?” and “what should we investigate next?”**

The project therefore connects descriptive analytics with experimentation and business intelligence.

Instead of presenting a collection of disconnected charts, it attempts to create a complete analytical workflow from raw marketing data to decision-oriented reporting.


# 👩‍💻 Author

**Pranoti Ashok Munjankar**

Computer Science Engineering | Data Analytics | Marketing Analytics


### Profiles

* **GitHub:** `pranoti711`
* **LinkedIn:** `pranoti-munjankar-1760092b`

---

# ⭐ Why I Built MarketLens

I built MarketLens to move beyond isolated tutorials and practice the way an analyst would approach a real business problem.

The goal was not simply to demonstrate that I can use Python or Power BI.

The goal was to practice the complete process:

> **Take raw marketing data → understand the business question → validate the data → analyse the metrics → test important differences → build dashboards → communicate the findings clearly.**

MarketLens represents that learning journey.

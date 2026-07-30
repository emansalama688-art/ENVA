
import streamlit as st
import pandas as pd
import json
from pathlib import Path

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------

st.set_page_config(
    page_title="ENVA",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

ROOT = Path(__file__).parent
DATA = ROOT / "data"

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------

with open(DATA / "ENVA_Final_Report.json", encoding="utf-8") as f:
    REPORT = json.load(f)

SUMMARY = pd.read_csv(DATA / "ENVA_Final_Summary.csv")

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

st.title("🌍 ENVA")

st.subheader(
"المنظومة الوطنية الذكية للرصد البيئي وتحليل صور الأقمار الصناعية ودعم اتخاذ القرار"
)

st.divider()

col1, col2, col3 = st.columns(3)

col1.metric("Study Area", REPORT["study_area"])
col2.metric("Current Year", REPORT["current_year"])
col3.metric("Land Cover Classes", len(SUMMARY))

st.divider()

st.success("ENVA Dashboard Ready")


# ============================================================
# LAND COVER CHARTS
# ============================================================

st.subheader("📊 Land Cover Statistics")

try:

    chart_df = SUMMARY.copy()

    numeric_cols = chart_df.select_dtypes(include="number").columns

    if len(numeric_cols) > 0:

        st.bar_chart(
            chart_df[numeric_cols]
        )

        st.line_chart(
            chart_df[numeric_cols]
        )

        st.area_chart(
            chart_df[numeric_cols]
        )

    else:

        st.info("No numeric columns available for visualization.")

except Exception as e:

    st.error(e)

st.divider()



# ============================================================
# PROJECT SUMMARY
# ============================================================

st.subheader("📋 ENVA Project Summary")

st.markdown(f"""
### Study Area

**{REPORT["study_area"]}**

---

### Current Year

**{REPORT["current_year"]}**

---

### Overall Accuracy

**{REPORT["overall_accuracy"]}%**

---

### Number of Land Cover Classes

**{len(SUMMARY)}**
""")

st.divider()

# ============================================================
# DOWNLOAD REPORT
# ============================================================

REPORT_PATH = DATA / "ENVA_Final_Report.json"

if REPORT_PATH.exists():

    with open(REPORT_PATH, "rb") as file:

        st.download_button(

            label="📥 Download Final Report",

            data=file,

            file_name="ENVA_Final_Report.json",

            mime="application/json"

        )


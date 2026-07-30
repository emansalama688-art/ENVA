
import streamlit as st
import pandas as pd
import json
from pathlib import Path

# ------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------

st.set_page_config(

    page_title="ENVA",

    page_icon="🌍",

    layout="wide",

    initial_sidebar_state="expanded"

)

# ------------------------------------------------------------
# Theme
# ------------------------------------------------------------

st.markdown("""

<style>

html,
body,
[class*="css"] {

    font-family: Arial;

}

.main {

    background:#F4F8FB;

}

.block-container{

    padding-top:1rem;

}

.title{

    font-size:46px;

    font-weight:800;

    color:#0B6E4F;

}

.subtitle{

    font-size:20px;

    color:#4F4F4F;

}

.metric{

    background:white;

    border-radius:18px;

    padding:20px;

    box-shadow:0 3px 10px rgba(0,0,0,.10);

}

footer{

    visibility:hidden;

}

header{

    visibility:hidden;

}

</style>

""",unsafe_allow_html=True)

# ------------------------------------------------------------
# Read Files
# ------------------------------------------------------------

ROOT = Path(__file__).parent

DATA = ROOT / "data"

with open(

    DATA / "ENVA_Final_Report.json",

    encoding="utf-8"

) as f:

    report = json.load(f)

summary = pd.read_csv(

    DATA / "ENVA_Final_Summary.csv"

)

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------

st.sidebar.image(

    "https://img.icons8.com/color/96/earth-planet.png",

    width=70

)

st.sidebar.title("ENVA")

st.sidebar.markdown("---")

st.sidebar.success(

    report["project"]

)

st.sidebar.info(

    report["study_area"]

)

st.sidebar.markdown("---")

st.sidebar.write(

    "Current Year"

)

st.sidebar.metric(

    "",

    report["current_year"]

)

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

st.markdown(

    '<div class="title">🌍 ENVA</div>',

    unsafe_allow_html=True

)

st.markdown(

    '<div class="subtitle">'
    'المنظومة الوطنية الذكية للرصد البيئي وتحليل صور الأقمار الصناعية ودعم اتخاذ القرار'
    '</div>',

    unsafe_allow_html=True

)

st.markdown("---")

# ------------------------------------------------------------
# KPI Cards
# ------------------------------------------------------------

c1,c2,c3,c4 = st.columns(4)

with c1:

    st.metric(

        "Study Area",

        report["study_area"]

    )

with c2:

    st.metric(

        "Current Year",

        report["current_year"]

    )

with c3:

    st.metric(

        "Land Cover",

        len(summary)

    )

with c4:

    st.metric(

        "Project",

        "ENVA"

    )

st.markdown("---")

# ------------------------------------------------------------
# Statistics
# ------------------------------------------------------------

st.subheader("Land Cover Statistics")

st.dataframe(

    summary,

    use_container_width=True

)

st.markdown("---")

st.success("ENVA Dashboard Ready")


import streamlit as st

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------

st.set_page_config(
    page_title="ENVA Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------

st.title("🌍 ENVA")

st.subheader(
    "Environmental Navigation & Visualization Assistant"
)

st.markdown(
"""
### المنظومة الوطنية الذكية للرصد البيئي وتحليل صور الأقمار الصناعية ودعم اتخاذ القرار
"""
)

st.markdown("---")

st.info(
"""
مرحبًا بك في منصة ENVA.

تستخدم المنصة الذكاء الاصطناعي وصور الأقمار الصناعية لرصد البيئة،
ودعم اتخاذ القرار، وتحليل الغطاء الأرضي،
واكتشاف التغيرات البيئية،
واقتراح أفضل مناطق التشجير الذكي.
"""
)

st.markdown("---")

# ----------------------------------------------------
# KPI PLACEHOLDERS
# ----------------------------------------------------

c1, c2, c3, c4 = st.columns(4)

c1.metric("🌱 Green Cover", "--")
c2.metric("🌳 Trees", "--")
c3.metric("🌍 CO₂", "--")
c4.metric("📍 Study Area", "--")

st.markdown("---")

st.success("✅ ENVA Dashboard Ready")

import streamlit as st
import streamlit as st
import pandas as pd
import json
from pathlib import Path

st.set_page_config(
    page_title="ENVA | Smart Afforestation",
    page_icon="🌳",
    layout="wide"
)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

try:
    with open(DATA / "ENVA_Afforestation_Report.json", encoding="utf-8") as f:
        AFF_REPORT = json.load(f)

    AFF_SUMMARY = pd.read_csv(
        DATA / "ENVA_Afforestation_Summary.csv"
    )

    st.success("✅ Smart Afforestation data loaded successfully")

except Exception as e:
    st.error(f"❌ Error loading files:\n\n{e}")
    st.stop()

st.title("🌳 Smart Afforestation")

st.subheader("التشجير الذكي")

st.markdown("---")

st.write("### AI Summary")

st.json(AFF_REPORT["AI_Summary"])

st.markdown("---")

st.write("### Afforestation Summary")

st.dataframe(
    AFF_SUMMARY,
    use_container_width=True
)

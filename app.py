import json
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

# ======================================================
# PAGE CONFIG
# ======================================================

st.set_page_config(
    page_title="ENVA — Environmental Intelligence Platform",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# LOAD CORE DATA (land cover report + summary)
# ======================================================

DATA_PATH = Path("data")

try:
    with open(
        DATA_PATH / "ENVA_Final_Report.json",
        encoding="utf-8"
    ) as f:
        REPORT = json.load(f)

    SUMMARY = pd.read_csv(
        DATA_PATH / "ENVA_Final_Summary.csv"
    )

except Exception as e:
    st.error(
        f"❌ Error loading ENVA data files\n\n{e}"
    )
    st.stop()

# ======================================================
# ENVIRONMENTAL INDICATORS — SHARED CONFIGURATION & LOADING
# (flexible multi-path lookup — ready to receive the Cell 1-25
#  exports from Google Drive regardless of exact folder layout
#  used when they are copied into the repo's data/ directory)
# ======================================================

INDICATOR_ORDER = ["EHRI", "EGLI", "EDRI", "ETHI", "ECSI", "EUDI", "EEPI"]

INDICATOR_INFO = {
    "EHRI": {
        "icon": "🔥", "title": "Environmental Heat Risk",
        "arabic": "مؤشر مخاطر الحرارة البيئية",
        "what": "قياس مكاني نسبي لمستوى الإجهاد/الخطر الحراري داخل منطقة الدراسة اعتمادًا على بيانات الاستشعار عن بعد.",
        "read": "القيمة مؤشر نسبي داخل نموذج ENVA، وليست درجة حرارة مئوية ولا احتمالًا إحصائيًا للخطر.",
        "map_meaning": "المناطق ذات القيم الأعلى تمثل بؤرًا حرارية نسبية تستحق أولوية أعلى في الفحص والتدخل.",
        "city_meaning": "هذه البؤر هي المرشح الأول لبرامج التظليل والتشجير الحضري وتحسين الأسطح والمواد العاكسة.",
        "recommendations": [
            "زيادة التشجير الحضري في البؤر الساخنة.",
            "تحسين الظل وتقييم الأسطح العمرانية عالية الامتصاص الحراري.",
            "إعطاء الأولوية للمناطق ذات الحرارة النسبية المرتفعة عند تخطيط التدخلات.",
        ],
        "class_key": "risk_classes", "score_key": "score_mean", "scale_label": "0 – 100",
    },
    "EGLI": {
        "icon": "🌿", "title": "Environmental Green Loss",
        "arabic": "مؤشر الفقد الأخضر والغطاء النباتي",
        "what": "مؤشر للتغير النسبي في الإشارة المرتبطة بالغطاء النباتي بين فترتين زمنيتين.",
        "read": "القيمة لا تعني عدد أشجار مفقودة بشكل مباشر؛ يجب تفسيرها مع فترة المقارنة والسياق الزراعي والموسمي.",
        "map_meaning": "المناطق ذات اللون الأحمر تمثل تراجعًا نسبيًا في الغطاء الأخضر، بينما الأخضر يمثل تحسنًا.",
        "city_meaning": "هذه هي المناطق المرشحة لحماية الغطاء النباتي القائم واستعادته قبل تفاقم الفقد.",
        "recommendations": [
            "فحص البؤر ذات التغير النباتي المرتفع ميدانيًا قبل اعتماد أي إجراء.",
            "حماية المناطق الخضراء ذات القيمة البيئية أو الزراعية.",
            "استمرار المراقبة الزمنية لاكتشاف الاتجاهات المستمرة بدل الحكم من لقطة واحدة.",
        ],
        "class_key": "change_classes", "score_key": "mean_ndvi_change", "scale_label": "NDVI Δ (-1..1)",
    },
    "EDRI": {
        "icon": "💧", "title": "Environmental Drought Risk",
        "arabic": "مؤشر مخاطر الجفاف البيئي",
        "what": "مؤشر مكاني نسبي يحدد مناطق الضغط المرتبط بالجفاف وفق مكونات نموذج ENVA.",
        "read": "القيم الأعلى تعني أولوية جفاف نسبية أعلى داخل منطقة الدراسة، وليست قياسًا مباشرًا لمحتوى رطوبة التربة.",
        "map_meaning": "المناطق الأعلى قيمة هي مناطق الضغط المائي النسبي الأكثر احتياجًا للمتابعة.",
        "city_meaning": "توجيه المتابعة المائية والزراعية نحو هذه المناطق يقلل من مخاطر تدهور الأراضي الزراعية.",
        "recommendations": [
            "توجيه المتابعة المائية إلى البؤر ذات القيم الأعلى.",
            "مراجعة كفاءة الري وإدارة الموارد المائية في المناطق المتأثرة.",
            "دمج المؤشر مع بيانات رطوبة التربة والقياسات الحقلية عند التخطيط التنفيذي.",
        ],
        "class_key": "risk_classes", "score_key": "score_mean", "scale_label": "0 – 100",
    },
    "ETHI": {
        "icon": "🌳", "title": "Environmental Vegetation Health",
        "arabic": "مؤشر صحة الغطاء النباتي/الشجري",
        "what": "مؤشر نسبي لحالة الغطاء النباتي أو حالته البيئية كما تم تعريفها في منهجية ENVA.",
        "read": "القيم الأعلى تعكس حالة أفضل وفق اتجاه المؤشر؛ لا تمثل تشخيصًا صحيًا ميدانيًا لشجرة بعينها.",
        "map_meaning": "المناطق ذات القيم المنخفضة هي الأولى بالفحص الميداني والمتابعة.",
        "city_meaning": "حماية المناطق ذات الحالة الجيدة، واستهداف المناطق المتدهورة بإجراءات استعادة مناسبة للسياق المحلي.",
        "recommendations": [
            "حماية المناطق ذات الحالة النباتية الجيدة من التدهور.",
            "استهداف المناطق منخفضة الحالة بإجراءات استعادة مناسبة للسياق المحلي.",
            "ربط النتائج بالمراقبة الميدانية قبل اعتماد تدخلات كبيرة.",
        ],
        "class_key": "health_classes", "score_key": "score_mean", "scale_label": "0 – 100",
    },
    "ECSI": {
        "icon": "🌱", "title": "Carbon Sequestration Potential",
        "arabic": "مؤشر إمكانات احتجاز الكربون",
        "what": "مؤشر نسبي لإمكانات الغطاء النباتي في المساهمة في احتجاز الكربون.",
        "read": "المؤشر ليس مخزون كربون مقاسًا ميدانيًا، وأي تحويل إلى طن CO₂ يحتاج نموذج كتلة حيوية ومعايرة محلية.",
        "map_meaning": "المناطق الأعلى قيمة تمثل إمكانات نسبية أعلى للامتصاص عبر الغطاء النباتي القائم.",
        "city_meaning": "حماية هذه المناطق يحافظ على قدرة المدينة النسبية على امتصاص الكربون؛ لا تُستخدم كرقم كربون معتمد دون نموذج محلي.",
        "recommendations": [
            "حماية الغطاء النباتي ذي الإمكانات الأعلى لاحتجاز الكربون.",
            "استخدام المناطق منخفضة الإمكانات مع أدلة التدهور كأولوية محتملة للاستعادة.",
            "عدم اعتماد أي رقم مطلق للكربون دون نموذج كتلة حيوية معتمد.",
        ],
        "class_key": "potential_classes", "score_key": "score_mean", "scale_label": "0 – 100",
    },
    "EUDI": {
        "icon": "🏙️", "title": "Urban Development Pressure",
        "arabic": "مؤشر ضغط التنمية الحضرية",
        "what": "مؤشر مكاني نسبي يوضح شدة الضغط العمراني والتجمع المكاني للمناطق المبنية.",
        "read": "القيم الأعلى تعني ضغطًا عمرانيًا نسبيًا أعلى داخل منطقة الدراسة، وليست تصنيفًا قانونيًا لاستخدامات الأراضي.",
        "map_meaning": "البؤر الأعلى قيمة هي مناطق التوسع العمراني الأكثر كثافة نسبيًا.",
        "city_meaning": "مراجعة هذه المناطق مقابل حدود الأراضي الزراعية والمناطق الحساسة بيئيًا أولوية تخطيطية.",
        "recommendations": [
            "مراقبة البؤر ذات الضغط العمراني المرتفع بصورة دورية.",
            "مراجعة التوسع العمراني مقابل حماية الأراضي الزراعية والمناطق الحساسة.",
            "استخدام بيانات GIS والجهات المختصة قبل أي قرار تنظيمي.",
        ],
        "class_key": "spatial_pressure_classes", "score_key": "eudi_summary_score", "scale_label": "0 – 100",
    },
    "EEPI": {
        "icon": "🎯", "title": "Environmental Ecological Priority",
        "arabic": "مؤشر الأولوية البيئية",
        "what": "مؤشر مركب يجمع نتائج المؤشرات البيئية الستة الأخرى لإنتاج ترتيب نسبي للأولوية في التدخل. هذا مؤشر ترتيب/أولوية مركب وليس قياسًا بيئيًا خامًا.",
        "read": "القيم الأعلى تعني أولوية بيئية مركبة أعلى وفق أوزان النموذج. الأوزان الحالية موثقة كمعلمات نموذجية وتحتاج اعتمادًا منهجيًا قبل اعتبارها نهائية.",
        "map_meaning": "المناطق ذات القيم الأعلى هي أكثر المناطق تجمعًا للمشكلات البيئية مجتمعة، لا لمشكلة واحدة بعينها.",
        "city_meaning": "تُستخدم هذه المناطق كنقطة بداية لترتيب التدخلات والموارد، مع مراجعة المكونات الستة قبل اتخاذ القرار.",
        "recommendations": [
            "استخدام المناطق الأعلى أولوية كنقطة بداية للفحص المتكامل.",
            "مراجعة المكونات الستة للمؤشر قبل تحديد نوع التدخل.",
            "عدم تحويل EEPI وحده إلى قرار تنفيذي أو تمويلي دون مراجعة الخبراء والأدلة الميدانية.",
        ],
        "class_key": None, "score_key": "eepi_summary_score", "scale_label": "0 – 100",
    },
}


MAP_ROOT_CANDIDATES = [
    # GitHub layout: official HTML indicator maps directly inside data/
    DATA_PATH,

    # Existing/local project structures — preserved for compatibility
    DATA_PATH / "app_data" / "indicator_maps",
    Path("app_data") / "indicator_maps",
    DATA_PATH / "maps" / "report_maps",
    DATA_PATH / "report_maps",
    DATA_PATH / "maps",
    Path("maps") / "report_maps",
]

APP_ROOT_CANDIDATES = [
    DATA_PATH / "indicators",
    DATA_PATH / "app_data",
    DATA_PATH,
    Path("app_data"),
]

METADATA_PATH_CANDIDATES = [
    DATA_PATH / "metadata",
    DATA_PATH / "indicators" / "metadata",
]


def first_existing(paths):
    for candidate in paths:
        if candidate.exists():
            return candidate
    return None


def load_json_file(path):
    try:
        with open(path, encoding="utf-8") as file_handle:
            return json.load(file_handle)
    except Exception:
        return {}


def score_text(value, indicator_name=None):
    if value is None:
        return "N/A"
    try:
        suffix = " / 100" if indicator_name not in (None, "EGLI") else ""
        return f"{float(value):.2f}{suffix}"
    except Exception:
        return str(value)


def load_indicator_app_data(name):
    candidates = [root / f"{name.lower()}_current.json" for root in APP_ROOT_CANDIDATES]
    path = first_existing(candidates)
    if path is None:
        return {}, None
    return load_json_file(path), path


def find_map_file(name):
    candidates = []

    # Preserve the original official HTML maps exactly as packaged.
    # Support both existing filename conventions:
    #   EHRI_map.html / ehri_map.html
    # The GitHub data/ layout uses lowercase filenames.
    filename_variants = [
        f"{name.lower()}_map.html",
        f"{name}_map.html",
    ]

    # Prefer the original official HTML map.
    for root in MAP_ROOT_CANDIDATES:
        for filename in filename_variants:
            candidates.append(root / filename)

    # PNG remains a fallback only when the official HTML asset is unavailable.
    png_variants = [
        f"{name.lower()}_map.png",
        f"{name}_map.png",
    ]
    for root in MAP_ROOT_CANDIDATES:
        for filename in png_variants:
            candidates.append(root / filename)

    return first_existing(candidates)


def load_indicator_metadata(name):
    cell_number = 11 + INDICATOR_ORDER.index(name)
    candidates = []
    for root in METADATA_PATH_CANDIDATES:
        candidates.append(root / f"cell_{cell_number}_{name.lower()}_metadata.json")
    path = first_existing(candidates)
    if path is None:
        return {}, None
    return load_json_file(path), path


def load_all_indicators():
    items = {}
    for name in INDICATOR_ORDER:
        app_data, app_path = load_indicator_app_data(name)
        metadata, metadata_path = load_indicator_metadata(name)
        items[name] = {
            "name": name,
            "data": app_data,
            "app_path": app_path,
            "map_path": find_map_file(name),
            "metadata": metadata,
            "metadata_path": metadata_path,
            "score": app_data.get(INDICATOR_INFO[name]["score_key"]),
        }
    return items


INDICATORS = load_all_indicators()
INDICATORS_AVAILABLE = any(item["data"] for item in INDICATORS.values())
INDICATORS_COMPLETE = all(item["data"] for item in INDICATORS.values())

_latest_run_path = first_existing(
    [root / "latest_verified_run.json" for root in APP_ROOT_CANDIDATES]
)
LATEST_RUN = load_json_file(_latest_run_path) if _latest_run_path else {}


# ======================================================
# CUSTOM STYLE — PROFESSIONAL THEME
# ======================================================

st.markdown(
    """
    <style>

    .main { background-color: #f4f7f6; }

    h1, h2, h3 {
        color: #145A32;
        font-family: 'Segoe UI', 'Trebuchet MS', sans-serif;
    }

    p, li, span, label {
        font-family: 'Segoe UI', 'Trebuchet MS', sans-serif;
    }

    div[data-testid="metric-container"] {
        background: white;
        padding: 16px;
        border-radius: 14px;
        border: 1px solid #e2e6ea;
        box-shadow: 0px 3px 10px rgba(20, 90, 50, 0.08);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d3d24 0%, #145A32 55%, #1b7a43 100%);
    }

    section[data-testid="stSidebar"] * { color: #f4f7f6 !important; }

    section[data-testid="stSidebar"] .stRadio > label { font-weight: 600; }

    div.stButton > button {
        border-radius: 10px;
        border: 1px solid #145A32;
        color: #145A32;
        font-weight: 600;
    }

    div.stButton > button:hover {
        background-color: #145A32;
        color: white;
        border: 1px solid #145A32;
    }

    div[data-testid="stDownloadButton"] > button {
        border-radius: 10px;
        background-color: #145A32;
        color: white;
        font-weight: 700;
        border: none;
    }

    div[data-testid="stDownloadButton"] > button:hover { background-color: #1b7a43; }

    .indicator-card {
        background: white;
        border-radius: 16px;
        padding: 16px 8px;
        text-align: center;
        border: 2px solid #e2e6ea;
        box-shadow: 0px 3px 10px rgba(20, 90, 50, 0.08);
    }

    .indicator-card.selected {
        border: 2px solid #145A32;
        background: #eafaf1;
        box-shadow: 0px 4px 14px rgba(20, 90, 50, 0.18);
    }

    .indicator-icon { font-size: 32px; }
    .indicator-code { font-weight: 800; color: #145A32; font-size: 15px; margin-top: 4px; }
    .indicator-score { font-size: 13px; color: #555; }

    .platform-header { display: flex; align-items: center; gap: 16px; padding: 10px 0 20px 0; }

    .badge-validated {
        background: #eafaf1; color: #145A32; border: 1px solid #145A32;
        padding: 3px 10px; border-radius: 20px; font-weight: 700; font-size: 13px;
    }

    .badge-review {
        background: #fef5e7; color: #b9770e; border: 1px solid #b9770e;
        padding: 3px 10px; border-radius: 20px; font-weight: 700; font-size: 13px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ======================================================
# PLATFORM LOGO — MERGED BRAIN + TREE + SATELLITE MARK
# (pure inline SVG — replaces the generic earth-planet icon,
#  no external image asset or internet connection required)
# ======================================================

def enva_logo_svg(size=110):
    """ENVA emblem: a glowing AI half-brain (left) merging into a tree
    (center), with a satellite orbiting above — intelligence, nature and
    space-based monitoring in one mark."""
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="bgGrad" cx="38%" cy="32%" r="78%">
          <stop offset="0%" stop-color="#12492f"/>
          <stop offset="100%" stop-color="#082516"/>
        </radialGradient>
        <radialGradient id="brainGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#aef3ff" stop-opacity="0.95"/>
          <stop offset="45%" stop-color="#4fd3e8" stop-opacity="0.55"/>
          <stop offset="100%" stop-color="#4fd3e8" stop-opacity="0"/>
        </radialGradient>
        <linearGradient id="brainFill" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#2f7d9c"/>
          <stop offset="100%" stop-color="#1c5470"/>
        </linearGradient>
      </defs>

      <!-- Badge background -->
      <circle cx="60" cy="62" r="56" fill="url(#bgGrad)" stroke="#eafaf1" stroke-width="2"/>

      <!-- Orbit ring -->
      <ellipse cx="60" cy="34" rx="46" ry="14" fill="none"
               stroke="#f1c40f" stroke-width="1.3" stroke-dasharray="3,4"
               transform="rotate(-8 60 34)"/>

      <!-- Satellite -->
      <g transform="translate(97,26) rotate(35)">
        <rect x="-6" y="-4" width="12" height="8" rx="1.5" fill="#f4f7f6" stroke="#082516" stroke-width="1"/>
        <rect x="-17" y="-2" width="9" height="4" fill="#2874a6" stroke="#082516" stroke-width="0.8"/>
        <rect x="8" y="-2" width="9" height="4" fill="#2874a6" stroke="#082516" stroke-width="0.8"/>
        <line x1="0" y1="-4" x2="0" y2="-9" stroke="#082516" stroke-width="1"/>
        <circle cx="0" cy="-10" r="1.4" fill="#f1c40f"/>
      </g>
      <path d="M90,34 C82,40 74,46 68,50" fill="none" stroke="#f1c40f"
            stroke-width="1.2" stroke-dasharray="2,3" stroke-linecap="round"/>

      <!-- LEFT HALF: glowing AI brain hemisphere -->
      <clipPath id="brainClip">
        <path d="M60,42
                 C46,40 33,50 33,64
                 C33,78 44,90 60,90 Z"/>
      </clipPath>
      <g clip-path="url(#brainClip)">
        <path d="M60,42
                 C46,40 33,50 33,64
                 C33,78 44,90 60,90 Z"
              fill="url(#brainFill)"/>
        <circle cx="48" cy="63" r="20" fill="url(#brainGlow)"/>
        <path d="M40,54 C45,50 49,55 46,59 C43,63 48,66 51,62"
              fill="none" stroke="#eafaf1" stroke-width="1.5" stroke-linecap="round" opacity="0.9"/>
        <path d="M38,68 C43,65 47,70 44,74 C41,78 47,80 50,76"
              fill="none" stroke="#eafaf1" stroke-width="1.5" stroke-linecap="round" opacity="0.9"/>
        <path d="M44,46 C48,44 52,48 49,52"
              fill="none" stroke="#eafaf1" stroke-width="1.3" stroke-linecap="round" opacity="0.7"/>
      </g>
      <path d="M60,42 C46,40 33,50 33,64 C33,78 44,90 60,90"
            fill="none" stroke="#eafaf1" stroke-width="1.4"/>

      <!-- Spark of light — the AI "idea" glow -->
      <circle cx="47" cy="58" r="3.4" fill="#ffffff"/>
      <circle cx="47" cy="58" r="7" fill="#aef3ff" opacity="0.45"/>
      <path d="M47,49 L47,52 M38,58 L41,58 M41.5,49.5 L43.5,51.5 M41.5,66.5 L43.5,64.5"
            stroke="#eafaf1" stroke-width="1.3" stroke-linecap="round" opacity="0.85"/>

      <!-- CENTER-RIGHT: tree, bridging the brain and the rest of the mark -->
      <path d="M59,96 L59,74 Q61,70 63,74 L63,96 Z" fill="#7a5230"/>
      <path d="M61,40
               C50,39 41,48 43,58
               C36,61 36,72 45,76
               C44,84 52,90 60,88
               C63,92 68,92 71,88
               C80,90 88,84 85,76
               C93,72 92,61 84,58
               C86,48 72,39 61,40 Z"
            fill="#2ecc71" stroke="#eafaf1" stroke-width="1.3"/>
      <path d="M66,64 C70,61 75,64 73,69 C71,73 77,75 76,80"
            fill="none" stroke="#0d3d24" stroke-width="1.5" stroke-linecap="round" opacity="0.75"/>
    </svg>
    """


def enva_cover_banner_svg():
    """Wide cover banner for the Home page — satellite + AI/brain-tree +
    city skyline, expressing ENVA's identity: satellite monitoring feeding
    an AI-driven environmental brain that protects green cover over a city."""
    return """
    <svg width="100%" height="230" viewBox="0 0 1000 230" xmlns="http://www.w3.org/2000/svg"
         preserveAspectRatio="xMidYMid slice">
      <defs>
        <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0d3d24"/>
          <stop offset="100%" stop-color="#1b7a43"/>
        </linearGradient>
      </defs>
      <rect width="1000" height="230" fill="url(#skyGrad)"/>

      <!-- stars / data dots -->
      <circle cx="80" cy="40" r="1.6" fill="#eafaf1" opacity="0.6"/>
      <circle cx="160" cy="70" r="1.2" fill="#eafaf1" opacity="0.5"/>
      <circle cx="260" cy="30" r="1.4" fill="#eafaf1" opacity="0.6"/>
      <circle cx="900" cy="50" r="1.6" fill="#eafaf1" opacity="0.6"/>
      <circle cx="820" cy="90" r="1.2" fill="#eafaf1" opacity="0.5"/>

      <!-- orbit -->
      <ellipse cx="500" cy="70" rx="430" ry="46" fill="none"
               stroke="#f1c40f" stroke-width="1.2" stroke-dasharray="4,5" opacity="0.65"/>

      <!-- satellite -->
      <g transform="translate(760,40) rotate(20)">
        <rect x="-10" y="-7" width="20" height="14" rx="2" fill="#f4f7f6" stroke="#0d3d24" stroke-width="1.4"/>
        <rect x="-28" y="-3" width="15" height="7" fill="#2874a6" stroke="#0d3d24" stroke-width="1"/>
        <rect x="13" y="-3" width="15" height="7" fill="#2874a6" stroke="#0d3d24" stroke-width="1"/>
        <line x1="0" y1="-7" x2="0" y2="-16" stroke="#0d3d24" stroke-width="1.4"/>
        <circle cx="0" cy="-18" r="2.2" fill="#f1c40f"/>
      </g>
      <path d="M735,55 C650,95 560,110 500,118" fill="none" stroke="#f1c40f"
            stroke-width="1.4" stroke-dasharray="3,4" opacity="0.85"/>

      <!-- LEFT: glowing AI half-brain -->
      <defs>
        <radialGradient id="bannerGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#aef3ff" stop-opacity="0.95"/>
          <stop offset="45%" stop-color="#4fd3e8" stop-opacity="0.5"/>
          <stop offset="100%" stop-color="#4fd3e8" stop-opacity="0"/>
        </radialGradient>
        <linearGradient id="bannerBrain" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#2f7d9c"/>
          <stop offset="100%" stop-color="#1c5470"/>
        </linearGradient>
      </defs>

      <clipPath id="bannerBrainClip">
        <path d="M500,90 C462,87 432,110 432,140 C432,170 460,196 500,196 Z"/>
      </clipPath>
      <g clip-path="url(#bannerBrainClip)">
        <path d="M500,90 C462,87 432,110 432,140 C432,170 460,196 500,196 Z" fill="url(#bannerBrain)"/>
        <circle cx="472" cy="138" r="34" fill="url(#bannerGlow)"/>
        <path d="M452,116 C462,108 472,118 465,126 C458,134 468,140 475,132"
              fill="none" stroke="#eafaf1" stroke-width="2.2" stroke-linecap="round" opacity="0.9"/>
        <path d="M448,148 C458,141 468,151 460,159 C452,167 464,171 470,163"
              fill="none" stroke="#eafaf1" stroke-width="2.2" stroke-linecap="round" opacity="0.9"/>
      </g>
      <path d="M500,90 C462,87 432,110 432,140 C432,170 460,196 500,196"
            fill="none" stroke="#eafaf1" stroke-width="1.8"/>
      <circle cx="470" cy="132" r="5" fill="#ffffff"/>
      <circle cx="470" cy="132" r="11" fill="#aef3ff" opacity="0.4"/>

      <!-- RIGHT: tree, growing beside the brain -->
      <path d="M500,90
               C476,88 456,106 460,126
               C444,131 444,154 464,163
               C462,181 480,195 498,190
               C504,199 516,199 522,190
               C542,195 560,181 556,163
               C576,154 576,131 558,126
               C562,106 524,88 500,90 Z"
            fill="#2ecc71" stroke="#eafaf1" stroke-width="1.8"/>
      <path d="M512,120 C520,114 530,120 526,129 C522,136 532,140 530,148"
            fill="none" stroke="#0d3d24" stroke-width="2" stroke-linecap="round" opacity="0.8"/>

      <!-- trunk -->
      <path d="M494,205 L494,222 Q500,226 506,222 L506,205 Z" fill="#7a5230"/>

      <!-- city skyline silhouette -->
      <g fill="#0d3d24" opacity="0.85">
        <rect x="40" y="175" width="26" height="55"/>
        <rect x="72" y="155" width="22" height="75"/>
        <rect x="100" y="190" width="26" height="40"/>
        <rect x="860" y="180" width="24" height="50"/>
        <rect x="890" y="160" width="22" height="70"/>
        <rect x="918" y="195" width="26" height="35"/>
      </g>

      <text x="500" y="30" text-anchor="middle" fill="#eafaf1"
            font-family="Segoe UI, Trebuchet MS, sans-serif" font-size="15" opacity="0.9">
        Environmental Intelligence Platform
      </text>
    </svg>
    """


# ======================================================
# PDF REPORT GENERATOR (professional, English)
# ======================================================
# Generated in English for reliable PDF font rendering. Arabic
# text shaping in PDF requires reshaping libraries (arabic-reshaper
# + python-bidi) not included here, to avoid garbled Arabic glyphs
# in an official stakeholder document.

def generate_recommendations_en(indicators):
    """Rule-based, transparent recommendations — never invented."""
    recs = []

    ehri = indicators.get("EHRI", {}).get("data", {})
    if isinstance(ehri.get("score_mean"), (int, float)) and ehri["score_mean"] >= 60:
        recs.append(
            "Heat Risk (EHRI) is elevated. Prioritize shading and urban tree "
            "planting in the high-risk zones identified on the EHRI map."
        )

    egli = indicators.get("EGLI", {}).get("data", {})
    if isinstance(egli.get("mean_ndvi_change"), (int, float)) and egli["mean_ndvi_change"] > 0.05:
        recs.append(
            "Green Loss (EGLI) shows a net vegetation decline since the "
            "baseline period. Field verification of loss hotspots is recommended."
        )

    edri = indicators.get("EDRI", {}).get("data", {})
    if isinstance(edri.get("score_mean"), (int, float)) and edri["score_mean"] >= 60:
        recs.append(
            "Drought Risk (EDRI) is elevated. Coordinate with local "
            "irrigation and agricultural authorities in the affected zones."
        )

    ethi = indicators.get("ETHI", {}).get("data", {})
    if isinstance(ethi.get("score_mean"), (int, float)) and ethi["score_mean"] < 50:
        recs.append(
            "Vegetation Health (ETHI) is below the moderate threshold. "
            "Ground-truth inspection of stressed vegetation zones is advised."
        )

    eudi = indicators.get("EUDI", {}).get("data", {})
    if isinstance(eudi.get("eudi_summary_score"), (int, float)) and eudi["eudi_summary_score"] >= 60:
        recs.append(
            "Urban Development pressure (EUDI) is high. Coordinate with "
            "urban planning authorities on green-space requirements for "
            "new development in high-pressure zones."
        )

    eepi = indicators.get("EEPI", {}).get("data", {})
    priority_class = eepi.get("eepi_priority_class")
    if priority_class in ("high", "critical"):
        recs.append(
            f"Overall Ecological Priority (EEPI) is classified as "
            f"'{priority_class.upper()}'. These areas should be prioritized "
            f"in the 100 Million Trees initiative site-selection process."
        )

    if not recs:
        recs.append(
            "No indicator currently exceeds its elevated-risk threshold. "
            "Routine periodic monitoring is recommended."
        )

    return recs


def build_indicators_pdf(indicators, info, latest_run):
    """Builds a professional stakeholder PDF report. Returns bytes or None."""

    if not FPDF_AVAILABLE:
        return None

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    primary = (20, 90, 50)
    gray = (90, 90, 90)

    pdf.set_fill_color(*primary)
    pdf.rect(0, 0, 210, 34, style="F")
    pdf.set_xy(12, 8)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, "ENVA - Environmental Indicators Report", ln=1)
    pdf.set_x(12)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Kafr El Dawwar City, Beheira Governorate, Egypt", ln=1)

    pdf.set_text_color(*gray)
    pdf.ln(14)
    pdf.set_font("Helvetica", "", 10)
    generated_at = latest_run.get("generated_at", datetime.now().isoformat())
    run_status = latest_run.get("validation_status", "UNKNOWN")
    pdf.cell(0, 6, f"Generated: {str(generated_at)[:19]}", ln=1)
    pdf.cell(0, 6, f"Overall validation status: {run_status}", ln=1)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*primary)
    pdf.cell(0, 8, "Executive Summary - All Indicators", ln=1)
    pdf.ln(1)

    col_widths = [22, 62, 28, 32, 40]
    headers = ["Code", "Indicator", "Score", "Confidence", "Validation"]

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(234, 250, 241)
    pdf.set_text_color(*primary)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 8, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    for code in INDICATOR_ORDER:
        meta = info[code]
        d = indicators.get(code, {}).get("data", {})
        score = d.get(meta["score_key"])
        score_str = f"{score:.2f}" if isinstance(score, (int, float)) else "N/A"
        row = [code, meta["title"], score_str,
               str(d.get("confidence", "N/A")), str(d.get("validation_status", "N/A"))]
        for w, val in zip(col_widths, row):
            pdf.cell(w, 7, val, border=1)
        pdf.ln()

    pdf.ln(6)

    for code in INDICATOR_ORDER:
        meta = info[code]
        d = indicators.get(code, {}).get("data", {})
        if not d:
            continue

        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*primary)
        pdf.cell(0, 8, f"{code} - {meta['title']}", ln=1)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 40, 40)

        score = d.get(meta["score_key"])
        score_str = f"{score:.2f}" if isinstance(score, (int, float)) else "N/A"
        pdf.multi_cell(0, 6,
            f"Score: {score_str}  |  Scale: {meta['scale_label']}  |  "
            f"Confidence: {d.get('confidence', 'N/A')}  |  "
            f"Validation: {d.get('validation_status', 'N/A')}  |  "
            f"Run ID: {d.get('run_id', 'N/A')}"
        )

        class_key = meta.get("class_key")
        classes = d.get(class_key) if class_key else None
        if isinstance(classes, dict) and classes:
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.cell(0, 6, "Class Breakdown:", ln=1)
            pdf.set_font("Helvetica", "", 9.5)
            for label, values in classes.items():
                if not isinstance(values, dict):
                    continue
                pct = values.get("percent_of_aoi", values.get("percent_of_vegetation"))
                pct_str = f"{pct:.1f}%" if isinstance(pct, (int, float)) else "N/A"
                area_km2 = values.get("area_km2")
                area_str = f"{area_km2:.3f} km2" if isinstance(area_km2, (int, float)) else "N/A"
                pdf.cell(0, 5.5, f"   - {label}: {area_str}  ({pct_str})", ln=1)

        pdf.ln(3)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*primary)
    pdf.cell(0, 8, "Recommendations for Relevant Authorities", ln=1)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(40, 40, 40)

    for i, rec in enumerate(generate_recommendations_en(indicators), start=1):
        pdf.multi_cell(0, 6.5, f"{i}. {rec}")
        pdf.ln(1)

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(*gray)
    pdf.multi_cell(0, 5,
        "Disclaimer: indicators are satellite-derived relative environmental "
        "measures produced by the ENVA analytical pipeline. Spatial indicators "
        "shown are decision-support analytical outputs and must be interpreted "
        "in light of their methodology, confidence level, and limitations. "
        "They do not replace field measurement or regulatory approval. Values "
        "marked 'REVIEW_REQUIRED' or with prototype confidence should be "
        "verified before being used as the sole basis for operational decisions."
    )

    output = pdf.output(dest="S")
    if isinstance(output, str):
        output = output.encode("latin-1")
    return bytes(output)


# ======================================================
# SIDEBAR
# ======================================================

with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding-bottom:6px;">
            {enva_logo_svg(100)}
        </div>
        <div style="text-align:center; font-size:22px; font-weight:800; letter-spacing:1px;">
            ENVA
        </div>
        <div style="text-align:center; font-size:12px; opacity:0.85; padding-bottom:10px;">
            Environmental Intelligence Platform
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "🏠 Home",
            "🛰️ Satellite Analysis",
            "📡 Environmental Indicators",
            "🌍 Interactive Map",
            "📊 Dashboard",
            "🤖 AI Report",
            "🚨 Early Warning",
            "🚜 Agricultural Encroachments",
            "🌳 Smart Afforestation",
            "📥 Reports",
            "🔮 Future Expansion",
        ],
        key="main_navigation"
    )

    st.markdown("---")

    if INDICATORS_AVAILABLE:
        _run_ok = LATEST_RUN.get("run_verified", False)
        _badge_class = "badge-validated" if _run_ok else "badge-review"
        _badge_text = "VALIDATED" if _run_ok else (LATEST_RUN.get("validation_status") or "REVIEW")
        st.markdown(f'<span class="{_badge_class}">● {_badge_text}</span>', unsafe_allow_html=True)
        if not INDICATORS_COMPLETE:
            _found = sum(1 for i in INDICATORS.values() if i["data"])
            st.caption(f"📡 {_found}/7 indicators loaded")
    else:
        st.caption("📡 Indicators data not loaded yet")


# ======================================================
# HOME
# ======================================================

if page == "🏠 Home":

    st.markdown(enva_cover_banner_svg(), unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="platform-header">
            {enva_logo_svg(64)}
            <div>
                <div style="font-size:30px; font-weight:800; color:#145A32;">ENVA</div>
                <div style="font-size:14px; color:#555;">
                    National Intelligent Platform for Environmental Monitoring,
                    Satellite Image Analysis &amp; Decision Support
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader(
        "المنظومة الوطنية الذكية للرصد البيئي وتحليل صور الأقمار الصناعية ودعم اتخاذ القرار"
    )

    st.markdown("---")

    st.markdown(
        """
### 📖 About ENVA

ENVA is an intelligent environmental platform designed to support decision
makers using satellite imagery, artificial intelligence, GIS technologies
and environmental analytics. The platform computes seven satellite-derived
environmental indicators (EHRI, EGLI, EDRI, ETHI, ECSI, EUDI, EEPI), each
with full evidence, methodology, and confidence tracking.

---

### نبذة عن المشروع

يعتمد المشروع على تحليل صور الأقمار الصناعية باستخدام الذكاء الاصطناعي
لرصد التغيرات البيئية ودعم متخذي القرار من خلال لوحة معلومات ذكية، وسبعة
مؤشرات بيئية موثقة بالأدلة والمنهجية ودرجة الثقة لكل نتيجة.

> **المؤشرات المكانية المعروضة هي مخرجات تحليلية داعمة للقرار، ويجب تفسيرها
> في ضوء المنهجية ودرجة الثقة والقيود، ولا تحل محل القياسات الميدانية أو
> الاعتماد التنظيمي.**
"""
    )

    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📍 Study Area", REPORT.get("study_area", "N/A"))
    c2.metric("📅 Current Year", REPORT.get("current_year", "N/A"))
    c3.metric("🎯 Accuracy", f'{REPORT.get("overall_accuracy", "N/A")} %' if REPORT.get("overall_accuracy") is not None else "N/A")
    c4.metric("🛰️ Land Cover Classes", len(SUMMARY))

    if INDICATORS_AVAILABLE:
        st.markdown("---")
        st.markdown("### 📡 Environmental Indicators Snapshot")

        icon_cols = st.columns(7)
        for col, code in zip(icon_cols, INDICATOR_ORDER):
            meta = INDICATOR_INFO[code]
            item = INDICATORS[code]
            with col:
                st.markdown(
                    f"""
                    <div class="indicator-card">
                        <div class="indicator-icon">{meta['icon']}</div>
                        <div class="indicator-code">{code}</div>
                        <div class="indicator-score">{score_text(item['score'], code)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        st.caption("افتحي '📡 Environmental Indicators' من القائمة الجانبية لعرض التفاصيل الكاملة.")

# ======================================================
# SATELLITE ANALYSIS
# ======================================================

elif page == "🛰️ Satellite Analysis":

    st.title("🛰️ Satellite Analysis")
    st.subheader("تحليل صور الأقمار الصناعية")

    st.markdown(
        """
يعرض هذا القسم نتائج تحليل صور الأقمار الصناعية المستخدمة في مشروع ENVA.

This section presents the satellite image analysis results generated by ENVA.
"""
    )

    st.markdown("---")

    st.write("### Land Cover Statistics")
    st.dataframe(SUMMARY, use_container_width=True)

    st.markdown("---")

    st.write("### Environmental Indicators")

    col1, col2, col3 = st.columns(3)

    vegetation = float(SUMMARY.loc[SUMMARY["Class_Name"] == "Vegetation", "Area_km2"].sum())
    urban = float(SUMMARY.loc[SUMMARY["Class_Name"] == "Urban", "Area_km2"].sum())
    bare = float(SUMMARY.loc[SUMMARY["Class_Name"] == "Bare Soil", "Area_km2"].sum())

    col1.metric("🌳 Vegetation", f"{vegetation:.2f} km²")
    col2.metric("🏙️ Urban", f"{urban:.2f} km²")
    col3.metric("🟤 Bare Soil", f"{bare:.2f} km²")

    st.markdown("---")

    if vegetation >= urban and vegetation >= bare:
        st.success(
            """
### AI Summary

✅ Vegetation is the dominant land cover.

### ملخص الذكاء الاصطناعي

✅ الغطاء النباتي يمثل النسبة الأكبر.
"""
        )
    else:
        st.info(
            """
### AI Summary

ℹ️ Vegetation is not currently the dominant land cover class.

### ملخص الذكاء الاصطناعي

ℹ️ الغطاء النباتي ليس العنصر المسيطر حاليًا — راجعي الجدول أعلاه.
"""
        )


# ======================================================
# ENVIRONMENTAL INDICATORS (7 INDICATORS + EEPI)
# Full 12-section layout: name, result, simple explanation,
# scientific interpretation, map, legend, priority areas,
# city meaning, recommendations, confidence/limitations,
# data source & period, evidence & methodology.
# ======================================================

elif page == "📡 Environmental Indicators":

    st.title("📡 ENVA Environmental Indicators")
    st.subheader("المؤشرات البيئية السبعة")

    st.info(
        "**المؤشرات المكانية المعروضة هي مخرجات تحليلية داعمة للقرار، "
        "ويجب تفسيرها في ضوء المنهجية ودرجة الثقة والقيود، ولا تحل محل "
        "القياسات الميدانية أو الاعتماد التنظيمي.**"
    )

    if not INDICATORS_AVAILABLE:
        st.error(
            "❌ لم يتم العثور على ملفات المؤشرات البيئية بعد.\n\n"
            "Export the Cell 24 output from the ENVA Colab notebook into "
            "`data/indicators/` to activate this page."
        )
        st.stop()

    if not INDICATORS_COMPLETE:
        _found = sum(1 for i in INDICATORS.values() if i["data"])
        st.warning(f"⚠️ {_found}/7 indicators currently available. The remaining indicators will appear once exported.")

    run_verified = LATEST_RUN.get("run_verified", False)
    if run_verified:
        st.success(f"✅ Latest run VALIDATED — {str(LATEST_RUN.get('generated_at', 'N/A'))[:19]}")
    elif LATEST_RUN:
        st.warning(f"⚠️ Latest run status: {LATEST_RUN.get('validation_status', 'UNKNOWN')}")

    st.markdown("---")

    # -------------------------------------------------
    # 1. ICON ROW — click an indicator
    # -------------------------------------------------

    if "selected_indicator" not in st.session_state:
        st.session_state.selected_indicator = "EEPI"

    icon_cols = st.columns(7)
    for col, code in zip(icon_cols, INDICATOR_ORDER):
        meta = INDICATOR_INFO[code]
        item = INDICATORS[code]
        with col:
            is_selected = st.session_state.selected_indicator == code
            card_class = "indicator-card selected" if is_selected else "indicator-card"
            st.markdown(
                f"""
                <div class="{card_class}">
                    <div class="indicator-icon">{meta['icon']}</div>
                    <div class="indicator-code">{code}</div>
                    <div class="indicator-score">{score_text(item['score'], code)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("عرض", key=f"btn_{code}", use_container_width=True):
                st.session_state.selected_indicator = code
                st.rerun()

    st.markdown("---")

    selected_indicator = st.session_state.selected_indicator
    info = INDICATOR_INFO[selected_indicator]
    selected = INDICATORS[selected_indicator]
    selected_data = selected["data"]

    if not selected_data:
        st.warning(f"⚠️ لا توجد بيانات لهذا المؤشر ({selected_indicator}) بعد.")
        st.stop()

    # -------------------------------------------------
    # 1 & 2. NAME + CURRENT RESULT
    # -------------------------------------------------

    st.header(f"{info['icon']} {selected_indicator} — {info['title']}")
    st.subheader(info["arabic"])

    score_value = selected["score"]

    metric_col, status_col = st.columns([1, 2])

    with metric_col:
        st.metric("النتيجة الحالية / Official ENVA Result", score_text(score_value, selected_indicator))

    with status_col:
        validation_status = selected_data.get("validation_status", "Not specified")
        confidence = selected_data.get("confidence", "Not specified")
        st.info(f"Validation status: {validation_status}\n\nConfidence: {confidence}")

    # -------------------------------------------------
    # 3 & 4. SIMPLE EXPLANATION + SCIENTIFIC INTERPRETATION
    # -------------------------------------------------

    st.markdown("### ℹ️ ما الذي يقيسه المؤشر؟ (شرح مبسط)")
    st.write(info["what"])

    st.markdown("### 🧭 كيف نفهم الرقم؟ (التفسير العلمي)")
    st.write(info["read"])

    # -------------------------------------------------
    # 5 & 6. MAP + COLOR LEGEND
    # -------------------------------------------------

    st.markdown("### 🗺️ الخريطة الرسمية للمؤشر")

    if selected["map_path"] is not None:
        map_path = selected["map_path"]
        if map_path.suffix == ".html":
            from streamlit.components.v1 import html as st_html
            with open(map_path, encoding="utf-8") as f:
                st_html(f.read(), height=560, scrolling=True)
        else:
            st.image(str(map_path), use_container_width=True,
                      caption=f"{selected_indicator} — {info['title']}")
        st.caption(info["map_meaning"])
    else:
        st.warning("الخريطة الرسمية لهذا المؤشر غير موجودة في حزمة بيانات المنصة الحالية.")

    st.markdown("##### 🎨 مفتاح الألوان")
    st.caption(
        "القيم المنخفضة (اللون الأخضر/الفاتح) تعني أولوية أقل، بينما القيم "
        "المرتفعة (اللون الأحمر/الداكن) تعني أولوية أعلى للفحص أو التدخل — "
        "وفق تدرج الخريطة الموضّح داخل ملف الخريطة نفسه."
    )

    # -------------------------------------------------
    # 7. TOP PRIORITY AREAS (ranked class breakdown)
    # -------------------------------------------------

    class_key = info["class_key"]
    classes = selected_data.get(class_key, {}) if class_key else None

    if isinstance(classes, dict) and classes:
        st.markdown("### 📌 أهم المناطق ذات الأولوية")

        class_rows = []
        for class_name, class_value in classes.items():
            if not isinstance(class_value, dict):
                continue
            row = {"Class": class_name}
            for key in ["area_m2", "area_km2", "percent_of_aoi", "percent_of_vegetation"]:
                if key in class_value:
                    row[key] = class_value[key]
            class_rows.append(row)

        if class_rows:
            class_df = pd.DataFrame(class_rows)
            sort_col = "percent_of_aoi" if "percent_of_aoi" in class_df.columns else (
                "percent_of_vegetation" if "percent_of_vegetation" in class_df.columns else None
            )
            if sort_col:
                class_df = class_df.sort_values(sort_col, ascending=False)

            st.dataframe(class_df, use_container_width=True, hide_index=True)

            if sort_col:
                fig = px.bar(class_df, x="Class", y=sort_col, color="Class",
                              title=f"{selected_indicator} — توزيع الفئات المكانية")
                st.plotly_chart(fig, use_container_width=True)

    if selected_indicator == "EEPI" and "input_indicators" in selected_data:
        st.markdown("### 🧩 مساهمة المؤشرات الستة في EEPI")
        contrib_rows = [
            {"Indicator": name, "Normalized Score": round(v.get("normalized_score", 0), 2),
             "Weight": v.get("weight"), "Contribution": round(v.get("weighted_contribution", 0), 2)}
            for name, v in selected_data["input_indicators"].items()
        ]
        st.dataframe(pd.DataFrame(contrib_rows), use_container_width=True, hide_index=True)
        st.caption(
            "EEPI مؤشر ترتيب/أولوية مركب، وليس قياسًا بيئيًا خامًا — "
            "راجعي المكونات الستة أعلاه قبل تحديد نوع التدخل."
        )

    # -------------------------------------------------
    # 8. WHAT DOES THIS MEAN FOR THE CITY?
    # -------------------------------------------------

    st.markdown("### 🏙️ ماذا تعني النتيجة للمدينة؟")
    st.write(info["city_meaning"])

    # -------------------------------------------------
    # 9. RECOMMENDATIONS
    # -------------------------------------------------

    st.markdown("### 🎯 التوصيات المقترحة")
    for recommendation in info["recommendations"]:
        st.write("• " + recommendation)
    st.caption("هذه توصيات تخطيطية داعمة للقرار، وليست أوامر تنفيذية أو نتائج قياس ميداني.")

    # -------------------------------------------------
    # 10. CONFIDENCE & LIMITATIONS
    # -------------------------------------------------

    caveats = selected_data.get("caveats", [])
    methodology = selected_data.get("methodology", {})

    if selected["metadata"]:
        methodology = selected["metadata"].get("methodology", methodology)
        caveats = (
            selected["metadata"].get("caveats")
            or methodology.get("caveats")
            or caveats
        )

    st.markdown("### ⚠️ مستوى الثقة والقيود")

    if caveats:
        for caveat in caveats:
            st.warning(str(caveat))
    else:
        st.info("يرجى الرجوع إلى سجل المنهجية والتوثيق الخاص بالمؤشر قبل استخدامه في قرار تنفيذي.")

    # -------------------------------------------------
    # 11. DATA SOURCE & ANALYSIS PERIOD
    # -------------------------------------------------

    st.markdown("### 🔎 مصدر البيانات وفترة التحليل")

    trace_col1, trace_col2 = st.columns(2)

    with trace_col1:
        st.write(f"Run ID: {selected_data.get('run_id', 'Not specified')}")
        if selected["app_path"] is not None:
            st.write(f"App data: {selected['app_path']}")

    with trace_col2:
        if selected["map_path"] is not None:
            st.write(f"Report map: {selected['map_path']}")
        if selected["metadata_path"] is not None:
            st.write(f"Metadata: {selected['metadata_path']}")

    data_sources = None
    if isinstance(methodology, dict):
        data_sources = methodology.get("inputs") or methodology.get("data_sources")
    if data_sources:
        st.write("Data sources:")
        st.json(data_sources)

    # -------------------------------------------------
    # 12. EVIDENCE & METHODOLOGY BUTTON
    # -------------------------------------------------

    with st.expander("📜 عرض الدليل والمنهجية الكاملة / View Evidence & Methodology"):
        st.json(selected_data)
        if selected["metadata"]:
            st.markdown("---")
            st.json(selected["metadata"])

    st.markdown("---")

    st.info(
        "ENVA Decision Support Rule: المؤشر يساعد في تحديد مكان الأولوية "
        "وفهم النمط البيئي، ولا يُستخدم منفردًا كبديل عن القياس الميداني "
        "أو الاعتماد التنظيمي."
    )

    if FPDF_AVAILABLE:
        pdf_bytes = build_indicators_pdf(INDICATORS, INDICATOR_INFO, LATEST_RUN)
        if pdf_bytes:
            st.download_button(
                label="⬇️ Download Full Indicators Report (PDF)",
                data=pdf_bytes,
                file_name="ENVA_Environmental_Indicators_Report.pdf",
                mime="application/pdf",
                key="indicators_page_pdf_download",
            )
    else:
        st.caption("PDF export requires the `fpdf2` package — add it to requirements.txt.")

elif page == "🌍 Interactive Map":

    st.title("🌍 Interactive Environmental Map")

    st.subheader("الخريطة التفاعلية")

    st.markdown("""
    تعرض هذه الصفحة خريطة الغطاء الأرضي الناتجة من تحليل صور الأقمار الصناعية.

    This page displays the interactive land cover map generated from satellite imagery.
    """)

    st.markdown("---")

    # ==================================================
    # INTERACTIVE EARTH ENGINE MAP
    # ==================================================

    st.markdown("### 🛰️ Satellite Environmental Map")

    st.write(
        "الخريطة التفاعلية تعرض طبقات الأقمار الصناعية "
        "والغطاء الأرضي ومنطقة الدراسة."
    )

    # --------------------------------------------------
    # MAP CONTAINER
    # --------------------------------------------------

    map_html = """
    <!DOCTYPE html>
    <html>
    <head>

        <meta charset="utf-8">

        <meta name="viewport"
              content="width=device-width,
                       initial-scale=1.0">

        <title>ENVA Interactive Map</title>

        <link
            rel="stylesheet"
            href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        />

        <script
            src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
        </script>

        <style>

            html, body {
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                background: #071827;
            }

            #map {
                width: 100%;
                height: 880px;
                min-height: 700px;
            }

            .leaflet-control-layers {
                background: rgba(255,255,255,0.96);
                border-radius: 10px;
            }

            .map-title {
                background: rgba(7,24,39,0.90);
                color: white;
                padding: 10px 16px;
                border-radius: 10px;
                font-family: Arial, sans-serif;
                font-weight: 700;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }

        </style>

    </head>

    <body>

        <div id="map"></div>

        <script>

            // ==================================================
            // CREATE MAP
            // ==================================================

            var map = L.map("map", {
                center: [31.130909905415095, 30.101980232169154],
                zoom: 11,
                zoomControl: true
            });


            // ==================================================
            // OPEN STREET MAP
            // ==================================================

            var osm = L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                {
                    maxZoom: 19,
                    attribution:
                        '&copy; OpenStreetMap contributors'
                }
            );


            // ==================================================
            // TRUE COLOR — GOOGLE EARTH ENGINE
            // ==================================================

            var trueColor = L.tileLayer(
                "https://earthengine.googleapis.com/v1/projects/carbide-theme-502500-b6/maps/edecd4b45ebac6aaa2d624c678e5cb28-87bdd295220d48a0f5d379d488a14dd3/tiles/{z}/{x}/{y}",
                {
                    maxZoom: 24,
                    attribution: "Google Earth Engine",
                    opacity: 1.0
                }
            );


            // ==================================================
            // LAND COVER — GOOGLE EARTH ENGINE
            // ==================================================

            var landCover = L.tileLayer(
                "https://earthengine.googleapis.com/v1/projects/carbide-theme-502500-b6/maps/6741bcd95f559abf8b80536e7655fa82-d1860385ad48f2d189c580e675049896/tiles/{z}/{x}/{y}",
                {
                    maxZoom: 24,
                    attribution: "Google Earth Engine",
                    opacity: 0.75
                }
            );


            // ==================================================
            // STUDY AREA — GOOGLE EARTH ENGINE
            // ==================================================

            var studyArea = L.tileLayer(
                "https://earthengine.googleapis.com/v1/projects/carbide-theme-502500-b6/maps/f5589abb5aad4d0ec79af757f6b7475f-c3398c3892b456e3473322ae971c6a7d/tiles/{z}/{x}/{y}",
                {
                    maxZoom: 24,
                    attribution: "Google Earth Engine",
                    opacity: 1.0
                }
            );


            // ==================================================
            // DEFAULT LAYERS
            // ==================================================

            osm.addTo(map);

            trueColor.addTo(map);


            // ==================================================
            // LAYER CONTROL
            // ==================================================

            var baseMaps = {

                "🗺️ OpenStreetMap":
                    osm,

                "🛰️ True Color":
                    trueColor

            };


            var overlayMaps = {

                "🌱 Land Cover":
                    landCover,

                "📍 Study Area":
                    studyArea

            };


            L.control.layers(
                baseMaps,
                overlayMaps,
                {
                    collapsed: false,
                    position: "topright"
                }
            ).addTo(map);


            // ==================================================
            // TITLE
            // ==================================================

            var titleControl =
                L.control({
                    position: "topleft"
                });

            titleControl.onAdd = function() {

                var div =
                    L.DomUtil.create(
                        "div",
                        "map-title"
                    );

                div.innerHTML =
                    "🛰️ ENVA Environmental Map";

                return div;
            };

            titleControl.addTo(map);


            // ==================================================
            // SCALE
            // ==================================================

            L.control.scale({
                imperial: false
            }).addTo(map);


            // ==================================================
            // FIX MAP SIZE
            // ==================================================

            setTimeout(function() {

                map.invalidateSize();

            }, 500);

        </script>

    </body>
    </html>
    """

    # ==================================================
    # DISPLAY MAP
    # ==================================================

    from streamlit.components.v1 import html

    html(
        map_html,
        height=900,
        scrolling=False
    )

    st.success(
        "✅ Interactive environmental map loaded successfully."
    )

    st.markdown("---")

    # ==================================================
    # AVAILABLE MAP LAYERS
    # ==================================================

    st.info("""
### 🗺️ Available Layers

🛰️ Land Cover

🌳 Vegetation

🏙️ Urban Areas

🟤 Bare Soil

💧 Water Bodies

يمكن استخدام الخريطة للتكبير والتصغير واستعراض المناطق المختلفة.
""")

    # ==================================================
    # OFFICIAL ENVIRONMENTAL INDICATOR MAPS — CELL 21
    # ==================================================

    st.markdown("---")
    st.markdown("### 📡 Official Environmental Indicator Maps")
    st.caption(
        "الخرائط التالية هي الخرائط الأصلية المعتمدة للمؤشرات السبعة، "
        "وتُعرض مباشرة داخل المنصة دون إعادة حساب أو إعادة رسم القيم. "
        "The original Cell 11-17 HTML maps are embedded directly in Streamlit."
    )

    official_map_available = False
    try:
        from streamlit.components.v1 import html as st_html
    except Exception:
        st_html = None

    official_map_cols = st.columns(2)

    for idx, code in enumerate(INDICATOR_ORDER):
        meta = INDICATOR_INFO[code]
        item = INDICATORS.get(code, {})
        map_path = item.get("map_path") if isinstance(item, dict) else None

        with official_map_cols[idx % 2]:
            st.markdown(f"#### {meta['icon']} {code} — {meta['title']}")

            if map_path is not None and Path(map_path).suffix.lower() == ".html" and st_html is not None:
                try:
                    with open(map_path, encoding="utf-8") as map_file:
                        original_map_html = map_file.read()

                    st_html(
                        original_map_html,
                        height=650,
                        scrolling=False
                    )

                    official_map_available = True
                    st.caption(
                        "Official original interactive HTML map — Cell 11-17 source preserved."
                    )

                except Exception as map_error:
                    st.warning(
                        f"تعذر عرض الخريطة الرسمية لـ {code}: {map_error}"
                    )

            elif map_path is not None:
                st.image(
                    str(map_path),
                    use_container_width=True,
                    caption=f"{code} — {meta['title']}"
                )
                official_map_available = True

            else:
                st.warning(
                    f"الخريطة الرسمية لـ {code} غير موجودة في حزمة المنصة."
                )

    if official_map_available:
        st.success(
            "✅ تم تحميل الخرائط الرسمية للمؤشرات المتاحة داخل المنصة مباشرة."
        )
    else:
        st.error(
            "❌ لم يتم العثور على ملفات الخرائط الرسمية. "
            "تأكدي من رفع app_data/indicator_maps إلى مستودع GitHub."
        )

# ======================================================
# ANALYTICS DASHBOARD
# ======================================================

elif page == "📊 Dashboard":

    st.title("📊 Environmental Analytics Dashboard")

    st.subheader("لوحة التحليلات البيئية")

    st.markdown(
        """
هذه الصفحة تعرض الإحصاءات البيئية المستخرجة من تحليل صور الأقمار الصناعية.

This dashboard summarizes the environmental indicators extracted from satellite imagery.
"""
    )

    st.markdown("---")

    # ===========================
    # KPI
    # ===========================

    c1, c2, c3, c4 = st.columns(4)

    total_area = float(
        SUMMARY["Area_km2"].sum()
    )

    vegetation = float(
        SUMMARY.loc[
            SUMMARY["Class_Name"] == "Vegetation",
            "Area_km2"
        ].sum()
    )

    urban = float(
        SUMMARY.loc[
            SUMMARY["Class_Name"] == "Urban",
            "Area_km2"
        ].sum()
    )

    bare = float(
        SUMMARY.loc[
            SUMMARY["Class_Name"] == "Bare Soil",
            "Area_km2"
        ].sum()
    )

    c1.metric(
        "📍 Study Area",
        REPORT.get("study_area", "N/A")
    )

    c2.metric(
        "🛰️ Classes",
        len(SUMMARY)
    )

    c3.metric(
        "🌳 Vegetation",
        f"{vegetation:.2f} km²"
    )

    c4.metric(
        "📐 Total Area",
        f"{total_area:.2f} km²"
    )

    st.markdown("---")

    # ===========================
    # LAND COVER TABLE
    # ===========================

    st.subheader("Land Cover Statistics")

    st.dataframe(
        SUMMARY,
        use_container_width=True
    )

    st.markdown("---")

    # ===========================
    # SIMPLE BAR CHART
    # ===========================

    st.subheader("Land Cover Distribution")

    chart_data = (
        SUMMARY
        .set_index("Class_Name")["Area_km2"]
    )

    st.bar_chart(chart_data)

    st.markdown("---")

    # ===========================
    # AI INSIGHTS
    # ===========================

    st.subheader("🤖 AI Insights")

    if vegetation > bare:

        st.success(
            """
Vegetation is the dominant land cover.

الغطاء النباتي يمثل المساحة الأكبر داخل منطقة الدراسة.
"""
        )

    if bare > urban:

        st.info(
            """
Bare soil is larger than urban expansion.

الأراضي الجرداء ما زالت أكبر من التوسع العمراني.
"""
        )

    if urban < vegetation:

        st.success(
            """
Urban expansion is still limited.

التوسع العمراني ما زال محدودًا مقارنة بالغطاء النباتي.
"""
        )

# ======================================================
# AI ENVIRONMENTAL REPORT
# ======================================================

elif page == "🤖 AI Report":

    st.title("🤖 ENVA AI Environmental Assistant")

    st.subheader("المساعد الذكي لتحليل البيئة")

    st.markdown(
        """
يقوم الذكاء الاصطناعي بتحليل نتائج صور الأقمار الصناعية
واستخراج أهم المؤشرات البيئية بصورة تلقائية.

The AI engine automatically interprets satellite analysis
and generates environmental insights.
"""
    )

    st.markdown("---")

    # =====================================
    # Load Statistics
    # =====================================

    vegetation = float(
        SUMMARY.loc[
            SUMMARY["Class_Name"] == "Vegetation",
            "Area_km2"
        ].sum()
    )

    urban = float(
        SUMMARY.loc[
            SUMMARY["Class_Name"] == "Urban",
            "Area_km2"
        ].sum()
    )

    bare = float(
        SUMMARY.loc[
            SUMMARY["Class_Name"] == "Bare Soil",
            "Area_km2"
        ].sum()
    )

    total = float(
        SUMMARY["Area_km2"].sum()
    )

    # =====================================
    # Prevent ZeroDivisionError
    # =====================================

    if total > 0:

        vegetation_percent = vegetation / total * 100
        urban_percent = urban / total * 100
        bare_percent = bare / total * 100

    else:

        vegetation_percent = 0.0
        urban_percent = 0.0
        bare_percent = 0.0

    # =====================================
    # Executive Summary
    # =====================================

    st.markdown("## 📄 Executive Summary")

    st.success(
        f"""
### 🇬🇧 English

The AI environmental analysis indicates that vegetation is the dominant land cover.

🌳 Vegetation: **{vegetation_percent:.1f}%**

🏙️ Urban: **{urban_percent:.1f}%**

🟤 Bare Soil: **{bare_percent:.1f}%**

Current observations are summarized for decision support; they do not by themselves establish overall environmental stability.

---

### 🇪🇬 العربية

يشير تحليل الذكاء الاصطناعي إلى أن الغطاء النباتي هو العنصر المسيطر داخل منطقة الدراسة.

🌳 الغطاء النباتي: **{vegetation_percent:.1f}%**

🏙️ العمران: **{urban_percent:.1f}%**

🟤 الأراضي الجرداء: **{bare_percent:.1f}%**

تقدم البيانات الحالية مؤشرات وصفية لدعم القرار، ولا تكفي وحدها لإثبات استقرار بيئي شامل.
"""
    )

    st.markdown("---")

    # =====================================
    # AI Status Cards
    # =====================================

    if vegetation_percent >= 60:
        status = "🟢 Stable"
    elif vegetation_percent >= 40:
        status = "🟡 Moderate"
    else:
        status = "🔴 Critical"

    if bare_percent >= 20:
        risk = "🔴 High"
    elif bare_percent >= 10:
        risk = "🟡 Medium"
    else:
        risk = "🟢 Low"

    confidence = REPORT.get("overall_accuracy")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Environmental Status",
        status
    )

    col2.metric(
        "Risk Level",
        risk
    )

    col3.metric(
        "Model / Data Confidence",
        f"{confidence}%" if isinstance(confidence, (int, float)) else "N/A"
    )

    st.markdown("---")
    # =====================================
    # AI ENVIRONMENTAL ASSESSMENT
    # =====================================

    st.subheader("🧠 ENVA Environmental Assessment")

    if vegetation_percent >= 70:

        ai_text = """
### 🌿 Environmental Interpretation

The available land-cover summary indicates a relatively favorable vegetation share; this should not be interpreted as a complete environmental-health diagnosis.

Vegetation is the dominant land cover,
but this should not be interpreted as proof of ecosystem stability or low environmental pressure.

Urban expansion remains limited.

Current satellite observations suggest that
the environmental condition is suitable for sustainable development.

---

### 🇪🇬 التفسير البيئي

تشير نتائج الذكاء الاصطناعي إلى أن المنطقة تتمتع بحالة بيئية جيدة.

يسيطر الغطاء النباتي على معظم مساحة المنطقة،
مما يعكس استقرارًا بيئيًا وانخفاض الضغوط البشرية.

ولا يزال التوسع العمراني محدودًا،
وهو ما يساعد على الحفاظ على الموارد الطبيعية.
"""

    elif vegetation_percent >= 50:

        ai_text = """
### 🌿 Environmental Interpretation

The available indicators support continued monitoring and preventive review.

Vegetation is still dominant,
however continuous monitoring is recommended
to detect any future land cover changes.

Urban development should be monitored periodically.

---

### 🇪🇬 التفسير البيئي

تشير النتائج إلى أن تشير المؤشرات المتاحة إلى الحاجة إلى متابعة مستمرة ومراجعة وقائية.

ورغم سيطرة الغطاء النباتي،
فإن المتابعة الدورية ضرورية
لاكتشاف أي تغيرات مستقبلية.

كما يوصى بمراقبة التوسع العمراني باستمرار.
"""

    else:

        ai_text = """
### ⚠ Environmental Interpretation

The AI engine detected a decline in vegetation.

This may indicate environmental degradation,
urban expansion,
or increasing land degradation.

Immediate monitoring is recommended.

---

### 🇪🇬 التفسير البيئي

اكتشف الذكاء الاصطناعي انخفاضًا واضحًا في الغطاء النباتي.

وقد يشير ذلك إلى
التوسع العمراني،
أو تدهور الأراضي،
أو انخفاض جودة البيئة.

يوصى بإجراء متابعة عاجلة.
"""

    st.success(ai_text)

    st.markdown("---")

    # =====================================
    # AI SMART RECOMMENDATIONS
    # =====================================

    st.subheader("🎯 AI Smart Recommendations")

    recommendations = []

    # Vegetation

    if vegetation_percent >= 70:

        recommendations.append(
            "🌳 Preserve existing vegetation and protect agricultural land."
        )

    elif vegetation_percent >= 50:

        recommendations.append(
            "🌱 Increase vegetation monitoring every season."
        )

    else:

        recommendations.append(
            "🚨 Immediate vegetation restoration is recommended."
        )

    # Bare Soil

    if bare_percent >= 20:

        recommendations.append(
            "🌾 Launch large-scale afforestation projects in bare soil regions."
        )

    elif bare_percent >= 10:

        recommendations.append(
            "🌱 Prioritize tree planting in degraded land."
        )

    # Urban

    if urban_percent >= 15:

        recommendations.append(
            "🏙️ Monitor urban expansion using monthly satellite imagery."
        )

    else:

        recommendations.append(
            "🏡 Urban growth is currently under acceptable limits."
        )

    # Water and Monitoring

    recommendations.append(
        "💧 Continue monitoring water resources using Sentinel imagery."
    )

    recommendations.append(
        "🛰️ Update environmental monitoring every month."
    )

    recommendations.append(
        "🤖 AI recommends maintaining continuous satellite observation."
    )

    for item in recommendations:

        st.write(item)

    st.markdown("---")

    # ==========================================================
    # AI DECISION SUPPORT
    # ==========================================================

    st.subheader("🧠 ENVA Decision Support")

    # =====================================
    # Sustainability Score
    # =====================================

    sustainability_score = round(
        vegetation_percent
        - (bare_percent * 0.5)
        - (urban_percent * 0.3),
        1
    )

    sustainability_score = max(
        0,
        min(100, sustainability_score)
    )

    # =====================================
    # Environmental Risk Score
    # =====================================

    risk_score = round(
        (bare_percent * 1.5)
        + urban_percent,
        1
    )

    # =====================================
    # Risk Level
    # =====================================

    if risk_score < 20:

        risk_level = "🟢 LOW"

    elif risk_score < 40:

        risk_level = "🟡 MODERATE"

    else:

        risk_level = "🔴 HIGH"

    # =====================================
    # Transparent rule-based decision support (not a trained predictive AI model)
    # =====================================

    if sustainability_score >= 70:

        decision = """
### ✅ ENVA Final Assessment

The available indicators do not show a basis for an unconditional stability claim.

No operational intervention decision should be made from this score alone; targeted review is recommended.

Routine environmental monitoring is recommended.

---

### 🇪🇬 القرار النهائي

لا ينبغي اعتبار النتيجة وحدها إثباتًا لاستقرار بيئي شامل.

لا تُتخذ قرارات تدخلية اعتمادًا على هذه النتيجة وحدها، ويوصى بالمراجعة المستهدفة.

يوصى بالمتابعة الدورية فقط.
"""

    elif sustainability_score >= 50:

        decision = """
### ⚠ ENVA Final Assessment

The study area is environmentally acceptable.

Preventive environmental actions are recommended.

---

### 🇪🇬 القرار النهائي

تشير المؤشرات المتاحة إلى الحاجة إلى متابعة مستمرة ومراجعة وقائية.

يوصى باتخاذ إجراءات وقائية للحفاظ على الموارد الطبيعية.
"""

    else:

        decision = """
### 🚨 ENVA Final Assessment

Targeted environmental review is recommended.

Restoration and afforestation programs should be considered.

---

### 🇪🇬 القرار النهائي

يوصى بتدخل بيئي عاجل.

ينصح بتنفيذ برامج إعادة التأهيل والتشجير.
"""

    # =====================================
    # Metrics
    # =====================================

    col1, col2 = st.columns(2)

    col1.metric(
        "🌍 Sustainability Score",
        f"{sustainability_score}/100"
    )

    col2.metric(
        "⚠ Environmental Risk",
        risk_level
    )

    st.markdown("---")

    st.success(decision)

    st.markdown("---")

    st.info(
        """
### Decision Support

ENVA automatically summarizes the available environmental indicators using the documented decision-support rules.
to support environmental planning and decision making.

يقوم الذكاء الاصطناعي بتحويل نتائج تحليل صور الأقمار الصناعية
إلى ملخص واضح يساعد متخذي القرار، مع الحفاظ على كون المخرجات تحليلية وداعمة للقرار.
"""
    )

    st.caption(
        "Generated automatically by ENVA Decision Support Engine."
    )

    st.markdown("---")

    # ==========================================================
    # ENVIRONMENTAL INDICATORS FORMAL REPORT (for stakeholders)
    # ==========================================================

    st.header("📡 Environmental Indicators Report")
    st.subheader("تقرير المؤشرات البيئية الرسمي")

    if not INDICATORS_AVAILABLE:
        st.warning(
            "⚠️ Environmental indicators data not available yet. "
            "This section will populate once indicator data is exported "
            "from the ENVA Colab notebook (Cell 24)."
        )
    else:
        report_generated_at = LATEST_RUN.get("generated_at", datetime.now().isoformat())
        run_status = LATEST_RUN.get("validation_status", "UNKNOWN")

        st.markdown(
            f"""
**Study Area:** {REPORT.get("study_area", "Kafr El Dawwar City")}
**Report Generated:** {str(report_generated_at)[:19]}
**Validation Status:** {run_status}
"""
        )

        summary_rows = []
        for code in INDICATOR_ORDER:
            meta = INDICATOR_INFO[code]
            d = INDICATORS[code]["data"]
            score = d.get(meta["score_key"])
            summary_rows.append({
                "Code": code,
                "Indicator": meta["title"],
                "Score": round(score, 2) if isinstance(score, (int, float)) else "N/A",
                "Confidence": d.get("confidence", "N/A"),
                "Validation": d.get("validation_status", "N/A"),
            })

        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

        for code in INDICATOR_ORDER:
            meta = INDICATOR_INFO[code]
            d = INDICATORS[code]["data"]
            score = d.get(meta["score_key"])
            score_str = score_text(score, code)
            with st.expander(f"{meta['icon']} {code} — {meta['title']} ({score_str})"):
                st.write(f"**{meta['arabic']}**")
                st.write(
                    f"Confidence: {d.get('confidence', 'N/A')} | "
                    f"Validation: {d.get('validation_status', 'N/A')} | "
                    f"Run ID: `{d.get('run_id', 'N/A')}`"
                )
                st.write(meta["city_meaning"])

        st.markdown("---")

        st.subheader("🎯 Recommendations for Relevant Authorities")
        for i, rec in enumerate(generate_recommendations_en(INDICATORS), start=1):
            st.write(f"{i}. {rec}")

        st.markdown("---")

        if FPDF_AVAILABLE:
            pdf_bytes = build_indicators_pdf(INDICATORS, INDICATOR_INFO, LATEST_RUN)
            if pdf_bytes:
                st.download_button(
                    label="⬇️ Download Official Indicators Report (PDF)",
                    data=pdf_bytes,
                    file_name="ENVA_Environmental_Indicators_Report.pdf",
                    mime="application/pdf",
                    key="ai_report_pdf_download",
                )
        else:
            st.info("PDF export requires the `fpdf2` package — add it to requirements.txt.")

# ======================================================
# SMART AFFORESTATION
# ======================================================

elif page == "🌳 Smart Afforestation":

    st.title("🌳 Smart Afforestation")

    st.subheader("التشجير الذكي")

    st.markdown(
        """
تستخدم هذه الصفحة نتائج الذكاء الاصطناعي وصور الأقمار الصناعية
لتحديد المناطق المناسبة للتشجير وتحسين الغطاء النباتي
ودعم التنمية البيئية المستدامة.

This module uses AI-based satellite analysis
to identify suitable afforestation areas
and support sustainable environmental planning.
"""
    )

    st.markdown("---")

    # ======================================================
    # LOAD DATA
    # ======================================================

    try:

        with open(
            DATA_PATH / "ENVA_Afforestation_Report.json",
            encoding="utf-8"
        ) as f:

            AFF_REPORT = json.load(f)

        AFF_SUMMARY = pd.read_csv(
            DATA_PATH / "ENVA_Afforestation_Summary.csv"
        )

    except Exception as e:

        st.error(
            f"❌ Error loading Smart Afforestation files\n\n{e}"
        )

        st.stop()

    st.success(
        "✅ Smart Afforestation data loaded successfully."
    )

    st.markdown("---")

    # ======================================================
    # AI SUMMARY
    # ======================================================

    st.subheader("🤖 AI Summary")

    ai_summary = AFF_REPORT.get("AI_Summary")

    if ai_summary:

        st.json(ai_summary)

    else:

        st.info(
            "AI summary is not available."
        )

    st.markdown("---")

    # ======================================================
    # SUMMARY TABLE
    # ======================================================

    st.subheader("📋 Afforestation Summary")

    st.dataframe(
        AFF_SUMMARY,
        use_container_width=True
    )

    st.markdown("---")

    # ======================================================
    # MAIN INDICATORS
    # ======================================================

    st.subheader("📊 Key Indicators")

    if "Recommended Area (km²)" in AFF_SUMMARY.columns:

        area = float(
            AFF_SUMMARY["Recommended Area (km²)"].iloc[0]
        )

    else:

        area = 0.0

    if "Estimated Trees" in AFF_SUMMARY.columns:

        trees = int(
            AFF_SUMMARY["Estimated Trees"].iloc[0]
        )

    else:

        trees = 0

    if "Annual Carbon (ton CO₂)" in AFF_SUMMARY.columns:

        carbon = float(
            AFF_SUMMARY["Annual Carbon (ton CO₂)"].iloc[0]
        )

    else:

        carbon = 0.0

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "🌱 Target Area",
        f"{area:.2f} km²"
    )

    c2.metric(
        "🌳 Estimated Trees",
        f"{trees:,}"
    )

    c3.metric(
        "🌍 Annual CO₂",
        f"{carbon:,.1f} ton"
    )

    st.markdown("---")

    # ======================================================
    # DECISION SUPPORT
    # ======================================================

    st.subheader("🧠 Smart Afforestation Decision Support")

    st.info(
        """
ENVA analyzes satellite-derived evidence to identify potential afforestation opportunities.
The module does not establish guaranteed site suitability without technical and field review.

The generated recommendations are analytical and do not by themselves establish realized environmental benefits or guaranteed carbon sequestration.

---

يقوم نظام ENVA بتحليل صور الأقمار الصناعية
لتحديد أفضل مواقع التشجير.

والنتائج لا تثبت بمفردها زيادة محققة في الغطاء النباتي أو معدلًا معتمدًا لاحتجاز الكربون دون تحقق ومتابعة.
"""
    )

    st.markdown("---")

    # ======================================================
    # RECOMMENDED ACTIONS
    # ======================================================

    st.subheader("🎯 Recommended Actions")

    actions = []

    if area > 0:

        actions.append(
            f"🌱 Afforest approximately {area:.2f} km²."
        )

    if trees > 0:

        actions.append(
            f"🌳 Plant approximately {trees:,} trees."
        )

    if "Recommended Tree" in AFF_SUMMARY.columns:

        recommended_tree = str(
            AFF_SUMMARY["Recommended Tree"].iloc[0]
        )

        actions.append(
            f"🌲 Recommended species: {recommended_tree}"
        )

    actions.append(
        "🛰️ Continue monitoring using Sentinel satellite imagery."
    )

    actions.append(
        "🌍 Update the environmental assessment periodically."
    )

    for item in actions:

        st.write(item)

    st.markdown("---")

    # ======================================================
    # AFFORESTATION SUMMARY TABLE
    # ======================================================

    st.subheader("🌱 Afforestation Analysis Summary")

    st.dataframe(
        AFF_SUMMARY,
        use_container_width=True
    )

    st.markdown("---")

    # ======================================================
    # BASIC INDICATORS
    # ======================================================

    st.subheader("📊 Afforestation Indicators")

    col1, col2, col3 = st.columns(3)

    records = len(AFF_SUMMARY)

    if "Recommended Area (km²)" in AFF_SUMMARY.columns:

        recommended_area = float(
            AFF_SUMMARY["Recommended Area (km²)"].sum()
        )

    else:

        recommended_area = 0.0

    if "Estimated Trees" in AFF_SUMMARY.columns:

        estimated_trees = int(
            AFF_SUMMARY["Estimated Trees"].sum()
        )

    else:

        estimated_trees = 0

    col1.metric(
        "📄 Analysis Records",
        records
    )

    col2.metric(
        "🌳 Recommended Area",
        f"{recommended_area:.2f} km²"
    )

    col3.metric(
        "🌱 Estimated Trees",
        f"{estimated_trees:,}"
    )

    st.markdown("---")

    # ======================================================
    # AI DECISION SUPPORT
    # ======================================================

    st.subheader("🤖 AI Decision Support")

    st.info(
        """
ENVA AI analyzes satellite imagery to determine the best locations
for afforestation according to environmental suitability.

يقوم الذكاء الاصطناعي بتحليل صور الأقمار الصناعية
لتحديد أفضل المناطق المناسبة للتشجير.
"""
    )

    st.markdown("---")

    # ======================================================
    # RECOMMENDED ACTIONS
    # ======================================================

    st.subheader("🎯 Recommended Actions")

    actions = []

    if "Recommended Tree" in AFF_SUMMARY.columns:

        tree = str(
            AFF_SUMMARY["Recommended Tree"].iloc[0]
        )

        actions.append(
            f"🌳 Recommended tree species: {tree}"
        )

    if "Recommended Area (km²)" in AFF_SUMMARY.columns:

        area = float(
            AFF_SUMMARY["Recommended Area (km²)"].iloc[0]
        )

        actions.append(
            f"🌱 Afforest approximately {area:.2f} km²."
        )

    if "Estimated Trees" in AFF_SUMMARY.columns:

        trees = int(
            AFF_SUMMARY["Estimated Trees"].iloc[0]
        )

        actions.append(
            f"🌲 Plant approximately {trees:,} trees."
        )

    if "Annual Carbon (ton CO₂)" in AFF_SUMMARY.columns:

        carbon = float(
            AFF_SUMMARY["Annual Carbon (ton CO₂)"].iloc[0]
        )

        actions.append(
            f"🌍 Expected annual CO₂ sequestration: "
            f"{carbon:,.1f} tons."
        )

    for action in actions:

        st.write(action)

    st.markdown("---")

    # ======================================================
    # AI RECOMMENDATION
    # ======================================================

    st.info(
        """
### 📋 ENVA Analytical Recommendation

The proposed afforestation program is identified as an analytical opportunity based on the available data.
Any implementation, species selection, or quantified carbon claim requires technical and field review.

---

### التوصية النهائية

تشير نتائج ENVA إلى أولوية تحليلية محتملة للتشجير؛ ويجب مراجعة الملاءمة الميدانية والجهات المختصة قبل التنفيذ.
"""
    )

    st.markdown("---")

    # ======================================================
    # CARBON SEQUESTRATION
    # ======================================================

    st.subheader("🌍 Estimated Carbon Sequestration")

    carbon_report = AFF_REPORT.get(
        "Carbon_Report",
        {}
    )

    if "Estimated Trees" in carbon_report:

        carbon_trees = carbon_report.get(
            "Estimated Trees"
        )

    else:

        carbon_trees = trees

    if "Estimated Annual Carbon (ton CO₂)" in carbon_report:

        annual_carbon = carbon_report.get(
            "Estimated Annual Carbon (ton CO₂)"
        )

    else:

        annual_carbon = carbon

    c1, c2 = st.columns(2)

    c1.metric(
        "🌱 Estimated Trees",
        f"{int(carbon_trees):,}"
    )

    c2.metric(
        "🌍 Annual CO₂",
        f"{float(annual_carbon):,.1f} ton"
    )

    st.markdown("---")

    # ======================================================
    # PROJECT IMPACT
    # ======================================================

    st.subheader("📈 Project Impact")

    if "Estimated Cost (EGP)" in AFF_SUMMARY.columns:

        cost = AFF_SUMMARY[
            "Estimated Cost (EGP)"
        ].iloc[0]

    else:

        cost = "N/A"

    if "Recommended Tree" in AFF_SUMMARY.columns:

        recommended_tree = str(
            AFF_SUMMARY["Recommended Tree"].iloc[0]
        )

    else:

        recommended_tree = "N/A"

    col1, col2 = st.columns(2)

    if isinstance(cost, (int, float)):

        col1.metric(
            "💰 Estimated Cost",
            f"{cost:,.0f} EGP"
        )

    else:

        col1.metric(
            "💰 Estimated Cost",
            cost
        )

    col2.metric(
        "🌳 Recommended Tree",
        recommended_tree
    )

    st.markdown("---")

    # ======================================================
    # PROJECT STATUS
    # ======================================================

    st.subheader("🚀 ENVA Decision Support")

    left, right = st.columns([2, 1])

    with left:

        st.markdown(
            """
### 🌍 ENVA Recommendation

Based on satellite-derived analysis and documented ENVA decision-support rules,
the proposed afforestation project is expected to:

- 🌳 Increase vegetation cover
- 🌍 Enhance carbon sequestration
- 💧 Protect soil resources
- 🌦 Improve climate resilience
- 🌱 Support sustainable environmental development

---

### توصية ENVA

تشير نتائج التحليل إلى أولوية محتملة لبرنامج التشجير المقترح
لتحسين الغطاء النباتي ودعم الإدارة البيئية المستدامة، مع ضرورة التحقق الميداني قبل التنفيذ.
"""
        )

    with right:

        st.metric(
            "Analysis Status",
            "ANALYTICAL"
        )

        st.metric(
            "Decision Status",
            "REVIEW REQUIRED"
        )

        st.metric(
            "Recommended Tree",
            str(recommended_tree)
        )

    st.markdown("---")

    # ======================================================
    # DOWNLOAD RESULTS
    # ======================================================

    st.subheader("📥 Download Results")

    col1, col2 = st.columns(2)

    with col1:

        csv = AFF_SUMMARY.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="⬇ Download Summary CSV",
            data=csv,
            file_name="ENVA_Afforestation_Summary.csv",
            mime="text/csv",
            key="download_afforestation_csv"
        )

    with col2:

        report = json.dumps(
            AFF_REPORT,
            indent=4,
            ensure_ascii=False
        )

        st.download_button(
            label="⬇ Download AI Report",
            data=report,
            file_name="ENVA_Afforestation_Report.json",
            mime="application/json",
            key="download_afforestation_report"
        )

    st.markdown("---")

    st.success(
        """
### ✅ Smart Afforestation Module Completed Successfully

The AI analysis has generated afforestation recommendations,
estimated environmental benefits,
and project implementation indicators.

تم إنشاء جميع مؤشرات مشروع التشجير الذكي بنجاح،
وأصبحت النتائج جاهزة للتنزيل والاستخدام.
"""
    )

    st.caption(
        "Generated automatically by ENVA Smart Afforestation Decision-Support Module."
    )

# ============================================================
# END OF PART 2
# ============================================================
# ==========================================================
# AI ENVIRONMENTAL REPORT
# ==========================================================

elif page == "🔮 Future Expansion":

    # ==================================================
    # PAGE INTRODUCTION
    # ==================================================

    st.title("🔮 ENVA Future Vision")

    st.subheader(
        "من نموذج أولي تجريبي مبسط إلى منظومة وطنية للذكاء البيئي"
    )

    st.markdown("""
    **From a Simple Prototype to a National Environmental
    Intelligence System**

    تمثل هذه الصفحة الرؤية المستقبلية لتطور ENVA.

    النسخة الحالية من المشروع هي نموذج أولي تجريبي مبسط
    لإثبات الفكرة الأساسية، بينما توضح هذه الصفحة كيف يمكن
    تطوير المنظومة مستقبلًا باستخدام تقنيات وبيانات أكثر تقدمًا.
    """)

    # ==================================================
    # PROTOTYPE NOTICE
    # ==================================================

    st.warning("""
    ⚠️ **Current Status — نموذج أولي تجريبي**

    النسخة الحالية من ENVA هي نموذج أولي مبسط جدًا
    تم تطويره لإثبات مفهوم دمج بيانات الأقمار الصناعية
    والتحليل البيئي والذكاء الاصطناعي ودعم اتخاذ القرار.

    **Future Vision**

    العناصر التالية تمثل مسار التطوير المستقبلي للمنظومة،
    وليست جميعها وظائف مطبقة بالكامل في النموذج الحالي.
    """)

    st.markdown("---")

    # ==================================================
    # ENVA — MORE THAN A PLATFORM
    # ==================================================

    st.header("🧠 ENVA — More Than a Platform")

    st.markdown("""
    **ENVA ليست مجرد منصة لعرض البيانات.**

    الرؤية المستقبلية هي تطوير ENVA إلى **منظومة ذكاء بيئي
    متكاملة** تستطيع جمع البيانات وتحليلها واكتشاف المخاطر
    والتنبؤ بها ثم تحويل نتائج التحليل إلى توصيات وقرارات
    قابلة للتنفيذ.
    """)

    st.markdown("### منظومة العمل المستقبلية")

    c1, c2, c3, c4 = st.columns(4)

    c1.info("""
    ### 🛰️ Data

    Satellite Data

    Environmental Data

    Ground Observations
    """)

    c2.info("""
    ### 🤖 Intelligence

    AI Models

    Computer Vision

    ENVA AI Agent
    """)

    c3.info("""
    ### 🚨 Prediction

    Risk Detection

    Forecasting

    Early Warning
    """)

    c4.info("""
    ### 🎯 Decision

    Recommendations

    Priority

    Government Action
    """)

    st.markdown("---")

    # ==================================================
    # FUTURE INTELLIGENCE CYCLE
    # ==================================================

    st.header("🔄 ENVA Future Intelligence Cycle")

    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#06261c,#0b3d2e,#06261c);
        padding:35px 20px;
        border-radius:25px;
        border:1px solid rgba(74,222,128,0.35);
        box-shadow:0 14px 40px rgba(0,0,0,0.30);
        text-align:center;
        margin:20px 0;
    ">

        <div style="
            font-size:30px;
            font-weight:900;
            color:#bbf7d0;
            margin-bottom:25px;
        ">
            🌍 ENVA Environmental Intelligence Cycle
        </div>

        <div style="
            display:flex;
            justify-content:center;
            align-items:center;
            gap:10px;
            flex-wrap:wrap;
        ">

            <div style="
                padding:18px 20px;
                border-radius:16px;
                background:rgba(14,116,144,0.30);
                color:#e0f2fe;
                font-weight:800;
            ">
                🛰️ Data
                <br>
                <small>البيانات</small>
            </div>

            <div style="font-size:25px;color:#86efac;">→</div>

            <div style="
                padding:18px 20px;
                border-radius:16px;
                background:rgba(37,99,235,0.25);
                color:#dbeafe;
                font-weight:800;
            ">
                🤖 AI Agent
                <br>
                <small>الوكيل الذكي</small>
            </div>

            <div style="font-size:25px;color:#86efac;">→</div>

            <div style="
                padding:18px 20px;
                border-radius:16px;
                background:rgba(124,58,237,0.25);
                color:#ede9fe;
                font-weight:800;
            ">
                🧠 Intelligence
                <br>
                <small>الذكاء</small>
            </div>

            <div style="font-size:25px;color:#86efac;">→</div>

            <div style="
                padding:18px 20px;
                border-radius:16px;
                background:rgba(234,88,12,0.25);
                color:#ffedd5;
                font-weight:800;
            ">
                🚨 Prediction
                <br>
                <small>التنبؤ</small>
            </div>

            <div style="font-size:25px;color:#86efac;">→</div>

            <div style="
                padding:18px 20px;
                border-radius:16px;
                background:rgba(22,163,74,0.25);
                color:#dcfce7;
                font-weight:800;
            ">
                🎯 Decision
                <br>
                <small>القرار</small>
            </div>

        </div>

    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ==================================================
    # FUTURE ECOSYSTEM
    # ==================================================

    st.header("🌐 ENVA Future Technology Ecosystem")

    st.markdown("""
    في المستقبل يمكن أن تعمل ENVA كمنظومة مترابطة
    تجمع عدة مصادر وتقنيات بدل الاعتماد على مصدر واحد للبيانات.
    """)

    f1, f2, f3 = st.columns(3)

    f1.info("""
    ### 🛰️ Satellite Intelligence

    صور أقمار صناعية عالية الدقة

    Radar + Optical

    Time-Series Monitoring

    Change Detection
    """)

    f2.info("""
    ### 📡 IoT Sensors

    Air Quality

    Temperature

    Humidity

    Water Quality

    Soil Moisture
    """)

    f3.info("""
    ### 🚁 Drone Monitoring

    Field Verification

    Agricultural Monitoring

    Fire Verification

    Urban Monitoring
    """)

    f4, f5, f6 = st.columns(3)

    f4.info("""
    ### 🤖 Advanced AI

    Deep Learning

    Computer Vision

    Predictive Analytics

    NLP
    """)

    f5.info("""
    ### 🏛️ Government GIS

    GIS Integration

    Authority Coordination

    Decision Support

    Action Tracking
    """)

    f6.info("""
    ### 📱 ENVA Mobile

    Alerts

    Field Reports

    Images

    Verification

    Team Communication
    """)

    # ==================================================
    # 3. ADVANCED SATELLITE INTELLIGENCE
    # ==================================================

    st.markdown("---")

    st.header("🛰️ Advanced Satellite Intelligence")

    st.subheader("الذكاء الفضائي المتقدم")

    st.write(
        "Future ENVA can evolve from basic satellite analysis "
        "into a continuous multi-source environmental intelligence system."
    )

    st.write(
        "يمكن تطوير ENVA مستقبلًا من تحليل صور الأقمار الصناعية "
        "إلى منظومة ذكاء فضائي مستمرة تعتمد على مصادر متعددة "
        "وتحليل التغيرات البيئية عبر الزمن."
    )

    # ==================================================
    # SATELLITE VISUAL
    # ==================================================

    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#061b2b,#0b3550,#071827);
        padding:35px 20px;
        border-radius:25px;
        border:1px solid rgba(56,189,248,0.35);
        box-shadow:0 14px 40px rgba(0,0,0,0.35);
        text-align:center;
        margin:20px 0;
    ">

        <div style="
            font-size:30px;
            font-weight:900;
            color:#bae6fd;
            margin-bottom:25px;
        ">
            🛰️ Satellite Intelligence
        </div>

        <div style="
            display:flex;
            justify-content:center;
            align-items:center;
            gap:12px;
            flex-wrap:wrap;
        ">

            <div style="
                padding:20px;
                border-radius:18px;
                background:rgba(14,116,144,0.30);
                color:#e0f2fe;
                font-weight:800;
            ">
                🛰️ Satellite
                <br>
                <small>بيانات فضائية</small>
            </div>

            <div style="font-size:28px;color:#7dd3fc;">→</div>

            <div style="
                padding:20px;
                border-radius:18px;
                background:rgba(37,99,235,0.25);
                color:#dbeafe;
                font-weight:800;
            ">
                🔍 Change Detection
                <br>
                <small>اكتشاف التغير</small>
            </div>

            <div style="font-size:28px;color:#7dd3fc;">→</div>

            <div style="
                padding:20px;
                border-radius:18px;
                background:rgba(124,58,237,0.25);
                color:#ede9fe;
                font-weight:800;
            ">
                🧠 Intelligence
                <br>
                <small>ذكاء بيئي</small>
            </div>

        </div>

    </div>
    """, unsafe_allow_html=True)

    s1, s2 = st.columns(2)

    with s1:

        st.markdown("### 🛰️ High-Resolution Satellite Data")

        st.write(
            "استخدام صور أقمار صناعية أعلى دقة للحصول على "
            "تفاصيل مكانية أكثر دقة."
        )

        st.markdown("""
        - Sentinel
        - Landsat
        - Commercial High-Resolution Imagery
        """)

    with s2:

        st.markdown("### 🔄 Continuous Monitoring")

        st.write(
            "متابعة التغيرات البيئية بصورة دورية بدل الاعتماد "
            "على تحليل صورة منفردة."
        )

        st.markdown("""
        - Historical Comparison
        - Time-Series Analysis
        - Change Detection
        """)

    st.markdown("---")

    st.markdown("### 🌍 Multi-Source Satellite Intelligence")

    m1, m2, m3 = st.columns(3)

    m1.info("""
    🛰️ **Optical Imagery**

    تحليل الغطاء النباتي،
    استخدامات الأراضي،
    والمناطق العمرانية.
    """)

    m2.info("""
    📡 **Radar Imagery**

    دعم الرصد في الظروف الجوية
    التي تحد من الاستفادة من
    الصور البصرية.
    """)

    m3.info("""
    ⏱️ **Time-Series Data**

    مقارنة التغيرات البيئية
    عبر فترات زمنية متعددة.
    """)

    st.markdown("---")

    st.markdown("### 🔄 Future Satellite Analysis Workflow")

    flow1, flow2, flow3, flow4 = st.columns(4)

    flow1.success("🛰️ Acquire\n\nجمع البيانات الفضائية")
    flow2.success("🧹 Process\n\nمعالجة وتنقية البيانات")
    flow3.success("🔍 Detect\n\nاكتشاف التغيرات")
    flow4.success("🧠 Understand\n\nتحويلها إلى ذكاء بيئي")

    st.markdown("---")

    st.markdown("### 🚀 Future Capabilities")

    cap1, cap2 = st.columns(2)

    cap1.markdown("""
    **🌳 Environmental Change**

    - Vegetation Change
    - Land-Cover Change
    - Deforestation
    - Land Degradation
    """)

    cap2.markdown("""
    **🏙️ Land & Urban Change**

    - Urban Expansion
    - Agricultural Encroachment
    - Water-Bodies Change
    - Environmental Hotspots
    """)

    st.success("""
    🎯 **Future Value**

    الانتقال من مجرد عرض صور الأقمار الصناعية
    إلى فهم التغيرات البيئية واكتشافها بصورة مستمرة،
    لتصبح البيانات الفضائية أحد المصادر الأساسية
    التي يعتمد عليها ENVA في الإنذار المبكر ودعم القرار.
    """)

    # ==================================================
    # 4. ADVANCED AI & PREDICTIVE ANALYTICS
    # ==================================================

    st.markdown("---")

    st.header("🤖 Advanced AI & Predictive Analytics")

    st.subheader("الذكاء الاصطناعي والتحليلات التنبؤية")

    st.write(
        "The future ENVA system is designed to move beyond "
        "describing environmental conditions toward predicting "
        "future risks and supporting proactive decisions."
    )

    st.write(
        "الرؤية المستقبلية لـ ENVA هي الانتقال من مجرد وصف "
        "الحالة البيئية إلى تحليلها والتنبؤ بالمخاطر المستقبلية "
        "ودعم اتخاذ إجراءات استباقية."
    )

    # ==================================================
    # AI VISUAL
    # ==================================================

    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#071827,#102b3d,#071827);
        padding:32px 22px;
        border-radius:24px;
        border:1px solid rgba(56,189,248,0.30);
        box-shadow:0 12px 35px rgba(0,0,0,0.30);
        text-align:center;
        margin:20px 0;
    ">

        <div style="
            font-size:30px;
            font-weight:900;
            color:#bae6fd;
            margin-bottom:8px;
        ">
            🧠 ENVA AI Intelligence Engine
        </div>

        <div style="
            font-size:16px;
            color:#cbd5e1;
            margin-bottom:25px;
        ">
            العقل الذكي للتحليل والتنبؤ واتخاذ القرار
        </div>

        <div style="
            display:flex;
            justify-content:center;
            align-items:center;
            gap:12px;
            flex-wrap:wrap;
        ">

            <div style="padding:18px 22px;border-radius:16px;background:rgba(14,116,144,0.30);color:#e0f2fe;font-weight:800;">
                🛰️ Data
                <br><small>البيانات</small>
            </div>

            <div style="font-size:25px;color:#86efac;">→</div>

            <div style="padding:18px 22px;border-radius:16px;background:rgba(37,99,235,0.25);color:#dbeafe;font-weight:800;">
                🤖 AI Models
                <br><small>نماذج الذكاء الاصطناعي</small>
            </div>

            <div style="font-size:25px;color:#86efac;">→</div>

            <div style="padding:18px 22px;border-radius:16px;background:rgba(124,58,237,0.25);color:#ede9fe;font-weight:800;">
                🔮 Prediction
                <br><small>التنبؤ</small>
            </div>

            <div style="font-size:25px;color:#86efac;">→</div>

            <div style="padding:18px 22px;border-radius:16px;background:rgba(22,163,74,0.25);color:#dcfce7;font-weight:800;">
                🎯 Decision
                <br><small>القرار</small>
            </div>

        </div>

    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🧠 Future AI Capabilities")

    ai1, ai2, ai3 = st.columns(3)

    ai1.info("""
    🔍 **Computer Vision**

    تحليل صور الأقمار الصناعية
    واكتشاف الأنماط والتغيرات البيئية.
    """)

    ai2.info("""
    📈 **Predictive Analytics**

    تحليل السلاسل الزمنية
    والتنبؤ بالاتجاهات والمخاطر.
    """)

    ai3.info("""
    🧠 **Deep Learning**

    نماذج أكثر تقدمًا لفهم
    الأنماط البيئية المعقدة.
    """)

    st.markdown("---")

    st.markdown("### 🔄 ENVA AI Intelligence Cycle")

    p1, p2, p3, p4 = st.columns(4)

    p1.success("🔍 Detect\n\nاكتشاف التغير أو الخطر")
    p2.success("🧠 Analyze\n\nتحليل السبب والخصائص")
    p3.success("🔮 Predict\n\nتوقع التطورات المستقبلية")
    p4.success("🎯 Recommend\n\nاقتراح الإجراء المناسب")

    st.markdown("---")

    st.markdown("### 🔮 Future Prediction Areas")

    r1, r2 = st.columns(2)

    r1.markdown("""
    **🌱 Environmental Prediction**

    - Vegetation Trends
    - Drought Risk
    - Land Degradation
    - Water Stress
    - Agricultural Change
    """)

    r2.markdown("""
    **🚨 Risk Prediction**

    - Fire Probability
    - Flood Risk
    - Heatwave Risk
    - Pollution Risk
    - Environmental Hotspots
    """)

    st.markdown("---")

    st.header("🤖 ENVA AI Agent")

    st.write(
        "في الرؤية المستقبلية، يمكن تطوير ENVA AI Agent "
        "ليعمل كروبوت برمجي ذكي قادر على تشغيل عمليات التحليل "
        "وتجميع النتائج ومقارنتها ثم تقديم ملخص وتوصية قابلة للفهم."
    )

    agent1, agent2, agent3 = st.columns(3)

    agent1.markdown("""
    ### 📥 Observe

    Collect environmental information

    جمع البيانات والمعلومات البيئية
    """)

    agent2.markdown("""
    ### 🧠 Reason

    Analyze patterns and risks

    تحليل الأنماط والمخاطر
    """)

    agent3.markdown("""
    ### 🎯 Act

    Recommend a response

    اقتراح الإجراء المناسب
    """)

    st.success("""
    🚀 **Future AI Vision**

    الهدف المستقبلي ليس أن تقوم ENVA بعرض البيانات فقط،
    بل أن تتحول إلى منظومة ذكية تستطيع:

    **Detect → Analyze → Predict → Recommend**

    أي:

    **اكتشاف → تحليل → تنبؤ → توصية**

    بما يساعد الجهات المختصة على الانتقال من
    **Reactive Response** إلى **Proactive Environmental Management**.
    """)

    # ==================================================
    # 5. NATIONAL EARLY WARNING SYSTEM
    # ==================================================

    st.markdown("---")

    st.header("🚨 National Early Warning System")

    st.subheader("منظومة الإنذار البيئي المبكر")

    st.write(
        "The future ENVA system can evolve from environmental "
        "monitoring into a predictive early warning system "
        "that detects emerging risks before they become critical."
    )

    st.write(
        "يمكن تطوير ENVA مستقبلًا من منظومة للرصد البيئي "
        "إلى نظام إنذار مبكر قادر على اكتشاف المخاطر المتوقعة "
        "والتنبيه إليها قبل تفاقمها."
    )

    # ==================================================
    # EARLY WARNING VISUAL
    # ==================================================

    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#07151f,#132b35,#07151f);
        padding:32px 20px;
        border-radius:25px;
        border:1px solid rgba(248,113,113,0.30);
        box-shadow:0 14px 40px rgba(0,0,0,0.35);
        text-align:center;
        margin:20px 0;
    ">

        <div style="
            font-size:30px;
            font-weight:900;
            color:#fecaca;
            margin-bottom:25px;
        ">
            🚨 ENVA Early Warning Engine
        </div>

        <div style="
            display:flex;
            justify-content:center;
            align-items:center;
            gap:10px;
            flex-wrap:wrap;
        ">

            <div style="padding:18px 20px;border-radius:16px;background:rgba(14,116,144,0.28);color:#e0f2fe;font-weight:800;">
                🛰️ Monitor
                <br><small>رصد</small>
            </div>

            <div style="font-size:25px;color:#86efac;">→</div>

            <div style="padding:18px 20px;border-radius:16px;background:rgba(124,58,237,0.25);color:#ede9fe;font-weight:800;">
                🔍 Detect
                <br><small>اكتشاف</small>
            </div>

            <div style="font-size:25px;color:#86efac;">→</div>

            <div style="padding:18px 20px;border-radius:16px;background:rgba(234,88,12,0.25);color:#ffedd5;font-weight:800;">
                🔮 Forecast
                <br><small>توقع</small>
            </div>

            <div style="font-size:25px;color:#86efac;">→</div>

            <div style="padding:18px 20px;border-radius:16px;background:rgba(220,38,38,0.25);color:#fee2e2;font-weight:800;">
                🚨 Alert
                <br><small>إنذار</small>
            </div>

            <div style="font-size:25px;color:#86efac;">→</div>

            <div style="padding:18px 20px;border-radius:16px;background:rgba(22,163,74,0.25);color:#dcfce7;font-weight:800;">
                🎯 Respond
                <br><small>استجابة</small>
            </div>

        </div>

    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚠️ Future Environmental Risk Categories")

    r1, r2, r3 = st.columns(3)

    r1.error("🔥 **Fire Risk**\n\nالتنبؤ باحتمالات الحرائق ومناطق الخطر.")
    r2.warning("🌵 **Drought Risk**\n\nرصد مؤشرات الجفاف والإجهاد المائي.")
    r3.warning("🌊 **Flood Risk**\n\nالتنبؤ بالمناطق المعرضة لمخاطر السيول والفيضانات.")

    r4, r5, r6 = st.columns(3)

    r4.warning("🌡️ **Heatwave Risk**\n\nاكتشاف والتنبؤ بموجات الحرارة الشديدة.")
    r5.error("🌫️ **Pollution Risk**\n\nرصد المناطق التي قد تواجه ارتفاعًا في مستويات التلوث.")
    r6.info("🌪️ **Extreme Weather**\n\nمتابعة مؤشرات الظواهر الجوية المتطرفة.")

    st.markdown("---")

    st.header("🔮 Risk Forecast")

    st.write(
        "في المستقبل يمكن للمنظومة إنتاج توقعات احتمالية "
        "للمخاطر البيئية خلال الأيام القادمة."
    )

    f1, f2, f3, f4 = st.columns(4)

    f1.metric("🔥 Fire Probability", "—", "Future Model")
    f2.metric("🌵 Drought Probability", "—", "Future Model")
    f3.metric("🌊 Flood Probability", "—", "Future Model")
    f4.metric("🌡️ Heatwave Probability", "—", "Future Model")

    st.caption(
        "Forecast values are part of the future system vision "
        "and are not operational predictions in the current prototype."
    )

    st.markdown("---")

    st.header("🎯 Risk Prioritization")

    p1, p2, p3 = st.columns(3)

    p1.info("🟢 **Low Risk**\n\nRoutine monitoring")
    p2.warning("🟡 **Moderate Risk**\n\nIncrease monitoring")
    p3.error("🔴 **Critical Risk**\n\nImmediate response")

    st.markdown("---")

    st.header("🤖 AI Recommendation")

    st.write(
        "بعد اكتشاف الخطر، يمكن لـ ENVA AI Agent تحليل "
        "مستوى الخطورة وتحديد الأولوية واقتراح الإجراء المناسب."
    )

    a1, a2, a3 = st.columns(3)

    a1.markdown("""
    ### 🔎 Risk Assessment

    **ما الذي يحدث؟**

    تحديد نوع الخطر وموقعه ومدى انتشاره.
    """)

    a2.markdown("""
    ### 🎯 Priority

    **ما مدى خطورته؟**

    تحديد مستوى الأولوية ودرجة الاستجابة المطلوبة.
    """)

    a3.markdown("""
    ### 🏛️ Recommended Action

    **ماذا يجب أن نفعل؟**

    اقتراح الإجراء المناسب للجهة المختصة.
    """)

    st.success("""
    🚨 **From Reactive to Proactive**

    الهدف المستقبلي لمنظومة Early Warning هو الانتقال من:

    **Detecting Problems After They Occur**

    إلى:

    **Predicting Risks Before They Escalate**

    أي الانتقال من الاستجابة بعد وقوع المشكلة
    إلى الإدارة الاستباقية للمخاطر البيئية.
    """)

    # ==================================================
    # 6. IoT ENVIRONMENTAL SENSORS
    # ==================================================

    st.markdown("---")

    st.header("📡 IoT Environmental Sensors")

    st.subheader("الاستشعار البيئي الميداني")

    st.write(
        "Future ENVA can integrate real-time ground sensor data "
        "with satellite observations and AI models to create a "
        "continuous multi-source environmental monitoring system."
    )

    st.write(
        "يمكن ربط ENVA مستقبلًا بأجهزة استشعار ميدانية "
        "ترسل بيانات بيئية بصورة مستمرة، ليتم دمجها مع "
        "بيانات الأقمار الصناعية ونماذج الذكاء الاصطناعي."
    )

    # ==================================================
    # IOT VISUAL
    # ==================================================

    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#061923,#0b3034,#071923);
        padding:35px 20px;
        border-radius:25px;
        border:1px solid rgba(45,212,191,0.35);
        box-shadow:0 14px 40px rgba(0,0,0,0.35);
        text-align:center;
        margin:20px 0;
    ">

        <div style="
            font-size:30px;
            font-weight:900;
            color:#99f6e4;
            margin-bottom:25px;
        ">
            📡 ENVA Multi-Source Environmental Intelligence
        </div>

        <div style="
            display:flex;
            justify-content:center;
            align-items:center;
            gap:12px;
            flex-wrap:wrap;
        ">

            <div style="padding:20px 24px;border-radius:18px;background:rgba(14,116,144,0.28);border:1px solid rgba(56,189,248,0.40);color:#e0f2fe;font-weight:800;">
                🛰️ Satellite Data
                <br><small>بيانات الأقمار الصناعية</small>
            </div>

            <div style="font-size:25px;color:#5eead4;">+</div>

            <div style="padding:20px 24px;border-radius:18px;background:rgba(13,148,136,0.25);border:1px solid rgba(45,212,191,0.45);color:#ccfbf1;font-weight:800;">
                📡 IoT Sensors
                <br><small>أجهزة الاستشعار</small>
            </div>

            <div style="font-size:25px;color:#5eead4;">+</div>

            <div style="padding:20px 24px;border-radius:18px;background:rgba(22,163,74,0.25);border:1px solid rgba(74,222,128,0.45);color:#dcfce7;font-weight:800;">
                🤖 AI
                <br><small>الذكاء الاصطناعي</small>
            </div>

        </div>

        <div style="
            font-size:30px;
            color:#5eead4;
            margin:18px 0;
        ">
            ↓
        </div>

        <div style="
            display:inline-block;
            padding:18px 32px;
            border-radius:18px;
            background:rgba(124,58,237,0.22);
            border:1px solid rgba(167,139,250,0.45);
            color:#ede9fe;
            font-size:20px;
            font-weight:900;
        ">
            🌍 Integrated Environmental Intelligence
            <br><small>ذكاء بيئي متكامل</small>
        </div>

    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Future Environmental Sensor Network")

    s1, s2, s3 = st.columns(3)

    s1.info("""
    🌫️ **Air Quality**

    PM2.5
    PM10
    CO₂
    NO₂
    Other pollutants
    """)

    s2.info("""
    🌡️ **Climate Sensors**

    Temperature
    Humidity
    Wind Speed
    Solar Radiation
    """)

    s3.info("""
    💧 **Water & Soil**

    Water Quality
    Water Level
    Soil Moisture
    Soil Conditions
    """)

    st.markdown("---")

    st.markdown("### 🔄 Real-Time Environmental Data Flow")

    d1, d2, d3, d4 = st.columns(4)

    d1.success("📡 Sensors\n\nCollect")
    d2.success("☁️ Data Layer\n\nTransmit")
    d3.success("🤖 ENVA AI\n\nAnalyze")
    d4.success("🚨 Alert\n\nRespond")

    st.markdown("---")

    st.header("🎯 Future Sensor Use Cases")

    u1, u2 = st.columns(2)

    u1.markdown("""
    ### 🌫️ Air Pollution Monitoring

    يمكن للحساسات الميدانية دعم ENVA في:

    - اكتشاف ارتفاع مستويات الملوثات.
    - مقارنة القياسات الأرضية بالبيانات الفضائية.
    - تحديد المناطق الأكثر تعرضًا للتلوث.
    - دعم منظومة Early Warning.
    """)

    u2.markdown("""
    ### 💧 Water & Soil Monitoring

    يمكن استخدام البيانات الميدانية في:

    - متابعة جودة المياه.
    - قياس رطوبة التربة.
    - دعم تحليل الجفاف.
    - تحسين قرارات إدارة الموارد الطبيعية.
    """)

    st.markdown("---")

    st.header("🛰️ + 📡 Satellite–Ground Verification")

    st.write(
        "من أهم الإضافات المستقبلية ربط البيانات الفضائية "
        "بالقياسات الميدانية للتحقق من نتائج التحليل وتحسين "
        "موثوقية النماذج."
    )

    v1, v2, v3 = st.columns(3)

    v1.markdown("""
    **🛰️ Satellite Observation**

    What is detected from space?
    """)

    v2.markdown("""
    **📡 Ground Measurement**

    What is measured on site?
    """)

    v3.markdown("""
    **🧠 AI Validation**

    Do both sources agree?
    """)

    st.success("""
    🌍 **Future Value**

    دمج الأقمار الصناعية مع أجهزة الاستشعار الميدانية
    سيجعل ENVA قادرة على بناء صورة بيئية أكثر شمولًا
    من خلال الجمع بين:

    **Satellite Data + Ground Sensors + AI**

    بما يدعم تحسين دقة الرصد والإنذار المبكر
    والتحليلات البيئية المستقبلية.
    """)

    # ==================================================
    # FUTURE INTELLIGENCE FINAL VISION
    # ==================================================

    st.markdown("---")

    st.header("🌍 ENVA — National Environmental Intelligence")

    st.markdown("""
    ### **From Data → Intelligence → Prediction → Warning → Decision → Action**
    """)

    st.markdown("""
    **ENVA aims to evolve from a simplified experimental
    prototype into an integrated national environmental
    intelligence and decision-support system.**

    تهدف ENVA مستقبلًا إلى التطور من نموذج أولي تجريبي
    مبسط إلى منظومة وطنية متكاملة للذكاء البيئي ودعم
    اتخاذ القرار، تجمع بين بيانات الأقمار الصناعية،
    والذكاء الاصطناعي، والاستشعار الميداني، والتحليلات
    التنبؤية، والإنذار المبكر.
    """)

    st.success(
        "🌱 ENVA Future Vision — Building Environmental Intelligence for Better Decisions"
    )

    st.caption(
        "Generated automatically by ENVA Future Vision."
    )
elif page == "🚜 Agricultural Encroachments":

    st.title("🌾 Agricultural Encroachment Monitoring")

    st.subheader(
        "رصد التعديات والتغيرات على الأراضي الزراعية"
    )

    st.markdown("""
    يهدف هذا الجزء من ENVA إلى رصد التغيرات التي تحدث
    على الأراضي الزراعية من خلال مقارنة صور الأقمار
    الصناعية في فترتين زمنيتين مختلفتين.

    **Before Image → After Image → Change Detection**
    """)

    st.warning("""
    ⚠️ **نموذج أولي تجريبي**

    النتائج الحالية تمثل كشفًا أوليًا للتغيرات بين الصور،
    ولا تعتبر إثباتًا نهائيًا لوجود تعديات.
    """)

    st.markdown("---")


    # ==================================================
    # PATHS
    # ==================================================

    from pathlib import Path
    import numpy as np
    from PIL import Image

    ENCROACHMENT_DIR = Path(
        "data/agricultural_encroachment"
    )

    ENCROACHMENT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    BEFORE_IMAGE = (
        ENCROACHMENT_DIR / "before.png"
    )

    AFTER_IMAGE = (
        ENCROACHMENT_DIR / "after.png"
    )


    # ==================================================
    # 1. BEFORE / AFTER SATELLITE IMAGES
    # ==================================================

    st.header(
        "🛰️ Satellite Image Comparison"
    )

    st.write(
        "تبدأ عملية اكتشاف التغير من مقارنة صور الأقمار "
        "الصناعية للمنطقة نفسها في فترتين زمنيتين مختلفتين."
    )

    before_col, after_col = st.columns(2)


    # --------------------------------------------------
    # BEFORE
    # --------------------------------------------------

    with before_col:

        st.markdown(
            "### 🛰️ Before — الصورة السابقة"
        )

        if BEFORE_IMAGE.exists():

            before_preview = Image.open(
                BEFORE_IMAGE
            ).convert("RGB")

            st.image(
                before_preview,
                use_container_width=True,
                caption="Previous Satellite Image"
            )

        else:

            st.info("""
            🛰️ **Before Image**

            لم يتم إضافة الصورة السابقة بعد.

            المسار المطلوب:

            `data/agricultural_encroachment/before.png`
            """)


    # --------------------------------------------------
    # AFTER
    # --------------------------------------------------

    with after_col:

        st.markdown(
            "### 🛰️ After — الصورة الحديثة"
        )

        if AFTER_IMAGE.exists():

            after_preview = Image.open(
                AFTER_IMAGE
            ).convert("RGB")

            st.image(
                after_preview,
                use_container_width=True,
                caption="Recent Satellite Image"
            )

        else:

            st.info("""
            🛰️ **After Image**

            لم يتم إضافة الصورة الحديثة بعد.

            المسار المطلوب:

            `data/agricultural_encroachment/after.png`
            """)


    st.markdown("---")


    # ==================================================
    # 2. CHANGE DETECTION
    # ==================================================

    st.header(
        "🔄 Change Detection"
    )

    st.write(
        "يتم هنا إجراء مقارنة أولية بين صورتي Before وAfter "
        "لاكتشاف المناطق التي يظهر بها اختلاف مكاني."
    )


    # --------------------------------------------------
    # Check images
    # --------------------------------------------------

    if BEFORE_IMAGE.exists() and AFTER_IMAGE.exists():

        try:

            # ==========================================
            # Load Images
            # ==========================================

            before = Image.open(
                BEFORE_IMAGE
            ).convert("RGB")

            after = Image.open(
                AFTER_IMAGE
            ).convert("RGB")


            # ==========================================
            # Match Dimensions
            # ==========================================

            if before.size != after.size:

                st.info(
                    "ℹ️ أبعاد الصورتين مختلفة، "
                    "سيتم توحيد أبعاد الصورة الحديثة."
                )

                after = after.resize(
                    before.size
                )


            # ==========================================
            # Convert to NumPy
            # ==========================================

            before_array = np.asarray(
                before,
                dtype=np.float32
            )

            after_array = np.asarray(
                after,
                dtype=np.float32
            )


            # ==========================================
            # Pixel Difference
            # ==========================================

            difference = np.mean(
                np.abs(
                    before_array - after_array
                ),
                axis=2
            )


            # ==========================================
            # Threshold
            # ==========================================

            threshold = st.slider(
                "🔧 Change Detection Threshold",
                min_value=5,
                max_value=100,
                value=35,
                step=5,
                help=(
                    "القيم الأقل تكشف تغيرات أكثر، "
                    "والقيم الأعلى تجعل الكشف أكثر تحفظًا."
                )
            )


            # ==========================================
            # Changed Pixels
            # ==========================================

            changed_pixels = (
                difference >= threshold
            )


            # ==========================================
            # Percentage
            # ==========================================

            changed_percentage = (
                changed_pixels.mean() * 100
            )


            # ==========================================
            # Normalize Difference Map
            # ==========================================

            max_difference = (
                difference.max()
            )

            if max_difference > 0:

                change_map = (
                    difference
                    / max_difference
                    * 255
                ).astype(np.uint8)

            else:

                change_map = np.zeros_like(
                    difference,
                    dtype=np.uint8
                )


            # ==========================================
            # Change Mask
            # ==========================================

            change_mask = (
                changed_pixels.astype(
                    np.uint8
                ) * 255
            )


            # ==================================================
            # DISPLAY BEFORE / AFTER
            # ==================================================

            st.markdown(
                "### 🛰️ Before / After"
            )

            result_col1, result_col2 = st.columns(2)

            with result_col1:

                st.image(
                    before,
                    caption="Before",
                    use_container_width=True
                )

            with result_col2:

                st.image(
                    after,
                    caption="After",
                    use_container_width=True
                )


            # ==================================================
            # CHANGE MAP
            # ==================================================

            st.markdown(
                "### 🗺️ Detected Change Map"
            )

            st.image(
                change_map,
                caption=(
                    "Pixel Difference — "
                    "Higher intensity indicates greater change"
                ),
                use_container_width=True
            )


            # ==================================================
            # SIGNIFICANT CHANGE MASK
            # ==================================================

            st.markdown(
                "### 🔍 Significant Change Areas"
            )

            st.image(
                change_mask,
                caption=(
                    "Thresholded Change Mask"
                ),
                use_container_width=True
            )


            # ==================================================
            # STATISTICS
            # ==================================================

            st.markdown("---")

            m1, m2, m3 = st.columns(3)

            with m1:

                st.metric(
                    "Detected Change",
                    f"{changed_percentage:.2f}%"
                )

            with m2:

                st.metric(
                    "Changed Pixels",
                    f"{int(changed_pixels.sum()):,}"
                )

            with m3:

                st.metric(
                    "Threshold",
                    threshold
                )


            # ==================================================
            # INTERPRETATION
            # ==================================================

            if changed_percentage < 1:

                st.success(
                    f"""
                    🟢 **Low Detected Change**

                    نسبة البكسلات التي أظهرت تغيرًا:

                    **{changed_percentage:.2f}%**
                    """
                )

            elif changed_percentage < 10:

                st.info(
                    f"""
                    🔵 **Moderate Detected Change**

                    نسبة البكسلات التي أظهرت تغيرًا:

                    **{changed_percentage:.2f}%**
                    """
                )

            else:

                st.warning(
                    f"""
                    🟡 **High Detected Change**

                    نسبة البكسلات التي أظهرت تغيرًا:

                    **{changed_percentage:.2f}%**

                    هذه النسبة لا تعني تلقائيًا وجود تعديات.
                    """
                )


            # ==================================================
            # SCIENTIFIC WARNING
            # ==================================================

            st.markdown("---")

            st.warning("""
            ⚠️ **Important Scientific Interpretation**

            اختلاف البكسلات بين الصورتين لا يعني تلقائيًا
            وجود تعدٍ على الأراضي الزراعية.

            يمكن أن ينتج التغير عن:

            - اختلاف الإضاءة.
            - اختلاف الموسم الزراعي.
            - تغير الغطاء النباتي.
            - الحصاد أو الزراعة الجديدة.
            - اختلاف الرطوبة.
            - السحب أو الظلال.
            - اختلاف جودة أو ظروف التصوير.

            لذلك تعتبر هذه النتيجة:

            **Preliminary Change Detection**

            وليست:

            **Confirmed Agricultural Encroachment**
            """)


            # ==================================================
            # SAVE RESULTS FOR PART 2
            # ==================================================

            st.session_state[
                "encroachment_before"
            ] = before

            st.session_state[
                "encroachment_after"
            ] = after

            st.session_state[
                "changed_pixels"
            ] = changed_pixels

            st.session_state[
                "change_map"
            ] = change_map

            st.session_state[
                "change_mask"
            ] = change_mask

            st.session_state[
                "change_percentage"
            ] = changed_percentage

            st.session_state[
                "change_threshold"
            ] = threshold


            st.success(
                "✅ Change Detection completed successfully."
            )


        except Exception as e:

            st.error(
                f"❌ Unable to perform Change Detection: {e}"
            )

            st.exception(e)


    else:

        st.info("""
        🛰️ **Change Detection is waiting for imagery**

        أضيفي صورتَي Before وAfter أولًا:

        `data/agricultural_encroachment/before.png`

        `data/agricultural_encroachment/after.png`
        """)


    # ==================================================
    # PART 1 END
    # ==================================================

    st.markdown("---")

    st.caption(
        "ENVA — Agricultural Encroachment Monitoring | Part 1"
    )

# ======================================================
# EARLY WARNING (data-driven — built from real indicator risk classes)
# ======================================================

elif page == "🚨 Early Warning":

    st.title("🚨 Early Warning System")
    st.subheader("نظام الإنذار المبكر البيئي")

    st.markdown(
        """
يفحص هذا النظام نتائج المؤشرات البيئية السبعة تلقائيًا، ويصدر تنبيهات لأي
منطقة تجاوزت عتبة الخطورة المحددة لكل مؤشر.

This system automatically screens the seven environmental indicators and
raises alerts for any risk/pressure class exceeding its defined threshold.
"""
    )

    st.markdown("---")

    if not INDICATORS_AVAILABLE:
        st.info(
            "ℹ️ No indicator data available yet — early warning screening "
            "will activate automatically once indicator data is exported "
            "from the ENVA Colab notebook."
        )
        st.stop()

    ALERT_THRESHOLD_PERCENT = 15.0
    HIGH_RISK_LABELS = {"high", "critical", "very_high", "high_pressure", "very_high_pressure"}

    alerts = []

    for code in INDICATOR_ORDER:
        meta = INDICATOR_INFO[code]
        d = INDICATORS[code]["data"]
        class_key = meta.get("class_key")
        classes = d.get(class_key) if class_key else None
        if not isinstance(classes, dict):
            continue

        for label, values in classes.items():
            if not isinstance(values, dict) or label.lower() not in HIGH_RISK_LABELS:
                continue
            percent = values.get("percent_of_aoi", values.get("percent_of_vegetation", 0)) or 0
            if percent >= ALERT_THRESHOLD_PERCENT:
                alerts.append({
                    "indicator": code, "icon": meta["icon"], "name": meta["title"],
                    "class": label, "percent": percent,
                    "area_km2": values.get("area_km2", 0),
                })

    if alerts:
        st.error(f"🚨 {len(alerts)} active alert(s) detected")

        for alert in sorted(alerts, key=lambda a: a["percent"], reverse=True):
            st.markdown(
                f"**{alert['icon']} {alert['indicator']} — {alert['name']}**"
                f" &nbsp;|&nbsp; Class: `{alert['class']}`"
                f" &nbsp;|&nbsp; Affected: **{alert['percent']:.1f}%**"
                f" ({alert['area_km2']:.3f} km²)"
            )
            st.progress(min(alert["percent"] / 100, 1.0))
            st.markdown("---")
    else:
        st.success(f"✅ No indicator class currently exceeds the {ALERT_THRESHOLD_PERCENT:.0f}% alert threshold.")

    st.markdown("---")
    st.caption(
        f"Alert threshold: {ALERT_THRESHOLD_PERCENT:.0f}% of AOI/vegetation area in a "
        "high/critical/very-high class. This is a configurable prototype parameter."
    )

# ======================================================
# REPORTS (downloads hub)
# ======================================================

elif page == "📥 Reports":

    st.title("📥 Reports & Downloads")
    st.subheader("التقارير والملفات القابلة للتحميل")

    st.markdown(
        """
هذه الصفحة تجمع كل التقارير والملفات القابلة للتنزيل من منصة ENVA في مكان واحد.

This page consolidates all downloadable reports and data files from the ENVA platform.
"""
    )

    st.markdown("---")

    st.subheader("📡 Environmental Indicators")

    if INDICATORS_AVAILABLE:
        if FPDF_AVAILABLE:
            pdf_bytes = build_indicators_pdf(INDICATORS, INDICATOR_INFO, LATEST_RUN)
            if pdf_bytes:
                st.download_button(
                    label="⬇️ Environmental Indicators Report (PDF)",
                    data=pdf_bytes,
                    file_name="ENVA_Environmental_Indicators_Report.pdf",
                    mime="application/pdf",
                    key="reports_page_pdf_download",
                )
        for code in INDICATOR_ORDER:
            meta = INDICATOR_INFO[code]
            d = INDICATORS[code]["data"]
            if d:
                st.download_button(
                    label=f"⬇️ {meta['icon']} {code} — Raw Data (JSON)",
                    data=json.dumps(d, ensure_ascii=False, indent=2),
                    file_name=f"{code}_current.json",
                    mime="application/json",
                    key=f"reports_json_{code}",
                )
    else:
        st.info("Indicator reports will appear here once indicator data is available.")

    st.markdown("---")

    st.subheader("🛰️ Land Cover")

    st.download_button(
        label="⬇️ Land Cover Summary (CSV)",
        data=SUMMARY.to_csv(index=False),
        file_name="ENVA_Final_Summary.csv",
        mime="text/csv",
    )

    st.download_button(
        label="⬇️ Final Report (JSON)",
        data=json.dumps(REPORT, ensure_ascii=False, indent=2),
        file_name="ENVA_Final_Report.json",
        mime="application/json",
    )

    st.markdown("---")

    st.subheader("🌳 Smart Afforestation")

    aff_report_path = DATA_PATH / "ENVA_Afforestation_Report.json"
    aff_summary_path = DATA_PATH / "ENVA_Afforestation_Summary.csv"

    if aff_report_path.exists() and aff_summary_path.exists():
        with open(aff_report_path, encoding="utf-8") as f:
            st.download_button(
                label="⬇️ Afforestation Report (JSON)",
                data=f.read(),
                file_name="ENVA_Afforestation_Report.json",
                mime="application/json",
            )
        st.download_button(
            label="⬇️ Afforestation Summary (CSV)",
            data=pd.read_csv(aff_summary_path).to_csv(index=False),
            file_name="ENVA_Afforestation_Summary.csv",
            mime="text/csv",
        )
    else:
        st.caption("Afforestation reports not available yet.")

    st.markdown("---")
    st.caption("ENVA — Reports & Downloads Hub")

else:
    st.error("⚠️ Unknown page selected.")

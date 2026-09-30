import base64
import hashlib
import os
import re
import textwrap
import time
import uuid
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
from pypdf import PdfReader
import requests
import streamlit as st
import streamlit.components.v1 as components


# ============================================================
# UNROTTEN — SEC AUDIT INTELLIGENCE
# ============================================================

APP_NAME = "Unrotten"
GROQ_MODEL = "openai/gpt-oss-20b"

st.set_page_config(
    page_title="Unrotten — SEC Audit Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Google AdSense Script
components.html(
    """
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9891132261459814"
            crossorigin="anonymous"></script>
    """,
    height=0,
    width=0,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "theme_mode": "System",
    "source_type": "Chat without a document",
    "session_id": uuid.uuid4().hex[:8],
    "chat_histories": {},
    "conversation_states": {},
}

for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ============================================================
# ASSETS
# ============================================================

def find_asset(filename: str) -> Path | None:
    candidates = [
        BASE_DIR / "assets" / filename,
        BASE_DIR / "Unrotten_Apple_Glass_Theme" / "assets" / filename,
        BASE_DIR / "unrotten_glass" / "assets" / filename,
        BASE_DIR.parent / "Unrotten_Apple_Glass_Theme" / "assets" / filename,
    ]

    for path in candidates:
        if path.exists():
            return path

    try:
        matches = list(BASE_DIR.rglob(filename))
        return matches[0] if matches else None
    except Exception:
        return None


LOGO_PATH = find_asset("unrotten_mark.png")


# ============================================================
# GROQ
# ============================================================

def load_groq_key() -> str:
    key = ""

    try:
        key = st.secrets.get("GROQ_API_KEY", "") or ""
    except Exception:
        pass

    if not key:
        key = os.getenv("GROQ_API_KEY", "") or ""

    return str(key).strip().strip('"').strip("'")


GROQ_API_KEY = load_groq_key()

if not GROQ_API_KEY:
    st.error(
        "Groq API key not found.\n\n"
        "Create:\n"
        "`C:\\Users\\rajes\\Documents\\Unrotten\\.streamlit\\secrets.toml`\n\n"
        "with:\n\n"
        'GROQ_API_KEY = "gsk_..."'
    )
    st.stop()

client = Groq(api_key=GROQ_API_KEY)


# ============================================================
# CHROMADB
# ============================================================

@st.cache_resource
def get_chroma_client():
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


@st.cache_resource
def get_embedding_function():
    return embedding_functions.DefaultEmbeddingFunction()


chroma_client = get_chroma_client()
embedding_fn = get_embedding_function()


# ============================================================
# UI / THEME
# ============================================================

BASE_CSS = """
<style>
html, body, [class*="css"] {
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "SF Pro Text",
        Inter,
        "Segoe UI",
        sans-serif !important;
}

.stApp {
    min-height: 100vh;
}

.main .block-container {
    max-width: 1450px;
    padding: 26px 32px 60px !important;
}

section[data-testid="stSidebar"] > div {
    padding: 18px 15px 24px !important;
}

.glass-card {
    border-radius: 26px;
    padding: 24px 26px;
    background: rgba(255,255,255,.58);
    border: 1px solid rgba(255,255,255,.82);
    box-shadow:
        0 22px 60px rgba(70,50,42,.09),
        inset 0 1px 0 rgba(255,255,255,.9);
    backdrop-filter: blur(28px) saturate(125%);
    -webkit-backdrop-filter: blur(28px) saturate(125%);
}

.hero-card {
    min-height: 150px;
}

.hero-title {
    font-size: clamp(2.7rem, 5vw, 4.2rem);
    line-height: .88;
    font-weight: 900;
    letter-spacing: -.08em;
}

.hero-subtitle {
    margin-top: 10px;
    font-size: .98rem;
}

.hero-pill {
    display: inline-block;
    margin-top: 12px;
    padding: 7px 12px;
    border-radius: 999px;
    font-size: .72rem;
    font-weight: 750;
}

.logo-main {
    width: 68px;
    height: 68px;
    object-fit: contain;
}

.logo-hero {
    width: 105px;
    height: 105px;
    object-fit: contain;
}

.side-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
}

.side-logo {
    width: 42px;
    height: 42px;
    object-fit: contain;
}

.side-name {
    font-weight: 900;
    font-size: 1.18rem;
    letter-spacing: -.04em;
}

.side-sub {
    font-size: .68rem;
}

.scope-card {
    position: relative;
    overflow: hidden;
    margin-top: 8px;
}

.scope-card::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
}

.scope-label {
    font-size: .63rem;
    font-weight: 800;
    letter-spacing: .13em;
    text-transform: uppercase;
}

.scope-name {
    font-size: 1.42rem;
    font-weight: 850;
    letter-spacing: -.04em;
    margin-top: 4px;
}

.scope-flow {
    font-size: .76rem;
    margin-top: 5px;
}

.status-pill {
    display: inline-block;
    padding: 7px 11px;
    border-radius: 999px;
    font-size: .72rem;
    font-weight: 800;
}

.section-title {
    font-size: .98rem;
    font-weight: 800;
    margin-top: 22px;
    margin-bottom: 4px;
}

.section-subtitle {
    font-size: .76rem;
    margin-bottom: 11px;
}

[data-testid="stChatMessage"] {
    border-radius: 21px !important;
    padding: 13px 18px !important;
    margin-bottom: 10px !important;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] td,
[data-testid="stChatMessage"] th {
    line-height: 1.68 !important;
}

[data-testid="stChatInput"] {
    border-radius: 22px !important;
}

[data-testid="stChatInput"] > div {
    border-radius: 22px !important;
    background: rgba(255,255,255,.86) !important;
    border: 1px solid rgba(120,105,95,.20) !important;
    box-shadow:
        0 18px 42px rgba(57,43,37,.10),
        inset 0 1px 0 rgba(255,255,255,.95) !important;
}

[data-testid="stChatInput"] textarea {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    caret-color: #111111 !important;
    font-size: .98rem !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #766c65 !important;
    opacity: 1 !important;
}

.stButton > button {
    min-height: 46px !important;
    border-radius: 15px !important;
    font-weight: 650 !important;
}

.indexing-card {
    min-height: 245px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border-radius: 28px;
    padding: 30px;
}

.indexing-orbit {
    width: 82px;
    height: 82px;
    position: relative;
    display: grid;
    place-items: center;
    margin-bottom: 18px;
}

.indexing-orbit::before,
.indexing-orbit::after {
    content: "";
    position: absolute;
    inset: 2px;
    border: 3px solid transparent;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.indexing-orbit::after {
    inset: 11px;
    animation-direction: reverse;
    animation-duration: 1.6s;
}

.indexing-orbit img {
    width: 43px;
    height: 43px;
    object-fit: contain;
}

.indexing-title {
    font-weight: 850;
    font-size: 1rem;
}

.indexing-detail {
    margin-top: 6px;
    max-width: 680px;
    text-align: center;
    font-size: .78rem;
    line-height: 1.5;
}

.indexing-bar {
    margin-top: 16px;
    width: min(430px, 88%);
    height: 5px;
    border-radius: 999px;
    overflow: hidden;
}

.indexing-bar > div {
    height: 100%;
    border-radius: inherit;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

@media (max-width: 900px) {
    .main .block-container {
        padding: 16px 12px 40px !important;
    }

    .logo-hero {
        display: none !important;
    }

    .hero-title {
        font-size: 2.55rem;
    }
}
</style>
"""

LIGHT_CSS = """
<style>
.stApp {
    background:
        radial-gradient(circle at 8% 0%, rgba(255,255,255,.98), transparent 28%),
        radial-gradient(circle at 94% 7%, rgba(190,146,128,.22), transparent 29%),
        radial-gradient(circle at 45% 100%, rgba(213,222,228,.33), transparent 35%),
        #f4f0ed !important;
    color: #2e2723 !important;
}

section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(250,247,245,.83), rgba(232,226,222,.73))
        !important;
    border-right: 1px solid rgba(255,255,255,.85) !important;
}

section[data-testid="stSidebar"] * {
    color: #463a34 !important;
}

.glass-card {
    background: rgba(255,255,255,.56) !important;
}

.scope-card::before {
    background: linear-gradient(180deg, #8d5b4a, #c39a8b);
}

.scope-label,
.scope-flow,
.section-subtitle {
    color: #92857d !important;
}

.scope-name,
.section-title {
    color: #382e29 !important;
}

.hero-title {
    color: #8d5b4a;
}

.hero-subtitle {
    color: #756b65;
}

.hero-pill {
    color: #754d40;
    background: rgba(141,91,74,.09);
    border: 1px solid rgba(141,91,74,.14);
}

[data-testid="stChatMessage"] {
    background: rgba(255,255,255,.48) !important;
    border: 1px solid rgba(255,255,255,.78) !important;
    box-shadow: 0 16px 40px rgba(67,49,41,.06) !important;
}

[data-testid="stChatInput"] > div {
    background: rgba(255,255,255,.69) !important;
    border: 1px solid rgba(255,255,255,.90) !important;
}

.stButton > button {
    background: rgba(255,255,255,.48) !important;
    border: 1px solid rgba(255,255,255,.82) !important;
    color: #443732 !important;
}

[data-testid="stChatInput"] > div {
    background: rgba(255,255,255,.86) !important;
    border: 1px solid rgba(120,105,95,.20) !important;
}

[data-testid="stChatInput"] textarea {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    caret-color: #111111 !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #766c65 !important;
    opacity: 1 !important;
}

.indexing-card {
    background: rgba(255,255,255,.58);
    border: 1px solid rgba(255,255,255,.83);
}

.indexing-orbit::before {
    border-top-color: #8d5b4a;
    border-right-color: rgba(141,91,74,.18);
}

.indexing-orbit::after {
    border-top-color: #b98a76;
    border-right-color: rgba(185,138,118,.15);
}

.indexing-title { color: #41352f; }
.indexing-detail { color: #8f8179; }
.indexing-bar { background: rgba(141,91,74,.10); }

.indexing-bar > div {
    background: linear-gradient(90deg, #8d5b4a, #c69f90, #8d5b4a);
}
</style>
"""

DARK_CSS = """
<style>
.stApp {
    background:
        radial-gradient(circle at 8% 0%, rgba(255,255,255,.04), transparent 28%),
        radial-gradient(circle at 92% 8%, rgba(179,124,101,.16), transparent 29%),
        #171514 !important;
    color: #eee6e1 !important;
}

section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(31,28,27,.93), rgba(20,18,17,.91))
        !important;
    border-right-color: rgba(255,255,255,.09) !important;
}

section[data-testid="stSidebar"] * {
    color: #e6ddd7 !important;
}

.glass-card {
    background: rgba(41,37,35,.62) !important;
    border-color: rgba(255,255,255,.11) !important;
    box-shadow:
        0 20px 55px rgba(0,0,0,.23),
        inset 0 1px 0 rgba(255,255,255,.06) !important;
}

.scope-card::before {
    background: linear-gradient(180deg, #b77f69, #805343);
}

.scope-label,
.scope-flow,
.section-subtitle {
    color: #a69992 !important;
}

.scope-name,
.section-title {
    color: #f0e8e2 !important;
}

.hero-title {
    color: #c3917d;
}

.hero-subtitle {
    color: #b3a69f !important;
}

.hero-pill {
    color: #d8baac;
    background: rgba(196,145,125,.12);
    border-color: rgba(196,145,125,.16);
}

[data-testid="stChatMessage"] {
    background: rgba(43,39,37,.67) !important;
    border-color: rgba(255,255,255,.10) !important;
}

[data-testid="stChatInput"] > div {
    background: rgba(28,25,24,.94) !important;
    border: 1px solid rgba(255,255,255,.15) !important;
}

[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    caret-color: #ffffff !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #a79d96 !important;
    opacity: 1 !important;
}

.stButton > button {
    background: rgba(255,255,255,.055) !important;
    border-color: rgba(255,255,255,.10) !important;
    color: #eee5df !important;
}

.indexing-card {
    background: rgba(42,38,36,.69);
    border-color: rgba(255,255,255,.11);
    box-shadow:
        0 22px 60px rgba(0,0,0,.25),
        inset 0 1px 0 rgba(255,255,255,.06);
}

.indexing-orbit::before {
    border-top-color: #c3917d;
    border-right-color: rgba(195,145,125,.22);
}

.indexing-orbit::after {
    border-top-color: #e0b8a6;
    border-right-color: rgba(224,184,166,.18);
}

.indexing-title { color: #eee6e0; }
.indexing-detail { color: #aaa09a; }
.indexing-bar { background: rgba(196,145,125,.10); }

.indexing-bar > div {
    background: linear-gradient(90deg, #c3917d, #e0b8a6, #c3917d);
}
</style>
"""

SYSTEM_DARK_CSS = """
<style>
@media (prefers-color-scheme: dark) {
    .stApp {
        background:
            radial-gradient(circle at 8% 0%, rgba(255,255,255,.04), transparent 28%),
            radial-gradient(circle at 92% 8%, rgba(179,124,101,.16), transparent 29%),
            #171514 !important;
        color: #eee6e1 !important;
    }

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, rgba(31,28,27,.93), rgba(20,18,17,.91))
            !important;
    }

    section[data-testid="stSidebar"] * {
        color: #e6ddd7 !important;
    }

    .glass-card,
    .scope-card,
    [data-testid="stChatMessage"] {
        background: rgba(41,37,35,.62) !important;
        border-color: rgba(255,255,255,.11) !important;
    }

    .scope-label,
    .scope-flow,
    .section-subtitle {
        color: #a69992 !important;
    }

    .scope-name,
    .section-title {
        color: #f0e8e2 !important;
    }

    .hero-title {
        color: #c3917d;
    }

    .hero-subtitle {
        color: #b3a69f !important;
    }
}
</style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)

if st.session_state["theme_mode"] == "Dark":
    st.markdown(DARK_CSS, unsafe_allow_html=True)
elif st.session_state["theme_mode"] == "System":
    st.markdown(LIGHT_CSS + SYSTEM_DARK_CSS, unsafe_allow_html=True)
else:
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)


# ============================================================
# SIDEBAR — CHAT FIRST
# ============================================================

DEMO_COMPANIES = {
    "Apple Inc. (AAPL)": (
        "Apple_10K",
        "AAPL",
        "0000320193",
    ),
    "Alphabet Inc. (GOOGL)": (
        "Alphabet_10K",
        "GOOGL",
        "0001652044",
    ),
    "Tesla, Inc. (TSLA)": (
        "Tesla_10K",
        "TSLA",
        "0001318605",
    ),
    "Microsoft Corporation (MSFT)": (
        "Microsoft_10K",
        "MSFT",
        "0000789019",
    ),
}

with st.sidebar:

    if LOGO_PATH:
        st.image(
            str(LOGO_PATH),
            width=43,
        )

    st.markdown("### Document")

    source_type = st.radio(
        "Mode",
        [
            "Chat without a document",
            "Use Pre-loaded SEC Filing",
            "Upload Custom PDF",
        ],
        key="source_type",
        label_visibility="collapsed",
    )

    selected_folder = None
    current_ticker = None
    current_cik = None
    target_dir = None
    is_custom_upload = False

    if source_type == "Use Pre-loaded SEC Filing":

        company_choice = st.selectbox(
            "SEC filing",
            list(DEMO_COMPANIES.keys()),
        )

        (
            selected_folder,
            current_ticker,
            current_cik,
        ) = DEMO_COMPANIES[
            company_choice
        ]

        target_dir = (
            DATA_DIR
            / "shared"
            / selected_folder
        )

        target_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    elif source_type == "Upload Custom PDF":

        is_custom_upload = True

        uploaded_file = st.file_uploader(
            "Upload a 10-K PDF",
            type=["pdf"],
        )

        if uploaded_file:

            selected_folder = re.sub(
                r"[^A-Za-z0-9_-]",
                "_",
                Path(
                    uploaded_file.name
                ).stem,
            )

            target_dir = (
                DATA_DIR
                / "user"
                / st.session_state["session_id"]
                / selected_folder
            )

            target_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            upload_path = (
                target_dir
                / "raw_10k.pdf"
            )

            data = uploaded_file.getvalue()

            if (
                not upload_path.exists()
                or upload_path.stat().st_size != len(data)
            ):

                upload_path.write_bytes(
                    data
                )

    st.markdown("---")

    st.markdown("### Appearance")

    st.radio(
        "Theme",
        [
            "Light",
            "Dark",
            "System",
        ],
        key="theme_mode",
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("---")

    if st.button(
        "Reset conversation",
        use_container_width=True,
    ):

        reset_key = (
            selected_folder
            or "general"
        )

        st.session_state[
            "chat_histories"
        ][
            reset_key
        ] = []

        st.session_state[
            "conversation_states"
        ][
            reset_key
        ] = ""

        st.rerun()


# ============================================================
# SEC FUNCTIONS
# ============================================================

def fetch_sec_filing(
    ticker: str,
    cik: str,
    target_dir: Path,
) -> bool:

    txt_path = target_dir / "raw_10k.txt"

    if (
        txt_path.exists()
        and txt_path.stat().st_size > 1000
    ):
        return True

    headers = {
        "User-Agent":
            "Unrotten ResearchApp/6.0 "
            "(audit@unrotten.org)"
    }

    try:

        response = requests.get(
            (
                "https://data.sec.gov/submissions/"
                f"CIK{cik.zfill(10)}.json"
            ),
            headers=headers,
            timeout=20,
        )

        response.raise_for_status()

        recent = (
            response
            .json()
            .get("filings", {})
            .get("recent", {})
        )

        forms = recent.get(
            "form",
            [],
        )

        index = next(
            (
                i
                for i, form
                in enumerate(forms)
                if form == "10-K"
            ),
            None,
        )

        if index is None:
            return False

        accession = recent[
            "accessionNumber"
        ][index]

        primary_doc = recent[
            "primaryDocument"
        ][index]

        archive_url = (
            "https://www.sec.gov/Archives/"
            f"edgar/data/{int(cik)}/"
            f"{accession.replace('-', '')}/"
            f"{primary_doc}"
        )

        response = requests.get(
            archive_url,
            headers=headers,
            timeout=25,
        )

        response.raise_for_status()

        clean = re.sub(
            r"<script.*?>.*?</script>",
            " ",
            response.text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        clean = re.sub(
            r"<style.*?>.*?</style>",
            " ",
            clean,
            flags=re.DOTALL | re.IGNORECASE,
        )

        clean = re.sub(
            r"<[^>]+>",
            " ",
            clean,
        )

        clean = (
            clean
            .replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
        )

        clean = re.sub(
            r"\s+",
            " ",
            clean,
        ).strip()

        if len(clean) < 1000:
            return False

        txt_path.write_text(
            clean,
            encoding="utf-8",
        )

        return True

    except requests.RequestException as exc:

        st.error(
            f"SEC request failed: {exc}"
        )

        return False

    except Exception as exc:

        st.error(
            f"Could not prepare the SEC filing: {exc}"
        )

        return False


def document_hash(
    target_dir: Path,
) -> str:

    pdf = target_dir / "raw_10k.pdf"
    txt = target_dir / "raw_10k.txt"

    path = (
        pdf
        if pdf.exists()
        else txt
    )

    if not path.exists():
        return ""

    digest = hashlib.sha256()

    with path.open("rb") as handle:

        while True:

            block = handle.read(
                1024 * 1024
            )

            if not block:
                break

            digest.update(
                block
            )

    return digest.hexdigest()


def load_text(
    target_dir: Path,
) -> str:

    pdf = target_dir / "raw_10k.pdf"
    txt = target_dir / "raw_10k.txt"

    if pdf.exists():

        reader = PdfReader(
            str(pdf)
        )

        pages = []

        for page in reader.pages:

            extracted = (
                page.extract_text()
                or ""
            )

            if extracted.strip():
                pages.append(extracted)

        text = "\n".join(
            pages
        )

        txt.write_text(
            text,
            encoding="utf-8",
        )

        return text

    if txt.exists():

        return txt.read_text(
            encoding="utf-8"
        )

    return ""


# ============================================================
# INDEXING
# ============================================================

def show_index_stage(
    placeholder,
    title: str,
    detail: str,
    progress: int,
) -> None:
    """
    Native Streamlit indexing UI.
    Deliberately does NOT use unsafe HTML so the indexing stage
    can never appear as raw <div> markup in the app.
    """
    pct = max(0, min(100, int(progress)))

    with placeholder.container():
        st.markdown(
            f"### {title}"
        )

        st.caption(
            detail
        )

        st.progress(
            pct / 100.0,
            text=f"{pct}%"
        )



def build_index(
    target_dir: Path,
    collection_name: str,
):

    text = load_text(
        target_dir
    )

    if len(
        text.strip()
    ) < 100:

        st.error(
            "The filing does not contain enough readable text."
        )

        return None, 0

    placeholder = st.empty()

    show_index_stage(
        placeholder,
        "Reading filing",
        (
            "Extracting the filing and understanding "
            "its document structure."
        ),
        10,
    )

    time.sleep(0.12)

    chunk_size = 1200
    overlap = 240
    step = chunk_size - overlap

    chunks = []
    ids = []
    metadata = []

    # Cover chunk improves company/address retrieval.
    cover = text[:2600]

    if len(cover.strip()) > 50:

        chunks.append(
            "[COVER / CORPORATE METADATA]\n"
            + cover
        )

        ids.append(
            "cover_page_meta"
        )

        metadata.append(
            {
                "source": "10-K",
                "kind": "cover",
                "chunk_index": 0,
            }
        )

    for start in range(
        0,
        len(text),
        step,
    ):

        chunk = text[
            start:start + chunk_size
        ]

        if len(chunk.strip()) <= 50:
            continue

        number = len(chunks)

        chunks.append(chunk)
        ids.append(f"chunk_{number}")

        metadata.append(
            {
                "source": "10-K",
                "kind": "body",
                "chunk_index": number,
            }
        )

    show_index_stage(
        placeholder,
        "Building document chunks",
        (
            f"Created {len(chunks):,} overlapping evidence passages "
            "for precise retrieval."
        ),
        44,
    )

    time.sleep(0.12)

    if not chunks:

        placeholder.empty()

        return None, 0

    show_index_stage(
        placeholder,
        "Mapping vectors in ChromaDB",
        (
            "Embedding filing passages and storing them "
            "in the local vector index."
        ),
        68,
    )

    try:

        try:

            chroma_client.delete_collection(
                name=collection_name
            )

        except Exception:
            pass

        collection = (
            chroma_client.create_collection(
                name=collection_name,
                embedding_function=embedding_fn,
                metadata={
                    "document_hash":
                        document_hash(
                            target_dir
                        )
                },
            )
        )

        batch_size = 100

        for start in range(
            0,
            len(chunks),
            batch_size,
        ):

            end = min(
                start + batch_size,
                len(chunks),
            )

            collection.add(
                documents=chunks[
                    start:end
                ],
                ids=ids[
                    start:end
                ],
                metadatas=metadata[
                    start:end
                ],
            )

            show_index_stage(
                placeholder,
                "Mapping vectors in ChromaDB",
                (
                    f"Stored {end:,} of "
                    f"{len(chunks):,} evidence vectors…"
                ),
                68 + int(
                    27 * end / len(chunks)
                ),
            )

    except Exception as exc:

        placeholder.empty()

        st.error(
            f"ChromaDB indexing failed: {exc}"
        )

        return None, 0

    show_index_stage(
        placeholder,
        "Ready for analysis",
        (
            "The filing is indexed. Unrotten can now "
            "retrieve grounded SEC evidence."
        ),
        100,
    )

    time.sleep(0.25)
    placeholder.empty()

    return collection, len(chunks)


def get_collection(
    target_dir: Path,
    collection_name: str,
):

    if not (
        (target_dir / "raw_10k.pdf").exists()
        or
        (target_dir / "raw_10k.txt").exists()
    ):
        return None

    current_hash = document_hash(
        target_dir
    )

    try:

        collection = (
            chroma_client.get_collection(
                name=collection_name,
                embedding_function=embedding_fn,
            )
        )

        metadata = (
            collection.metadata
            or {}
        )

        if (
            collection.count() > 0
            and metadata.get(
                "document_hash"
            )
            == current_hash
        ):

            return collection

    except Exception:
        pass

    collection, _ = build_index(
        target_dir,
        collection_name,
    )

    return collection


# ============================================================
# CONTEXT MEMORY
# ============================================================

MAX_RECENT_MESSAGES = 6
MAX_MEMORY_CHARS = 6000

FOLLOWUP_HINTS = (
    "it",
    "its",
    "they",
    "them",
    "this",
    "that",
    "these",
    "those",
    "one",
    "ones",
    "former",
    "latter",
    "first",
    "second",
    "third",
    "previous",
    "same",
    "again",
    "also",
    "instead",
    "what about",
    "how much is that",
    "how much was that",
    "what percentage",
    "how does that",
    "compare it",
    "compare that",
)


def history_text(messages) -> str:

    if not messages:
        return "[NO RECENT CONVERSATION]"

    parts = []

    for message in messages:

        content = str(
            message.get(
                "content",
                "",
            )
        ).strip()

        if content:

            parts.append(
                f"{message.get('role', 'unknown').upper()}: "
                f"{content}"
            )

    return (
        "\n".join(parts)
        if parts
        else "[NO RECENT CONVERSATION]"
    )


def looks_like_followup(
    prompt: str,
) -> bool:

    text = re.sub(
        r"\s+",
        " ",
        prompt.lower(),
    ).strip()

    if len(text.split()) <= 7:
        return True

    padded = f" {text} "

    return any(
        f" {hint} " in padded
        for hint in FOLLOWUP_HINTS
    )


def get_conversation_state(
    folder_name: str,
) -> str:

    return st.session_state[
        "conversation_states"
    ].get(
        folder_name,
        "",
    )


def resolve_query(
    folder_name: str,
    prompt: str,
) -> str:

    state = get_conversation_state(
        folder_name
    )

    history = st.session_state[
        "chat_histories"
    ].get(
        folder_name,
        [],
    )

    recent = history_text(
        history[
            -MAX_RECENT_MESSAGES:
        ][:-1]
    )

    if (
        not state
        and
        recent == "[NO RECENT CONVERSATION]"
    ):
        return prompt

    if not looks_like_followup(
        prompt
    ):
        return prompt

    resolver_prompt = f"""
Rewrite the user's latest question into ONE standalone
SEC filing retrieval query.

Resolve references using only the conversation state and
recent conversation.

Do not invent facts, numbers, dates, entities, or filing
content.

Output ONLY the rewritten query.

CONVERSATION STATE:
{state or "[NONE]"}

RECENT CONVERSATION:
{recent}

LATEST USER QUESTION:
{prompt}
"""

    try:

        response = (
            client
            .chat
            .completions
            .create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content":
                            "Rewrite ambiguous follow-ups into "
                            "standalone SEC retrieval queries. "
                            "Never invent facts.",
                    },
                    {
                        "role": "user",
                        "content": resolver_prompt,
                    },
                ],
                temperature=0,
                max_completion_tokens=250,
            )
        )

        value = (
            response
            .choices[0]
            .message
            .content
            if response.choices
            else ""
        )

        return (
            (value or "").strip()
            or prompt
        )

    except Exception:

        return prompt


def update_memory(
    folder_name: str,
    question: str,
    answer: str,
) -> None:

    existing = get_conversation_state(
        folder_name
    )

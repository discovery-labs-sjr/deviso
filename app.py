from __future__ import annotations

import base64
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from deviso_core import (
    FLAGS,
    NOMS_DEVISES,
    TAUX_SECOURS,
    clean_rates,
    convert_amount,
    currency_label,
    fetch_history,
    fetch_live_rates,
    format_date,
    format_number,
)

st.set_page_config(
    page_title="DEVIS'O — Convertisseur de devises",
    page_icon="💱",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Branding / browser metadata
# ---------------------------------------------------------------------------

ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#16B8FF"/>
      <stop offset="55%" stop-color="#3E6BFF"/>
      <stop offset="100%" stop-color="#8B47FF"/>
    </linearGradient>
  </defs>
  <rect width="120" height="120" rx="30" fill="#06132E"/>
  <path d="M34 34h26l22 26-22 26H34l22-26z" fill="url(#g)"/>
  <path d="M50 44h8l15 16-15 16h-8l15-16z" fill="#06132E"/>
</svg>
"""
ICON_B64 = base64.b64encode(ICON_SVG.encode()).decode()

st.markdown(
    f"""
    <link rel="icon" href="data:image/svg+xml;base64,{ICON_B64}">
    <link rel="apple-touch-icon" href="data:image/svg+xml;base64,{ICON_B64}">
    <meta name="theme-color" content="#06132E">
    <meta name="mobile-web-app-capable" content="yes">
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Premium mobile-first UI
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #050B19;
    --panel: rgba(8, 24, 52, 0.78);
    --panel-strong: rgba(9, 29, 62, 0.96);
    --border: rgba(110, 165, 255, 0.20);
    --text: #F7FAFF;
    --muted: #95A7C7;
    --cyan: #17B9FF;
    --blue: #3C71FF;
    --purple: #874AFF;
    --green: #20D7B2;
    --gold: #FFC94A;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    color: var(--text) !important;
}

.stApp {
    min-height: 100vh;
    background:
        radial-gradient(circle at 15% 0%, rgba(31, 126, 255, 0.20), transparent 26%),
        radial-gradient(circle at 88% 10%, rgba(122, 73, 255, 0.16), transparent 22%),
        radial-gradient(circle at 50% 82%, rgba(12, 95, 194, 0.10), transparent 30%),
        linear-gradient(180deg, #040918 0%, #071228 46%, #050B19 100%);
}

[data-testid="stHeader"] {
    background: transparent !important;
}

#MainMenu, footer {
    visibility: hidden !important;
}

[data-testid="stToolbar"] {
    display: none !important;
}

.main .block-container {
    width: min(100%, 920px);
    padding: 1.1rem 1rem 3.5rem 1rem !important;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0.2rem 0 1.35rem 0;
}

.brand-mark {
    width: 44px;
    height: 44px;
    display: grid;
    place-items: center;
    border-radius: 14px;
    background:
        linear-gradient(145deg, rgba(23,185,255,.20), rgba(65,95,255,.14)),
        #07172F;
    border: 1px solid rgba(92,160,255,.28);
    box-shadow: 0 10px 30px rgba(0, 92, 255, .18);
    color: #FFFFFF;
    font-size: 24px;
    font-weight: 800;
}

.brand-name {
    font-size: 1.60rem;
    line-height: 1;
    font-weight: 800;
    letter-spacing: -0.055em;
}

.brand-name span {
    background: linear-gradient(100deg, #FFFFFF 0%, #DDE9FF 45%, #62AEFF 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.brand-tagline {
    margin-top: 5px;
    color: var(--muted);
    font-size: .78rem;
}

.section-label {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: .2rem 0 .55rem;
    font-size: .77rem;
    color: #89A1C9;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .11em;
}

.hero-card,
.info-card,
.result-card,
.utility-card,
.history-card {
    background:
        linear-gradient(180deg, rgba(14, 38, 78, .84), rgba(5, 17, 37, .92));
    border: 1px solid var(--border);
    border-radius: 24px;
    box-shadow:
        0 22px 58px rgba(0, 0, 0, .38),
        inset 0 1px 0 rgba(255,255,255,.035);
}

.hero-card {
    padding: 1rem;
    margin-bottom: 1rem;
}

.pair-title {
    color: #91A8D0;
    font-size: .80rem;
    font-weight: 700;
    margin-bottom: .65rem;
}

.pair-block {
    background: rgba(8, 23, 52, .82);
    border: 1px solid rgba(101, 151, 232, .18);
    border-radius: 20px;
    padding: .65rem .75rem .72rem;
}

.pair-label {
    color: #8198BD;
    font-size: .73rem;
    font-weight: 600;
    margin: 0 0 .35rem .05rem;
}

.pair-note {
    color: #8398BA;
    font-size: .69rem;
    margin-top: .2rem;
}

.swap-wrap {
    display: flex;
    justify-content: center;
    margin: -1.45rem 0 -1.45rem;
    position: relative;
    z-index: 2;
}

.swap-wrap button {
    width: 48px !important;
    height: 48px !important;
    border-radius: 50% !important;
    background: linear-gradient(145deg, #1B3F9B, #301A93) !important;
    border: 1px solid rgba(99, 128, 255, .75) !important;
    box-shadow: 0 12px 28px rgba(41, 57, 172, .34), 0 0 0 5px rgba(7, 16, 39, .82);
    padding: 0 !important;
    font-size: 1.25rem !important;
}

.amount-label {
    color: #91A8D0;
    font-size: .80rem;
    font-weight: 700;
    margin: 1rem 0 .5rem;
}

.result-card {
    padding: 1.05rem 1.1rem 1rem;
    background:
        radial-gradient(circle at 88% 12%, rgba(126,79,255,.16), transparent 32%),
        linear-gradient(145deg, rgba(12, 72, 146, .78), rgba(31, 21, 83, .86));
    border-color: rgba(68, 136, 255, .34);
    margin-top: .85rem;
}

.result-eyebrow {
    color: #9CB4DF;
    font-size: .74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .09em;
}

.result-value {
    margin: .3rem 0 .45rem;
    font-size: clamp(2rem, 8vw, 3.3rem);
    line-height: 1.02;
    font-weight: 800;
    letter-spacing: -.055em;
    color: #FFFFFF;
    overflow-wrap: anywhere;
}

.result-meta {
    display: flex;
    flex-wrap: wrap;
    gap: .42rem;
    color: #B1C1DE;
    font-size: .73rem;
}

.pill {
    display: inline-flex;
    align-items: center;
    gap: .35rem;
    border-radius: 999px;
    padding: .34rem .58rem;
    border: 1px solid rgba(119, 161, 226, .18);
    background: rgba(255,255,255,.035);
}

.pill-live {
    border-color: rgba(32, 215, 178, .25);
    color: #4CE6C8;
    background: rgba(32,215,178,.08);
}

.pill-offline {
    border-color: rgba(255, 174, 74, .22);
    color: #FFD38A;
    background: rgba(255,174,74,.07);
}

.quick-grid {
    margin: .8rem 0 .15rem;
}

.quick-title {
    color: #90A7CB;
    font-size: .73rem;
    font-weight: 700;
    margin-bottom: .45rem;
}

.info-card {
    padding: .9rem 1rem;
    margin-top: .85rem;
}

.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    padding: .35rem 0;
}

.info-label {
    color: #8299BD;
    font-size: .75rem;
}

.info-value {
    color: #F5F8FF;
    font-weight: 700;
    font-size: .80rem;
    text-align: right;
}

.features {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: .75rem;
    margin: 1rem 0;
}

.feature {
    min-height: 95px;
    background: rgba(8, 23, 52, .66);
    border: 1px solid rgba(101, 151, 232, .16);
    border-radius: 18px;
    padding: .82rem;
}

.feature-icon {
    width: 32px;
    height: 32px;
    display: grid;
    place-items: center;
    border-radius: 11px;
    background: rgba(52, 107, 255, .14);
    border: 1px solid rgba(84, 132, 255, .20);
    font-size: 1rem;
}

.feature-title {
    margin-top: .7rem;
    font-size: .74rem;
    color: #F0F5FF;
    font-weight: 700;
}

.feature-sub {
    margin-top: .22rem;
    font-size: .66rem;
    color: #7E96BD;
}

.tabs-wrap {
    margin-top: 1.05rem;
}

.stTabs [data-baseweb="tab-list"] {
    gap: .35rem;
    background: rgba(6, 16, 35, .72);
    border: 1px solid rgba(92, 143, 228, .13);
    border-radius: 15px;
    padding: .28rem;
}

.stTabs [data-baseweb="tab"] {
    color: #7F95B9 !important;
    border-radius: 11px;
    padding: .6rem .75rem;
    font-weight: 700;
    font-size: .73rem;
}

.stTabs [aria-selected="true"] {
    color: #FFFFFF !important;
    background: linear-gradient(145deg, rgba(36, 92, 188, .68), rgba(71, 51, 152, .58));
}

.stTextInput input,
.stNumberInput input,
div[data-baseweb="select"] > div {
    background: rgba(7, 21, 48, .92) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(111, 158, 232, .18) !important;
    border-radius: 14px !important;
    min-height: 47px !important;
}

.stTextInput input::placeholder {
    color: #617799 !important;
}

.stSlider [data-baseweb="slider"] {
    padding-left: .2rem;
    padding-right: .2rem;
}

.stSlider [role="slider"] {
    background-color: #63A8FF !important;
}

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    min-height: 47px !important;
    border-radius: 14px !important;
    border: 1px solid rgba(100, 150, 250, .18) !important;
    background: rgba(12, 31, 68, .92) !important;
    color: #F8FBFF !important;
    font-weight: 700 !important;
    font-size: .79rem !important;
    box-shadow: none !important;
}

.stFormSubmitButton > button,
.primary-cta {
    background: linear-gradient(110deg, #12B5FF 0%, #356EFF 52%, #854AFF 100%) !important;
    border: none !important;
    color: #FFFFFF !important;
    box-shadow: 0 13px 30px rgba(62, 112, 255, .27) !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    filter: brightness(1.07);
    transform: translateY(-1px);
}

div[data-testid="stExpander"] {
    border: 1px solid rgba(104, 150, 224, .15) !important;
    border-radius: 18px !important;
    background: rgba(7, 21, 47, .58) !important;
}

div[data-testid="stAlert"] {
    border-radius: 15px !important;
}

div[data-testid="stDataFrame"] {
    border-radius: 15px;
    overflow: hidden;
}

.footer-note {
    margin-top: 1.35rem;
    padding: .85rem 1rem;
    border-top: 1px solid rgba(98, 142, 208, .11);
    color: #617694;
    font-size: .65rem;
    text-align: center;
    line-height: 1.6;
}

.small-muted {
    color: #7188AA;
    font-size: .71rem;
}

.empty-state {
    padding: 1.15rem;
    border-radius: 17px;
    border: 1px dashed rgba(114, 157, 225, .20);
    background: rgba(8, 23, 50, .50);
    color: #8096B9;
    text-align: center;
    font-size: .78rem;
}

@media (max-width: 680px) {
    .main .block-container {
        padding-left: .72rem !important;
        padding-right: .72rem !important;
    }

    .features {
        grid-template-columns: 1fr;
    }

    .feature {
        min-height: 76px;
    }

    .brand-name {
        font-size: 1.42rem;
    }

    .brand-mark {
        width: 40px;
        height: 40px;
        border-radius: 12px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800, show_spinner=False)
def load_rates() -> tuple[dict[str, float], bool, str]:
    return fetch_live_rates()


@st.cache_data(ttl=3600, show_spinner=False)
def load_history(src: str, tgt: str, days: int = 30):
    return fetch_history(src, tgt, days)


rates, live, rate_date = load_rates()
rates = clean_rates(rates)

currencies = sorted(
    set(rates.keys()) | set(TAUX_SECOURS.keys()),
    key=lambda code: (0 if code in ("EUR", "XOF", "USD") else 1, code),
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

defaults: dict[str, Any] = {
    "src": "EUR" if "EUR" in currencies else currencies[0],
    "tgt": "XOF" if "XOF" in currencies else ("USD" if "USD" in currencies else currencies[min(1, len(currencies) - 1)]),
    "amount": 100.0,
    "fee_pct": 0.0,
    "alert_threshold": 0.0,
    "history": [],
    "last_conversion": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Keep widget state valid if the provider list changes.
if st.session_state.src not in currencies:
    st.session_state.src = currencies[0]
if st.session_state.tgt not in currencies:
    st.session_state.tgt = currencies[min(1, len(currencies) - 1)]

# ---------------------------------------------------------------------------
# Small actions
# ---------------------------------------------------------------------------

def swap_currencies() -> None:
    st.session_state.src, st.session_state.tgt = (
        st.session_state.tgt,
        st.session_state.src,
    )


def select_pair(src: str, tgt: str) -> None:
    if src in currencies and tgt in currencies:
        st.session_state.src = src
        st.session_state.tgt = tgt


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="brand">
        <div class="brand-mark">↗</div>
        <div>
            <div class="brand-name"><span>DEVIS'O</span></div>
            <div class="brand-tagline">Le monde en une seule conversion</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

status_class = "pill-live" if live else "pill-offline"
status_text = "● Taux en temps réel" if live else "● Mode secours"
status_date = format_date(rate_date) if live else "taux de secours intégrés"

st.markdown(
    f"""
    <div class="section-label">
        <span>Convertisseur</span>
        <span class="pill {status_class}">{status_text}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Quick pair controls must appear before the selectboxes so state can be changed safely.
q1, q2, q3 = st.columns(3)
with q1:
    if st.button("EUR → XOF", use_container_width=True):
        select_pair("EUR", "XOF")
        st.rerun()
with q2:
    if st.button("USD → EUR", use_container_width=True):
        select_pair("USD", "EUR")
        st.rerun()
with q3:
    if st.button("EUR → USD", use_container_width=True):
        select_pair("EUR", "USD")
        st.rerun()

# Swap also lives above the form so Streamlit widget state remains consistent.
swap_space = st.columns([1, 1.2, 1])
with swap_space[1]:
    st.markdown('<div class="swap-wrap">', unsafe_allow_html=True)
    if st.button("⇅", help="Inverser les devises", use_container_width=True):
        swap_currencies()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Conversion form
# ---------------------------------------------------------------------------

st.markdown('<div class="hero-card">', unsafe_allow_html=True)
st.markdown('<div class="pair-title">Choisissez votre paire</div>', unsafe_allow_html=True)

with st.form("conversion_form", clear_on_submit=False):
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="pair-block">', unsafe_allow_html=True)
        st.markdown('<div class="pair-label">DE</div>', unsafe_allow_html=True)
        source = st.selectbox(
            "Devise de départ",
            currencies,
            index=currencies.index(st.session_state.src),
            format_func=currency_label,
            label_visibility="collapsed",
            key="src",
        )
        st.markdown(
            f'<div class="pair-note">{NOMS_DEVISES.get(source, source)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="pair-block">', unsafe_allow_html=True)
        st.markdown('<div class="pair-label">VERS</div>', unsafe_allow_html=True)
        target = st.selectbox(
            "Devise cible",
            currencies,
            index=currencies.index(st.session_state.tgt),
            format_func=currency_label,
            label_visibility="collapsed",
            key="tgt",
        )
        st.markdown(
            f'<div class="pair-note">{NOMS_DEVISES.get(target, target)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="amount-label">MONTANT À CONVERTIR</div>', unsafe_allow_html=True)
    amount = st.number_input(
        "Montant",
        min_value=0.0,
        step=10.0,
        format="%.2f",
        label_visibility="collapsed",
        key="amount",
    )

    submitted = st.form_submit_button(
        "⚡  Convertir",
        use_container_width=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Advanced options
# ---------------------------------------------------------------------------

with st.expander("Options avancées", expanded=False):
    fee_pct = st.slider(
        "Frais de l'opérateur (%)",
        min_value=0.0,
        max_value=5.0,
        value=float(st.session_state.fee_pct),
        step=0.05,
        help="Appliquez un pourcentage aux devises reçues. Laissez à 0 % sans frais.",
        key="fee_pct",
    )
    alert_threshold = st.number_input(
        "Avertir si le montant reçu est inférieur à",
        min_value=0.0,
        value=float(st.session_state.alert_threshold),
        step=50.0,
        format="%.2f",
        help="Ce seuil agit sur la conversion affichée. Il ne déclenche pas de notification externe.",
        key="alert_threshold",
    )

# ---------------------------------------------------------------------------
# Current course
# ---------------------------------------------------------------------------

current_rate = 0.0
try:
    current_rate = float(rates[target]) / float(rates[source])
except (KeyError, ZeroDivisionError):
    current_rate = 0.0

st.markdown(
    f"""
    <div class="info-card">
        <div class="info-row">
            <div class="info-label">Cours actuel</div>
            <div class="info-value">1 {source} = {format_number(current_rate, 6)} {target}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Dernière mise à jour</div>
            <div class="info-value">{status_date}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Convert + result
# ---------------------------------------------------------------------------

if submitted:
    try:
        conversion = convert_amount(
            amount=amount,
            src=source,
            tgt=target,
            rates=rates,
            fee_pct=fee_pct,
        )
        record = {
            "Heure": datetime.now().strftime("%d/%m/%Y • %H:%M"),
            "Paire": f"{source} → {target}",
            "Montant": f"{format_number(amount)} {source}",
            "Résultat": f"{format_number(conversion['net'])} {target}",
            "Taux": f"{format_number(conversion['rate'], 6)}",
            "Frais": f"{format_number(conversion['fee'])} {target}",
        }
        st.session_state.last_conversion = {
            "source": source,
            "target": target,
            "amount": amount,
            **conversion,
        }
        st.session_state.history.insert(0, record)
        st.session_state.history = st.session_state.history[:30]
    except ValueError as exc:
        st.error(str(exc))

last = st.session_state.last_conversion

if last is not None:
    result_source = last["source"]
    result_target = last["target"]
    result_amount = float(last["amount"])
    result_net = float(last["net"])
    result_rate = float(last["rate"])
    result_fee = float(last["fee"])

    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-eyebrow">Vous recevez</div>
            <div class="result-value">{format_number(result_net)} {result_target}</div>
            <div class="result-meta">
                <span class="pill">Pour {format_number(result_amount)} {result_source}</span>
                <span class="pill">1 {result_source} = {format_number(result_rate, 6)} {result_target}</span>
                <span class="pill">Frais : {format_number(result_fee)} {result_target}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    threshold = float(st.session_state.alert_threshold)
    if threshold > 0 and result_net < threshold:
        st.warning(
            f"Le montant reçu ({format_number(result_net)} {result_target}) "
            f"est inférieur à votre seuil de {format_number(threshold)} {result_target}."
        )
else:
    st.markdown(
        """
        <div class="result-card">
            <div class="result-eyebrow">Votre résultat</div>
            <div class="result-value">Prêt à convertir</div>
            <div class="result-meta">
                <span class="pill">Saisissez un montant</span>
                <span class="pill">Puis appuyez sur Convertir</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Secondary navigation
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="features">
        <div class="feature">
            <div class="feature-icon">⌁</div>
            <div class="feature-title">Graphique</div>
            <div class="feature-sub">Évolution sur 30 jours</div>
        </div>
        <div class="feature">
            <div class="feature-icon">◷</div>
            <div class="feature-title">Historique</div>
            <div class="feature-sub">Vos conversions récentes</div>
        </div>
        <div class="feature">
            <div class="feature-icon">▦</div>
            <div class="feature-title">Toutes les devises</div>
            <div class="feature-sub">Recherche rapide</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_history, tab_graph, tab_currencies = st.tabs(
    ["Historique", "Graphique 30j", "Toutes les devises"]
)

with tab_history:
    if st.session_state.history:
        hist_df = pd.DataFrame(st.session_state.history)
        st.markdown("#### Conversions récentes")
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
        csv = hist_df.to_csv(index=False).encode("utf-8")
        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "Télécharger CSV",
                data=csv,
                file_name="deviso_historique.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with d2:
            if st.button("Effacer l'historique", use_container_width=True):
                st.session_state.history = []
                st.rerun()
    else:
        st.markdown(
            '<div class="empty-state">Aucune conversion enregistrée pour le moment.</div>',
            unsafe_allow_html=True,
        )

with tab_graph:
    st.markdown("#### Évolution du taux")
    st.caption(
        f"Paire actuelle : {source} → {target} • période : 30 jours"
    )

    with st.spinner("Chargement de l'historique…"):
        hist, hist_kind = load_history(source, target, 30)

    if hist is not None and len(hist) >= 2:
        chart_df = hist.copy()
        chart_df["Date"] = pd.to_datetime(chart_df["Date"])
        chart_df = chart_df.sort_values("Date").set_index("Date")[["Taux"]]
        st.line_chart(chart_df, height=300)

        first_value = float(chart_df["Taux"].iloc[0])
        last_value = float(chart_df["Taux"].iloc[-1])
        variation = ((last_value / first_value) - 1) * 100 if first_value else 0.0
        direction = "▲" if variation >= 0 else "▼"
        qualifier = {
            "réel": "Données historiques",
            "dérivé": "Taux dérivé du cours EUR/XOF",
        }.get(hist_kind, "Historique")
        st.caption(
            f"{direction} {variation:+.2f}% • {qualifier}"
        )
    else:
        st.markdown(
            """
            <div class="empty-state">
                Historique indisponible pour cette paire actuellement.<br>
                Aucun graphique simulé n'est affiché pour éviter de confondre
                une estimation avec une donnée de marché.
            </div>
            """,
            unsafe_allow_html=True,
        )

with tab_currencies:
    st.markdown("#### Explorer les devises")
    search = st.text_input(
        "Rechercher",
        placeholder="Ex. USD, dollar, CFA…",
        label_visibility="collapsed",
    ).strip().lower()

    base_amount = float(amount)
    rows: list[dict[str, Any]] = []
    for code in currencies:
        name = NOMS_DEVISES.get(code, code)
        haystack = f"{code} {name}".lower()
        if search and search not in haystack:
            continue

        try:
            converted = convert_amount(
                amount=base_amount,
                src=source,
                tgt=code,
                rates=rates,
                fee_pct=0,
            )["net"]
            per_eur = float(rates[code])
        except (ValueError, KeyError):
            continue

        rows.append(
            {
                "Devise": f"{FLAGS.get(code, '◉')} {code}",
                "Nom": name,
                f"{format_number(base_amount)} {source}": format_number(converted),
                "Cours / 1 EUR": format_number(per_eur, 6),
            }
        )

    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            f"{len(rows)} devise(s) affichée(s) • calculé à partir de {format_number(base_amount)} {source}"
        )
    else:
        st.markdown(
            '<div class="empty-state">Aucune devise ne correspond à votre recherche.</div>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Footer / transparency
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <div class="footer-note">
        <strong>DEVIS'O</strong> • Données : Frankfurter.app lorsque disponibles.<br>
        XOF conservé comme taux de référence de secours • Les taux sont indicatifs.<br>
        {"Dernière donnée live : " + format_date(rate_date) if live else "Le mode secours est actif."}
    </div>
    """,
    unsafe_allow_html=True,
)

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import base64


# =========================================================
# CONFIG + ICÔNE
# =========================================================
st.set_page_config(
    page_title="DEVIS'O",
    page_icon="💱",
    layout="centered",
    initial_sidebar_state="collapsed"
)


ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0A84FF"/>
      <stop offset="100%" style="stop-color:#0066CC"/>
    </linearGradient>
  </defs>
  <rect width="100" height="100" rx="24" fill="url(#g)"/>
  <text x="50" y="66" font-size="48" text-anchor="middle" fill="white" font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-weight="600">💱</text>
</svg>
"""
ICON_B64 = base64.b64encode(ICON_SVG.encode()).decode()


st.markdown(f"""
<link rel="icon" href="data:image/svg+xml;base64,{ICON_B64}">
<link rel="apple-touch-icon" href="data:image/svg+xml;base64,{ICON_B64}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#0B0C10">
""", unsafe_allow_html=True)


# =========================================================
# CSS PREMIUM
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');


html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}


.stApp {
    background: linear-gradient(160deg, #0B0C10 0%, #15171F 50%, #0F1117 100%) !important;
}


.main .block-container {
    padding-top: 1.4rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 440px !important;
}


/* Cartes glass */
.card {
    background: rgba(255, 255, 255, 0.045);
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 22px 20px;
    margin-bottom: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
}


.card-result {
    background: linear-gradient(145deg, rgba(10, 132, 255, 0.15), rgba(10, 132, 255, 0.05));
    border: 1px solid rgba(10, 132, 255, 0.25);
}


h1 {
    font-weight: 700 !important;
    letter-spacing: -0.8px !important;
    font-size: 1.9rem !important;
    margin-bottom: 0 !important;
    color: #FFFFFF !important;
}


.subtitle {
    color: #8E8E93 !important;
    font-size: 0.95rem !important;
    margin-top: 4px !important;
    margin-bottom: 22px !important;
    text-align: center;
}


/* Metric géant */
div[data-testid="stMetricValue"] > div {
    font-size: 2.35rem !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
    letter-spacing: -0.5px;
}


div[data-testid="stMetricLabel"] {
    color: #8E8E93 !important;
    font-size: 0.85rem !important;
}


/* Inputs */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
.stNumberInput input {
    background-color: rgba(255, 255, 255, 0.06) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: white !important;
}


/* Tabs */
button[data-baseweb="tab"] {
    color: #8E8E93 !important;
    font-weight: 500 !important;
}
button[aria-selected="true"] {
    color: #FFFFFF !important;
    border-bottom-color: #0A84FF !important;
}


/* Boutons */
div.stButton > button {
    background: linear-gradient(135deg, #0A84FF 0%, #0066CC 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
    height: 46px !important;
    transition: all 0.2s ease;
}
div.stButton > button:hover {
    filter: brightness(1.1);
    box-shadow: 0 4px 20px rgba(10, 132, 255, 0.35);
}


/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(11, 12, 16, 0.97) !important;
}


.stCaption, .stMarkdown p {
    color: #8E8E93 !important;
}


/* Petit badge live */
.badge-live {
    display: inline-block;
    background: rgba(52, 199, 89, 0.15);
    color: #34C759;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 20px;
    letter-spacing: 0.3px;
}
.badge-offline {
    display: inline-block;
    background: rgba(255, 149, 0, 0.15);
    color: #FF9500;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 20px;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# DONNÉES & API
# =========================================================
TAUX_SECOURS = {
    "EUR": 1.0,
    "USD": 1.085,
    "GBP": 0.842,
    "JPY": 162.4,
    "CAD": 1.48,
    "CHF": 0.955,
    "XOF": 655.957
}


@st.cache_data(ttl=1800, show_spinner=False)
def obtenir_taux_reels():
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=EUR", timeout=6)
        r.raise_for_status()
        data = r.json()
        rates = data.get("rates", {})
        rates["EUR"] = 1.0
        return rates, True, data.get("date", "")
    except Exception:
        return {}, False, ""


@st.cache_data(ttl=3600, show_spinner=False)
def obtenir_historique(src: str, tgt: str):
    if src == "XOF" or tgt == "XOF":
        return None
    try:
        fin = datetime.utcnow().date()
        debut = fin - timedelta(days=30)
        url = f"https://api.frankfurter.app/{debut}..{fin}?from={src}&to={tgt}"
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()
        rates = data.get("rates", {})
        if not rates:
            return None
        df = pd.DataFrame([
            {"Date": pd.to_datetime(d), "Taux": v[tgt]}
            for d, v in rates.items()
        ]).sort_values("Date").set_index("Date")
        return df
    except Exception:
        return None


# Fusion : API + XOF forcé
api_rates, est_live, date_taux = obtenir_taux_reels()
taux = TAUX_SECOURS.copy()
taux.update(api_rates)          # l’API écrase, XOF reste
DEVISES = list(taux.keys())


# Session
if "historique" not in st.session_state:
    st.session_state.historique = []
if "source_idx" not in st.session_state:
    st.session_state.source_idx = 0
if "cible_idx" not in st.session_state:
    st.session_state.cible_idx = 1


def inverser():
    st.session_state.source_idx, st.session_state.cible_idx = (
        st.session_state.cible_idx, st.session_state.source_idx
    )


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("### DEVIS'O")
    if est_live:
        st.markdown(f'<span class="badge-live">● LIVE • {date_taux}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-offline">● SECOURS</span>', unsafe_allow_html=True)


    st.write("")
    st.caption("Taux de référence (base EUR)")
    for d in DEVISES:
        st.text(f"{d}  →  {taux[d]:.4f}")


    st.divider()
    if st.button("Effacer l'historique", use_container_width=True):
        st.session_state.historique = []
        st.rerun()


# =========================================================
# HEADER
# =========================================================
st.markdown("<h1 style='text-align:center;'>DEVIS'O</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Conversion de devises simple, rapide et transparente</p>", unsafe_allow_html=True)


# =========================================================
# RÉSULTAT EN PREMIER (très visible)
# =========================================================
# On calcule d'abord pour pouvoir afficher le résultat en haut
# (les widgets sont plus bas)


# Pour que les selectbox fonctionnent, on les met un peu plus bas
# mais le résultat reste le premier élément fort


col_src, col_swap, col_tgt = st.columns([4.2, 1.1, 4.2])


with col_src:
    devise_source = st.selectbox("De", DEVISES, index=st.session_state.source_idx, label_visibility="collapsed", key="src")
with col_swap:
    st.write("")
    if st.button("⇄", help="Inverser", use_container_width=True):
        inverser()
        st.rerun()
with col_tgt:
    devise_cible = st.selectbox("Vers", DEVISES, index=st.session_state.cible_idx, label_visibility="collapsed", key="tgt")


st.session_state.source_idx = DEVISES.index(devise_source)
st.session_state.cible_idx = DEVISES.index(devise_cible)


montant = st.number_input("Montant à convertir", min_value=0.0, value=100.0, step=10.0, format="%.2f")


# Calcul
taux_src = taux[devise_source]
taux_cbl = taux[devise_cible]
montant_eur = montant / taux_src if taux_src else 0
conversion_brute = montant_eur * taux_cbl
frais_pct = st.slider("Frais de l'opérateur (%)", 0.0, 5.0, 0.0, 0.05, help="Laissez à 0 si aucun frais")
frais = conversion_brute * (frais_pct / 100)
resultat = conversion_brute - frais
taux_affiche = taux_cbl / taux_src if taux_src else 0


# ========== RÉSULTAT PRINCIPAL ==========
st.markdown('<div class="card card-result">', unsafe_allow_html=True)
st.metric(
    label=f"Vous recevez",
    value=f"{resultat:,.2f} {devise_cible}"
)
st.caption(f"1 {devise_source} = {taux_affiche:.4f} {devise_cible}   •   Frais : {frais:,.2f} {devise_cible}")
st.markdown('</div>', unsafe_allow_html=True)


# Alerte seuil
seuil = st.number_input("M'alerter si le résultat est inférieur à", min_value=0.0, value=0.0, step=50.0, label_visibility="collapsed", placeholder="Seuil d'alerte (optionnel)")
if seuil > 0 and resultat < seuil:
    st.warning(f"Le montant obtenu est inférieur à votre seuil de {seuil:,.2f} {devise_cible}")


# =========================================================
# ONGLETS
# =========================================================
tab1, tab2, tab3 = st.tabs(["Historique", "Graphique 30j", "Toutes les devises"])


with tab1:
    if montant > 0:
        entree = {
            "Heure": datetime.now().strftime("%H:%M"),
            "Détail": f"{montant:,.2f} {devise_source} → {resultat:,.2f} {devise_cible}",
            "Taux": f"{taux_affiche:.4f}"
        }
        if not st.session_state.historique or st.session_state.historique[0]["Détail"] != entree["Détail"]:
            st.session_state.historique.insert(0, entree)
            st.session_state.historique = st.session_state.historique[:15]


    if st.session_state.historique:
        df = pd.DataFrame(st.session_state.historique)
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Télécharger CSV", data=csv, file_name="deviso_historique.csv", mime="text/csv", use_container_width=True)
    else:
        st.caption("Aucune conversion pour le moment.")


with tab2:
    with st.spinner("Chargement…"):
        df_hist = obtenir_historique(devise_source, devise_cible)


    if df_hist is not None and len(df_hist) > 2:
        st.line_chart(df_hist, color="#0A84FF", height=260)
        var = ((df_hist["Taux"].iloc[-1] / df_hist["Taux"].iloc[0]) - 1) * 100
        st.caption(f"{'▲' if var >= 0 else '▼'} {var:+.2f}% sur 30 jours • Données réelles")
    else:
        st.caption("Historique réel indisponible pour cette paire (XOF non supporté). Simulation :")
        np.random.seed(hash(devise_source + devise_cible) % 2**32)
        dates = pd.date_range(end=datetime.today(), periods=30)
        base = taux_affiche
        noise = np.random.normal(0, 0.002, 30).cumsum()
        sim = pd.DataFrame({"Taux": base + noise}, index=dates)
        st.line_chart(sim, color="#0A84FF", height=260)


with tab3:
    st.caption(f"Valeur de {montant:,.2f} {devise_source}")
    rows = []
    for d in DEVISES:
        val = (montant / taux[devise_source]) * taux[d]
        rows.append({"Devise": d, "Montant": f"{val:,.2f}", "Cours EUR": f"{taux[d]:.4f}"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# Footer
st.write("")
st.caption("Données : Frankfurter.app • XOF en taux fixe • À titre indicatif")

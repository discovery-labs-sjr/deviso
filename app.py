import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from io import BytesIO
import base64


# =========================================================
# 1. CONFIGURATION + ICÔNE PERSONNALISÉE
# =========================================================
st.set_page_config(
    page_title="DEVIS'O",
    page_icon="💱",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# SVG icône personnalisée (thème bleu Apple / glass)
ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#007aff"/>
      <stop offset="100%" style="stop-color:#0056b3"/>
    </linearGradient>
  </defs>
  <rect width="100" height="100" rx="22" fill="url(#g)"/>
  <text x="50" y="68" font-size="52" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-weight="700">💱</text>
</svg>
"""
ICON_B64 = base64.b64encode(ICON_SVG.encode()).decode()


st.markdown(f"""
<link rel="icon" href="data:image/svg+xml;base64,{ICON_B64}">
<link rel="apple-touch-icon" href="data:image/svg+xml;base64,{ICON_B64}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0d0e15">
""", unsafe_allow_html=True)


# =========================================================
# 2. CSS LIQUID GLASS
# =========================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0d0e15 0%, #1a1c29 100%) !important;
}
.main .block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
    max-width: 480px !important;
}
.apple-container {
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    border-radius: 22px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    padding: 20px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    margin-top: 8px;
    margin-bottom: 16px;
}
h1, h2, h3, h4, p, span, label, div, li {
    color: #ffffff !important;
}
div[data-testid="stMetricValue"] > div {
    color: #ffffff !important;
    font-size: 2.1rem !important;
    font-weight: 700 !important;
}
div[data-testid="stMetricLabel"] > div {
    color: #a1a1a6 !important;
}
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background-color: rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
}
button[data-baseweb="tab"] {
    color: #86868b !important;
}
button[aria-selected="true"] {
    color: #ffffff !important;
    border-bottom-color: #007aff !important;
}
div.stButton > button {
    background: linear-gradient(135deg, #007aff 0%, #0056b3 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
    padding: 11px 18px !important;
    width: 100% !important;
}
div[data-testid="stSidebar"] {
    background: rgba(13, 14, 21, 0.95) !important;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# 3. TAUX DE SECOURS + API
# =========================================================
TAUX_SECOURS = {
    "EUR": 1.0,
    "USD": 1.09,
    "GBP": 0.85,
    "JPY": 165.50,
    "CAD": 1.50,
    "CHF": 0.96,
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
        # Ne garder que les devises supportées
        return {k: rates[k] for k in TAUX_SECOURS if k in rates}, True, data.get("date", "")
    except Exception:
        return TAUX_SECOURS.copy(), False, ""


@st.cache_data(ttl=3600, show_spinner=False)
def obtenir_historique(devise_source: str, devise_cible: str):
    """Récupère les 30 derniers jours de taux réels via Frankfurter"""
    try:
        fin = datetime.utcnow().date()
        debut = fin - timedelta(days=30)
        # Frankfurter ne gère pas XOF → on fallback
        if devise_source == "XOF" or devise_cible == "XOF":
            return None
        url = f"https://api.frankfurter.app/{debut}..{fin}?from={devise_source}&to={devise_cible}"
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()
        rates = data.get("rates", {})
        if not rates:
            return None
        df = pd.DataFrame([
            {"Date": pd.to_datetime(d), "Taux": v[devise_cible]}
            for d, v in rates.items()
        ]).sort_values("Date").set_index("Date")
        return df
    except Exception:
        return None


# =========================================================
# 4. SESSION STATE
# =========================================================
if "historique" not in st.session_state:
    st.session_state.historique = []


if "source_idx" not in st.session_state:
    st.session_state.source_idx = 0
if "cible_idx" not in st.session_state:
    st.session_state.cible_idx = 1


taux, est_live, date_taux = obtenir_taux_reels()
st.session_state.taux = taux
DEVISES = list(taux.keys())


def inverser_devises():
    st.session_state.source_idx, st.session_state.cible_idx = (
        st.session_state.cible_idx,
        st.session_state.source_idx
    )


# =========================================================
# 5. SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("### 💧 DEVIS'O Réglages")
    if est_live:
        st.success(f"Taux live • {date_taux}")
    else:
        st.warning("Taux de secours (API indisponible)")


    st.caption("Taux de référence (base EUR)")
    for d in DEVISES:
        st.text(f"{'💶' if d == 'EUR' else '🔄'} {d} : {taux[d]:.4f}")


    st.divider()
    if st.button("🗑️ Effacer l'historique", use_container_width=True):
        st.session_state.historique = []
        st.rerun()


# =========================================================
# 6. INTERFACE PRINCIPALE
# =========================================================
st.markdown("<h1 style='text-align:center;font-weight:700;letter-spacing:-1px;margin-bottom:0;'>DEVIS'O</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#a1a1a6;font-size:15px;margin-top:4px;margin-bottom:20px;'>Le change de devises, version fluide et transparente.</p>", unsafe_allow_html=True)


st.markdown('<div class="apple-container">', unsafe_allow_html=True)


onglet1, onglet2, onglet3 = st.tabs(["💱 Convertir", "📊 Graphique", "📋 Vue d'ensemble"])


# -------------------- ONGLET 1 : CONVERTIR --------------------
with onglet1:
    col_m, col_f = st.columns(2)
    with col_m:
        montant = st.number_input("Montant", min_value=0.0, value=200.0, step=1.0, format="%.2f")
    with col_f:
        frais_pourcent = st.slider("Frais opérateur (%)", 0.0, 5.0, 0.0, 0.1)


    c1, c_btn, c2 = st.columns([4.2, 1.2, 4.2])
    with c1:
        devise_source = st.selectbox("De", DEVISES, index=st.session_state.source_idx, key="src")
    with c_btn:
        st.write("")
        st.write("")
        if st.button("🔄", help="Inverser les devises", use_container_width=True):
            inverser_devises()
            st.rerun()
    with c2:
        devise_cible = st.selectbox("Vers", DEVISES, index=st.session_state.cible_idx, key="tgt")


    # Mettre à jour les index
    st.session_state.source_idx = DEVISES.index(devise_source)
    st.session_state.cible_idx = DEVISES.index(devise_cible)


    # Calcul
    taux_src = taux[devise_source]
    taux_cbl = taux[devise_cible]
    montant_en_eur = montant / taux_src if taux_src else 0
    conversion_brute = montant_en_eur * taux_cbl
    montant_frais = conversion_brute * (frais_pourcent / 100)
    conversion_finale = conversion_brute - montant_frais
    taux_reel = taux_cbl / taux_src if taux_src else 0


    # Alerte seuil
    seuil_alerte = st.number_input("Alerte si résultat < (optionnel)", min_value=0.0, value=0.0, step=10.0)


    st.write("")
    st.metric(
        label=f"Total converti ({devise_cible})",
        value=f"{conversion_finale:,.2f} {devise_cible}"
    )
    st.caption(f"1 {devise_source} = {taux_reel:.4f} {devise_cible}  •  Frais : {montant_frais:,.2f} {devise_cible}")


    if seuil_alerte > 0 and conversion_finale < seuil_alerte:
        st.warning(f"⚠️ Le montant obtenu ({conversion_finale:,.2f}) est inférieur au seuil de {seuil_alerte:,.2f} {devise_cible}")


    # Ajout automatique à l'historique (seulement si montant > 0)
    if montant > 0:
        entree = {
            "Heure": datetime.now().strftime("%H:%M:%S"),
            "Conversion": f"{montant:,.2f} {devise_source} → {conversion_finale:,.2f} {devise_cible}",
            "Taux": f"{taux_reel:.4f}"
        }
        # Évite les doublons trop rapprochés
        if not st.session_state.historique or st.session_state.historique[0]["Conversion"] != entree["Conversion"]:
            st.session_state.historique.insert(0, entree)
            # Limite à 20 entrées
            st.session_state.historique = st.session_state.historique[:20]


    # Historique
    if st.session_state.historique:
        st.markdown("##### 📜 Historique de la session")
        df_hist = pd.DataFrame(st.session_state.historique)
        st.dataframe(df_hist, use_container_width=True, hide_index=True)


        csv = df_hist.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Télécharger l'historique (CSV)",
            data=csv,
            file_name="historique_deviso.csv",
            mime="text/csv",
            use_container_width=True
        )


# -------------------- ONGLET 2 : GRAPHIQUE RÉEL --------------------
with onglet2:
    st.markdown(f"#### Tendance {devise_source} → {devise_cible}")
    
    with st.spinner("Chargement des 30 derniers jours…"):
        df_hist = obtenir_historique(devise_source, devise_cible)


    if df_hist is not None and not df_hist.empty:
        st.line_chart(df_hist, color="#007aff", height=280)
        variation = ((df_hist["Taux"].iloc[-1] / df_hist["Taux"].iloc[0]) - 1) * 100
        couleur = "🟢" if variation >= 0 else "🔴"
        st.caption(f"{couleur} Variation sur 30 jours : {variation:+.2f}%  •  Données réelles Frankfurter")
    else:
        st.info("Graphique historique non disponible pour cette paire (XOF non supporté par l’API ou erreur réseau). Affichage d’une simulation.")
        np.random.seed(sum(ord(c) for c in devise_source + devise_cible))
        dates = pd.date_range(end=datetime.today(), periods=30)
        base = taux[devise_cible] / taux[devise_source]
        variations = np.random.normal(0, 0.0025, 30).cumsum()
        sim = pd.DataFrame({"Taux": base + variations}, index=dates)
        st.line_chart(sim, color="#007aff", height=280)
        st.caption("⚠️ Données simulées (à titre illustratif)")


# -------------------- ONGLET 3 : VUE D'ENSEMBLE --------------------
with onglet3:
    st.markdown(f"#### {montant:,.2f} {devise_source} convertis")
    rows = []
    for d in DEVISES:
        val = (montant / taux[devise_source]) * taux[d]
        rows.append({
            "Devise": d,
            "Montant": f"{val:,.2f}",
            "Cours (1 EUR)": f"{taux[d]:.4f}"
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


st.markdown('</div>', unsafe_allow_html=True)


# Footer
st.caption("Données fournies par Frankfurter.app • À titre indicatif uniquement • DEVIS'O")

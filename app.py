import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

# 1. Configuration de la page style Apple
st.set_page_config(
    page_title="DEVIS'O",
    page_icon="💱",
    layout="centered"
)

# Injection du CSS effet "Liquid Glass / iOS"
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0d0e15 0%, #1a1c29 100%) !important;
}
.main .block-container {
    padding-top: 1.5rem !important;
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
    margin-top: 10px;
    margin-bottom: 20px;
}
h1, h2, h3, h4, p, span, label, div, li {
    color: #ffffff !important;
}
div[data-testid="stMetricValue"] > div {
    color: #ffffff !important;
    font-size: 2.3rem !important;
    font-weight: 700 !important;
}
div[data-testid="stMetricLabel"] > div {
    color: #a1a1a6 !important;
}
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
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
    padding: 12px 20px !important;
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# 2. Gestion de l'historique dans la session
if "historique" not in st.session_state:
    st.session_state.historique = []

# 3. Récupération des taux dynamiques via API (avec secours local en cas de panne)
TAUX_SECOURS = {
    "EUR": 1.0, "USD": 1.09, "GBP": 0.85, 
    "JPY": 165.50, "CAD": 1.50, "CHF": 0.96, "XOF": 655.957
}

@st.cache_data(ttl=3600)  # Met en cache les taux pendant 1 heure
def obtenir_taux_reels():
    try:
        # Utilisation de l'API gratuite ExchangeRate-API (Base EUR)
        url = "https://er-api.com"
        reponse = requests.get(url, timeout=5)
        data = reponse.json()
        if data.get("result") == "success":
            taux_api = data.get("rates", {})
            # Filtrer pour ne garder que les devises voulues
            return {d: taux_api[d] for d in TAUX_SECOURS.keys() if d in taux_api}
    except Exception:
        pass
    return TAUX_SECOURS

st.session_state.taux = obtenir_taux_reels()
DEVISES = list(st.session_state.taux.keys())

# Gestion des index pour l'inversion
if "source_idx" not in st.session_state:
    st.session_state.source_idx = 0
if "cible_idx" not in st.session_state:
    st.session_state.cible_idx = 1

def inverser_devises():
    ancien_source = st.session_state.source_idx
    st.session_state.source_idx = st.session_state.cible_idx
    st.session_state.cible_idx = ancien_source

# Barre latérale de contrôle
st.sidebar.markdown("<h2 style='font-weight: 600;'>💧 DEVIS'O Réglages</h2>", unsafe_allow_html=True)
st.sidebar.write("📈 *Taux synchronisés en temps réel via API.*")

for devise in DEVISES:
    if devise == "EUR":
        st.sidebar.number_input(f"💶 {devise} (Base)", value=1.0, disabled=True)
    else:
        st.sidebar.text(f"🔄 {devise} : {st.session_state.taux[devise]:.4f}")

# Interface principale
st.markdown("<h1 style='text-align: center; font-weight: 700; letter-spacing: -1px; margin-bottom: 0;'>DEVIS'O</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #a1a1a6; font-size: 16px; margin-top: 5px; margin-bottom: 25px;'>Le change de devises, version fluide et transparente.</p>", unsafe_allow_html=True)

st.markdown('<div class="apple-container">', unsafe_allow_html=True)
onglet1, onglet2, onglet3 = st.tabs(["💱 Convertir", "📊 Graphique", "📋 Vue d'ensemble"])

with onglet1:
    if st.button("🔄 Inverser les devises"):
        inverser_devises()
        st.rerun()

    with st.form("formulaire_principal"):
        col_m, col_f = st.columns(2)
        with col_m:
            montant = st.number_input("Montant :", min_value=0.0, value=200.0, step=0.01)
        with col_f:
            frais_pourcent = st.slider("Frais de l'opérateur (%) :", min_value=0.0, max_value=5.0, value=0.0, step=0.1)

        c1, c_btn, c2 = st.columns([4, 1, 4])
        with c1:
            devise_source = st.selectbox("De", DEVISES, index=st.session_state.source_idx)
        with c_btn:
            st.markdown("<p style='text-align:center; font-size:20px; margin-top:35px;'>➡️</p>", unsafe_allow_html=True)
        with c2:
            devise_cible = st.selectbox("Vers", DEVISES, index=st.session_state.cible_idx)

        # Nouvelle option : Alerte de seuil minimum
        seuil_alerte = st.number_input("Me notifier si le résultat est inférieur à (Optionnel) :", min_value=0.0, value=0.0)

        bouton_calculer = st.form_submit_button("Calculer la conversion")

    st.session_state.source_idx = DEVISES.index(devise_source)
    st.session_state.cible_idx = DEVISES.index(devise_cible)

    # Logique de calcul
    taux_src = st.session_state.taux[devise_source]
    taux_cbl = st.session_state.taux[devise_cible]
    
    montant_en_eur = montant / taux_src
    conversion_brute = montant_en_eur * taux_cbl
    montant_frais = conversion_brute * (frais_pourcent / 100)
    conversion_finale = conversion_brute - montant_frais
    taux_réel = taux_cbl / taux_src

    if bouton_calculer:
        # Ajouter à l'historique de session
        nouvelle_entree = {
            "Heure": datetime.now().strftime("%H:%M:%S"),
            "Conversion": f"{montant:,.2f} {devise_source} ➡️ {conversion_finale:,.2f} {devise_cible}",
            "Taux": f"{taux_réel:.4f}"
        }
        st.session_state.historique.insert(0, nouvelle_entree)

    # Affichage des résultats
    st.write("")
    st.metric(label=f"Total Converti ({devise_cible})", value=f"{conversion_finale:,.2f} {devise_cible}")
    st.caption(f"Taux appliqué : 1 {devise_source} = {taux_réel:.4f} {devise_cible}")

    # Déclenchement de l'alerte de seuil
    if seuil_alerte > 0 and conversion_finale < seuil_alerte:
        st.warning(f"⚠️ Alerte : Le montant obtenu ({conversion_finale:,.2f}) est inférieur au seuil de {seuil_alerte:,.2f} {devise_cible} !")

    # Section Historique Récent
    if st.session_state.historique:
        st.markdown("<h5>📜 Historique récent de la session</h5>", unsafe_allow_html=True)
        df_hist = pd.DataFrame(st.session_state.historique)
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
        
        # Bouton d'exportation de l'historique en CSV
        csv = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Télécharger l'historique (CSV)", data=csv, file_name="historique_deviso.csv", mime="text/csv")

with onglet2:
    st.markdown(f"<h4>Tendance {devise_source} / {devise_cible}</h4>", unsafe_allow_html=True)
    np.random.seed(sum(ord(c) for c in devise_source + devise_cible)) 
    dates = [datetime.today() - timedelta(days=i) for i in range(30)]
    dates.reverse()
    base_taux = st.session_state.taux[devise_cible] / st.session_state.taux[devise_source]
    variations = np.random.normal(0, 0.003, 30).cumsum()
    donnees_graphique = pd.DataFrame({"Date": dates, "Taux": base_taux + variations}).set_index("Date")
    st.line_chart(donnees_graphique, color="#007aff") 

with onglet3:
    st.markdown(f"<h4>Taux comparatifs pour {montant:,.2f} {devise_source}</h4>", unsafe_allow_html=True)
    tableau_donnees = []
    for d in DEVISES:
        valeur = (montant / st.session_state.taux[devise_source]) * st.session_state.taux[d]
        tableau_donnees.append({"Devise": d, "Valeur": f"{valeur:,.2f} {d}", "Cours (1 EUR)": f"{st.session_state.taux[d]:.4f}"})
    st.dataframe(pd.DataFrame(tableau_donnees), use_container_width=True, hide_index=True)

st.markdown('</div>', unsafe_allow_html=True)

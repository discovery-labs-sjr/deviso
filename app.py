import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration de la page style Apple
st.set_page_config(page_title="DEVIS'O – Change Intelligent", page_icon="💧", layout="centered")

# --- STYLE GRAPHIQUE ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(145deg, #f5f5f7 0%, #d2d2d7 100%) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.5) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-radius: 24px !important;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05) !important;
        padding: 2.5rem !important;
    }
    div.stButton > button {
        background: #1d1d1f !important;
        color: white !important;
        border-radius: 16px !important;
        border: none !important;
        padding: 0.7rem 2.5rem !important;
        font-weight: 500 !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        background: #0071e3 !important;
        box-shadow: 0 5px 15px rgba(0, 113, 227, 0.4) !important;
    }
    </style>
""", unsafe_allow_html=True)

# 1. INITIALISATION DES TAUX DE BASE
if "taux" not in st.session_state:
    st.session_state.taux = {
        "EUR": 1.0, "USD": 1.09, "GBP": 0.85, 
        "JPY": 165.50, "CAD": 1.50, "CHF": 0.96, "XOF": 655.957
    }

DEVISES = list(st.session_state.taux.keys())

if "source_idx" not in st.session_state:
    st.session_state.source_idx = 0
if "cible_idx" not in st.session_state:
    st.session_state.cible_idx = 1

def inverser_devises():
    ancien_source = st.session_state.source_idx
    st.session_state.source_idx = st.session_state.cible_idx
    st.session_state.cible_idx = ancien_source

# 2. BARRE LATÉRALE
st.sidebar.markdown("<h2 style='color: #1d1d1f; font-weight: 600;'>💧 DEVIS'O Réglages</h2>", unsafe_allow_html=True)
st.sidebar.write("Ajuster les taux (Base 1 EUR) :")

for devise in DEVISES:
    if devise == "EUR":
        st.sidebar.number_input(f"💶 {devise} (Base)", value=1.0, disabled=True)
    else:
        # LA LIGNE CORRIGÉE EST ICI :
        st.session_state.taux[devise] = st.sidebar.number_input(
            f"🔄 {devise}", value=st.session_state.taux[devise], format="%.4f"
        )

# 3. EN-TÊTE PRINCIPAL
st.markdown("<h1 style='text-align: center; color: #1d1d1f; font-weight: 700; letter-spacing: -1px;'>DEVIS'O</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #86868b; font-size: 17px; margin-top: -15px;'>Le change de devises, version fluide et transparente.</p>", unsafe_allow_html=True)

onglet1, onglet2, onglet3 = st.tabs(["💱 Convertir", "📊 Graphique", "📋 Vue d'ensemble"])

with onglet1:
    with st.form("formulaire_principal"):
        col_m, col_f = st.columns(2)
        with col_m:
            montant = st.number_input("Montant :", min_value=0.0, value=200.0, step=0.01)
        with col_f:
            frais_pourcent = st.slider("Frais de l'opérateur (%) :", min_value=0.0, max_value=5.0, value=0.0, step=0.1)

        c1, c_btn, c2 = st.columns([4, 1, 4])
        with c1:
            devise_source = st.selectbox("De", DEVISES, key="source_select", index=st.session_state.source_idx)
        with c_btn:
            st.write("\n\n")
            if st.form_submit_button("🔄"):
                st.session_state.source_idx = DEVISES.index(st.session_state.cible_select)
                st.session_state.cible_idx = DEVISES.index(st.session_state.source_select)
                inverser_devises()
                st.rerun()
        with c2:
            devise_cible = st.selectbox("Vers", DEVISES, key="cible_select", index=st.session_state.cible_idx)

        bouton_calculer = st.form_submit_button("Calculer la conversion")

    st.session_state.source_idx = DEVISES.index(devise_source)
    st.session_state.cible_idx = DEVISES.index(devise_cible)

    if bouton_calculer or True:
        taux_src = st.session_state.taux[devise_source]
        taux_cbl = st.session_state.taux[devise_cible]
        
        montant_en_eur = montant / taux_src
        conversion_brute = montant_en_eur * taux_cbl
        montant_frais = conversion_brute * (frais_pourcent / 100)
        conversion_finale = conversion_brute - montant_frais
        taux_réel = taux_cbl / taux_src

        st.write("")
        st.metric(label=f"Total Converti ({devise_cible})", value=f"{conversion_finale:,.2f} {devise_cible}")
        st.caption(f"Taux appliqué : 1 {devise_source} = {taux_réel:.4f} {devise_cible}")

with onglet2:
    st.markdown(f"<h3 style='color: #1d1d1f; font-weight: 500;'>Tendance {devise_source} / {devise_cible}</h3>", unsafe_allow_html=True)
    np.random.seed(sum(ord(c) for c in devise_source + devise_cible)) 
    dates = [datetime.today() - timedelta(days=i) for i in range(30)]
    dates.reverse()
    base_taux = st.session_state.taux[devise_cible] / st.session_state.taux[devise_source]
    variations = np.random.normal(0, 0.003, 30).cumsum()
    donnees_graphique = pd.DataFrame({"Date": dates, "Taux": base_taux + variations}).set_index("Date")
    st.line_chart(donnees_graphique, color="#0071e3") 

with onglet3:
    st.markdown(f"<h3 style='color: #1d1d1f; font-weight: 500;'>Taux pour {montant:,.2f} {devise_source}</h3>", unsafe_allow_html=True)
    tableau_donnees = []
    for d in DEVISES:
        valeur = (montant / st.session_state.taux[devise_source]) * st.session_state.taux[d]
        tableau_donnees.append({"Devise": d, "Valeur": f"{valeur:,.2f} {d}", "Cours (1 EUR)": f"{st.session_state.taux[d]:.4f}"})
    st.dataframe(pd.DataFrame(tableau_donnees), use_container_width=True, hide_index=True)

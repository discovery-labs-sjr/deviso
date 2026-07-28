import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration de la page style Apple
st.set_page_config(page_title="DEVIS'O – Change Intelligent", page_icon="💧", layout="centered")

# --- CSS RADICAL DE VISIBILITÉ POUR MOBILE ---
st.markdown("""
    <style>
    /* Fond dégradé global */
    .stApp {
        background: linear-gradient(145deg, #f5f5f7 0%, #d2d2d7 100%) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    /* On supprime absolument TOUS les fonds blancs par défaut de Streamlit */
    div[data-testid="stForm"], 
    .stFormSubmitButton, 
    div[data-testid="stMetric"],
    div[data-testid="stMetricValue"] {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* BLOCAGE DE LA SURCOUCHE BLANCHE SUR LES CHIFFRES ET ENCRE NOIRE INTENSE */
    div[data-testid="stMetricValue"] > div {
        color: #1d1d1f !important; /* Noir profond style Apple */
        font-size: 2.5rem !important; /* Écrit en très gros */
        font-weight: 700 !important; /* Texte très épais */
        text-shadow: 0px 1px 2px rgba(255, 255, 255, 0.8) !important; /* Ombre blanche derrière pour détacher le texte */
    }
    
    div[data-testid="stMetricLabel"] > div {
        color: #515154 !important; /* Gris foncé pour le libellé */
        font-weight: 600 !important;
    }

    /* Notre boîte principale en verre translucide épuré */
    .apple-box {
        background: rgba(255, 255, 255, 0.5) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03) !important;
        padding: 20px !important;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    
    /* Bouton d'action */
    div.stButton > button {
        background: #1d1d1f !important;
        color: white !important;
        border-radius: 14px !important;
        border: none !important;
        padding: 0.7rem 2rem !important;
        font-weight: 500 !important;
        width: 100% !important;
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

# 3. EN-TÊTE PRINCIPAL
st.markdown("<h1 style='text-align: center; color: #1d1d1f; font-weight: 700; letter-spacing: -1px; margin-bottom: 0;'>DEVIS'O</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #515154; font-size: 16px; margin-top: 5px;'>Le change de devises, version fluide et transparente.</p>", unsafe_allow_html=True)

# DEBUT DU BLOC STYLE APPLE
st.markdown('<div class="apple-box">', unsafe_allow_html=True)

onglet1, onglet2, onglet3 = st.tabs(["💱 Convertir", "📊 Graphique", "📋 Vue d'ensemble"])

with onglet1:
    with st.form("formulaire_principal"):
        col_m, col_f = st.columns(2)
        with col_m:
            montant = st.number_input("Montant :", min_value=0.0, value=200.0, step=0.01)
        with col_f:
            frais_pourcent = st.slider("Frais de l'opérateur (%) :", min_value=0.0, max_value=5.0, value=0.0, step=0.1)

        c1, c_btn, c2 = st.columns(3)
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
    st.markdown(f"<h4 style='color: #1d1d1f; font-weight: 500;'>Tendance {devise_source} / {devise_cible}</h4>", unsafe_allow_html=True)
    np.random.seed(sum(ord(c) for c in devise_source + devise_cible)) 
    dates = [datetime.today() - timedelta(days=i) for i in range(30)]
    dates.reverse()
    base_taux = st.session_state.taux[devise_cible] / st.session_state.taux[devise_source]
    variations = np.random.normal(0, 0.003, 30).cumsum()
    donnees_graphique = pd.DataFrame({"Date": dates, "Taux": base_taux + variations}).set_index("Date")
    st.line_chart(donnees_graphique, color="#0071e3") 

with onglet3:
    st.markdown(f"<h4 style='color: #1d1d1f; font-weight: 500;'>Taux pour {montant:,.2f} {devise_source}</h4>", unsafe_allow_html=True)
    tableau_donnees = []
    for d in DEVISES:
        valeur = (montant / st.session_state.taux[devise_source]) * st.session_state.taux[d]
        tableau_donnees.append({"Devise": d, "Valeur": f"{valeur:,.2f} {d}", "Cours (1 EUR)": f"{st.session_state.taux[d]:.4f}"})
    st.dataframe(pd.DataFrame(tableau_donnees), use_container_width=True, hide_index=True)

st.markdown('</div>', unsafe_allow_html=True) # FIN DU BLOC

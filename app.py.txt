import streamlit as st
import requests
import urllib3

# Désactive les alertes de sécurité dans le terminal
urllib3.disable_warnings()

st.set_page_config(page_title="Convertisseur de Devises", page_icon="💱", layout="centered")

st.title("💱 Convertisseur de Devises en Temps Réel")
st.write("Cette application utilise des taux de change mis à jour en direct.")

DEVISES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "XOF"]

with st.form("convertisseur_form"):
    montant = st.number_input("Montant à convertir :", min_value=0.0, value=1.0, step=0.01)
    
    col1, col2 = st.columns(2)
    with col1:
        devise_source = st.selectbox("De (Devise d'origine) :", DEVISES, index=1)
    with col2:
        devise_cible = st.selectbox("Vers (Devise de destination) :", DEVISES, index=0)
        
    bouton_valider = st.form_submit_button("Convertir")

if bouton_valider:
    if devise_source == devise_cible:
        st.success(f"**{montant:,.2f} {devise_source}** est égal à **{montant:,.2f} {devise_cible}**")
    else:
        url = f"https://er-api.com{devise_source}"
        
        try:
            # AJOUT DE VERIFY=FALSE POUR EVITER LE BLOCAGE WINDOWS
            reponse = requests.get(url, verify=False)
            donnees = reponse.json()
            
            if donnees.get("result") == "success":
                taux = donnees["rates"].get(devise_cible)
                
                if taux:
                    resultat = montant * taux
                    st.metric(
                        label=f"Résultat de la conversion ({devise_source} ➡️ {devise_cible})",
                        value=f"{resultat:,.2f} {devise_cible}"
                    )
                    st.info(f"Taux de change actuel : 1 {devise_source} = {taux:.4f} {devise_cible}")
                else:
                    st.error("Impossible de trouver le taux pour la devise cible.")
            else:
                st.error("Erreur lors de la récupération des taux de change.")
                
        except Exception as e:
            st.error("Erreur de connexion. Veuillez vérifier votre accès internet.")

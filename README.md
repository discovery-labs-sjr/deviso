# DEVIS'O

Convertisseur de devises moderne, mobile-first et lisible.

## Fonctionnalités

- conversion explicite avec bouton **Convertir**
- inversion des devises sans désynchronisation des champs
- taux live via Frankfurter.app avec mode secours
- gestion du XOF sans le laisser être écrasé par la réponse API
- frais d'opérateur optionnels
- seuil d'avertissement local
- historique des conversions enregistrées dans la session
- export CSV
- graphique 30 jours avec données réelles lorsque disponibles
- historique dérivé pour les paires impliquant XOF au lieu d'une fausse simulation
- recherche dans les devises disponibles

## Lancer en local

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Déploiement

Pour Render, utilisez :

- **Runtime** : Python
- **Build command** : `pip install -r requirements.txt`
- **Start command** : `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`

Aucune clé API n'est requise pour la configuration actuelle.

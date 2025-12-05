# Stock Market Screener PWA - Guide d'installation

## 📋 Prérequis

- Python 3.x
- pip (gestionnaire de paquets Python)

## 🚀 Installation

### 1. Installer les dépendances Python

Dans le dossier PWA, exécutez :

```bash
pip install -r requirements.txt
```

Ou manuellement :

```bash
pip install tradingview-screener yfinance pandas
```

### 2. Lancer l'application

```bash
./start_app.sh
```

Ou manuellement :

```bash
python server.py
```

### 3. Accéder à l'application

Ouvrez votre navigateur à l'adresse : **http://localhost:8000**

## 💡 Utilisation

1. **Screening** : Cliquez sur "Lancer le Screening" dans l'onglet Screening
   - Le serveur exécutera automatiquement le code Python
   - Les données de TradingView et Yahoo Finance seront récupérées en temps réel
   - Les résultats s'afficheront dans le tableau

2. **Backtest** : Configurez vos paramètres et lancez le backtest (fonctionnalité à venir)

3. **Paramètres** : Ajustez les critères de screening et de stratégie selon vos besoins

## 🔧 Fonctionnement technique

- **Frontend** : Application web progressive (PWA) en HTML/CSS/JavaScript
- **Backend** : Serveur Python personnalisé (`server.py`)
- **Screening** : Utilise le code du notebook `screener.ipynb`
  - Interroge TradingView pour la pré-sélection
  - Filtre avec Yahoo Finance (VWAP)
  - Renvoie les résultats en JSON à l'application

## 📝 Notes

- Le screening peut prendre quelques minutes selon le nombre d'actions à analyser
- Les données sont récupérées en temps réel à chaque demande
- L'application fonctionne hors ligne après la première visite (PWA)

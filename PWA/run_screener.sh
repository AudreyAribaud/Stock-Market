#!/bin/bash

echo "🚀 Mise à jour des données du Screener..."
echo "----------------------------------------"

# Vérifier si python3 est disponible
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Erreur: Python n'est pas installé."
    exit 1
fi

# Lancer le script de génération de données
$PYTHON_CMD generate_data.py

echo ""
echo "✅ Données mises à jour !"
echo "----------------------------------------"
echo "🌐 Lancement du serveur PWA..."
echo "   Accédez à http://localhost:8000"
echo ""

# Lancer le serveur HTTP
$PYTHON_CMD -m http.server 8000

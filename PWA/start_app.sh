#!/bin/bash

echo "🚀 Démarrage de l'application Stock Market Screener..."
echo "----------------------------------------------------"

# Vérifier si python3 est disponible
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Erreur: Python n'est pas installé."
    exit 1
fi

echo "🌐 Lancement du serveur intelligent..."
echo "   Le screener sera exécuté à la demande depuis l'interface."
echo "   Accédez à http://localhost:8000"
echo ""

# Lancer le serveur Python intelligent
$PYTHON_CMD server.py

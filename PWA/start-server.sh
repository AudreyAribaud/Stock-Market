#!/bin/bash

# Script pour lancer le serveur local de la PWA Stock Market Screener

echo "🚀 Lancement du serveur Stock Market Screener PWA..."
echo ""
echo "L'application sera accessible sur:"
echo "  http://localhost:8000"
echo ""
echo "Pour installer l'application:"
echo "  1. Ouvrez http://localhost:8000 dans votre navigateur"
echo "  2. Cliquez sur le bouton '📥 Installer' dans le header"
echo "  3. Confirmez l'installation"
echo ""
echo "Pour visualiser les icônes:"
echo "  Ouvrez http://localhost:8000/icons-preview.html"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

# Vérifier si Python est installé
if command -v python3 &> /dev/null; then
    python3 -m http.server 8000
elif command -v python &> /dev/null; then
    python -m http.server 8000
else
    echo "❌ Python n'est pas installé. Veuillez installer Python pour lancer le serveur."
    echo ""
    echo "Alternatives:"
    echo "  - Node.js: npx http-server -p 8000"
    echo "  - PHP: php -S localhost:8000"
    exit 1
fi

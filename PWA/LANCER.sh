#!/bin/bash

echo "🚀 Démarrage de Stock Market Screener PWA..."
echo ""

# Déterminer le port
PORT=8000

# Vérifier si le port est déjà utilisé
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Le port $PORT est déjà utilisé."
    echo "Essayez de fermer l'autre serveur ou utilisez un autre port."
    exit 1
fi

echo "📂 Dossier: $(pwd)"
echo "🌐 URL: http://localhost:$PORT"
echo ""
echo "✨ Pour installer l'application:"
echo "   1. Ouvrez http://localhost:$PORT dans votre navigateur"
echo "   2. Cliquez sur le bouton '📥 Installer' dans le header"
echo ""
echo "⏹️  Pour arrêter: Appuyez sur Ctrl+C"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Lancer le serveur Python
if command -v python3 &> /dev/null; then
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    python -m http.server $PORT
else
    echo "❌ Erreur: Python n'est pas installé"
    echo ""
    echo "Alternatives:"
    echo "  • Installez Python: sudo apt install python3"
    echo "  • Ou utilisez: npx http-server -p $PORT"
    echo "  • Ou utilisez: php -S localhost:$PORT"
    exit 1
fi

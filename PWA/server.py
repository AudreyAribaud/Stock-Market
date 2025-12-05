import http.server
import socketserver
import json
import sys
import os
from urllib.parse import urlparse

# Import de la logique du screener
try:
    from generate_data import generate_screener_data
except ImportError as e:
    print(f"❌ Erreur d'importation: {e}")
    print("\nVérifiez que les librairies nécessaires sont installées:")
    print("  pip install tradingview-screener yfinance pandas")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur inattendue lors de l'import: {e}")
    sys.exit(1)

PORT = 8000

class ScreenerRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Analyse de l'URL demandée
        parsed_path = urlparse(self.path)
        
        # Si l'URL est /api/screener, on lance le script Python
        if parsed_path.path == '/api/screener':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*') # Pour éviter les soucis CORS
            self.end_headers()
            
            print("\n⚡ Demande de screening reçue depuis l'application...")
            try:
                # Exécution du screener
                data = generate_screener_data()
                
                # Envoi de la réponse JSON au navigateur
                response = json.dumps(data).encode('utf-8')
                self.wfile.write(response)
                print("✅ Données envoyées à l'application.\n")
                
            except Exception as e:
                print(f"❌ Erreur lors du screening: {e}")
                error_response = json.dumps({"error": str(e)}).encode('utf-8')
                self.wfile.write(error_response)
                
        else:
            # Sinon, comportement normal (servir les fichiers HTML, CSS, JS...)
            super().do_GET()

print(f"🚀 Serveur PWA intelligent démarré sur http://localhost:{PORT}")
print("   Prêt à exécuter le screener à la demande.")

# Configuration du serveur pour permettre le redémarrage rapide (reuse address)
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer(("", PORT), ScreenerRequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur.")
        httpd.server_close()

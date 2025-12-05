# Stock Market Screener PWA

Application Progressive Web App pour le screening et le backtest de stratégies de trading.

## 🚀 Fonctionnalités

- **Screening** : Filtrez les actions selon vos critères personnalisés
- **Backtest** : Testez vos stratégies de trading sur des données historiques
- **Paramètres** : Configurez votre stratégie en détail
- **Mode sombre/clair** : Basculez entre les thèmes
- **📥 Installation PWA** : Installez l'application sur votre bureau ou écran d'accueil

## 📥 Installation de l'application

### Sur ordinateur (Chrome, Edge, etc.)

1. Ouvrez l'application dans votre navigateur
2. Cliquez sur le bouton **"📥 Installer"** dans le header
3. Confirmez l'installation dans la boîte de dialogue
4. L'application sera ajoutée à votre bureau et au menu démarrer

**Alternative :** Vous pouvez aussi cliquer sur l'icône d'installation dans la barre d'adresse du navigateur.

### Sur mobile (Android/iOS)

#### Android (Chrome)
1. Ouvrez l'application dans Chrome
2. Appuyez sur le bouton **"📥 Installer"** dans le header
3. Ou appuyez sur le menu (⋮) puis "Installer l'application"
4. L'application sera ajoutée à votre écran d'accueil

#### iOS (Safari)
1. Ouvrez l'application dans Safari
2. Appuyez sur le bouton de partage (□↑)
3. Sélectionnez "Sur l'écran d'accueil"
4. Confirmez l'ajout

## 🛠️ Développement local

Pour tester l'application localement :

```bash
# Servir l'application avec Python
python -m http.server 8000

# Ou avec Node.js
npx http-server -p 8000

# Ou avec PHP
php -S localhost:8000
```

Puis ouvrez `http://localhost:8000` dans votre navigateur.

**Note :** Pour tester l'installation PWA, vous devez :
- Utiliser HTTPS (ou localhost)
- Avoir un service worker enregistré
- Avoir un fichier manifest.json valide

## 📱 Fonctionnement du bouton d'installation

Le bouton d'installation apparaît automatiquement lorsque :
- L'application répond aux critères PWA
- Le navigateur supporte l'installation
- L'application n'est pas déjà installée

Le bouton se cache automatiquement après l'installation.

## 🎨 Caractéristiques

- Design moderne avec gradients et animations
- Interface responsive (mobile et desktop)
- Notifications toast pour les actions importantes
- Thème sombre par défaut avec option de thème clair
- Icône animée sur le bouton d'installation

## 📄 Fichiers

- `index.html` : Structure de l'application
- `app.js` : Logique JavaScript et gestion PWA
- `styles.css` : Styles et animations
- `manifest.json` : Configuration PWA
- `service-worker.js` : Service Worker pour le mode hors ligne
- `icons/` : Icônes de l'application en différentes tailles
- `icons-preview.html` : Page de démonstration des icônes

## 🎨 Icônes

L'application dispose d'icônes personnalisées dans 8 tailles différentes :

- **72x72** - Petite icône
- **96x96** - Raccourcis et petits affichages
- **128x128** - Taille standard
- **144x144** - Windows tiles
- **152x152** - iOS
- **192x192** - Android (taille recommandée)
- **384x384** - Haute résolution
- **512x512** - Splash screen et grande taille

**Design** : Fusée 🚀 avec gradient indigo/rose sur fond sombre, reflétant le thème de l'application.

Pour visualiser toutes les icônes, ouvrez `icons-preview.html` dans votre navigateur.

## 🔧 Configuration

Les paramètres de l'application sont sauvegardés localement dans le navigateur via `localStorage`.

---

Créé avec ❤️ pour les traders

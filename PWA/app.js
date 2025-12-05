// ========================
// App Initialization
// ========================

// Register Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('service-worker.js')
            .then(registration => {
                console.log('Service Worker registered:', registration);
            })
            .catch(error => {
                console.log('Service Worker registration failed:', error);
            });
    });
}

// PWA Install Prompt
let deferredPrompt;
const installButton = document.getElementById('installButton');

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    // Show the install button
    if (installButton) {
        installButton.style.display = 'flex';
    }
});

// Handle install button click
if (installButton) {
    installButton.addEventListener('click', async () => {
        if (!deferredPrompt) {
            return;
        }

        // Show the install prompt
        deferredPrompt.prompt();

        // Wait for the user to respond to the prompt
        const { outcome } = await deferredPrompt.userChoice;

        console.log(`User response to the install prompt: ${outcome}`);

        // Clear the deferredPrompt for next time
        deferredPrompt = null;

        // Hide the install button
        installButton.style.display = 'none';
    });
}

// Listen for app installed event
window.addEventListener('appinstalled', () => {
    console.log('PWA was installed');
    // Hide the install button
    if (installButton) {
        installButton.style.display = 'none';
    }
    // Show a success toast
    showToast('Succès', 'Application installée avec succès!', 'success');
});


// ========================
// State Management
// ========================

const appState = {
    screeningResults: [],
    backtestResults: {},
    settings: {},
    theme: localStorage.getItem('theme') || 'dark'
};

// ========================
// DOM Elements
// ========================

const elements = {
    // Tabs
    tabButtons: document.querySelectorAll('.tab-button'),
    tabContents: document.querySelectorAll('.tab-content'),

    // Theme
    themeToggle: document.getElementById('themeToggle'),

    // Screening
    startScreening: document.getElementById('startScreening'),
    screeningResults: document.getElementById('screeningResults'),
    resultsCount: document.getElementById('resultsCount'),
    resultsTable: document.getElementById('resultsTable'),

    // Backtest
    startBacktest: document.getElementById('startBacktest'),
    backtestResults: document.getElementById('backtestResults'),
    backtestMetrics: document.getElementById('backtestMetrics'),
    backtestCharts: document.getElementById('backtestCharts'),

    // Settings
    saveSettings: document.getElementById('saveSettings'),

    // Loading
    loadingOverlay: document.getElementById('loadingOverlay'),

    // Toast
    toastContainer: document.getElementById('toastContainer')
};

// ========================
// Event Listeners
// ========================

// Tab Navigation
elements.tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.dataset.tab;
        switchTab(tabName);
    });
});

// Theme Toggle
elements.themeToggle.addEventListener('click', toggleTheme);

// Range Inputs - Update Display Values
const rangeInputs = [
    { input: 'allocPct', display: 'allocPctValue', suffix: '%' },
    { input: 'leverage', display: 'leverageValue', suffix: 'x' },
    { input: 'lookbackDays', display: 'lookbackDaysValue', suffix: '' }
];

rangeInputs.forEach(({ input, display, suffix }) => {
    const inputElement = document.getElementById(input);
    const displayElement = document.getElementById(display);

    if (inputElement && displayElement) {
        inputElement.addEventListener('input', (e) => {
            displayElement.textContent = e.target.value + suffix;
        });
    }
});

// Screening Button
elements.startScreening.addEventListener('click', handleScreening);

// Backtest Button
elements.startBacktest.addEventListener('click', handleBacktest);

// Save Settings Button
elements.saveSettings.addEventListener('click', handleSaveSettings);

// ========================
// Functions
// ========================

function switchTab(tabName) {
    // Update tab buttons
    elements.tabButtons.forEach(button => {
        button.classList.toggle('active', button.dataset.tab === tabName);
    });

    // Update tab contents
    elements.tabContents.forEach(content => {
        content.classList.toggle('active', content.id === tabName);
    });
}

function toggleTheme() {
    const currentTheme = document.body.classList.contains('light-theme') ? 'dark' : 'light';

    if (currentTheme === 'light') {
        document.body.classList.add('light-theme');
        elements.themeToggle.querySelector('.theme-icon').textContent = '☀️';
        localStorage.setItem('theme', 'light');
    } else {
        document.body.classList.remove('light-theme');
        elements.themeToggle.querySelector('.theme-icon').textContent = '🌙';
        localStorage.setItem('theme', 'dark');
    }
}

function showLoading() {
    elements.loadingOverlay.classList.add('active');
}

function hideLoading() {
    elements.loadingOverlay.classList.remove('active');
}

function showToast(title, message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-title">${title}</div>
        <div class="toast-message">${message}</div>
    `;

    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========================
// Screening Functions
// ========================

function getScreeningParams() {
    return {
        priceMin: parseFloat(document.getElementById('priceMin').value),
        priceMax: parseFloat(document.getElementById('priceMax').value),
        marketCapMin: parseFloat(document.getElementById('marketCapMin').value),
        avgVolumeMin: parseFloat(document.getElementById('avgVolumeMin').value),
        volumeMin: parseFloat(document.getElementById('volumeMin').value),
        changeMin: parseFloat(document.getElementById('changeMin').value),
        relativeVolumeMin: parseFloat(document.getElementById('relativeVolumeMin').value),
        useSma50: document.getElementById('useSma50').checked,
        useSma100: document.getElementById('useSma100').checked,
        useSma200: document.getElementById('useSma200').checked,
        useVwapFilter: document.getElementById('useVwapFilter').checked
    };
}

async function handleScreening() {
    showLoading();

    try {
        const params = getScreeningParams();

        // Simulate API call - In production, this would call a real API
        // For demonstration, we'll create mock data
        await simulateScreening(params);

        displayScreeningResults();
        showToast('Succès', 'Screening terminé avec succès!', 'success');
    } catch (error) {
        console.error('Screening error:', error);
        showToast('Erreur', 'Une erreur est survenue lors du screening', 'error');
    } finally {
        hideLoading();
    }
}

async function simulateScreening(params) {
    try {
        console.log("Appel du screener sur le serveur...");

        // Appel à notre nouveau serveur intelligent
        // Cela va déclencher l'exécution du script Python generate_data.py
        const response = await fetch('/api/screener');

        if (!response.ok) {
            throw new Error(`Erreur serveur: ${response.status}`);
        }

        let results = await response.json();

        if (results.error) {
            throw new Error(results.error);
        }

        console.log(`${results.length} résultats reçus du serveur.`);

        // Filtrage côté client pour affiner si besoin
        appState.screeningResults = results.filter(item => {
            return item.price >= params.priceMin &&
                item.price <= params.priceMax &&
                item.volume >= params.volumeMin &&
                item.change >= params.changeMin &&
                item.relativeVolume >= params.relativeVolumeMin;
        });

    } catch (error) {
        console.error('Erreur lors du screening:', error);
        showToast('Erreur', 'Impossible de lancer le screener. Vérifiez que server.py est lancé.', 'error');

        // Fallback sur la simulation uniquement si le serveur ne répond pas
        await new Promise(resolve => setTimeout(resolve, 1000));
        const mockTickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'AMD', 'NFLX', 'INTC'];
        appState.screeningResults = mockTickers
            .filter(() => Math.random() > 0.3)
            .map(ticker => ({
                ticker,
                price: (Math.random() * (params.priceMax - params.priceMin) + params.priceMin).toFixed(2),
                volume: Math.floor(Math.random() * 10000000 + params.volumeMin),
                change: (Math.random() * 10 - 2).toFixed(2),
                relativeVolume: (Math.random() * 2 + 1).toFixed(2)
            }));
    }
}

function displayScreeningResults() {
    if (appState.screeningResults.length === 0) {
        elements.screeningResults.style.display = 'none';
        showToast('Information', 'Aucun ticker trouvé avec ces critères', 'warning');
        return;
    }

    elements.resultsCount.textContent = `${appState.screeningResults.length} tickers candidats trouvés après screening`;

    const tableHTML = `
        <table>
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>Prix ($)</th>
                    <th>Volume</th>
                    <th>Variation (%)</th>
                    <th>RVol</th>
                </tr>
            </thead>
            <tbody>
                ${appState.screeningResults.map(result => `
                    <tr>
                        <td><strong>${result.ticker}</strong></td>
                        <td>$${result.price}</td>
                        <td>${formatNumber(result.volume)}</td>
                        <td style="color: ${result.change >= 0 ? 'var(--success-color)' : 'var(--danger-color)'}">
                            ${result.change >= 0 ? '+' : ''}${result.change}%
                        </td>
                        <td>${result.relativeVolume}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    elements.resultsTable.innerHTML = tableHTML;
    elements.screeningResults.style.display = 'block';
}

// ========================
// Backtest Functions
// ========================

function getBacktestParams() {
    return {
        initialCapital: parseFloat(document.getElementById('initialCapital').value),
        allocPct: parseFloat(document.getElementById('allocPct').value),
        leverage: parseFloat(document.getElementById('leverage').value),
        lookbackDays: parseInt(document.getElementById('lookbackDays').value)
    };
}

function getStrategySettings() {
    return {
        enableProfitTarget: document.getElementById('enableProfitTarget').checked,
        profitPct: parseFloat(document.getElementById('profitPct').value),
        profitAmount: parseFloat(document.getElementById('profitAmount').value),
        keybarAtrLength: parseInt(document.getElementById('keybarAtrLength').value),
        keybarAtrMult: parseFloat(document.getElementById('keybarAtrMult').value),
        keybarVolAvgLength: parseInt(document.getElementById('keybarVolAvgLength').value),
        keybarMinBodyPct: parseFloat(document.getElementById('keybarMinBodyPct').value),
        volumeSmaCheck: document.getElementById('volumeSmaCheck').checked,
        volumeSmaLength: parseInt(document.getElementById('volumeSmaLength').value),
        rrsPriceChangeLength: parseInt(document.getElementById('rrsPriceChangeLength').value),
        rrsAtrLength: parseInt(document.getElementById('rrsAtrLength').value),
        rvolNDayAvg: parseInt(document.getElementById('rvolNDayAvg').value),
        rvolHighlightThres: parseFloat(document.getElementById('rvolHighlightThres').value),
        rvolSoftHighlightThres: parseFloat(document.getElementById('rvolSoftHighlightThres').value),
        nAtrPeriod: parseInt(document.getElementById('nAtrPeriod').value),
        nAtrMultip: parseFloat(document.getElementById('nAtrMultip').value),
        checklist: {
            alignedRelativeStrength: document.getElementById('checkAlignedRelativeStrength').checked,
            rrs30mCrossover: document.getElementById('checkRrs30mCrossover').checked,
            keybarVwapBreakout: document.getElementById('checkKeybarVwapBreakout').checked,
            redToGreenStrike: document.getElementById('checkRedToGreenStrike').checked,
            haBullishReversal: document.getElementById('checkHaBullishReversal').checked,
            bullishThrust: document.getElementById('checkBullishThrust').checked,
            atrTrailingStopBullishCross: document.getElementById('checkAtrTrailingStopBullishCross').checked,
            breakoutHod1: document.getElementById('checkBreakoutHod1').checked
        }
    };
}

async function handleBacktest() {
    if (appState.screeningResults.length === 0) {
        showToast('Attention', 'Veuillez d\'abord effectuer un screening', 'warning');
        return;
    }

    showLoading();

    try {
        const backtestParams = getBacktestParams();
        const strategySettings = getStrategySettings();

        // Simulate backtest - In production, this would call a real API
        await simulateBacktest(backtestParams, strategySettings);

        displayBacktestResults();
        showToast('Succès', 'Backtest terminé avec succès!', 'success');
    } catch (error) {
        console.error('Backtest error:', error);
        showToast('Erreur', 'Une erreur est survenue lors du backtest', 'error');
    } finally {
        hideLoading();
    }
}

async function simulateBacktest(params, settings) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Generate mock backtest results
    const totalTrades = Math.floor(Math.random() * 50 + 10);
    const winningTrades = Math.floor(totalTrades * (Math.random() * 0.4 + 0.4)); // 40-80% win rate

    appState.backtestResults = {
        trades: totalTrades,
        winrate: ((winningTrades / totalTrades) * 100).toFixed(2),
        avgWin: (Math.random() * 100 + 50).toFixed(2),
        avgLoss: -(Math.random() * 50 + 20).toFixed(2),
        totalPnl: (Math.random() * 5000 - 1000).toFixed(2),
        totalPnlPct: (Math.random() * 50 - 10).toFixed(2),
        maxDrawdown: -(Math.random() * 20 + 5).toFixed(2)
    };
}

function displayBacktestResults() {
    const results = appState.backtestResults;

    const metricsHTML = `
        <div class="metric-card">
            <div class="metric-label">Nombre de trades</div>
            <div class="metric-value">${results.trades}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Taux de réussite</div>
            <div class="metric-value ${results.winrate >= 50 ? 'positive' : 'negative'}">${results.winrate}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Gain moyen</div>
            <div class="metric-value positive">$${results.avgWin}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Perte moyenne</div>
            <div class="metric-value negative">$${results.avgLoss}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">P&L Total</div>
            <div class="metric-value ${results.totalPnl >= 0 ? 'positive' : 'negative'}">$${results.totalPnl}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">P&L Total (%)</div>
            <div class="metric-value ${results.totalPnlPct >= 0 ? 'positive' : 'negative'}">${results.totalPnlPct}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Drawdown Max</div>
            <div class="metric-value negative">${results.maxDrawdown}%</div>
        </div>
    `;

    elements.backtestMetrics.innerHTML = metricsHTML;

    // Create mock chart placeholders
    const chartsHTML = `
        <div class="chart-wrapper">
            <h3 style="margin-bottom: 1rem; color: var(--text-primary);">Courbe de capital</h3>
            <div style="height: 300px; display: flex; align-items: center; justify-content: center; background: var(--bg-secondary); border-radius: var(--radius-sm);">
                <p style="color: var(--text-muted);">Graphique de la courbe de capital</p>
            </div>
        </div>
        <div class="chart-wrapper">
            <h3 style="margin-bottom: 1rem; color: var(--text-primary);">Distribution des trades</h3>
            <div style="height: 300px; display: flex; align-items: center; justify-content: center; background: var(--bg-secondary); border-radius: var(--radius-sm);">
                <p style="color: var(--text-muted);">Graphique de distribution</p>
            </div>
        </div>
    `;

    elements.backtestCharts.innerHTML = chartsHTML;
    elements.backtestResults.style.display = 'block';
}

// ========================
// Settings Functions
// ========================

function handleSaveSettings() {
    const settings = {
        backtest: getBacktestParams(),
        strategy: getStrategySettings()
    };

    localStorage.setItem('appSettings', JSON.stringify(settings));
    showToast('Succès', 'Paramètres sauvegardés avec succès!', 'success');
}

function loadSettings() {
    const savedSettings = localStorage.getItem('appSettings');

    if (savedSettings) {
        try {
            const settings = JSON.parse(savedSettings);
            // Apply saved settings to form inputs
            // This would require mapping each setting to its corresponding input
            showToast('Information', 'Paramètres chargés', 'success');
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }
}

// ========================
// Utility Functions
// ========================

function formatNumber(num) {
    return new Intl.NumberFormat('fr-FR').format(num);
}

function formatCurrency(num) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'USD'
    }).format(num);
}

// ========================
// Initialize App
// ========================

function initApp() {
    // Apply saved theme
    if (appState.theme === 'light') {
        document.body.classList.add('light-theme');
        elements.themeToggle.querySelector('.theme-icon').textContent = '☀️';
    }

    // Load saved settings
    loadSettings();

    console.log('Stock Market Screener PWA initialized');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

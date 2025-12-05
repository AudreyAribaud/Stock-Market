import json
from tradingview_screener import Query, col
import pandas as pd
import yfinance as yf
import os
from datetime import datetime

def generate_screener_data():
    print("🚀 Démarrage du screening (TradingView + Yahoo Finance)...")
    
    # 1. TradingView Screener (Pré-sélection)
    print("1️⃣  Interrogation de TradingView...")
    try:
        tickers = (
            Query()
            .select('name', 'close', 'volume', 'change', 'relative_volume_10d_calc')
            .where(
                col('type') == 'stock',
                col('exchange').isin(['NASDAQ', 'NYSE']),
                col('close').between(25, 250),
                col('market_cap_basic') >= 1_000_000_000,
                col('average_volume_30d_calc') > 1_000_000,
                col('volume') > 1_000_000,
                col('change') > 0,
                col('relative_volume') > 1.2,
                col('SMA50') < col('close'),
                col('SMA100') < col('close'),
                col('SMA200') < col('close')
            )
            .order_by('volume', ascending=False)
            .limit(3000)
            .get_scanner_data()
        )
    except Exception as e:
        print(f"❌ Erreur TradingView: {e}")
        return

    if not tickers or len(tickers) < 2:
        print("⚠️  Aucun résultat trouvé sur TradingView.")
        return

    # Extraction du DataFrame
    df_tv = tickers[1]
    print(f"✅ {len(df_tv)} actions trouvées sur TradingView.")

    # 2. Yahoo Finance Filter (VWAP check)
    print("2️⃣  Filtrage via Yahoo Finance (VWAP)...")
    
    final_results = []
    
    # On parcourt les résultats TradingView
    # df_tv contient: name, close, volume, change, relative_volume_10d_calc
    
    total = len(df_tv)
    for index, row in df_tv.iterrows():
        symbol = row['name']
        tv_price = row['close']
        tv_volume = row['volume']
        tv_change = row['change']
        tv_rvol = row['relative_volume_10d_calc']
        
        print(f"   [{index+1}/{total}] Vérification {symbol}...", end="\r")
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Données intraday 5m pour VWAP
            # Note: yfinance peut être lent, on essaie d'optimiser
            intraday = ticker.history(period='1d', interval='5m')
            
            if len(intraday) < 1:
                continue

            # Calcul VWAP
            # VWAP = Cumulative(Price * Volume) / Cumulative(Volume)
            vwap_series = (intraday['Close'] * intraday['Volume']).cumsum() / intraday['Volume'].cumsum()
            
            if vwap_series.empty:
                continue
                
            vwap_last = vwap_series.iloc[-1]
            
            # Récupérer le prix actuel (soit du dernier close 5m, soit de l'info)
            current_price = intraday['Close'].iloc[-1]
            
            # Condition du notebook: vwap_last <= price
            if vwap_last <= current_price:
                final_results.append({
                    "ticker": symbol,
                    "price": round(current_price, 2),
                    "volume": int(tv_volume),
                    "change": round(tv_change, 2),
                    "relativeVolume": round(tv_rvol, 2),
                    "vwap": round(vwap_last, 2)
                })
                
        except Exception as e:
            # print(f"Erreur sur {symbol}: {e}")
            continue

    print(f"\n✅ {len(final_results)} actions retenues après filtrage VWAP.")

    return final_results

if __name__ == "__main__":
    results = generate_screener_data()
    
    # 3. Sauvegarde en JSON (seulement si exécuté directement)
    output_file = "screener_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)
        
    print(f"💾 Résultats sauvegardés dans {output_file}")
    
    # Création d'un fichier de métadonnées pour le timestamp
    meta = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(results)
    }
    with open("screener_meta.json", "w") as f:
        json.dump(meta, f, indent=4)

import streamlit as st
from tradingview_screener import Query, col
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Screening des actions long", layout="wide")

st.title("📈 Screening des actions long")
st.write("Filtrage initial via TradingView puis affinage avec données intraday Yahoo Finance.")

# --- Paramètres utilisateur ---
min_price = st.sidebar.number_input("Prix minimum", value=25, step=1)
max_price = st.sidebar.number_input("Prix maximum", value=250, step=1)
min_market_cap = st.sidebar.number_input("Market Cap minimum", value=1_000_000_000, step=100_000_000)
min_avg_vol = st.sidebar.number_input("Volume moyen 30j minimum", value=1_000_000, step=100_000)
min_vol = st.sidebar.number_input("Volume actuel minimum", value=1_000_000, step=100_000)
min_change = st.sidebar.number_input("Variation min (%)", value=0.0, step=0.1)
min_rel_vol = st.sidebar.number_input("Relative Volume minimum", value=1.2, step=0.1)

if st.button("🔍 Lancer le screening"):
    with st.spinner("Récupération des tickers depuis TradingView..."):
        tickers_data = (
            Query()
            .select('name', 'close', 'volume', 'relative_volume_10d_calc')
            .where(
                col('type') == 'stock',
                col('exchange').isin(['NASDAQ', 'NYSE']),
                col('close').between(min_price, max_price),
                col('market_cap_basic') >= min_market_cap,
                col('average_volume_30d_calc') > min_avg_vol,
                col('volume') > min_vol,
                col('change') > min_change,
                col('relative_volume') > min_rel_vol,
                col('SMA50') < col('close'),
                col('SMA100') < col('close'),
                col('SMA200') < col('close'),
            )
            .order_by('volume', ascending=False)
            .limit(3000)
            .get_scanner_data()
        )

        df_tickers = tickers_data[1]
        tickers_list = df_tickers['name'].tolist()
        st.success(f"{len(tickers_list)} actions extraites après filtrage initial.")
        st.dataframe(df_tickers)

    # --- Screening VWAP + EMA8 ---
    with st.spinner("Analyse VWAP + EMA8..."):
        results_vwap_ema = []
        for symbol in tickers_list:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                price = info.get('currentPrice')

                intraday = ticker.history(period='1d', interval='5m')
                if len(intraday) < 8:
                    continue

                vwap = (intraday['Close'] * intraday['Volume']).cumsum() / intraday['Volume'].cumsum()
                vwap_last = vwap.iloc[-1]
                ema8 = intraday['Close'].ewm(span=8, adjust=False).mean().iloc[-1]

                if vwap_last <= price and ema8 <= price:
                    results_vwap_ema.append({"ticker": symbol, "price": price, "VWAP": vwap_last, "EMA8": ema8})
            except Exception:
                continue

        df_vwap_ema = pd.DataFrame(results_vwap_ema)
        st.subheader(f"✅ {len(df_vwap_ema)} actions passent le filtre VWAP + EMA8")
        st.dataframe(df_vwap_ema)

    # --- Screening VWAP seul ---
    with st.spinner("Analyse VWAP seul..."):
        results_vwap = []
        for symbol in tickers_list:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                price = info.get('currentPrice')

                intraday = ticker.history(period='1d', interval='5m')
                vwap = (intraday['Close'] * intraday['Volume']).cumsum() / intraday['Volume'].cumsum()
                vwap_last = vwap.iloc[-1]

                if vwap_last <= price:
                    results_vwap.append({"ticker": symbol, "price": price, "VWAP": vwap_last})
            except Exception:
                continue

        df_vwap = pd.DataFrame(results_vwap)
        st.subheader(f"✅ {len(df_vwap)} actions passent le filtre VWAP seul")
        st.dataframe(df_vwap)

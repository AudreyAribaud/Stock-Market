# app.py

import streamlit as st
from tradingview_screener import Query, col
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import mplfinance as mpf

# ========================
# Config Streamlit
# ========================
st.set_page_config(page_title="Backtest Multi-Titres", layout="wide")
st.title("Stock Market Screener & Backtest")

# ========================
# Paramètres utilisateur
# ========================
initial_capital = st.sidebar.number_input("Capital initial ($)", 1000, 1_000_000, 10_000, step=1000)
alloc_pct = st.sidebar.slider("Allocation par trade (%)", 1, 100, 10)
leverage = st.sidebar.slider("Levier", 1, 5, 1)
lookback_days = st.sidebar.slider("Nombre de jours d'historique", 1, 30, 15)

# ========================
# Fonctions techniques
# ========================
def fetch_5m_data(tickers, start, end):
    df = yf.download(tickers, start=start, end=end, interval="5m",
                     group_by="ticker", threads=True, auto_adjust=False)
    if not isinstance(df.columns, pd.MultiIndex):
        df = pd.concat({tickers[0]: df}, axis=1)
    return df

def split_by_ticker(df_multi):
    return {t: df_multi[t].rename(columns=str.lower) for t in df_multi.columns.levels[0]}

def get_df5(ticker, start, end):
    df5_all = fetch_5m_data([ticker], start, end)
    df5 = split_by_ticker(df5_all)[ticker]
    df5.index = pd.to_datetime(df5.index)
    return df5.dropna(subset=["open", "high", "low", "close", "volume"])

def ema(series, period): return series.ewm(span=period, adjust=False).mean()

def atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    return ranges.max(axis=1).rolling(period, min_periods=period).mean()

def detect_keybars(df):
    atr20 = atr(df, 20)
    vol_ma20 = df["volume"].rolling(20).mean()
    range_candle = df["high"] - df["low"]
    return (range_candle > 1.5 * atr20) & (df["volume"] > 1.5 * vol_ma20)

def compute_signals(df):
    ema100 = ema(df["close"], 100)
    keybar = detect_keybars(df)
    rrs_ok = df["close"] > df["low"].rolling(20).min()
    long_entry = keybar & (df["close"] > ema100) & rrs_ok
    long_exit = (df["close"] < ema100) | (df["close"] < df["low"].shift())
    return long_entry.fillna(False), long_exit.fillna(False)

def build_trade_log(df, long_entry, long_exit, ticker):
    trades = []
    in_pos = False
    entry_time = None
    entry_price = None
    atr_stop = None
    atr14 = atr(df, 14)
    for i, ts in enumerate(df.index):
        price = df["close"].iloc[i]
        if not in_pos and long_entry.iloc[i]:
            in_pos = True
            entry_time = ts
            entry_price = price
            atr_stop = price - 2 * atr14.iloc[i]
        elif in_pos:
            atr_stop = max(atr_stop, price - 2 * atr14.iloc[i])
            if long_exit.iloc[i] or price < atr_stop:
                exit_time = ts
                exit_price = price
                pnl_pct = (exit_price / entry_price - 1.0) * 100.0
                trades.append({
                    "ticker": ticker,
                    "entry_time": entry_time,
                    "entry_price": entry_price,
                    "exit_time": exit_time,
                    "exit_price": exit_price,
                    "pnl_pct": pnl_pct,
                    "duration": exit_time - entry_time
                })
                in_pos = False
    return pd.DataFrame(trades)

def equity_curve(df, trades_df):
    equity = pd.Series(initial_capital, index=df.index, dtype=float)
    cash = initial_capital
    in_pos = False
    entry_price = None
    alloc_value = 0.0
    entries_idx = set(trades_df["entry_time"]) if not trades_df.empty else set()
    exits_idx = set(trades_df["exit_time"]) if not trades_df.empty else set()
    for ts in df.index:
        price = df.at[ts, "close"]
        if (ts in entries_idx) and not in_pos:
            in_pos = True
            entry_price = price
            alloc_value = cash * (alloc_pct / 100.0) * leverage
        unrealized = alloc_value * (price / entry_price - 1.0) if in_pos else 0.0
        if (ts in exits_idx) and in_pos:
            realized = alloc_value * (price / entry_price - 1.0)
            cash += realized
            in_pos = False
            entry_price = None
            alloc_value = 0.0
            unrealized = 0.0
        equity.at[ts] = cash + unrealized
    return equity

def compute_metrics(trades_df, equity):
    if trades_df.empty:
        return {"trades": 0, "winrate_%": 0, "avg_win_%": 0,
                "avg_loss_%": 0, "total_pnl_%": 0, "max_drawdown_%": 0}
    wins = trades_df["pnl_pct"] > 0
    return {
        "trades": len(trades_df),
        "winrate_%": round(wins.mean() * 100, 2),
        "avg_win_%": round(trades_df.loc[wins, "pnl_pct"].mean() if wins.any() else 0, 2),
        "avg_loss_%": round(trades_df.loc[~wins, "pnl_pct"].mean() if (~wins).any() else 0, 2),
        "total_pnl_%": round((equity.iloc[-1] / equity.iloc[0] - 1.0) * 100, 2),
        "max_drawdown_%": round((equity / equity.cummax() - 1.0).min() * 100, 2)
    }

def plot_trades_and_equity(df, trades_df, equity, ticker):
    if trades_df.empty:
        st.write(f"{ticker}: Aucun trade à afficher.")
        return

    buys = pd.Series(np.nan, index=df.index)
    sells = pd.Series(np.nan, index=df.index)
    for _, r in trades_df.iterrows():
        if r["entry_time"] in df.index:
            buys[r["entry_time"]] = df.at[r["entry_time"], "low"] * 0.995
        if r["exit_time"] in df.index:
            sells[r["exit_time"]] = df.at[r["exit_time"], "high"] * 1.005

    apds = [
        mpf.make_addplot(buys, type='scatter', marker='^', markersize=60, color='g'),
        mpf.make_addplot(sells, type='scatter', marker='v', markersize=60, color='r')
    ]

    # 🔹 Graphique chandeliers avec trades
    mpf.plot(
        df,
        type='candle',
        style='charles',
        addplot=apds,
        volume=False,
        show_nontrading=False,
        title=f"{ticker} – Trades exécutés"
    )

    # 🔹 Graphique de la courbe de capital
    fig_eq, ax_eq = plt.subplots(figsize=(8, 4))
    ax_eq.plot(equity.index, equity, color='blue', label='Capital')
    ax_eq.set_title(f"Courbe de capital – {ticker}")
    ax_eq.grid(True)
    ax_eq.legend()
    st.pyplot(fig_eq)

# ========================
# Fonction pour récupérer les tickers avec TradingView + VWAP
# ========================
@st.cache_data
def get_tickers():
    tickers = (
        Query()
        .select('name', 'close', 'volume', 'relative_volume_10d_calc')
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
            col('SMA200') < col('close'),
        )
        .order_by('volume', ascending=False)
        .limit(3000)
        .get_scanner_data()
    )
    df = tickers[1]
    return df['name'].tolist()

# ========================
# Screening des actions
# ========================
if st.button("🔍 Lancer le screening"):
    st.info("Screening en cours...")
    tickers_list = get_tickers()
    results = []

    for symbol in tickers_list:
        try:
            ticker = yf.Ticker(symbol)
            price = ticker.info.get('currentPrice', 0)
            intraday = ticker.history(period='1d', interval='5m')
            if intraday.empty: continue
            vwap = (intraday['Close'] * intraday['Volume']).cumsum() / intraday['Volume'].cumsum()
            if price >= vwap.iloc[-1]:
                results.append({'ticker': symbol})
        except Exception:
            continue

    df_screened = pd.DataFrame(results)
    st.session_state['df_screened'] = df_screened
    st.write(f"**{len(df_screened)} tickers candidats trouvés après filtrage VWAP**")
    st.dataframe(df_screened)

# ========================
# Backtest multi-titres
# ========================
if 'df_screened' in st.session_state and not st.session_state['df_screened'].empty:
    if st.button("Lancer le backtest"):
        df = st.session_state['df_screened']
        start_date = (datetime.today() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        end_date = datetime.today().strftime('%Y-%m-%d')
        all_metrics = {}

        for ticker in df['ticker'].tolist():
            st.subheader(f"Analyse : {ticker}")
            df_price = get_df5(ticker, start_date, end_date)
            long_entry, long_exit = compute_signals(df_price)
            trades_df = build_trade_log(df_price, long_entry, long_exit, ticker)
            if trades_df.empty:
                st.write("Aucun trade exécuté.")
                continue
            equity = equity_curve(df_price, trades_df)
            metrics = compute_metrics(trades_df, equity)
            all_metrics[ticker] = metrics
            st.write(trades_df)
            plot_trades_and_equity(df_price, trades_df, equity, ticker)

        if all_metrics:
            st.subheader("Récapitulatif global")
            st.dataframe(pd.DataFrame(all_metrics).T)

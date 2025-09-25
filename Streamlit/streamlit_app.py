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
st.title("🚀 Stock Market Screener & Backtest")

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

def detect_keybars(df, atr_length, atr_mult, vol_avg_length, min_body_pct):
    atr_val = atr(df, atr_length)
    vol_ma = df["volume"].rolling(vol_avg_length).mean()
    range_candle = df["high"] - df["low"]
    body_size = (df["close"] - df["open"]).abs()
    body_pct = body_size / range_candle * 100
    return (
        (range_candle > atr_mult * atr_val) &
        (df["volume"] > 1.5 * vol_ma) &
        (body_pct > min_body_pct)
    )

def compute_rrs(df, price_change_length, atr_length):
    # Exemple simple : prix > plus bas sur price_change_length ET ATR > moyenne ATR_length
    rrs_price = df["close"] > df["low"].rolling(price_change_length).min()
    rrs_atr = atr(df, atr_length) > atr(df, atr_length).mean()
    return rrs_price & rrs_atr

def compute_relative_volume(df, n_day_avg, highlight_thres, soft_highlight_thres):
    avg_vol = df["volume"].rolling(n_day_avg).mean()
    rvol = df["volume"] / avg_vol
    return (rvol > highlight_thres) | (rvol > soft_highlight_thres)

def signal_checklist_long(df, checklist_long):
    filters = []
    if checklist_long["Aligned relative strength filter"]:
        filters.append(df["close"] > ema(df["close"], 30))
    if checklist_long["RRS 30m crossover 0"]:
        filters.append(df["close"].diff(6) > 0)
    if checklist_long["Keybar VWAP breakout"]:
        vwap = (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()
        filters.append(df["close"] > vwap)
    if checklist_long["Red to green strike"]:
        filters.append(df["close"] > df["open"])
    if checklist_long["HA Bullish reversal"]:
        filters.append(df["close"] > df["open"])
    if checklist_long["Bullish thrust"]:
        filters.append(df["close"].pct_change() > 0.01)
    if checklist_long["ATR trailing stop bullish cross"]:
        filters.append(df["close"] > ema(df["close"], 14))
    if checklist_long["Breakout of HOD[1]"]:
        filters.append(df["close"] > df["high"].shift(1))
    # Combine tous les filtres cochés en logique OR
    if filters:
        return np.logical_or.reduce(filters)
    else:
        return pd.Series(False, index=df.index)
    
def compute_signals(
    df,
    keybar_atr_length,
    keybar_atr_mult,
    keybar_vol_avg_length,
    keybar_min_body_pct,
    rrs_price_change_length,
    rrs_atr_length,
    rvol_n_day_avg,
    rvol_highlight_thres,
    rvol_soft_highlight_thres,
    checklist_long,
    volume_sma_check,
    volume_sma_length
):
    keybar = detect_keybars(df, keybar_atr_length, keybar_atr_mult, keybar_vol_avg_length, keybar_min_body_pct)
    rrs_ok = compute_rrs(df, rrs_price_change_length, rrs_atr_length)
    checklist_ok = signal_checklist_long(df, checklist_long)
    # Volume logic : OR between volume SMA and relative volume
    vol_sma = df["volume"].rolling(volume_sma_length).mean() if volume_sma_check else pd.Series(0, index=df.index)
    volume_ok = (df["volume"] > vol_sma)
    rvol_ok = compute_relative_volume(df, rvol_n_day_avg, rvol_highlight_thres, rvol_soft_highlight_thres)
    # Combine volume_ok OR rvol_ok
    volume_final = volume_ok | rvol_ok
    # Final entry logic: keybar AND rrs_ok AND (volume_ok OR rvol_ok) AND checklist_ok
    long_entry = keybar & rrs_ok & volume_final & checklist_ok
    # Bearish reversal: close < open (simplified, adapt if you want Heikin Ashi or other)
    long_exit = df["close"] < df["open"]
    return long_entry.fillna(False), long_exit.fillna(False)

def build_trade_log(
    df, long_entry, long_exit, ticker,
    profit_pct, profit_amount,
    nATRPeriod, nATRMultip,
    enable_profit_target
):
    trades = []
    in_pos = False
    entry_time = None
    entry_price = None
    atr_stop = None
    atr_custom = atr(df, nATRPeriod)
    for i, ts in enumerate(df.index):
        price = df["close"].iloc[i]
        if not in_pos and long_entry.iloc[i]:
            in_pos = True
            entry_time = ts
            entry_price = price
            atr_stop = price - nATRMultip * atr_custom.iloc[i]
        elif in_pos:
            atr_stop = max(atr_stop, price - nATRMultip * atr_custom.iloc[i])
            reached_profit_pct = (price / entry_price - 1.0) * 100.0 >= profit_pct if enable_profit_target else False
            reached_profit_amount = (price - entry_price) >= profit_amount if enable_profit_target else False
            if long_exit.iloc[i] or price < atr_stop or reached_profit_pct or reached_profit_amount:
                exit_time = ts
                exit_price = price
                pnl_pct = (exit_price / entry_price - 1.0) * 100.0
                trades.append({
                    "ticker": ticker,
                    "entry_time": entry_time,
                    "entry_price": entry_price,
                    "exit_time": exit_time,
                    "exit_price": exit_price,
                    "pnl_%": pnl_pct,
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
    wins = trades_df["pnl_%"] > 0
    alloc_value = initial_capital * (alloc_pct / 100.0) * leverage

    return {
        "trades": len(trades_df),
        "winrate_%": round(wins.mean() * 100, 2),
        "avg_win_$": round(trades_df.loc[wins, "pnl_%"].mean() / 100 * alloc_value if wins.any() else 0, 2),
        # "avg_win_%": round(trades_df.loc[wins, "pnl_%"].mean() if wins.any() else 0, 2),
        "avg_loss_$": round(trades_df.loc[~wins, "pnl_%"].mean() / 100 * alloc_value if (~wins).any() else 0, 2),
        # "avg_loss_%": round(trades_df.loc[~wins, "pnl_%"].mean() if (~wins).any() else 0, 2),
        "total_pnl_$": round(equity.iloc[-1] - equity.iloc[0], 2),
        "total_pnl_%": round((equity.iloc[-1] / equity.iloc[0] - 1.0) * 100, 2),
        "max_drawdown_%": round((equity / equity.cummax() - 1.0).min() * 100, 2)
    }

def plot_trades_and_equity(df, trades_df, equity, ticker):
    if trades_df.empty:
        st.write(f"{ticker}: Aucun trade à afficher.")
        return

    # Préparation des signaux d'achat/vente
    buys = pd.Series(np.nan, index=df.index)
    sells = pd.Series(np.nan, index=df.index)
    for _, r in trades_df.iterrows():
        if r["entry_time"] in df.index:
            buys[r["entry_time"]] = df.at[r["entry_time"], "low"] * 0.995
        if r["exit_time"] in df.index:
            sells[r["exit_time"]] = df.at[r["exit_time"], "high"] * 1.005

    # Création des sous-colonnes pour afficher les deux graphiques côte à côte
    col1, col2 = st.columns(2)

    # 🔹 Graphique chandeliers avec trades
    with col1:
        fig_candle, ax_candle = mpf.plot(
            df,
            type='candle',
            style='charles',
            addplot=[
                mpf.make_addplot(buys, type='scatter', marker='^', markersize=60, color='g'),
                mpf.make_addplot(sells, type='scatter', marker='v', markersize=60, color='r')
            ],
            volume=False,
            show_nontrading=False,
            returnfig=True,  # <- clé pour récupérer la figure matplotlib
            figsize=(8, 4)
        )
        ax_candle[0].set_title(f"{ticker} – Chandeliers & Trades")
        st.pyplot(fig_candle)

    # 🔹 Graphique de la courbe de capital
    with col2:
        fig_eq, ax_eq = plt.subplots(figsize=(8, 4))
        ax_eq.plot(equity.index, equity, color='blue', label='Capital')
        ax_eq.set_title(f"Courbe de capital – {ticker}")
        ax_eq.grid(True)
        ax_eq.legend()
        st.pyplot(fig_eq)


# ========================
# Paramètres du screening
# ========================
with st.sidebar.expander("Paramètres screening", expanded=False):
    price_min = st.number_input("Prix minimum ($)", min_value=0, value=25)
    price_max = st.number_input("Prix maximum ($)", min_value=0, value=250)
    market_cap_min = st.number_input("Market Cap minimum ($)", min_value=0, value=1_000_000_000)
    avg_volume_min = st.number_input("Volume moyen 30j minimum", min_value=0, value=1_000_000)
    volume_min = st.number_input("Volume minimum", min_value=0, value=1_000_000)
    change_min = st.number_input("Variation minimum (%)", min_value=0.0, value=0.0)
    relative_volume_min = st.number_input("Relative Volume minimum", min_value=0.0, value=1.2)
    # Checkbox pour SMA
    use_sma50 = st.checkbox("SMA50 < Close", value=True)
    use_sma100 = st.checkbox("SMA100 < Close", value=True)
    use_sma200 = st.checkbox("SMA200 < Close", value=True)
    # Checkbox pour VWAP
    use_vwap_filter = st.checkbox("VWAP 5m <= price", value=True)


# ========================
# Fonction de récupération des tickers
# ========================
@st.cache_data
def get_tickers(
    price_min, price_max, market_cap_min, avg_volume_min,
    volume_min, change_min, relative_volume_min,
    use_sma50, use_sma100, use_sma200
):
    query = Query().select('name', 'close', 'volume', 'relative_volume_10d_calc').where(
        col('type') == 'stock',
        col('exchange').isin(['NASDAQ', 'NYSE']),
        col('close').between(price_min, price_max),
        col('market_cap_basic') >= market_cap_min,
        col('average_volume_30d_calc') > avg_volume_min,
        col('volume') > volume_min,
        col('change') > change_min,
        col('relative_volume') > relative_volume_min,
    )

    # Conditions SMA activées selon les checkboxes
    if use_sma50:
        query = query.where(col('SMA50') < col('close'))
    if use_sma100:
        query = query.where(col('SMA100') < col('close'))
    if use_sma200:
        query = query.where(col('SMA200') < col('close'))

    tickers = query.order_by('volume', ascending=False).limit(100).get_scanner_data()
    df = tickers[1]
    return df['name'].tolist()

# ========================
# Screening des actions
# ========================
if st.button("🔍 Lancer le screening LONG"):
    st.info("Screening en cours...")
    tickers_list = get_tickers(
        price_min, price_max, market_cap_min, avg_volume_min,
        volume_min, change_min, relative_volume_min,
        use_sma50, use_sma100, use_sma200
    )
    results = []

    for symbol in tickers_list:
        try:
            ticker = yf.Ticker(symbol)
            price = ticker.info.get('currentPrice', 0)
            intraday = ticker.history(period='1d', interval='5m')
            if intraday.empty:
                continue
            vwap = (intraday['Close'] * intraday['Volume']).cumsum() / intraday['Volume'].cumsum()
           # Filtre VWAP activé ou désactivé
            if use_vwap_filter:
                if price >= vwap.iloc[-1]:
                    results.append({'ticker': symbol})
            else:
                results.append({'ticker': symbol})
        except Exception:
            continue

    st.session_state['df_screened'] = pd.DataFrame(results)

# 🔹 Toujours afficher le screening s'il existe déjà
if 'df_screened' in st.session_state and not st.session_state['df_screened'].empty:
    df_screened = st.session_state['df_screened']
    st.write(f"**{len(df_screened)} tickers candidats trouvés après screening**")
    st.dataframe(df_screened)


# ========================
# Paramètres Backtest
# ========================
with st.sidebar.expander("Paramètres du compte du Backtest", expanded=False):
    initial_capital = st.number_input("Capital initial ($)", 1000, 1_000_000, 10_000, step=1000)
    alloc_pct = st.slider("Allocation par trade (%)", 1, 100, 10)
    leverage = st.slider("Levier", 1, 5, 1)
    lookback_days = st.slider("Nombre de jours d'historique", 1, 30, 15)

# ========================
# Paramètres Stratégie
# ========================

with st.sidebar.expander("Paramètres de la stratégie", expanded=False):
    st.subheader("Profit Target")
    enable_profit_target = st.checkbox("Activer le profit target", value=True)
    profit_pct = st.number_input("Profit cible (%)", min_value=0.1, max_value=100.0, value=1.0, step=0.1)
    profit_amount = st.number_input("Profit cible ($)", min_value=1, max_value=10000, value=50, step=1)
   
    st.subheader("Keybars Inputs")
    keybar_atr_length = st.number_input("ATR longueur", min_value=1, max_value=1000, value=390, step=1)
    keybar_atr_mult = st.number_input("ATR multiplicateur", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
    keybar_vol_avg_length = st.number_input("Volume Average Length", min_value=1, max_value=1000, value=390, step=1)
    keybar_min_body_pct = st.number_input("Minimum Body size (%)", min_value=0.0, max_value=100.0, value=75.0, step=0.1)
    volume_sma_check = st.checkbox("Activer le filtre Volume SMA", value=False)
    volume_sma_length = st.number_input("Volume SMA Length", min_value=1, max_value=1000, value=50, step=1)

    st.subheader("RRS Inputs")
    rrs_price_change_length = st.number_input("Price change length", min_value=1, max_value=100, value=12, step=1)
    rrs_atr_length = st.number_input("ATR longueur", min_value=1, max_value=100, value=12, step=1)

    st.subheader("Relative Volume")
    rvol_n_day_avg = st.number_input("N Day average", min_value=1, max_value=30, value=5, step=1)
    rvol_highlight_thres = st.number_input("RVol Highlight Thres", min_value=0.1, max_value=10.0, value=1.5, step=0.1)
    rvol_soft_highlight_thres = st.number_input("RVol Soft Highlight Thres", min_value=0.1, max_value=10.0, value=1.2, step=0.1)

    st.subheader("ATR Trailing Stop Params")
    nATRPeriod = st.number_input("ATR Trailing Stop Period", min_value=1, max_value=100, value=14, step=1)
    nATRMultip = st.number_input("ATR Trailing Stop Multiplicateur", min_value=0.1, max_value=10.0, value=2.0, step=0.1)

    st.subheader("Signal Checklist long")
    checklist_long = {
        "Aligned relative strength filter": st.checkbox("Aligned relative strength filter", value=True),
        "RRS 30m crossover 0": st.checkbox("RRS 30m crossover 0", value=True),
        "Keybar VWAP breakout": st.checkbox("Keybar VWAP breakout", value=True),
        "Red to green strike": st.checkbox("Red to green strike", value=True),
        "HA Bullish reversal": st.checkbox("HA Bullish reversal", value=True),
        "Bullish thrust": st.checkbox("Bullish thrust", value=True),
        "ATR trailing stop bullish cross": st.checkbox("ATR trailing stop bullish cross", value=True),
        "Breakout of HOD[1]": st.checkbox("Breakout of HOD[1]", value=True),
    }

# ========================
# Backtest multi-titres
# ========================
if 'df_screened' in st.session_state and not st.session_state['df_screened'].empty:
    if st.button("Lancer le backtest LONG"):
        df = st.session_state['df_screened']
        start_date = (datetime.today() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        end_date = datetime.today().strftime('%Y-%m-%d')
        all_metrics = {}
        all_trades = {}

        for ticker in df['ticker'].tolist():
            df_price = get_df5(ticker, start_date, end_date)
            long_entry, long_exit = compute_signals(
                df_price,
                keybar_atr_length,
                keybar_atr_mult,
                keybar_vol_avg_length,
                keybar_min_body_pct,
                rrs_price_change_length,
                rrs_atr_length,
                rvol_n_day_avg,
                rvol_highlight_thres,
                rvol_soft_highlight_thres,
                checklist_long,
                volume_sma_check,
                volume_sma_length
            )
            trades_df = build_trade_log(
                df_price, long_entry, long_exit, ticker,
                profit_pct, profit_amount,
                nATRPeriod, nATRMultip,
                enable_profit_target
            )
            if trades_df.empty:
                continue
            equity = equity_curve(df_price, trades_df)
            metrics = compute_metrics(trades_df, equity)
            all_metrics[ticker] = metrics
            all_trades[ticker] = (df_price, trades_df, equity)

        if all_metrics:
            st.subheader("Récapitulatif global positions LONG")
            st.dataframe(pd.DataFrame(all_metrics).T)

        for ticker, (df_price, trades_df, equity) in all_trades.items():
            with st.expander(f"Analyse : {ticker}", expanded=False):
                st.write(trades_df)
                plot_trades_and_equity(df_price, trades_df, equity, ticker)



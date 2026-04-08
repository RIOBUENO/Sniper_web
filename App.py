import streamlit as st
import yfinance as yf
import pandas_ta as ta
import requests
import time

# --- CONFIGURACIÓN SILENCIOSA ---
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
SIMBOLOS = [
    "EURAUD=X", "EURCAD=X", "EURCHF=X", "GBPAUD=X", "GBPCAD=X",
    "GBPJPY=X", "AUDUSD=X", "AUDCAD=X", "AUDJPY=X", "EURUSD=X"
]

def enviar_telegram(msj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msj, "parse_mode": "Markdown"})
    except:
        pass

def motor_invisible():
    for s in SIMBOLOS:
        try:
            df_15m = yf.download(s, interval="15m", period="5d", progress=False)
            df_1m = yf.download(s, interval="1m", period="1d", progress=False)
            
            if df_1m.empty: continue

            # Cálculos internos
            rsi = ta.rsi(df_1m['Close'], length=14).iloc[-1]
            macd = ta.macd(df_1m['Close'])
            ml, ms = macd['MACD_12_26_9'].iloc[-1], macd['MACDs_12_26_9'].iloc[-1]
            stoch = ta.stoch(df_1m['High'], df_1m['Low'], df_1m['Close'])
            sk, sd = stoch['STOCHk_14_3_3'].iloc[-1], stoch['STOCHd_14_3_3'].iloc[-1]
            
            precio = df_1m['Close'].iloc[-1]
            sop = df_15m['Low'].tail(50).min()
            res = df_15m['High'].tail(50).max()

            # Lógica de disparo (7/10)
            p_call = 0
            if rsi < 30: p_call += 2
            if ml > ms: p_call += 2
            if sk < 20 and sk > sd: p_call += 3
            if precio <= sop * 1.0005: p_call += 3

            if p_call >= 7:
                enviar_telegram(f"🎯 *ALERTA*\n{s} | CALL\nScore: {p_call}/10\nPx: {precio:.5f}")
                continue

            p_put = 0
            if rsi > 70: p_put += 2
            if ml < ms: p_put += 2
            if sk > 80 and sk < sd: p_put += 3
            if precio >= res * 0.9995: p_put += 3

            if p_put >= 7:
                enviar_telegram(f"🎯 *ALERTA*\n{s} | PUT\nScore: {p_put}/10\nPx: {precio:.5f}")
        except:
            continue

# --- INTERFAZ VACÍA ---
st.set_page_config(page_title=".", layout="centered")

if "run" not in st.session_state:
    st.session_state.run = False

if not st.session_state.run:
    if st.button("ON"):
        st.session_state.run = True
        enviar_telegram("⚡ *SISTEMA ACTIVO*")
        st.rerun()
else:
    # Una vez activo, la página no muestra nada
    while True:
        motor_invisible()
        time.sleep(60)

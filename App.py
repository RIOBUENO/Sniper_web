import streamlit as st
import yfinance as yf
import pandas_ta as ta
import requests
import time

# --- CONFIGURACIÓN ---
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
SIMBOLOS = [
    "EURAUD=X", "EURCAD=X", "EURCHF=X", "GBPAUD=X", "GBPCAD=X",
    "GBPJPY=X", "AUDUSD=X", "AUDCAD=X", "AUDJPY=X", "EURUSD=X"
]

def enviar(txt):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": txt, "parse_mode": "Markdown"})
    except:
        pass

def motor_sniper():
    for s in SIMBOLOS:
        try:
            # Datos para el análisis de confluencia
            d15 = yf.download(s, interval="15m", period="5d", progress=False)
            d1 = yf.download(s, interval="1m", period="1d", progress=False)
            
            if d1.empty or d15.empty: continue

            # Indicadores (Tu plan de 10 puntos)
            c = d1['Close']
            rsi = ta.rsi(c, length=14).iloc[-1]
            macd = ta.macd(c)
            ml, ms = macd['MACD_12_26_9'].iloc[-1], macd['MACDs_12_26_9'].iloc[-1]
            stoch = ta.stoch(d1['High'], d1['Low'], c)
            sk, sd = stoch['STOCHk_14_3_3'].iloc[-1], stoch['STOCHd_14_3_3'].iloc[-1]
            
            px = c.iloc[-1]
            sop = d15['Low'].tail(50).min()
            res = d15['High'].tail(50).max()

            # Confluencia CALL
            p = 0
            if rsi < 30: p += 2
            if ml > ms: p += 2
            if sk < 20 and sk > sd: p += 3
            if px <= sop * 1.0005: p += 3
            if p >= 7:
                enviar(f"🎯 *SNIPER CALL*\n💎 {s}\n🔥 Score: {p}/10\n💰 Px: {px:.5f}")
                continue

            # Confluencia PUT
            p = 0
            if rsi > 70: p += 2
            if ml < ms: p += 2
            if sk > 80 and sk < sd: p += 3
            if px >= res * 0.9995: p += 3
            if p >= 7:
                enviar(f"🎯 *SNIPER PUT*\n💎 {s}\n🔥 Score: {p}/10\n💰 Px: {px:.5f}")
        except:
            continue

# --- INTERFAZ CERO ERRORES ---
st.set_page_config(page_title="OFFLINE", layout="centered")

if "activo" not in st.session_state:
    st.session_state.activo = False

if not st.session_state.activo:
    if st.button("🚀 ENCENDER BOT"):
        st.session_state.activo = True
        enviar("⚡ *SISTEMA SNIPER ONLINE* - Sin errores de nodo.")
        st.rerun()
else:
    # La página queda en blanco, todo el trabajo ocurre aquí:
    st.success("BOT CORRIENDO EN SEGUNDO PLANO...")
    while True:
        motor_sniper()
        time.sleep(60)

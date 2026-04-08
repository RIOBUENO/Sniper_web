import streamlit as st
import time
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime

# ======================================================
# 1. CONFIGURACIÓN
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

SIMBOLOS = [
    "EURAUD=X", "EURCAD=X", "EURCHF=X", "GBPAUD=X", "GBPCAD=X",
    "GBPJPY=X", "AUDUSD=X", "AUDCAD=X", "AUDJPY=X", "EURUSD=X",
    "GBPUSD=X", "USDJPY=X", "USDCAD=X", "USDCHF=X", "NZDUSD=X"
]

COOLDOWN = {}

# ======================================================
# 2. MOTOR SNIPER (MURALLA Y FIBO)
# ======================================================
def analizar_sniper(s):
    try:
        # Descarga data de 1 min (2 días para asegurar 240 velas)
        df = yf.download(s, interval="1m", period="2d", progress=False)
        if len(df) < 240: return

        # Indicadores
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        # Análisis Muralla (240 velas)
        df_240 = df.tail(240)
        soporte = df_240['Low'].min()
        resistencia = df_240['High'].max()
        toques = ((df_240['Low'] - soporte).abs() <= (soporte * 0.0002)).sum()

        # Fibonacci (50-70%)
        rango = resistencia - soporte
        f50, f70 = resistencia - (0.5 * rango), resistencia - (0.7 * rango)

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # SEÑAL TRAYECTORIA (Cruce 3/9 + Fibo)
        if f70 <= precio <= f50 and v_act['EMA20'] > v_ant['EMA20']:
            if v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']:
                enviar(s, precio, toques, "🚀 TRAYECTORIA (2 MIN)")

        # SEÑAL COLISIÓN (Muralla 35x)
        if toques >= 35 and abs(precio - soporte) <= (precio * 0.0004):
            est = "🔥 REBOTE" if v_act['RSI'] > 55 else "⚠️ RUPTURA"
            enviar(s, precio, toques, f"🧱 COLISIÓN: {est}")

    except:
        pass

def enviar(s, p, t, tipo):
    key = f"{s}_{tipo}"
    if key not in COOLDOWN or (time.time() - COOLDOWN[key] > 600):
        bot.send_message(CHAT_ID, f"🎯 SNIPER V10\nActivo: {s}\nPrecio: {p:.5f}\nToques: {t}\nInfo: {tipo}")
        COOLDOWN[key] = time.time()

# ======================================================
# 3. INTERFAZ ESTÁTICA (EVITA EL ERROR REMOVECHILD)
# ======================================================
st.title("🏹 Raúl Sniper Pro V10")
st.info("Radar activo 📡. Las señales se envían a Telegram.")

# Solo arranca si es día de semana
if datetime.now().weekday() < 5:
    if 'ready' not in st.session_state:
        bot.send_message(CHAT_ID, "🚀 Radar Online")
        st.session_state.ready = True

    # Bucle silencioso: NO hay st.write ni st.text aquí adentro
    while True:
        for s in SIMBOLOS:
            analizar_sniper(s)
            time.sleep(0.5)
        time.sleep(25)
else:
    st.error("Mercado Cerrado.")

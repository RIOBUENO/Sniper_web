import streamlit as st
import time
import yfinance as yf
import pandas_ta as ta
import telebot
import threading

# 1. CONFIGURACIÓN
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

SIMBOLOS = [
    "EURAUD=X", "EURCAD=X", "EURCHF=X", "GBPAUD=X", "GBPCAD=X",
    "GBPJPY=X", "AUDUSD=X", "AUDCAD=X", "AUDJPY=X", "EURUSD=X",
    "GBPUSD=X", "USDJPY=X", "USDCAD=X", "USDCHF=X", "NZDUSD=X"
]

# 2. MOTOR (HILO SEPARADO)
def motor_silencioso():
    cooldown = {}
    while True:
        try:
            for s in SIMBOLOS:
                df = yf.download(s, interval="1m", period="1d", progress=False)
                if df.empty or len(df) < 50: continue

                # Lógica simplificada para máxima velocidad
                df['EMA3'] = ta.ema(df['Close'], length=3)
                df['EMA9'] = ta.ema(df['Close'], length=9)
                df['EMA20'] = ta.ema(df['Close'], length=20)
                
                soporte = df['Low'].tail(120).min()
                precio = float(df['Close'].iloc[-1])
                toques = ((df['Low'].tail(120) - soporte).abs() <= (soporte * 0.0003)).sum()

                # Alerta Muralla
                if abs(precio - soporte) <= (precio * 0.0005) and toques >= 25:
                    tag = f"{s}_M"
                    if tag not in cooldown or (time.time() - cooldown[tag] > 600):
                        bot.send_message(CHAT_ID, f"🧱 MURALLA: {s} @ {precio:.5f} ({toques} toques)")
                        cooldown[tag] = time.time()

                time.sleep(1)
            time.sleep(15)
        except:
            time.sleep(10)

# 3. INTERFAZ (MÍNIMA ABSOLUTA)
st.title("Sniper Activo")

if "ejecutando" not in st.session_state:
    thread = threading.Thread(target=motor_silencioso, daemon=True)
    thread.start()
    st.session_state.ejecutando = True
    bot.send_message(CHAT_ID, "🚀 Motor Sniper V10 Iniciado.")

st.write("El bot está corriendo en segundo plano. Puedes cerrar esta ventana.")

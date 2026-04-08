import streamlit as st
import telebot
import yfinance as yf
import pandas_ta as ta
import threading
import time

# --- CONFIGURACIÓN ---
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

SIMBOLOS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X"]

# --- RESPUESTA A TUS PREGUNTAS ---
@bot.message_handler(commands=['status', 'pregunta'])
def responder(message):
    bot.reply_to(message, "🏹 Raúl Sniper V10\n✅ Estado: Online y escuchando.")

# --- MOTOR DE ANÁLISIS ---
def motor_sniper():
    while True:
        for s in SIMBOLOS:
            try:
                df = yf.download(s, interval="1m", period="1d", progress=False)
                if df.empty: continue
                precio = df['Close'].iloc[-1]
                soporte = df['Low'].tail(50).min()
                if precio <= soporte * 1.0002:
                    bot.send_message(CHAT_ID, f"🎯 ALERTA: {s} en zona ({precio:.5f})")
            except: continue
        time.sleep(30)

# --- INTERFAZ STREAMLIT ---
st.title("🏹 Sniper Búnker V10")
st.success("Sistema conectado. El control es por Telegram.")

if 'activo' not in st.session_state:
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    threading.Thread(target=motor_sniper, daemon=True).start()
    st.session_state.activo = True
    bot.send_message(CHAT_ID, "🚀 Sistema reseteado desde cero. Escribe /status")

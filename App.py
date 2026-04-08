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

PARES = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X"]

# --- FUNCIONES DEL SNIPER ---
def escanear_una_vez():
    alertas = 0
    for p in PARES:
        try:
            df = yf.download(p, interval="1m", period="1d", progress=False)
            if df.empty: continue
            precio = df['Close'].iloc[-1]
            # Ejemplo rápido de soporte
            soporte = df['Low'].tail(30).min()
            if precio <= soporte * 1.0002:
                bot.send_message(CHAT_ID, f"🎯 SNIPER: {p} en Soporte ({precio:.5f})")
                alertas += 1
        except: continue
    return alertas

# --- COMANDOS DE TELEGRAM ---
@bot.message_handler(commands=['start', 'status'])
def responder_status(message):
    bot.reply_to(message, "✅ Raúl Sniper V10 Online\n📡 Esperando órdenes.")

# --- PROCESOS EN SEGUNDO PLANO ---
def iniciar_bot():
    bot.infinity_polling()

# --- INTERFAZ SENCILLA ---
st.title("🏹 Sniper V10 - Base Limpia")

if 'bot_thread' not in st.session_state:
    threading.Thread(target=iniciar_bot, daemon=True).start()
    st.session_state.bot_thread = True
    bot.send_message(CHAT_ID, "🚀 Bot conectado correctamente.")

st.success("Conexión con Telegram: OK")

if st.button("🔍 Escanear Mercado Ahora"):
    with st.spinner("Buscando entradas..."):
        encontradas = escanear_una_vez()
        st.write(f"Escaneo terminado. Alertas enviadas: {encontradas}")

st.info("Escribe /status en Telegram para probar la comunicación.")

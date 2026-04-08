import streamlit as st
import telebot
import yfinance as yf
import pandas_ta as ta
import threading
import time
from datetime import datetime

# ======================================================
# 1. CONFIGURACIÓN
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

# Divisas a monitorear
SIMBOLOS = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X",
    "EURJPY=X", "GBPJPY=X", "EURAUD=X", "EURCAD=X", "GBPCHF=X"
]

# ======================================================
# 2. ESCUCHA DE COMANDOS (TELEGRAM)
# ======================================================
@bot.message_handler(commands=['status', 'info', 'pregunta'])
def respuesta_comandos(message):
    ahora = datetime.now().strftime('%H:%M:%S')
    respuesta = (f"🏹 *Raúl Sniper V10*\n"
                 f"✅ *Estado:* Operativo y Vigilando\n"
                 f"📡 *Pares:* {len(SIMBOLOS)}\n"
                 f"⏰ *Hora:* {ahora}\n"
                 f"💰 *Mercado:* Forex 24/5")
    bot.reply_to(message, respuesta, parse_mode="Markdown")

# ======================================================
# 3. LÓGICA DEL SCANNER (SEGUNDO PLANO)
# ======================================================
def motor_sniper():
    cooldown = {}
    while True:
        for s in SIMBOLOS:
            try:
                # Descarga rápida de 1 día para análisis de 1m
                df = yf.download(s, interval="1m", period="1d", progress=False)
                if df.empty: continue
                
                precio = df['Close'].iloc[-1]
                soporte = df['Low'].tail(50).min()
                
                # Ejemplo de señal simple: El precio toca soporte importante
                if precio <= soporte * 1.0002:
                    if s not in cooldown or (time.time() - cooldown[s] > 600):
                        bot.send_message(CHAT_ID, f"🎯 *SNIPER ALERTA*\n💎 Activo: {s}\n💰 Precio: {precio:.5f}\n🧱 Zona de Soporte alcanzada.")
                        cooldown[s] = time.time()
            except:
                continue
        time.sleep(30) # Escaneo cada 30 segundos

# ======================================================
# 4. INTERFAZ DE STREAMLIT (ESTABLE)
# ======================================================
st.title("🏹 Raúl Sniper Búnker V10")
st.write("---")

# Iniciamos los hilos solo una vez
if 'ejecutando' not in st.session_state:
    # Hilo para que el bot responda mensajes en Telegram
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    # Hilo para que el motor analice el mercado sin parar
    threading.Thread(target=motor_sniper, daemon=True).start()
    
    st.session_state.ejecutando = True
    bot.send_message(CHAT_ID, "🚀 *Sistema Raúl Sniper Reiniciado*\nEstado: Online y Escuchando.")

st.success("✅ El bot está conectado con Telegram.")
st.info("💡 **Cómo usarlo:**\n- No cierres esta pestaña.\n- Ve a Telegram y escribe `/status` para saber si el bot te oye.\n- Las señales llegarán solas cuando se cumplan las condiciones.")

import streamlit as st
import time
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime
import holidays

# ======================================================
# 1. CONFIGURACIÓN Y CREDENCIALES
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

# Las 15 divisas solicitadas
SIMBOLOS = [
    "EURAUD=X", "EURCAD=X", "EURCHF=X", "GBPAUD=X", "GBPCAD=X",
    "GBPJPY=X", "AUDUSD=X", "AUDCAD=X", "AUDJPY=X", "EURUSD=X",
    "GBPUSD=X", "USDJPY=X", "USDCAD=X", "USDCHF=X", "NZDUSD=X"
]

COOLDOWN = {}

# ======================================================
# 2. MOTOR DE ANÁLISIS: MURALLA, FIBO Y TRAYECTORIA
# ======================================================
def analizar_sniper(s):
    try:
        # Descargamos data de 1 min (2 días para asegurar las 240 velas)
        df = yf.download(s, interval="1m", period="2d", progress=False)
        if len(df) < 240: return

        # Indicadores Técnicos
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        # 1. Filtro Muralla (35 toques en las últimas 240 velas)
        df_240 = df.tail(240)
        soporte = df_240['Low'].min()
        resistencia = df_240['High'].max()
        # Margen de precisión para detectar el "toque"
        margen = soporte * 0.0002 
        toques = ((df_240['Low'] - soporte).abs() <= margen).sum()

        # 2. Fibonacci (Zona de retroceso 50-70%)
        rango = resistencia - soporte
        fibo_50 = resistencia - (0.50 * rango)
        fibo_70 = resistencia - (0.70 * rango)

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # --- SEÑAL 1: TRAYECTORIA UNIFORME (Gatillo 2 min) ---
        if fibo_70 <= precio <= fibo_50 and v_act['EMA20'] > v_ant['EMA20']:
            # Confirmación con cruce de EMA 3 sobre 9
            if v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']:
                enviar_telegram(s, precio, toques, "🚀 TRAYECTORIA UNIFORME")

        # --- SEÑAL 2: COLISIÓN EN MURALLA ---
        if toques >= 35 and abs(precio - soporte) <= (precio * 0.0004):
            rsi_val = v_act['RSI']
            # Diagnóstico de fuerza según RSI
            if rsi_val > 55:
                est = "🔥 REBOTE CONFIRMADO"
            elif rsi_val < 40:
                est = "⚠️ POSIBLE RUPTURA"
            else:
                est = "⌛ LATERALIZANDO"
            
            enviar_telegram(s, precio, toques, f"🧱 COLISIÓN: {est}")

    except Exception:
        pass

def enviar_telegram(s, p, t, tipo):
    clave = f"{s}_{tipo}"
    # Cooldown de 10 minutos para no saturar con el mismo activo
    if clave not in COOLDOWN or (time.time() - COOLDOWN[clave] > 600):
        msg = (f"🎯 *RAÚL SNIPER V10*\n\n"
               f"💎 *Activo:* {s}\n"
               f"💰 *Precio:* {p:.5f}\n"
               f"🧱 *Choques:* {t}\n"
               f"📡 *Señal:* {tipo}")
        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
        COOLDOWN[clave] = time.time()

# ======================================================
# 3. INTERFAZ ESTABLE Y BUCLE DE EJECUCIÓN
# ======================================================
st.set_page_config(page_title="Raúl Sniper V10", layout="centered")
st.title("🏹 Raúl Sniper Pro V10")
st.write("Estado: **Radar Escaneando...** 📡")
st.info("Las señales se envían automáticamente a Telegram. No cierres esta pestaña.")

# Filtro de seguridad para fines de semana y feriados
ahora = datetime.now()
feriados_us = holidays.US()

if ahora.weekday() < 5 and ahora not in feriados_us:
    if 'bot_on' not in st.session_state:
        bot.send_message(CHAT_ID, "🚀 *Bot V10 Online*")
        st.session_state.bot_on = True

    # BUCLE SILENCIOSO: Evita el error 'removeChild' al no actualizar la UI web
    while True:
        for s in SIMBOLOS:
            analizar_sniper(s)
            time.sleep(0.5) 
        time.sleep(20)
else:
    st.error("Mercado Cerrado o Día Festivo. El bot está en pausa.")

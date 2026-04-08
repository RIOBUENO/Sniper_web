import streamlit as st
import time
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime

# ======================================================
# 1. CONFIGURACIÓN (Tus credenciales)
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

SIMBOLOS = ["EURUSD=X", "GBPUSD=X", "EURCHF=X", "GBPJPY=X", "BTC-USD", "ETH-USD", "AUDUSD=X"]

# Parámetros Sniper
TOLERANCIA_MURO = 0.0005  
MIN_TOQUES = 35           
COOLDOWN = {}

# ======================================================
# 2. PROCESAMIENTO TÉCNICO
# ======================================================

def enviar_alerta(titulo, msg):
    try:
        bot.send_message(CHAT_ID, f"⚠️ *{titulo}*\n\n{msg}", parse_mode="Markdown")
    except: pass

def procesar_sniper(s):
    try:
        # Descarga de datos
        df = yf.download(s, interval="1m", period="1d", progress=False)
        if df.empty or len(df) < 50: return

        # Indicadores
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        
        # Muralla
        zona_soporte = df['Low'].rolling(window=50).min().iloc[-1]
        margen = zona_soporte * 0.0003
        toques = ((df['Low'] - zona_soporte).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # Lógica: EMA20 alcista + Cerca del Muro + 35 Toques + Cruce 3/9
        if v_act['EMA20'] > v_ant['EMA20'] and abs(precio - zona_soporte) <= (precio * TOLERANCIA_MURO):
            if toques >= MIN_TOQUES and (v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']):
                if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 600):
                    enviar_alerta("¡DISPARA SNIPER!", f"Activo: {s}\nPrecio: {precio:.5f}\nMuralla: {toques} toques")
                    COOLDOWN[s] = time.time()
    except: pass

# ======================================================
# 3. INTERFAZ (SIN DIBUJOS QUE DEN ERROR)
# ======================================================

st.title("Raúl Sniper Elite V8.2")
st.write("Sistema cargado. Las señales llegan a Telegram.")

# Mensaje de inicio (Solo una vez)
if 'ready' not in st.session_state:
    enviar_alerta("SISTEMA ONLINE", "Bot activo. Versión estable sin errores visuales.")
    st.session_state.ready = True

# ======================================================
# 4. LOOP INFINITO
# ======================================================

while True:
    for s in SIMBOLOS:
        procesar_sniper(s)
        time.sleep(1) # Un segundo entre pares para no saturar
    
    time.sleep(30) # Pausa de medio minuto entre escaneos

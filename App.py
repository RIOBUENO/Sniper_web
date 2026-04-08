import streamlit as st
import time
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime

# ======================================================
# 1. CONFIGURACIÓN (Tus datos)
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
# 2. LÓGICA DE TRADING (Pura)
# ======================================================

def enviar_alerta(titulo, msg):
    try:
        bot.send_message(CHAT_ID, f"⚠️ *{titulo}*\n\n{msg}", parse_mode="Markdown")
    except:
        pass

def procesar_sniper(s):
    try:
        # Descarga de datos
        df = yf.download(s, interval="1m", period="1d", progress=False)
        if df.empty or len(df) < 50: return

        # Indicadores técnicos
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        
        # Muralla (Soporte de 50 velas)
        zona_soporte = df['Low'].rolling(window=50).min().iloc[-1]
        margen = zona_soporte * 0.0003
        toques = ((df['Low'] - zona_soporte).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # CONDICIÓN DE DISPARO
        # 1. EMA20 con tendencia alcista
        # 2. Precio cerca de la muralla
        # 3. Al menos 35 toques históricos
        # 4. Cruce de EMA 3 sobre EMA 9
        if v_act['EMA20'] > v_ant['EMA20'] and abs(precio - zona_soporte) <= (precio * TOLERANCIA_MURO):
            if toques >= MIN_TOQUES and (v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']):
                if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 600):
                    enviar_alerta("¡DISPARA SNIPER!", f"Activo: {s}\nPrecio: {precio:.5f}\nMuralla: {toques} toques")
                    COOLDOWN[s] = time.time()
    except:
        pass

# ======================================================
# 3. INTERFAZ ESTÁTICA (Para no romper el Node)
# ======================================================

st.title("Raúl Sniper Elite V8.2")
st.write("Estado: Escaneando activos en segundo plano.")
st.write("Las señales se envían directamente a Telegram.")

# Notificación de inicio
if 'session_active' not in st.session_state:
    enviar_alerta("SISTEMA ONLINE", "Bot activo. Versión estable sin errores de interfaz.")
    st.session_state.session_active = True

# ======================================================
# 4. LOOP INFINITO DE EJECUCIÓN
# ======================================================

while True:
    for s in SIMBOLOS:
        procesar_sniper(s)
        time.sleep(1) # Pausa técnica para evitar bloqueos de API
    
    time.sleep(30) # Pausa entre ciclos de escaneo

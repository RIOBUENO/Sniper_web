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
# 2. LÓGICA DE TRADING
# ======================================================

def enviar_alerta(titulo, msg):
    try:
        bot.send_message(CHAT_ID, f"⚠️ *{titulo}*\n\n{msg}", parse_mode="Markdown")
    except: pass

def procesar_sniper(s):
    try:
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

        # Filtros: EMA20 Alcista + Muralla + Cruce 3/9
        if v_act['EMA20'] > v_ant['EMA20'] and abs(precio - zona_soporte) <= (precio * TOLERANCIA_MURO):
            if toques >= MIN_TOQUES and (v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']):
                if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 600):
                    enviar_alerta("¡DISPARA SNIPER!", f"Activo: {s}\nPrecio: {precio:.5f}\nConfirmación: Muralla ({toques} toques)")
                    COOLDOWN[s] = time.time()
    except: pass

# ======================================================
# 3. INTERFAZ MUERTA (PARA EVITAR ERRORES)
# ======================================================

st.set_page_config(page_title="Raúl Sniper V8.2", layout="centered")
st.title("Raúl Sniper Elite V8.2 🕵️")
st.write("### ✅ EL BOT ESTÁ OPERANDO EN EL FONDO.")
st.write("La interfaz visual se desactivó para garantizar estabilidad. Revisa tu Telegram para señales.")

# Inicialización silenciosa
if 'ready' not in st.session_state:
    enviar_alerta("SISTEMA ONLINE", "Resurrección completada. Escaneando en silencio...")
    st.session_state.ready = True

# ======================================================
# 4. LOOP INFINITO (SIN DIBUJO)
# ======================================================

while True:
    try:
        # Escaneo silencioso
        for s in SIMBOLOS:
            procesar_sniper(s)
            time.sleep(1)
        
        # Pausa larga para que la web no intente refrescarse
        time.sleep(30)
        
    except Exception:
        time.sleep(10)
        continue

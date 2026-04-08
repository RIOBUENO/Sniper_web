import streamlit as st
import time
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime

# ======================================================
# 1. CONFIGURACIÓN (Tus credenciales integradas)
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

# Activos a monitorear
SIMBOLOS = [
    "EURUSD=X", "GBPUSD=X", "EURCHF=X", "GBPJPY=X", 
    "BTC-USD", "ETH-USD", "SOL-USD", "AUDUSD=X"
]

# Parámetros Estratégicos
TOLERANCIA_MURO = 0.0005  
MIN_TOQUES = 35           
COOLDOWN = {}

# ======================================================
# 2. FUNCIONES DE OPERACIÓN
# ======================================================

def enviar_alerta(titulo, msg):
    """Envía la señal a Telegram"""
    try:
        bot.send_message(CHAT_ID, f"⚠️ *{titulo}*\n\n{msg}", parse_mode="Markdown")
    except:
        pass

def procesar_sniper(s):
    """Lógica de escaneo y disparo"""
    try:
        # Descarga rápida de datos
        df = yf.download(s, interval="1m", period="1d", progress=False)
        if df.empty or len(df) < 50: return

        # Cálculo de Indicadores
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        
        # Detección de Muralla (Soporte)
        zona_soporte = df['Low'].rolling(window=50).min().iloc[-1]
        margen = zona_soporte * 0.0003
        toques = ((df['Low'] - zona_soporte).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # CONDICIONES DE DISPARO
        t_alcista = v_act['EMA20'] > v_ant['EMA20']
        cerca_muro = abs(precio - zona_soporte) <= (precio * TOLERANCIA_MURO)

        if t_alcista and cerca_muro and toques >= MIN_TOQUES:
            # Gatillo: Cruce EMA 3 sobre 9
            if v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']:
                # Evitar alertas repetidas (Cooldown 10 min)
                if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 600):
                    msg = f"Activo: {s}\nOP: COMPRA (1-2 min)\nPrecio: {precio:.5f}\nConfirmación: Muralla {toques}T"
                    enviar_alerta("¡DISPARA SNIPER!", msg)
                    COOLDOWN[s] = time.time()
    except:
        pass

# ======================================================
# 3. INTERFAZ STREAMLIT (ESTABLE)
# ======================================================

st.set_page_config(page_title="Raúl Sniper Elite", layout="centered")
st.title("Raúl Sniper Elite V8.2 🕵️")
st.success("BOT EN EJECUCIÓN: El sistema está escaneando el mercado.")
st.info("Toda la actividad se reportará a tu Telegram. Esta página se mantiene estática para evitar errores.")

# Notificación de inicio
if 'iniciado' not in st.session_state:
    enviar_alerta("SISTEMA ONLINE", "El bot ha arrancado correctamente con los nuevos requisitos. ¡A cobrar!")
    st.session_state.iniciado = True

# ======================================================
# 4. LOOP PRINCIPAL (FONDO)
# ======================================================

while True:
    try:
        # Escaneo de cada par
        for s in SIMBOLOS:
            procesar_sniper(s)
            time.sleep(1) # Pausa técnica para no saturar Yahoo Finance
        
        # Espera 15 segundos antes del siguiente ciclo completo
        time.sleep(15)
        
    except Exception as e:
        # Si algo falla, espera y sigue
        time.sleep(10)
        continue

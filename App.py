import streamlit as st
import time
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime

# ======================================================
# 1. CREDENCIALES (Tus bases)
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

# Activos con mayor liquidez para evitar "barridos" falsos
SIMBOLOS = ["EURUSD=X", "GBPUSD=X", "GBPJPY=X", "BTC-USD", "ETH-USD", "AUDUSD=X"]

# Configuración Técnica
MIN_TOQUES = 35           # Tu filtro de zona de choque
COOLDOWN = {}

# ======================================================
# 2. EL CEREBRO: ANALIZADOR DE IMPULSOS
# ======================================================

def procesar_sniper(s):
    try:
        # Analizamos 240 velas para ver la tendencia uniforme
        df = yf.download(s, interval="1m", period="5d", progress=False)
        if df.empty or len(df) < 240: return

        # Indicadores de Trayectoria
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        
        # --- ZONA DE CHOQUE Y LIQUIDEZ ---
        df_240 = df.tail(240)
        zona_soporte = df_240['Low'].min()
        margen = zona_soporte * 0.0003
        
        # Contamos los choques en la orilla
        toques = ((df_240['Low'] - zona_soporte).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # --- VALIDACIÓN DE TENDENCIA UNIFORME ---
        # La EMA 20 debe estar por encima de la zona y subiendo para aprovechar el impulso
        impulso_alcista = v_act['EMA20'] > v_ant['EMA20'] and precio > v_act['EMA20']
        
        # --- FILTRO ANTIPENDEJEO (Barrido de Liquidez) ---
        # Si el RSI está muy plano, está barriendo. Si sube, hay rebote.
        df['RSI'] = ta.rsi(df['Close'], length=14)
        confirmacion_fuerza = df['RSI'].iloc[-1] > 50

        # --- REGLA DE DISPARO AL CIERRE DE VELA ---
        if toques >= MIN_TOQUES and impulso_alcista and confirmacion_fuerza:
            # Cruce de EMA 3 sobre 9 al cierre
            if v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']:
                
                distancia_muro = abs(precio - zona_soporte) / precio
                if distancia_muro <= 0.0010: # Solo si está en la trayectoria de la orilla
                    
                    if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 600):
                        msg = (f"🎯 ¡DISPARO SNIPER!\n"
                               f"Activo: {s}\n"
                               f"Precio: {precio:.5f}\n"
                               f"Zona de Choque: {toques} toques\n"
                               f"Estado: Impulso en trayectoria EMA20\n"
                               f"Cruce 3/9: Confirmado ✅")
                        
                        bot.send_message(CHAT_ID, msg)
                        COOLDOWN[s] = time.time()
    except:
        pass

# ======================================================
# 3. INTERFAZ MUERTA (PARA QUE NO SE CAIGA)
# ======================================================

st.title("Raúl Sniper Elite V8.2")
st.write("Analizando zonas de choque y barrido de liquidez...")
st.write("Estado: ACTIVO (Solo Telegram)")

if 'iniciado' not in st.session_state:
    bot.send_message(CHAT_ID, "🚀 Sniper V8.2 Online: Buscando zonas de +35 choques e impulsos en EMA20.")
    st.session_state.iniciado = True

# ======================================================
# 4. BUCLE DE FONDO
# ======================================================

while True:
    for s in SIMBOLOS:
        procesar_sniper(s)
        time.sleep(1)
    time.sleep(15)

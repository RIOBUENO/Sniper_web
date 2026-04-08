import streamlit as st
import time
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime

# ======================================================
# 1. CREDENCIALES
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

SIMBOLOS = ["EURUSD=X", "GBPUSD=X", "EURCHF=X", "GBPJPY=X", "BTC-USD", "ETH-USD", "AUDUSD=X"]

# Parámetros de la Estrategia Original
MIN_TOQUES = 35           
TOLERANCIA_MURO = 0.0005  
COOLDOWN = {}

# ======================================================
# 2. LÓGICA DE TRADING (Impulso y Zona de Choque)
# ======================================================

def procesar_sniper(s):
    try:
        # Descarga de datos para análisis de tendencia uniforme
        df = yf.download(s, interval="1m", period="5d", progress=False)
        if df.empty or len(df) < 240: return

        # Cálculo de EMAs para la trayectoria
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        
        # Análisis de la Muralla (Últimas 240 velas)
        df_240 = df.tail(240)
        zona_soporte = df_240['Low'].min()
        margen = zona_soporte * 0.0003
        toques = ((df_240['Low'] - zona_soporte).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # FILTROS FUNDAMENTALES
        # 1. Impulso: EMA 20 alcista y precio por encima
        impulso_alcista = v_act['EMA20'] > v_ant['EMA20'] and precio > v_act['EMA20']
        
        # 2. Zona de Choque: Mínimo 35 toques para confirmar liquidez
        # 3. Gatillo: Cruce de EMA 3 sobre EMA 9 al cierre
        if toques >= MIN_TOQUES and impulso_alcista:
            if v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']:
                
                # Verificación de cercanía a la orilla (Trayectoria)
                if abs(precio - zona_soporte) <= (precio * TOLERANCIA_MURO):
                    if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 600):
                        msg = (f"🎯 ¡SEÑAL SNIPER DETECTADA!\n"
                               f"Activo: {s}\n"
                               f"Precio: {precio:.5f}\n"
                               f"Zona de Choque: {toques} toques\n"
                               f"Confirmación: Impulso EMA20 + Cruce 3/9")
                        
                        bot.send_message(CHAT_ID, msg)
                        COOLDOWN[s] = time.time()
    except:
        pass

# ======================================================
# 3. INTERFAZ ESTÁTICA (A PRUEBA DE ERRORES)
# ======================================================

st.title("Raúl Sniper Elite V8.2")
st.write("### ✅ BOT OPERATIVO")
st.write("Análisis de 240 velas activo. Las señales se envían a Telegram.")

# Notificación de reinicio exitoso
if 'init' not in st.session_state:
    bot.send_message(CHAT_ID, "🚀 Bot Sniper restablecido. Buscando zonas de choque y barrido de liquidez.")
    st.session_state.init = True

# ======================================================
# 4. LOOP DE FONDO
# ======================================================

while True:
    for s in SIMBOLOS:
        procesar_sniper(s)
        time.sleep(1)
    time.sleep(20)

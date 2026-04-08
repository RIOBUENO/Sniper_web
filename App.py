import streamlit as st
import time
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime

# ======================================================
# 1. CREDENCIALES (Tus datos reales)
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

# Activos a monitorear
SIMBOLOS = [
    "EURUSD=X", "GBPUSD=X", "EURCHF=X", "GBPJPY=X", 
    "BTC-USD", "ETH-USD", "SOL-USD", "AUDUSD=X"
]

# Configuración de Estrategia (La orilla que estudiamos)
TOLERANCIA_MURO = 0.0005  
MIN_TOQUES = 35           # Tu filtro de alta calidad
COOLDOWN = {}             # Para que no te sature el celular

# ======================================================
# 2. EL CEREBRO (Análisis de Velas)
# ======================================================

def enviar_alerta(titulo, msg):
    try:
        bot.send_message(CHAT_ID, f"⚠️ *{titulo}*\n\n{msg}", parse_mode="Markdown")
    except:
        pass

def procesar_sniper(s):
    try:
        # Descargamos suficiente histórico para el análisis de 240 velas si es necesario
        # Usamos interval 1m para precisión de Sniper
        df = yf.download(s, interval="1m", period="5d", progress=False)
        if df.empty or len(df) < 240: return

        # Indicadores Técnicos
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        
        # --- BUSCANDO LA MURALLA ---
        # Analizamos las últimas 240 velas para encontrar el soporte más fuerte
        lookback = 240
        df_recent = df.tail(lookback)
        zona_soporte = df_recent['Low'].min()
        
        # Contamos cuántas veces el precio tocó esa "orilla"
        margen = zona_soporte * 0.0003
        toques = ((df_recent['Low'] - zona_soporte).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # --- REGLAS DE ORO ---
        # 1. EMA 20 tiene que venir subiendo (Tendencia)
        t_alcista = v_act['EMA20'] > v_ant['EMA20']
        
        # 2. El precio tiene que estar pegado a la zona (La orilla)
        cerca_muro = abs(precio - zona_soporte) <= (precio * TOLERANCIA_MURO)

        # 3. Solo si hay más de 35 toques (Calidad)
        if t_alcista and cerca_muro and toques >= MIN_TOQUES:
            
            # 4. GATILLO: Cruce de la 3 sobre la 9 (El disparo)
            if v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']:
                
                # Evitamos mandar 500 mensajes por la misma señal
                if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 600):
                    msg = (f"Activo: {s}\n"
                           f"Precio Actual: {precio:.5f}\n"
                           f"Muralla Detectada: {zona_soporte:.5f}\n"
                           f"Calidad de Zona: {toques} toques\n"
                           f"Confirmación: EMA 20 Alcista + Cruce 3/9")
                    
                    enviar_alerta("¡DISPARA SNIPER!", msg)
                    COOLDOWN[s] = time.time()
    except:
        pass

# ======================================================
# 3. LA PÁGINA (ESTÁTICA TOTAL)
# ======================================================

# No ponemos nada que cambie, solo un título y ya.
st.title("Raúl Sniper V8.2")
st.write("Estado: Monitoreando 240 velas por activo.")
st.write("Señales activas vía Telegram.")

# Notificación de arranque
if 'online' not in st.session_state:
    enviar_alerta("SISTEMA ONLINE", "Analizando el mercado sin gráficos para máxima estabilidad.")
    st.session_state.online = True

# ======================================================
# 4. EL BUCLE (FONDO)
# ======================================================

while True:
    for s in SIMBOLOS:
        procesar_sniper(s)
        time.sleep(0.5) # Respiro para que no nos bloqueen por intensidad
    
    # Esperamos 20 segundos antes de volver a escanear todo
    time.sleep(20)

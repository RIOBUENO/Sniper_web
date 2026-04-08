import streamlit as st
import time
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime

# ======================================================
# 1. CREDENCIALES (YA INTEGRADAS)
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

# Activos a monitorear
SIMBOLOS = [
    "EURUSD=X", "GBPUSD=X", "EURCHF=X", "GBPJPY=X", 
    "BTC-USD", "ETH-USD", "SOL-USD", "AUDUSD=X"
]

# Configuración de Estrategia
TOLERANCIA_MURO = 0.0005  
MIN_TOQUES = 35           
COOLDOWN = {}

# ======================================================
# 2. LÓGICA DE TRADING (COPILOTO + SNIPER)
# ======================================================

def es_horario_seguro():
    ahora_utc = datetime.utcnow()
    hora_actual = ahora_utc.strftime("%H:%M")
    bloqueos = [("06:30", "07:30"), ("12:30", "13:30"), ("15:30", "16:30")]
    for inicio, fin in bloqueos:
        if inicio <= hora_actual <= fin: return False
    return True

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

        # Indicadores
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # Muralla
        zona_soporte = df['Low'].rolling(window=50).min().iloc[-1]
        margen = zona_soporte * 0.0003
        toques = ((df['Low'] - zona_soporte).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # --- RADAR ---
        distancia = abs(precio - zona_soporte) / precio
        if 0.0008 <= distancia <= 0.0025:
            if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 900):
                enviar_alerta("AVISO DE RADAR", f"Activo: {s}\nZona: {zona_soporte:.5f}\nToques: {toques}\nCopiloto analizando...")
                COOLDOWN[s] = time.time()

        # --- SNIPER ---
        t_alcista = v_act['EMA20'] > v_ant['EMA20']
        cerca_muro = abs(precio - zona_soporte) <= (precio * TOLERANCIA_MURO)

        if t_alcista and cerca_muro and toques >= MIN_TOQUES:
            if v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']:
                if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 600):
                    enviar_alerta("¡DISPARA SNIPER!", f"Activo: {s}\nOP: COMPRA (1-2 min)\nPrecio: {precio:.5f}")
                    COOLDOWN[s] = time.time()
    except:
        pass

# ======================================================
# 3. INTERFAZ ESTÁTICA (ANTI-ERRORES)
# ======================================================

st.set_page_config(page_title="Raúl Sniper Elite", layout="centered")
st.title("Raúl Sniper Elite V8.2 🕵️")
st.success("SISTEMA ACTIVO: El bot está operando en el fondo.")
st.write("Puedes cerrar esta ventana, las señales llegarán a tu Telegram.")

# Función para responder /status
def revisar_comandos():
    try:
        updates = bot.get_updates(offset=-1, timeout=1)
        for u in updates:
            if u.message and u.message.text == "/status":
                bot.send_message(u.message.chat.id, "✅ Operativo. Escaneando el mercado.")
    except:
        pass

# Mensaje inicial
if 'iniciado' not in st.session_state:
    enviar_alerta("SISTEMA ONLINE", "Bot activo. Prueba escribiendo /status en Telegram.")
    st.session_state.iniciado = True

# ======================================================
# 4. LOOP INFINITO (SIN ELEMENTOS VISUALES QUE CAMBIEN)
# ======================================================

while True:
    try:
        revisar_comandos()
        
        if es_horario_seguro():
            for s in SIMBOLOS:
                procesar_sniper(s)
                time.sleep(1) # Respiro
        
        time.sleep(15) # Frecuencia de escaneo
        
    except Exception as e:
        time.sleep(10)
        continue

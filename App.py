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

SIMBOLOS = [
    "EURUSD=X", "GBPUSD=X", "EURCHF=X", "GBPJPY=X", 
    "BTC-USD", "ETH-USD", "SOL-USD", "AUDUSD=X"
]

# Configuración de Estrategia
TOLERANCIA_MURO = 0.0005  
MIN_TOQUES = 35           
COOLDOWN = {}

# ======================================================
# 2. FUNCIONES LÓGICAS (EL CEREBRO)
# ======================================================

def es_horario_seguro():
    ahora_utc = datetime.utcnow()
    hora_actual = ahora_utc.strftime("%H:%M")
    # Bloqueos de apertura/cierre
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
        df = yf.download(s, interval="1m", period="1d", progress=False)
        if df.empty or len(df) < 50: return

        # Indicadores Sniper
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # Detección de Muralla
        zona_soporte = df['Low'].rolling(window=50).min().iloc[-1]
        margen = zona_soporte * 0.0003
        toques = ((df['Low'] - zona_soporte).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # --- LÓGICA DE RADAR (Aviso previo) ---
        distancia = abs(precio - zona_soporte) / precio
        if 0.0008 <= distancia <= 0.0025:
            if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 900):
                enviar_alerta("AVISO DE RADAR", f"Activo: {s}\nZona: {zona_soporte:.5f}\nToques: {toques}\nCopiloto: Analizando entrada.")
                COOLDOWN[s] = time.time()

        # --- LÓGICA SNIPER (Disparo) ---
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
# 3. INTERFAZ ESTÁTICA (A PRUEBA DE ERRORES)
# ======================================================

st.set_page_config(page_title="Raúl Sniper Elite", page_icon="🕵️")
st.title("Raúl Sniper Elite V8.2 🚀")
st.success("BOT OPERATIVO EN EL SERVIDOR")
st.info("La interfaz web se ha desactivado para evitar errores de Node. Toda la información llegará a tu Telegram.")

# Listener para el comando /status
def revisar_comandos():
    try:
        updates = bot.get_updates(offset=-1, timeout=1)
        for u in updates:
            if u.message and u.message.text == "/status":
                bot.send_message(u.message.chat.id, "🤖 Raúl Sniper: Estoy activo y vigilando el mercado. No te fallaré, chamo.")
    except:
        pass

if 'iniciado' not in st.session_state:
    enviar_alerta("SISTEMA CONECTADO", "El bot ha superado el error de Node. Estoy escaneando.")
    st.session_state.iniciado = True

# ======================================================
# 4. LOOP DE EJECUCIÓN (FONDO)
# ======================================================

while True:
    try:
        # Escuchar Telegram
        revisar_comandos()
        
        # Ejecutar Estrategia
        if es_horario_seguro():
            for s in SIMBOLOS:
                procesar_sniper(s)
                time.sleep(0.5)
        
        # Pausa larga para que la web no se recargue locamente
        time.sleep(20)
        
    except Exception:
        time.sleep(10)
        continue

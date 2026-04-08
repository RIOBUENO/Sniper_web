import streamlit as st
import time
import datetime
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime, timedelta

# ======================================================
# 1. CONFIGURACIÓN MAESTRA
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

SIMBOLOS = [
    "EURUSD=X", "GBPUSD=X", "EURCHF=X", "GBPJPY=X", 
    "BTC-USD", "ETH-USD", "SOL-USD", "AUDUSD=X"
]

# Parámetros Estratégicos
TOLERANCIA_MURO = 0.0005  # 0.05%
MIN_TOQUES = 35           
COOLDOWN = {}

# ======================================================
# 2. FUNCIONES DEL COPILOTO
# ======================================================

def es_horario_seguro():
    ahora_utc = datetime.utcnow()
    hora_actual = ahora_utc.strftime("%H:%M")
    # Bloqueos de apertura/cierre
    bloqueos = [("06:30", "07:30"), ("12:30", "13:30"), ("15:30", "16:30")]
    for inicio, fin in bloqueos:
        if inicio <= hora_actual <= fin:
            return False
    return True

def analizar_uniformidad(df_camino):
    if len(df_camino) < 10: return False
    desviacion = df_camino['Close'].std()
    promedio = df_camino['Close'].mean()
    return desviacion < (promedio * 0.01)

def predecir_movimiento(toques, rsi):
    if toques > 40 and rsi > 70: return "REBOTE PROBABLE 📉"
    if toques < 15 and rsi < 60: return "POSIBLE RUPTURA 💥"
    return "CHOQUE EN CURSO 🛡️"

def enviar_alerta(titulo, msg):
    texto = f"⚠️ *{titulo}*\n\n{msg}"
    try:
        bot.send_message(CHAT_ID, texto, parse_mode="Markdown")
    except:
        pass

# ======================================================
# 3. MOTOR LÓGICO
# ======================================================

def procesar_sniper(s):
    try:
        df = yf.download(s, interval="1m", period="1d", progress=False)
        if df.empty or len(df) < 50: return

        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        zona_soporte = df['Low'].rolling(window=50).min().iloc[-1]
        margen = zona_soporte * 0.0003
        toques = ((df['Low'] - zona_soporte).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # --- RADAR COPILOTO ---
        distancia = abs(precio - zona_soporte) / precio
        if 0.0008 <= distancia <= 0.0025:
            if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 900):
                uniforme = analizar_uniformidad(df.tail(10))
                pred = predecir_movimiento(toques, v_act['RSI'])
                info = (f"Activo: {s}\nZona: {zona_soporte:.5f}\n"
                        f"Toques: {toques}\nFibo Apto: {'SÍ' if uniforme else 'NO'}\n"
                        f"Copiloto: {pred}")
                enviar_alerta("AVISO DE RADAR", info)
                COOLDOWN[s] = time.time()

        # --- DISPARO SNIPER ---
        t_alcista = v_act['EMA20'] > v_ant['EMA20']
        cerca_muro = abs(precio - zona_soporte) <= (precio * TOLERANCIA_MURO)

        if t_alcista and cerca_muro and toques >= MIN_TOQUES:
            if v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']:
                msg_final = (f"🔥 *¡DISPARA SNIPER!* 🔥\n\n"
                             f"Activo: {s}\nOP: COMPRA (1-2 min)\n"
                             f"Precio: {precio:.5f}\nConfirmación: 3/9 + Muralla")
                enviar_alerta("SEÑAL CONFIRMADA", msg_final)
                COOLDOWN[s] = time.time() + 600

    except Exception as e:
        print(f"Error en {s}: {e}")

# ======================================================
# 4. INTERFAZ Y LOOP (FIJADO PARA STREAMLIT)
# ======================================================

st.set_page_config(page_title="Raúl Sniper Elite", page_icon="🕵️")
st.title("Raúl Sniper Elite V8.2 🕵️")
st.markdown("---")
st.info("Escaneando mercado... Las señales llegarán a tu Telegram.")

# Contenedor estable para evitar errores de Nodo/JavaScript
placeholder = st.empty()

# Mensaje inicial de conexión
if 'conectado' not in st.session_state:
    enviar_alerta("SISTEMA ONLINE", "Copiloto y Sniper activos. ¡A cobrar, chamo!")
    st.session_state.conectado = True

while True:
    with placeholder.container():
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.write(f"🟢 **Bot en ejecución:** {ahora} (UTC)")
        
        if es_horario_seguro():
            for s in SIMBOLOS:
                procesar_sniper(s)
        else:
            st.warning("⚠️ Pausa de seguridad: Apertura o Cierre de Sesión.")
            
    time.sleep(15)

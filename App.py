import streamlit as st
import time
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime
import holidays

# ======================================================
# 1. CONFIGURACIÓN Y CREDENCIALES
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

# Las 15 divisas solicitadas
SIMBOLOS = [
    "EURAUD=X", "EURCAD=X", "EURCHF=X", "GBPAUD=X", "GBPCAD=X",
    "GBPJPY=X", "AUDUSD=X", "AUDCAD=X", "AUDJPY=X", "EURUSD=X",
    "GBPUSD=X", "USDJPY=X", "USDCAD=X", "USDCHF=X", "NZDUSD=X"
]

COOLDOWN = {}

# ======================================================
# 2. FILTROS DE SEGURIDAD (DÍAS Y HORAS)
# ======================================================
def mercado_abierto():
    ahora = datetime.now()
    # Filtro Fines de Semana (Sábado=5, Domingo=6)
    if ahora.weekday() >= 5:
        return False, "Mercado Cerrado (Fin de Semana)"
    
    # Filtro Días Festivos (USA y UK por impacto en Forex)
    us_holidays = holidays.US()
    uk_holidays = holidays.UK()
    if ahora in us_holidays or ahora in uk_holidays:
        return False, f"Día Festivo Detectado"
    
    return True, "Operativo"

# ======================================================
# 3. LÓGICA DE ANÁLISIS: MURALLA, FIBO Y TRAYECTORIA
# ======================================================
def analizar_sniper(s):
    try:
        # Descarga de datos (240 velas para análisis de muralla)
        df = yf.download(s, interval="1m", period="2d", progress=False)
        if len(df) < 240: return

        # Indicadores Técnicos
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        # --- FILTRO DE MURALLA (35 toques en 240 velas) ---
        df_240 = df.tail(240)
        soporte_historico = df_240['Low'].min()
        margen = soporte_historico * 0.0002 
        toques = ((df_240['Low'] - soporte_historico).abs() <= margen).sum()

        # --- CÁLCULO DE FIBONACCI (Impulso y Retroceso) ---
        alto_reciente = df_240['High'].max()
        rango = alto_reciente - soporte_historico
        fibo_50 = alto_reciente - (0.50 * rango)
        fibo_70 = alto_reciente - (0.70 * rango)

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # --- DIAGNÓSTICO DE TRAYECTORIA (2 MINUTOS) ---
        # Condición: Impulso uniforme, precio sobre EMA 20 y en zona Fibo
        en_trayectoria = fibo_70 <= precio <= fibo_50
        confirmacion_ema20 = v_act['EMA20'] > v_ant['EMA20'] and precio > v_act['EMA20']
        cruce_3_9 = v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']

        if confirmacion_ema20 and en_trayectoria and cruce_3_9:
            lanzar_alerta(s, precio, toques, "🚀 TRAYECTORIA UNIFORME (2 MIN)")

        # --- DIAGNÓSTICO EN ZONA DE COLISIÓN ---
        cerca_de_choque = abs(precio - soporte_historico) <= (precio * 0.0004)
        
        if cerca_de_choque and toques >= 35:
            # Análisis de fuerza en el choque
            rsi_val = v_act['RSI']
            if rsi_val > 55:
                veredicto = "🔥 REBOTE CONFIRMADO"
            elif rsi_val < 40:
                veredicto = "⚠️ POSIBLE RUPTURA"
            else:
                veredicto = "⌛ ZONA MUERTA (Lateralizando)"
            
            lanzar_alerta(s, precio, toques, f"🧱 COLISIÓN EN MURALLA\nVeredicto: {veredicto}")

    except:
        pass

def lanzar_alerta(s, precio, toques, tipo):
    clave = f"{s}_{tipo}"
    if clave not in COOLDOWN or (time.time() - COOLDOWN[clave] > 600):
        msg = (f"🎯 *SNIPER V10 DISPARA*\n\n"
               f"💎 *Activo:* {s}\n"
               f"💰 *Precio:* {precio:.5f}\n"
               f"🧱 *Toques Muralla:* {toques}\n"
               f"📡 *Estado:* {tipo}")
        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
        COOLDOWN[clave] = time.time()

# ======================================================
# 4. EJECUCIÓN (STREAMLIT)
# ======================================================
st.set_page_config(page_title="Raúl Sniper V10", layout="centered")
st.title("🏹 Raúl Sniper Pro V10")

abierto, mensaje = mercado_abierto()

if abierto:
    st.success(f"Sistema Operativo: {mensaje}")
    if 'iniciado' not in st.session_state:
        bot.send_message(CHAT_ID, "✅ *Bot V10 Online:* 15 Divisas, Muralla 35x y Fibo activados.")
        st.session_state.iniciado = True

    while True:
        for s in SIMBOLOS:
            analizar_sniper(s)
            time.sleep(0.5)
        time.sleep(15)
else:
    st.error(f"Bot en pausa: {mensaje}")

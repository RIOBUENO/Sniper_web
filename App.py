import streamlit as st
import time
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime

# ======================================================
# 1. CONFIGURACIÓN Y CREDENCIALES
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

SIMBOLOS = ["EURUSD=X", "GBPUSD=X", "GBPJPY=X", "BTC-USD", "ETH-USD", "AUDUSD=X"]
MIN_TOQUES = 35  # Tu filtro de muralla
COOLDOWN = {}

# ======================================================
# 2. CEREBRO TÉCNICO: FIBONACCI & MURALLA
# ======================================================

def analizar_sniper(s):
    try:
        # Descarga de 240 velas para análisis de zona de choque
        df = yf.download(s, interval="1m", period="5d", progress=False)
        if df.empty or len(df) < 240: return

        # Indicadores de Trayectoria
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        
        # --- DETECCIÓN DE MURALLA (Zona de Choque) ---
        df_recent = df.tail(240)
        max_periodo = df_recent['High'].max()
        min_periodo = df_recent['Low'].min()
        
        # Muralla Inferior (Soporte de 35 toques)
        margen = min_periodo * 0.0003
        toques = ((df_recent['Low'] - min_periodo).abs() <= margen).sum()

        # --- CÁLCULO DE FIBONACCI (Impulso y Retroceso) ---
        # Definimos el impulso reciente
        alto_impulso = df_recent['High'].max()
        bajo_impulso = df_recent['Low'].min()
        rango = alto_impulso - bajo_impulso
        
        # Niveles de oro: 50% y 70%
        fibo_50 = alto_impulso - (0.50 * rango)
        fibo_70 = alto_impulso - (0.70 * rango)

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # --- LÓGICA DE DECISIÓN ---
        
        # 1. ¿Va en trayectoria? (EMA 20 arriba y precio en zona Fibo)
        en_fibo = fibo_70 <= precio <= fibo_50
        tendencia_fuerte = v_act['EMA20'] > v_ant['EMA20']
        
        # 2. GATILLO: Cruce 3/9 en cierre de vela
        cruce_al_cierre = v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']

        # 3. DETECTOR DE REBOTE O RUPTURA EN MURALLA
        cerca_muralla = abs(precio - min_periodo) <= (precio * 0.0005)
        
        pronostico = ""
        if cerca_muralla:
            # Si hay fuerza (RSI subiendo) es REBOTE, si el precio se queda "pendejeando" es RUPTURA
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            pronostico = "🔥 PROBABLE REBOTE" if rsi > 45 else "⚠️ PELIGRO: POSIBLE RUPTURA"

        # --- DISPARO ---
        if toques >= MIN_TOQUES and tendencia_fuerte and en_fibo and cruce_al_cierre:
            
            if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 600):
                msg = (f"🎯 *¡SNIPER FIBONACCI DISPARA!*\n\n"
                       f"📈 *Activo:* {s}\n"
                       f"💰 *Precio:* {precio:.5f}\n"
                       f"🧱 *Muralla:* {toques} toques detectados\n"
                       f"📏 *Fibo:* En zona de oro (50%-70%)\n"
                       f"🚀 *Impulso:* EMA 20 Confirmada\n"
                       f"⚔️ *Cruce 3/9:* EXITOSO al cierre\n"
                       f"🔮 *Estado Muralla:* {pronostico}")
                
                bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                COOLDOWN[s] = time.time()
    except Exception as e:
        pass

# ======================================================
# 3. INTERFAZ STREAMLIT (Limpia)
# ======================================================

st.set_page_config(page_title="Raúl Sniper V9", layout="centered")
st.title("🏹 Raúl Sniper Pro+ V9")
st.subheader("Estrategia: Muralla 35x + Fibo 50-70%")
st.write("---")
st.info("El bot está analizando impulsos, retrocesos y zonas de choque en tiempo real.")

if 'ready' not in st.session_state:
    bot.send_message(CHAT_ID, "✅ *Sistema V9 Online*\nEstrategia de Fibonacci y Muralla cargada.", parse_mode="Markdown")
    st.session_state.ready = True

# ======================================================
# 4. BUCLE INFINITO
# ======================================================

while True:
    for s in SIMBOLOS:
        analizar_sniper(s)
        time.sleep(1)
    time.sleep(15)

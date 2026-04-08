import streamlit as st
import time
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime

# ======================================================
# 1. CONFIGURACIÓN (TUS CREDENCIALES)
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

SIMBOLOS = [
    "EURAUD=X", "EURCAD=X", "EURCHF=X", "GBPAUD=X", "GBPCAD=X",
    "GBPJPY=X", "AUDUSD=X", "AUDCAD=X", "AUDJPY=X", "EURUSD=X",
    "GBPUSD=X", "USDJPY=X", "USDCAD=X", "USDCHF=X", "NZDUSD=X"
]

# Usamos caché para que el cooldown sobreviva a recargas
if 'cooldown' not in st.session_state:
    st.session_state.cooldown = {}

# ======================================================
# 2. MOTOR DE ANÁLISIS SILENCIOSO
# ======================================================
def analizar_sniper(s):
    try:
        df = yf.download(s, interval="1m", period="1d", progress=False)
        if df.empty or len(df) < 50: return

        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)

        df_reciente = df.tail(120)
        soporte_h = df_reciente['Low'].min()
        resistencia_h = df_reciente['High'].max()
        margen = soporte_h * 0.0003 
        toques = ((df_reciente['Low'] - soporte_h).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = float(v_act['Close'])

        # Lógica Muralla 25x
        if abs(precio - soporte_h) <= (precio * 0.0005) and toques >= 25:
            enviar_alerta(s, precio, toques, "🧱 MURALLA 25x")

        # Lógica Trayectoria
        rango = resistencia_h - soporte_h
        fibo_50, fibo_70 = resistencia_h - (0.5*rango), resistencia_h - (0.7*rango)
        if (fibo_70 <= precio <= fibo_50) and (v_act['EMA20'] > v_ant['EMA20']):
            if v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']:
                enviar_alerta(s, precio, toques, "🚀 IMPULSO")
    except:
        pass

def enviar_alerta(s, precio, toques, tipo):
    clave = f"{s}_{tipo}"
    ahora = time.time()
    if clave not in st.session_state.cooldown or (ahora - st.session_state.cooldown[clave] > 600):
        msg = f"🎯 *RAÚL SNIPER*\n💎 *Activo:* {s}\n💰 *Precio:* {precio:.5f}\n🧱 *Toques:* {toques}\n📡 *Alerta:* {tipo}"
        try:
            bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
            st.session_state.cooldown[clave] = ahora
        except:
            pass

# ======================================================
# 3. INTERFAZ "FANTASMA" (SOLO TELEGRAM)
# ======================================================
st.set_page_config(page_title="Raúl Sniper Engine")
st.title("🏹 Engine en ejecución")
st.info("La web no se actualizará. Todo el monitoreo es por Telegram.")

# El bucle ahora es un fragmento que NO imprime nada en pantalla
@st.fragment(run_every=60)
def engine_loop():
    # Esta función corre en segundo plano cada minuto
    for s in SIMBOLOS:
        analizar_sniper(s)
        time.sleep(1) # Pausa suave para evitar bloqueos de IP

# Inicio automático
engine_loop()

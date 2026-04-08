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

if 'cooldown' not in st.session_state: st.session_state.cooldown = {}

# ======================================================
# 2. MOTOR DE ANÁLISIS (OPTIMIZADO)
# ======================================================
def analizar_sniper(s):
    try:
        # Descarga mínima para evitar bloqueos
        df = yf.download(s, interval="1m", period="1d", progress=False)
        if df.empty or len(df) < 50: return None

        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        df_reciente = df.tail(150)
        soporte_h = df_reciente['Low'].min()
        resistencia_h = df_reciente['High'].max()
        
        margen = soporte_h * 0.0003 
        toques = ((df_reciente['Low'] - soporte_h).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = float(v_act['Close'])

        # Lógica Muralla 25x
        distancia_zona = abs(precio - soporte_h) <= (precio * 0.0005)
        if distancia_zona and toques >= 25:
            enviar_alerta(s, precio, toques, "🧱 MURALLA 25x")

        # Lógica Trayectoria Fibo
        rango = resistencia_h - soporte_h
        fibo_50, fibo_70 = resistencia_h - (0.5*rango), resistencia_h - (0.7*rango)
        if (fibo_70 <= precio <= fibo_50) and (v_act['EMA20'] > v_ant['EMA20']) and (v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']):
            enviar_alerta(s, precio, toques, "🚀 IMPULSO")
            
        return f"{s}: {precio:.4f}"
    except: return None

def enviar_alerta(s, precio, toques, tipo):
    clave = f"{s}_{tipo}"
    ahora = time.time()
    if clave not in st.session_state.cooldown or (ahora - st.session_state.cooldown[clave] > 600):
        msg = f"🎯 *RAÚL SNIPER*\n💎 *Activo:* {s}\n💰 *Precio:* {precio:.5f}\n🧱 *Toques:* {toques}\n📡 *Alerta:* {tipo}"
        try:
            bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
            st.session_state.cooldown[clave] = ahora
        except: pass

# ======================================================
# 3. INTERFAZ ULTRA-LIGERA (EVITA EL ERROR DE NODO)
# ======================================================
st.set_page_config(page_title="Raúl Sniper V10")
st.title("🏹 Raúl Sniper Pro V10")

# Usamos un solo componente de texto que no cambia de estructura
monitor = st.empty()

# Función de ejecución controlada
def iniciar_radar():
    while True:
        ahora = datetime.now().strftime('%H:%M:%S')
        monitor.text(f"📡 Radar Activo | Última revisión: {ahora} | Esperando señales...")
        
        for s in SIMBOLOS:
            analizar_sniper(s)
            time.sleep(0.5) # Pausa técnica para estabilidad
            
        time.sleep(15) # Espera antes de la siguiente vuelta

# Solo inicia si es día de semana
if datetime.now().weekday() < 5:
    if st.button("🚀 ACTIVAR BOT (Modo Invisible)"):
        st.write("Bot iniciado. Puedes cerrar esta pestaña si el bot está en un servidor, o dejarla abierta sin tocar nada.")
        iniciar_radar()
else:
    st.error("Mercado cerrado.")

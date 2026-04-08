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

# Las 15 divisas confirmadas
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
    if ahora.weekday() >= 5: # Sábado y Domingo
        return False, "Mercado Cerrado (Fin de Semana)"
    
    us_holidays = holidays.US()
    if ahora in us_holidays:
        return False, "Día Festivo (USA)"
    
    return True, "Operativo"

# ======================================================
# 3. EL CEREBRO SNIPER: MURALLA, FIBO Y TRAYECTORIA
# ======================================================
def analizar_sniper(s):
    try:
        # Descarga de 240 velas para análisis de fondo
        df = yf.download(s, interval="1m", period="2d", progress=False)
        if len(df) < 240: return

        # Indicadores Técnicos
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        # --- FILTRO DE MURALLA (35 toques en 240 velas) ---
        df_240 = df.tail(240)
        soporte_h = df_240['Low'].min()
        resistencia_h = df_240['High'].max()
        margen = soporte_h * 0.0002 
        toques = ((df_240['Low'] - soporte_h).abs() <= margen).sum()

        # --- CÁLCULO DE FIBONACCI (Retroceso 50-70%) ---
        rango = resistencia_h - soporte_h
        fibo_50 = resistencia_h - (0.50 * rango)
        fibo_70 = resistencia_h - (0.70 * rango)

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # --- LÓGICA 1: TRAYECTORIA UNIFORME (2 MINUTOS) ---
        en_fibo = fibo_70 <= precio <= fibo_50
        tendencia_ema20 = v_act['EMA20'] > v_ant['EMA20'] and precio > v_act['EMA20']
        cruce_confirmado = v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']

        if tendencia_ema20 and en_fibo and cruce_confirmado:
            disparar_alerta(s, precio, toques, "🚀 TRAYECTORIA UNIFORME (2 MIN)")

        # --- LÓGICA 2: ZONA DE COLISIÓN (MURALLA) ---
        en_zona_choque = abs(precio - soporte_h) <= (precio * 0.0004)
        
        if en_zona_choque and toques >= 35:
            rsi_val = v_act['RSI']
            if rsi_val > 55:
                diagnostico = "🔥 REBOTE CONFIRMADO"
            elif rsi_val < 40:
                diagnostico = "⚠️ RUPTURA INMINENTE"
            else:
                diagnostico = "⌛ LATERALIZANDO (Sin fuerza)"
            
            disparar_alerta(s, precio, toques, f"🧱 COLISIÓN\nVeredicto: {diagnostico}")

    except:
        pass

def disparar_alerta(s, precio, toques, tipo):
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
# 4. INTERFAZ Y BUCLE DE EJECUCIÓN
# ======================================================
st.set_page_config(page_title="Raúl Sniper V10")
st.title("🏹 Raúl Sniper Pro V10")

abierto, mensaje = mercado_abierto()

if abierto:
    st.success(f"✅ Bot Online: {mensaje}")
    # Usamos un placeholder para evitar errores de actualización de nodos (removeChild)
    placeholder = st.empty()
    
    if 'bot_on' not in st.session_state:
        bot.send_message(CHAT_ID, "🚀 *Bot V10 Activado*\nMonitoreando 15 divisas.")
        st.session_state.bot_on = True

    while True:
        with placeholder.container():
            st.write(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
            for s in SIMBOLOS:
                analizar_sniper(s)
                time.sleep(0.5) # Evita bloqueos de yfinance
        time.sleep(15) # Pausa entre ciclos
else:
    st.error(f"😴 Bot en reposo: {mensaje}")

import streamlit as st
import time
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime
import holidays

# ======================================================
# 1. CONFIGURACIÓN DE CREDENCIALES
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

SIMBOLOS = [
    "EURAUD=X", "EURCAD=X", "EURCHF=X", "GBPAUD=X", "GBPCAD=X",
    "GBPJPY=X", "AUDUSD=X", "AUDCAD=X", "AUDJPY=X", "EURUSD=X",
    "GBPUSD=X", "USDJPY=X", "USDCAD=X", "USDCHF=X", "NZDUSD=X"
]

# Inicializar estados de sesión
if 'cooldown' not in st.session_state: st.session_state.cooldown = {}
if 'ejecutando' not in st.session_state: st.session_state.ejecutando = False

# ======================================================
# 2. MOTOR DE ANÁLISIS TÉCNICO
# ======================================================
def analizar_sniper(s):
    try:
        df = yf.download(s, interval="1m", period="1d", progress=False)
        if df.empty or len(df) < 60: return None

        # Indicadores
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        # Análisis de Muralla (25 toques)
        df_reciente = df.tail(150)
        soporte_h = df_reciente['Low'].min()
        resistencia_h = df_reciente['High'].max()
        
        margen = soporte_h * 0.0003 
        toques = ((df_reciente['Low'] - soporte_h).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = float(v_act['Close'])

        # GATILLO 1: MURALLA (REBOTE)
        distancia_zona = abs(precio - soporte_h) <= (precio * 0.0005)
        if distancia_zona and toques >= 25:
            rsi_val = v_act['RSI']
            veredicto = "🔥 REBOTE PROBABLE" if rsi_val < 42 else "👀 VIGILAR ZONA"
            enviar_alerta(s, precio, toques, f"🧱 MURALLA 25x\n{veredicto}")

        # GATILLO 2: TRAYECTORIA (FIBO 50-70)
        rango = resistencia_h - soporte_h
        fibo_50 = resistencia_h - (0.50 * rango)
        fibo_70 = resistencia_h - (0.70 * rango)
        
        en_fibo = fibo_70 <= precio <= fibo_50
        tendencia_ok = v_act['EMA20'] > v_ant['EMA20']
        cruce_3_9 = v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']

        if tendencia_ok and en_fibo and cruce_3_9:
            enviar_alerta(s, precio, toques, "🚀 IMPULSO TENDENCIAL")
            
        return f"{s}: {precio:.4f} | Toques: {toques}"
    except:
        return None

def enviar_alerta(s, precio, toques, tipo):
    clave = f"{s}_{tipo}"
    ahora = time.time()
    # Cooldown de 10 minutos (600 seg)
    if clave not in st.session_state.cooldown or (ahora - st.session_state.cooldown[clave] > 600):
        msg = (f"🎯 *RAÚL SNIPER V10*\n\n"
               f"💎 *Activo:* {s}\n"
               f"💰 *Precio:* {precio:.5f}\n"
               f"🧱 *Toques:* {toques}\n"
               f"📡 *Alerta:* {tipo}\n"
               f"⏰ *Hora:* {datetime.now().strftime('%H:%M:%S')}")
        try:
            bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
            st.session_state.cooldown[clave] = ahora
        except: pass

# ======================================================
# 3. INTERFAZ STREAMLIT (ESTABILIZADA)
# ======================================================
st.set_page_config(page_title="Raúl Sniper V10", page_icon="🏹")
st.title("🏹 Raúl Sniper Pro V10")

# Contenedores fijos para evitar errores de renderizado
status_ui = st.empty()
log_ui = st.empty()

# Control de ejecución
col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ INICIAR RADAR"):
        st.session_state.ejecutando = True
        bot.send_message(CHAT_ID, "✅ *Radar V10 Online - Sensibilidad 25x*")
with col2:
    if st.button("⏹️ DETENER"):
        st.session_state.ejecutando = False
        st.rerun()

# Bucle principal
if st.session_state.ejecutando:
    status_ui.success(f"📡 Escaneando 15 activos... (Actualizado: {datetime.now().strftime('%H:%M:%S')})")
    
    while st.session_state.ejecutando:
        resúmenes = []
        for s in SIMBOLOS:
            resultado = analizar_sniper(s)
            if resultado:
                resúmenes.append(resultado)
            time.sleep(0.3) # Respetar límites de API
        
        # Actualizar logs en la UI sin crear nuevos nodos
        log_ui.code("\n".join(resúmenes) if resúmenes else "Esperando datos...")
        
        # Pausa entre ciclos de escaneo completo
        time.sleep(10)
else:
    status_ui.info("Sistema en pausa. Presiona 'Iniciar Radar' para comenzar.")

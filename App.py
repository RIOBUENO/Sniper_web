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

# Las 15 divisas de Forex solicitadas
SIMBOLOS = [
    "EURAUD=X", "EURCAD=X", "EURCHF=X", "GBPAUD=X", "GBPCAD=X",
    "GBPJPY=X", "AUDUSD=X", "AUDCAD=X", "AUDJPY=X", "EURUSD=X",
    "GBPUSD=X", "USDJPY=X", "USDCAD=X", "USDCHF=X", "NZDUSD=X"
]

# Diccionario para evitar spam de mensajes (Cooldown de 10 min)
COOLDOWN = {}

# ======================================================
# 2. MOTOR DE ANÁLISIS TÉCNICO (MURALLA Y FIBO)
# ======================================================
def analizar_sniper(s):
    try:
        # Descargamos datos de 1 minuto (pedimos 2 días para asegurar 240 velas)
        df = yf.download(s, interval="1m", period="2d", progress=False)
        if len(df) < 240: return

        # Cálculo de Indicadores
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        # --- ANÁLISIS DE MURALLA (240 VELAS ATRÁS) ---
        df_240 = df.tail(240)
        soporte_h = df_240['Low'].min()
        resistencia_h = df_240['High'].max()
        
        # Filtro de choque: El precio debe estar a menos de 0.02% del soporte
        margen = soporte_h * 0.0002 
        toques = ((df_240['Low'] - soporte_h).abs() <= margen).sum()

        # --- ANÁLISIS TRAYECTORIA (FIBONACCI 50-70%) ---
        rango = resistencia_h - soporte_h
        fibo_50 = resistencia_h - (0.50 * rango)
        fibo_70 = resistencia_h - (0.70 * rango)

        v_act = df.iloc[-1] # Vela actual
        v_ant = df.iloc[-2] # Vela anterior (confirmación de cierre)
        precio = v_act['Close']

        # CONDICIÓN 1: TRAYECTORIA PARA 2 MINUTOS
        # Impulso uniforme, sobre EMA 20 y en zona Fibo
        en_fibo = fibo_70 <= precio <= fibo_50
        tendencia_ok = v_act['EMA20'] > v_ant['EMA20'] and precio > v_act['EMA20']
        cruce_3_9 = v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']

        if tendencia_ok and en_fibo and cruce_3_9:
            lanzar_alerta(s, precio, toques, "🚀 TRAYECTORIA UNIFORME (Gatillo 2 min)")

        # CONDICIÓN 2: ZONA DE COLISIÓN (MURALLA DE 35 TOQUES)
        en_zona_choque = abs(precio - soporte_h) <= (precio * 0.0004)
        
        if en_zona_choque and toques >= 35:
            rsi_val = v_act['RSI']
            # Diagnóstico de la barrera
            if rsi_val > 55:
                veredicto = "🔥 REBOTE CONFIRMADO"
            elif rsi_val < 40:
                veredicto = "⚠️ POSIBLE RUPTURA"
            else:
                veredicto = "⌛ MAMANDO MIEMBRO (Lateralizando)"
            
            lanzar_alerta(s, precio, toques, f"🧱 ZONA DE COLISIÓN\nVeredicto: {veredicto}")

    except Exception as e:
        pass

def lanzar_alerta(s, precio, toques, tipo):
    clave = f"{s}_{tipo}"
    if clave not in COOLDOWN or (time.time() - COOLDOWN[clave] > 600):
        msg = (f"🎯 *RAÚL SNIPER V10*\n\n"
               f"💎 *Activo:* {s}\n"
               f"💰 *Precio:* {precio:.5f}\n"
               f"🧱 *Toques Muralla:* {toques}\n"
               f"📡 *Alerta:* {tipo}\n"
               f"⏰ *Hora:* {datetime.now().strftime('%H:%M:%S')}")
        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
        COOLDOWN[clave] = time.time()

# ======================================================
# 3. INTERFAZ Y CONTROL DE OPERACIÓN
# ======================================================
st.set_page_config(page_title="Raúl Sniper V10", page_icon="🏹")
st.title("🏹 Raúl Sniper Pro V10")
st.write("Estado: **Radar Escaneando...** 📡")

# Filtro de Feriados y Fin de Semana
ahora = datetime.now()
us_hols = holidays.US()

if ahora.weekday() < 5 and ahora not in us_hols:
    st.success("✅ Mercado Forex Abierto - Monitoreando 15 Divisas")
    
    if 'iniciado' not in st.session_state:
        bot.send_message(CHAT_ID, "✅ *Radar V10 Activado*\nMuralla 35x y Fibo 50-70% operativos.")
        st.session_state.iniciado = True

    # Bucle silencioso para evitar errores de redibujado en Streamlit
    while True:
        for s in SIMBOLOS:
            analizar_sniper(s)
            time.sleep(0.5) 
        time.sleep(20)
else:
    st.error(f"😴 Mercado Cerrado o Festivo. El bot no operará hoy.")

import streamlit as st
import time
import yfinance as yf
import pandas_ta as ta
import telebot
import threading
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

# Cooldown global fuera del estado de sesión para hilos
COOLDOWN_GLOBAL = {}

# ======================================================
# 2. MOTOR DE ANÁLISIS (HILO INDEPENDIENTE)
# ======================================================
def motor_sniper():
    """Esta función corre por detrás, no toca la web."""
    while True:
        try:
            for s in SIMBOLOS:
                df = yf.download(s, interval="1m", period="1d", progress=False)
                if df.empty or len(df) < 50: continue

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
                    enviar_alerta_telegram(s, precio, toques, "🧱 MURALLA 25x")

                # Lógica Trayectoria
                rango = resistencia_h - soporte_h
                fibo_50, fibo_70 = resistencia_h - (0.5*rango), resistencia_h - (0.7*rango)
                if (fibo_70 <= precio <= fibo_50) and (v_act['EMA20'] > v_ant['EMA20']):
                    if v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']:
                        enviar_alerta_telegram(s, precio, toques, "🚀 IMPULSO")
                
                time.sleep(1) # Pausa entre activos
            
            time.sleep(20) # Pausa entre ciclos
        except Exception as e:
            time.sleep(10)

def enviar_alerta_telegram(s, precio, toques, tipo):
    clave = f"{s}_{tipo}"
    ahora = time.time()
    if clave not in COOLDOWN_GLOBAL or (ahora - COOLDOWN_GLOBAL[clave] > 600):
        msg = f"🎯 *RAÚL SNIPER*\n💎 *Activo:* {s}\n💰 *Precio:* {precio:.5f}\n🧱 *Toques:* {toques}\n📡 *Alerta:* {tipo}"
        try:
            bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
            COOLDOWN_GLOBAL[clave] = ahora
        except:
            pass

# ======================================================
# 3. INTERFAZ ESTÁTICA (NO SE MUEVE = NO DA ERROR)
# ======================================================
st.set_page_config(page_title="Sniper Engine")
st.title("🏹 Raúl Sniper V10")
st.success("MOTOR INICIADO: Monitoreo activo vía Telegram.")
st.info("Esta página es estática para evitar errores del navegador. No necesitas refrescarla.")

# Lanzar el motor en un hilo si no está corriendo
if "motor_vivo" not in st.session_state:
    t = threading.Thread(target=motor_sniper, daemon=True)
    t.start()
    st.session_state.motor_vivo = True
    try:
        bot.send_message(CHAT_ID, "🚀 *Motor Sniper V10 Iniciado con éxito.*")
    except:
        pass

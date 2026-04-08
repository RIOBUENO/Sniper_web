import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import time
from datetime import datetime

# --- CONFIGURACIÓN DE CREDENCIALES ---
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
SIMBOLOS = [
    "EURAUD=X", "EURCAD=X", "EURCHF=X", "GBPAUD=X", "GBPCAD=X",
    "GBPJPY=X", "AUDUSD=X", "AUDCAD=X", "AUDJPY=X", "EURUSD=X"
]

# --- MOTOR DE CONFLUENCIA (10 PUNTOS) ---
def motor_sniper(symbol):
    try:
        # Descarga de datos
        df_15m = yf.download(symbol, interval="15m", period="5d", progress=False)
        df_1m = yf.download(symbol, interval="1m", period="1d", progress=False)
        
        if df_1m.empty or df_15m.empty: return None

        # Indicadores Técnicos
        rsi = ta.rsi(df_1m['Close'], length=14).iloc[-1]
        
        macd = ta.macd(df_1m['Close'])
        m_line = macd['MACD_12_26_9'].iloc[-1]
        m_sig = macd['MACDs_12_26_9'].iloc[-1]
        
        stoch = ta.stoch(df_1m['High'], df_1m['Low'], df_1m['Close'])
        sk = stoch['STOCHk_14_3_3'].iloc[-1]
        sd = stoch['STOCHd_14_3_3'].iloc[-1]
        
        precio = df_1m['Close'].iloc[-1]
        soporte = df_15m['Low'].tail(50).min()
        resistencia = df_15m['High'].tail(50).max()

        # Sistema de Puntuación
        puntos = 0
        accion = "WAIT"

        # Lógica CALL
        if rsi < 30: puntos += 2
        if m_line > m_sig: puntos += 2
        if sk < 20 and sk > sd: puntos += 3
        if precio <= soporte * 1.0005: puntos += 3
        
        if puntos >= 7: accion = "CALL 🚀"

        # Lógica PUT (Si no hay puntos para CALL)
        if puntos < 5:
            p_put = 0
            if rsi > 70: p_put += 2
            if m_line < m_sig: p_put += 2
            if sk > 80 and sk < sd: p_put += 3
            if precio >= resistencia * 0.9995: p_put += 3
            if p_put >= 7:
                puntos = p_put
                accion = "PUT 🔻"

        # Enviar Telegram si es señal fuerte
        if puntos >= 7:
            msg = f"🎯 *ALERTA SNIPER*\n🔥 Score: {puntos}/10\n💎 Par: {symbol}\n📈 {accion}\n💰 Precio: {precio:.5f}"
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

        return {"par": symbol, "px": precio, "pts": puntos, "dir": accion}
    except:
        return None

# --- INTERFAZ DE SOLO TEXTO (ANTI-COLAPSO) ---
st.set_page_config(page_title="Sniper Pro Text-Only", layout="centered")
st.title("🏹 Sniper Pro+ | Consola de Texto")

# Espacio único que no se rompe
terminal = st.empty()

if st.toggle("🛰️ Iniciar Radar"):
    while True:
        reporte_texto = "### 📡 ESCANEO EN TIEMPO REAL\n"
        reporte_texto += f"Última actualización: {datetime.now().strftime('%H:%M:%S')}\n\n"
        reporte_texto += "| ACTIVO | PRECIO | SCORE | ESTADO |\n"
        reporte_texto += "| :--- | :--- | :--- | :--- |\n"
        
        for s in SIMBOLOS:
            res = motor_sniper(s)
            if res:
                reporte_texto += f"| {res['par']} | {res['px']:.5f} | {res['pts']}/10 | {res['dir']} |\n"
            time.sleep(0.5)

        # Actualizamos usando Markdown puro (Esto NO usa 'removeChild')
        with terminal.container():
            st.markdown(reporte_texto)
            st.info("Sistema operando en modo texto para máxima estabilidad.")
        
        time.sleep(60)

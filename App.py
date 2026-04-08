import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import time
import requests

# --- CONFIGURACIÓN TELEGRAM ---
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442" 

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensaje}&parse_mode=Markdown"
    try: requests.get(url)
    except: pass

st.set_page_config(page_title="Raúl Sniper Pro: Fibonacci Edition", layout="wide")

# --- SEGURIDAD ---
password = st.sidebar.text_input("Contraseña", type="password")
if password != "raul123":
    st.error("Introduce la clave, Raúl.")
    st.stop()

SIMBOLOS = ["SOL-USD", "PEPE-USD", "BTC-USD", "AUDUSD=X", "EURUSD=X", "GBPUSD=X", "GBPJPY=X"]
MIN_TOUCHES = 35 

if 'ultima_alerta' not in st.session_state:
    st.session_state.ultima_alerta = {}

def calcular_fibo_y_emas(df):
    # EMAs 3 y 9
    df['EMA3'] = df['Close'].ewm(span=3, adjust=False).mean()
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    
    # Cálculo de Fibonacci en el último Swing (20 velas)
    recent_high = df['High'].tail(20).max()
    recent_low = df['Low'].tail(20).min()
    diff = recent_high - recent_low
    level_618 = recent_high - (0.618 * diff) # Para compras
    level_618_v = recent_low + (0.618 * diff) # Para ventas
    
    return df, level_618, level_618_v, recent_high, recent_low

def analizar_elite(s):
    df_hist = yf.download(s, interval="15m", period="5d", progress=False)
    df_velas = yf.download(s, interval="1m", period="1h", progress=False)
    
    if len(df_velas) < 25: return None

    df_velas, fibo_buy, fibo_sell, r_high, r_low = calcular_fibo_y_emas(df_velas)
    
    v_actual = df_velas.iloc[-1]
    v_previa = df_velas.iloc[-2]
    precio = float(v_actual['Close'])
    
    # Buscador de Murallas (Igual que antes)
    highs, lows = df_hist['High'], df_hist['Low']
    precios_totales = pd.concat([highs, lows])
    umbral = precio * 0.0003
    best_p, max_t = 0, 0
    for p in precios_totales.unique()[:70]: 
        touches = ((highs >= p - umbral) & (lows <= p + umbral)).sum()
        if touches > max_t: max_t, best_p = touches, p
            
    dist_muralla = abs(precio - best_p)
    dist_pct = (dist_muralla / best_p) * 100
    
    confirmacion = None

    # --- LÓGICA DE GATILLO: EMA 3/9 + FIBO 61.8% ---
    # CASO COMPRA: Cruce alcista cerca del 61.8% Fibo y yendo hacia muralla arriba
    if best_p > precio:
        if v_actual['EMA3'] > v_actual['EMA9'] and v_previa['EMA3'] <= v_previa['EMA9']: # Cruce Alza
            if abs(precio - fibo_buy) / fibo_buy < 0.001: # Cerca del 61.8%
                confirmacion = "🚀 COMPRA (CALL) - CRUCE EMA + FIBO 61.8%"

    # CASO VENTA: Cruce bajista cerca del 61.8% Fibo y yendo hacia muralla abajo
    elif best_p < precio:
        if v_actual['EMA3'] < v_actual['EMA9'] and v_previa['EMA3'] >= v_previa['EMA9']: # Cruce Baja
            if abs(precio - fibo_sell) / fibo_sell < 0.001: # Cerca del 61.8%
                confirmacion = "📉 VENTA (PUT) - CRUCE EMA + FIBO 61.8%"

    return {
        "Par": s, "Precio": precio, "Muralla": best_p, 
        "Toques": max_t, "Confirmacion": confirmacion, "Dist": dist_pct
    }

placeholder = st.empty()
while True:
    with placeholder.container():
        st.write(f"⌛ Sniper Pro (EMA 3/9 + FIBO) activo: {datetime.datetime.now().strftime('%H:%M:%S')}")
        for s in SIMBOLOS:
            try:
                res = analizar_elite(s)
                if res and res['Confirmacion'] and res['Toques'] >= MIN_TOUCHES:
                    ahora = datetime.datetime.now()
                    if s not in st.session_state.ultima_alerta or (ahora - st.session_state.ultima_alerta[s]).seconds > 300:
                        msg = (f"🎯 *SNIPER ELITE: {s}*\n\n"
                               f"🔥 *GATILLO:* {res['Confirmacion']}\n"
                               f"💰 Precio: `{res['Precio']:.5f}`\n"
                               f"🏁 Objetivo Muralla: `{res['Muralla']:.5f}`\n"
                               f"Fuerza Muralla: {res['Toques']} toques.\n\n"
                               f"¡El retroceso terminó, métele al impulso!")
                        enviar_telegram(msg)
                        st.session_state.ultima_alerta[s] = ahora
            except: continue
    time.sleep(15)

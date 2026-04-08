import streamlit as st
import yfinance as yf
import pandas as pd
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

# --- REPORTE DE MERCADO (CADA 3 HORAS) ---
def generar_reporte_inteligencia(simbolos):
    reporte = "📊 *REPORTE DE ESTADO (3h)*\n"
    reporte += "----------------------------------\n"
    for s in simbolos:
        try:
            df = yf.download(s, period="1d", interval="5m", progress=False).tail(36)
            if df.empty: continue
            var = ((df.iloc[-1]['Close'] - df.iloc[0]['Close']) / df.iloc[0]['Close']) * 100
            vol = df['Close'].std() / df['Close'].mean() * 100
            
            if abs(var) < 0.05 or vol < 0.03: est = "💤 LATERAL"
            elif var > 0: est = "🚀 ALCISTA"
            else: est = "📉 BAJISTA"
            
            reporte += f"*{s}*: {est} | Var: {var:.2f}%\n"
        except: continue
    reporte += "\n🎯 _Rastreando murallas (+35 toques)..._"
    enviar_telegram(reporte)

st.set_page_config(page_title="Raúl Sniper Elite V5.1", layout="wide")

# --- LÓGICA DE ANÁLISIS ---
def analizar_movimiento(s):
    df_h = yf.download(s, interval="15m", period="5d", progress=False)
    df_v = yf.download(s, interval="1m", period="1h", progress=False)
    if len(df_v) < 20: return None

    # Indicadores para Trayecto
    df_v['E3'] = df_v['Close'].ewm(span=3, adjust=False).mean()
    df_v['E9'] = df_v['Close'].ewm(span=9, adjust=False).mean()
    
    # Rango OTE (Fibonacci)
    h_20, l_20 = df_v['High'].tail(20).max(), df_v['Low'].tail(20).min()
    diff = h_20 - l_20
    f50, f78 = h_20 - (0.50 * diff), h_20 - (0.78 * diff)

    v_act = df_v.iloc[-1]
    v_ant = df_v.iloc[-2]
    precio = float(v_act['Close'])
    
    # Análisis de Vela (Seguridad)
    tamanio = v_act['High'] - v_act['Low']
    cuerpo = abs(precio - v_act['Open'])
    
    # Buscador de Murallas (Mínimo 35, sin techo)
    precios_m = pd.concat([df_h['High'], df_h['Low']])
    u = precio * 0.0003
    max_t, best_p = 0, 0
    for p in precios_m.unique()[:80]:
        touches = ((df_h['High'] >= p - u) & (df_h['Low'] <= p + u)).sum()
        if touches > max_t: max_t, best_p = touches, p

    if max_t < 35: return None # Filtro base de 35 toques

    dist = (abs(precio - best_p) / best_p) * 100

    # --- 1. ZONA DE GUERRA (AQUÍ NO HAY EMAS) ---
    if dist <= 0.018:
        # REBOTE: Necesita mecha de rechazo > 30% de la vela
        if precio < best_p and (v_act['High'] - v_act['Open']) > (tamanio * 0.3):
            return {"a": "📉 REBOTE SEGURO (VENTA)", "p": precio, "m": best_p, "t": max_t}
        elif precio > best_p and (v_act['Open'] - v_act['Low']) > (tamanio * 0.3):
            return {"a": "🚀 REBOTE SEGURO (COMPRA)", "p": precio, "m": best_p, "t": max_t}
        
        # ROMPIMIENTO: Vela elefante (cuerpo > 70% de la vela)
        if cuerpo > (tamanio * 0.7):
            if precio > best_p + u: return {"a": "🧨 ROMPIMIENTO (CALL)", "p": precio, "m": best_p, "t": max_t}
            elif precio < best_p - u: return {"a": "🧨 ROMPIMIENTO (PUT)", "p": precio, "m": best_p, "t": max_t}

    # --- 2. TRAYECTO (CON EMAS Y FIBO) ---
    if 0.02 < dist <= 0.08:
        if f78 <= precio <= f50 and v_act['E3'] > v_act['E9'] and v_ant['E3'] <= v_ant['E9'] and best_p > precio:
            return {"a": "📡 TRAYECTO (Hacia Muralla)", "p": precio, "m": best_p, "t": max_t}

    return None

# --- EJECUCIÓN ---
SIMBOLOS = ["SOL-USD", "PEPE-USD", "BTC-USD", "AUDUSD=X", "EURUSD=X", "GBPUSD=X", "GBPJPY=X"]
if 'alertas' not in st.session_state: st.session_state.alertas = {}
if 'ultima_h' not in st.session_state: 
    st.session_state.ultima_h = 0

while True:
    # Reporte cada 3h
    if time.time() - st.session_state.ultima_h > 10800:
        generar_reporte_inteligencia(SIMBOLOS)
        st.session_state.ultima_h = time.time()

    for s in SIMBOLOS:
        res = analizar_movimiento(s)
        if res:
            key = f"{s}_{res['a']}"
            if key not in st.session_state.alertas or time.time() - st.session_state.alertas[key] > 300:
                msg = f"🛡️ *SNIPER {s}*\n\nAcción: {res['a']}\nPrecio: `{res['p']:.5f}`\n🔥 Muralla: `{res['m']:.5f}` (*{res['t']}* toques)"
                enviar_telegram(msg)
                st.session_state.alertas[key] = time.time()
    time.sleep(15)

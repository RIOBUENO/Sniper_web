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

st.set_page_config(page_title="Raúl Sniper Multi-Radar V6", layout="wide")

def analizar_todo(s):
    df_h = yf.download(s, interval="15m", period="5d", progress=False)
    df_v = yf.download(s, interval="1m", period="1h", progress=False)
    if len(df_v) < 25: return None

    # Indicadores
    df_v['E3'] = df_v['Close'].ewm(span=3, adjust=False).mean()
    df_v['E9'] = df_v['Close'].ewm(span=9, adjust=False).mean()
    
    # Fibonacci para Impulso
    h_20, l_20 = df_v['High'].tail(20).max(), df_v['Low'].tail(20).min()
    diff = h_20 - l_20
    f50, f78 = h_20 - (0.50 * diff), h_20 - (0.78 * diff) # Compras
    f50v, f78v = l_20 + (0.50 * diff), l_20 + (0.78 * diff) # Ventas

    v_act, v_ant = df_v.iloc[-1], df_v.iloc[-2]
    precio = float(v_act['Close'])
    
    # --- RADAR 1: MURALLAS (+35 TOQUES) ---
    precios_m = pd.concat([df_h['High'], df_h['Low']])
    u = precio * 0.0003
    max_t, best_p = 0, 0
    for p in precios_m.unique()[:80]:
        touches = ((df_h['High'] >= p - u) & (df_h['Low'] <= p + u)).sum()
        if touches > max_t: max_t, best_p = touches, p

    dist = (abs(precio - best_p) / best_p) * 100

    # Lógica de Zona de Guerra (Muralla)
    if dist <= 0.018 and max_t >= 35:
        tamanio = v_act['High'] - v_act['Low']
        if precio < best_p and (v_act['High'] - v_act['Open']) > (tamanio * 0.3):
            return {"tipo": "🛡️ MURALLA", "a": "📉 REBOTE VENTA", "p": precio, "m": best_p, "to": max_t}
        elif precio > best_p and (v_act['Open'] - v_act['Low']) > (tamanio * 0.3):
            return {"tipo": "🛡️ MURALLA", "a": "🚀 REBOTE COMPRA", "p": precio, "m": best_p, "to": max_t}

    # --- RADAR 2: IMPULSO SEGURO (TENDENCIA UNIFORME) ---
    # Confirmamos tendencia alcista (HH/HL) en las últimas 10 velas
    tendencia_alcista = df_v['Low'].tail(10).is_monotonic_increasing
    tendencia_bajista = df_v['High'].tail(10).is_monotonic_decreasing

    # Caso Compra tras retroceso
    if tendencia_alcista and f78 <= precio <= f50:
        if v_act['E3'] > v_act['E9'] and v_ant['E3'] <= v_ant['E9']:
            return {"tipo": "🚀 IMPULSO", "a": "COMPRA (Post-Retroceso)", "p": precio, "m": h_20, "to": "FIBO 61.8"}

    # Caso Venta tras retroceso
    if tendencia_bajista and f50v <= precio <= f78v:
        if v_act['E3'] < v_act['E9'] and v_ant['E3'] >= v_ant['E9']:
            return {"tipo": "📉 IMPULSO", "a": "VENTA (Post-Retroceso)", "p": precio, "m": l_20, "to": "FIBO 61.8"}

    return None

# --- EJECUCIÓN CONTINUA ---
SIMBOLOS = ["SOL-USD", "PEPE-USD", "BTC-USD", "AUDUSD=X", "EURUSD=X", "GBPUSD=X", "GBPJPY=X"]
if 'alertas' not in st.session_state: st.session_state.alertas = {}

while True:
    for s in SIMBOLOS:
        res = analizar_todo(s)
        if res:
            key = f"{s}_{res['tipo']}_{res['a']}"
            if key not in st.session_state.alertas or time.time() - st.session_state.alertas[key] > 400:
                msg = f"{res['tipo']} EN *{s}*\n\n"
                msg += f"Acción: {res['a']}\n"
                msg += f"Precio: `{res['p']:.5f}`\n"
                msg += f"Referencia: `{res['m']:.5f}` ({res['to']})"
                enviar_telegram(msg)
                st.session_state.alertas[key] = time.time()
    time.sleep(15)

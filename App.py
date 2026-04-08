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

# --- REPORTE CADA 3 HORAS ---
def generar_reporte_3h(simbolos):
    reporte = "📊 *ESTATUS DE MERCADO (3h)*\n"
    reporte += "----------------------------------\n"
    for s in simbolos:
        try:
            df = yf.download(s, period="1d", interval="5m", progress=False).tail(36)
            if df.empty: continue
            var = ((df.iloc[-1]['Close'] - df.iloc[0]['Close']) / df.iloc[0]['Close']) * 100
            reporte += f"*{s}*: {'🚀' if var > 0 else '📉'} {var:.2f}%\n"
        except: continue
    enviar_telegram(reporte)

st.set_page_config(page_title="Raúl Sniper Multi-Radar V7", layout="wide")

# --- MOTOR DE ANÁLISIS INDESTRUCTIBLE ---
def procesar_activo(s):
    try:
        # Descarga de data con paracaídas
        df_h = yf.download(s, interval="15m", period="5d", progress=False)
        df_v = yf.download(s, interval="1m", period="1h", progress=False)

        if df_v.empty or len(df_v) < 25: return None
        
        v_act = df_v.iloc[-1]
        v_ant = df_v.iloc[-2]
        
        # Filtro: Si el precio no se mueve (Mercado Cerrado), ignorar
        if v_act['High'] == v_act['Low'] == v_act['Open'] == v_act['Close']:
            return None

        precio = float(v_act['Close'])
        tamanio = v_act['High'] - v_act['Low']
        cuerpo = abs(precio - v_act['Open'])

        # --- SEÑAL TIPO 1: MURALLAS (RESISTENCIA/SOPORTE) ---
        precios_m = pd.concat([df_h['High'], df_h['Low']])
        u = precio * 0.0003
        max_t, best_p = 0, 0
        for p in precios_m.unique()[:80]:
            touches = ((df_h['High'] >= p - u) & (df_h['Low'] <= p + u)).sum()
            if touches > max_t: max_t, best_p = touches, p

        dist = (abs(precio - best_p) / best_p) * 100

        if max_t >= 35 and dist <= 0.018:
            # Lógica de rechazo seguro en zona de guerra
            if precio < best_p and (v_act['High'] - v_act['Open']) > (tamanio * 0.3):
                enviar_señal(s, "🛡️ MURALLA", "📉 REBOTE VENTA", precio, best_p, max_t)
            elif precio > best_p and (v_act['Open'] - v_act['Low']) > (tamanio * 0.3):
                enviar_señal(s, "🛡️ MURALLA", "🚀 REBOTE COMPRA", precio, best_p, max_t)
            elif cuerpo > (tamanio * 0.7):
                accion = "🧨 ROMPIMIENTO (CALL)" if precio > best_p else "🧨 ROMPIMIENTO (PUT)"
                enviar_señal(s, "🛡️ MURALLA", accion, precio, best_p, max_t)

        # --- SEÑAL TIPO 2: IMPULSO SEGURO (TENDENCIA) ---
        df_v['E3'] = df_v['Close'].ewm(span=3, adjust=False).mean()
        df_v['E9'] = df_v['Close'].ewm(span=9, adjust=False).mean()
        
        h_20, l_20 = df_v['High'].tail(20).max(), df_v['Low'].tail(20).min()
        diff = h_20 - l_20
        f50, f78 = h_20 - (0.50 * diff), h_20 - (0.78 * diff) # Compras
        f50v, f78v = l_20 + (0.50 * diff), l_20 + (0.78 * diff) # Ventas

        t_alcista = df_v['Low'].tail(10).is_monotonic_increasing
        t_bajista = df_v['High'].tail(10).is_monotonic_decreasing

        # Filtro de cierre de vela para EMAs
        if t_alcista and f78 <= precio <= f50:
            if v_act['E3'] > v_act['E9'] and v_ant['E3'] <= v_ant['E9']:
                enviar_señal(s, "🚀 IMPULSO", "COMPRA POST-RETROCESO", precio, h_20, "FIBO OTE")
        
        elif t_bajista and f50v <= precio <= f78v:
            if v_act['E3'] < v_act['E9'] and v_ant['E3'] >= v_ant['E9']:
                enviar_señal(s, "📉 IMPULSO", "VENTA POST-RETROCESO", precio, l_20, "FIBO OTE")

    except:
        pass # Ignora errores de conexión o datos nulos silenciosamente

def enviar_señal(simbolo, tipo, accion, precio, ref, info):
    key = f"{simbolo}_{tipo}_{accion}"
    ahora = time.time()
    if key not in st.session_state.alertas or ahora - st.session_state.alertas[key] > 420:
        msg = f"{tipo}: *{simbolo}*\n"
        msg += f"🔥 Acción: *{accion}*\n"
        msg += f"💰 Precio: `{precio:.5f}`\n"
        msg += f"📍 Ref: `{ref:.5f}` ({info})"
        enviar_telegram(msg)
        st.session_state.alertas[key] = ahora

# --- LOOP DE EJECUCIÓN ---
SIMBOLOS = ["SOL-USD", "PEPE-USD", "BTC-USD", "AUDUSD=X", "EURUSD=X", "GBPUSD=X", "GBPJPY=X"]
if 'alertas' not in st.session_state: st.session_state.alertas = {}
if 'ultima_h' not in st.session_state: st.session_state.ultima_h = 0

st.write("🕵️ Sniper Multi-Radar (Sin Errores) en ejecución...")

while True:
    # Reporte de 3 horas
    if time.time() - st.session_state.ultima_h > 10800:
        generar_reporte_3h(SIMBOLOS)
        st.session_state.ultima_h = time.time()

    for s in SIMBOLOS:
        procesar_activo(s)
    
    time.sleep(15)

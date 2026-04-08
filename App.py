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

# --- REPORTE DE ESTADO (CADA 3 HORAS) ---
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

st.set_page_config(page_title="Raúl Sniper Copiloto V8", layout="wide")

# --- FUNCIÓN DE SEÑALIZACIÓN ---
def enviar_señal(simbolo, tipo, accion, precio, ref, info, cooldown=420):
    key = f"{simbolo}_{tipo}_{accion}"
    ahora = time.time()
    if key not in st.session_state.alertas or ahora - st.session_state.alertas[key] > cooldown:
        msg = f"{tipo}: *{simbolo}*\n"
        msg += f"🔥 Acción: *{accion}*\n"
        msg += f"💰 Precio: `{precio:.5f}`\n"
        msg += f"📍 Ref: `{ref:.5f}` ({info})"
        enviar_telegram(msg)
        st.session_state.alertas[key] = ahora

# --- MOTOR DE ANÁLISIS ---
def procesar_sniper_v8(s):
    try:
        df_h = yf.download(s, interval="15m", period="5d", progress=False)
        df_v = yf.download(s, interval="1m", period="1h", progress=False)

        if df_v.empty or len(df_v) < 25: return
        
        v_act = df_v.iloc[-1]
        v_ant = df_v.iloc[-2]
        
        # Filtro Mercado Cerrado
        if v_act['High'] == v_act['Low']: return

        precio = float(v_act['Close'])
        tamanio = v_act['High'] - v_act['Low']
        cuerpo = abs(precio - v_act['Open'])

        # --- LÓGICA DE MURALLAS ---
        precios_m = pd.concat([df_h['High'], df_h['Low']])
        u = precio * 0.0003
        max_t, best_p = 0, 0
        for p in precios_m.unique()[:80]:
            touches = ((df_h['High'] >= p - u) & (df_h['Low'] <= p + u)).sum()
            if touches > max_t: max_t, best_p = touches, p

        dist = (abs(precio - best_p) / best_p) * 100

        # 1. PRE-ALERTA ZONA DE CHOQUE
        if 0.03 < dist <= 0.07 and max_t >= 35:
            enviar_señal(s, "👀 AVISO", "Acercándose a Zona de Choque", precio, best_p, f"Muralla {max_t} toques", cooldown=900)

        # 2. GATILLO MURALLA (ZONA DE GUERRA)
        if dist <= 0.018 and max_t >= 35:
            if precio < best_p and (v_act['High'] - v_act['Open']) > (tamanio * 0.3):
                enviar_señal(s, "🛡️ MURALLA", "📉 REBOTE VENTA", precio, best_p, f"{max_t} toques")
            elif precio > best_p and (v_act['Open'] - v_act['Low']) > (tamanio * 0.3):
                enviar_señal(s, "🛡️ MURALLA", "🚀 REBOTE COMPRA", precio, best_p, f"{max_t} toques")
            elif cuerpo > (tamanio * 0.7):
                acc = "🧨 ROMPIMIENTO (CALL)" if precio > best_p else "🧨 ROMPIMIENTO (PUT)"
                enviar_señal(s, "🛡️ MURALLA", acc, precio, best_p, f"{max_t} toques")

        # --- LÓGICA DE IMPULSO ---
        df_v['E3'] = df_v['Close'].ewm(span=3, adjust=False).mean()
        df_v['E9'] = df_v['Close'].ewm(span=9, adjust=False).mean()
        
        h_20, l_20 = df_v['High'].tail(20).max(), df_v['Low'].tail(20).min()
        diff = h_20 - l_20
        f50, f78 = h_20 - (0.50 * diff), h_20 - (0.78 * diff)
        f50v, f78v = l_20 + (0.50 * diff), l_20 + (0.78 * diff)

        t_alcista = df_v['Low'].tail(8).is_monotonic_increasing
        t_bajista = df_v['High'].tail(8).is_monotonic_decreasing

        # 3. PRE-ALERTA TENDENCIA
        if (t_alcista or t_bajista) and 0.08 < dist:
            enviar_señal(s, "📈 AVISO", "Tendencia en formación", precio, 0, "Atento a Impulso", cooldown=1200)

        # 4. GATILLO IMPULSO OTE (CIERRE EMA 3/9)
        if t_alcista and f78 <= precio <= f50:
            if v_act['E3'] > v_act['E9'] and v_ant['E3'] <= v_ant['E9']:
                enviar_señal(s, "🚀 IMPULSO", "COMPRA (1-2 min)", precio, h_20, "FIBO OTE")
        elif t_bajista and f50v <= precio <= f78v:
            if v_act['E3'] < v_act['E9'] and v_ant['E3'] >= v_ant['E9']:
                enviar_señal(s, "📉 IMPULSO", "VENTA (1-2 min)", precio, l_20, "FIBO OTE")

    except: pass

# --- LOOP PRINCIPAL ---
SIMBOLOS = ["SOL-USD", "PEPE-USD", "BTC-USD", "AUDUSD=X", "EURUSD=X", "GBPUSD=X", "GBPJPY=X"]
if 'alertas' not in st.session_state: st.session_state.alertas = {}
if 'ultima_h' not in st.session_state: st.session_state.ultima_h = 0

st.title("Raúl Sniper Copiloto V8")
st.write("🕵️ Radar de Murallas e Impulsos activo...")

while True:
    if time.time() - st.session_state.ultima_h > 10800:
        generar_reporte_3h(SIMBOLOS)
        st.session_state.ultima_h = time.time()

    for s in SIMBOLOS:
        procesar_sniper_v8(s)
    
    time.sleep(15)

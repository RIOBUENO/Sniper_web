import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import time
import requests

# --- CONFIGURACIÓN TELEGRAM ---
# Ya te puse tu token aquí abajo
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
# REEMPLAZA EL NÚMERO DE ABAJO POR TU CHAT ID (Sácalo de @userinfobot)
CHAT_ID = "TU_CHAT_ID_AQUI" 

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensaje}"
    try:
        requests.get(url)
    except:
        pass

st.set_page_config(page_title="Raúl Sniper Elite V3", layout="wide")

st.markdown("""
    <style>
    .gatillo-fuego { padding: 30px; border-radius: 15px; background-color: #00ff00; color: black; font-weight: bold; text-align: center; border: 4px solid #fff; animation: blinker 0.8s linear infinite; }
    @keyframes blinker { 50% { opacity: 0.2; } }
    .stInfo { background-color: #1e1e1e; color: #00ff00; border: 1px solid #00ff00; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Sniper Intelligence: Confirmación + Telegram")

# --- SEGURIDAD ---
password = st.sidebar.text_input("Contraseña", type="password")
if password != "raul123":
    st.error("Introduce la clave, menor.")
    st.stop()

# Lista de activos para Scalping
SIMBOLOS = ["SOL-USD", "PEPE-USD", "BTC-USD", "AUDUSD=X", "EURUSD=X", "GBPUSD=X", "GBPJPY=X"]
MIN_TOUCHES = 35 

# Memoria para no repetir mensajes de la misma señal
if 'ultima_alerta' not in st.session_state:
    st.session_state.ultima_alerta = {}

def analizar_precision(s):
    df_hist = yf.download(s, interval="15m", period="5d", progress=False)
    df_velas = yf.download(s, interval="1m", period="1h", progress=False)
    
    if df_velas.empty or len(df_velas) < 2:
        return None

    v_actual = df_velas.iloc[-1]
    v_previa = df_velas.iloc[-2]
    precio_actual = float(v_actual['Close'])
    
    highs = df_hist['High']
    lows = df_hist['Low']
    precios = pd.concat([highs, lows])
    umbral = precio_actual * 0.0003
    best_p = 0
    max_t = 0
    
    for p in precios.unique()[:70]: 
        touches = ((highs >= p - umbral) & (lows <= p + umbral)).sum()
        if touches > max_t:
            max_t = touches
            best_p = p
            
    distancia = abs(precio_actual - best_p)
    dist_pct = (distancia / best_p) * 100
    confirmacion = None
    
    # Solo dispara si la vela actual confirma la dirección después de limpiar zona
    if dist_pct < 0.02:
        # VENTA
        if v_actual['Close'] < v_actual['Open'] and v_actual['Close'] < v_previa['Close']:
            if precio_actual < best_p:
                confirmacion = "📉 VENTA (PUT) - FUERZA CONFIRMADA"
        # COMPRA
        elif v_actual['Close'] > v_actual['Open'] and v_actual['Close'] > v_previa['Close']:
            if precio_actual > best_p:
                confirmacion = "🚀 COMPRA (CALL) - FUERZA CONFIRMADA"
            
    return {
        "Par": s, "Precio": precio_actual, "Muralla": best_p, 
        "Toques": max_t, "Confirmacion": confirmacion
    }

placeholder = st.empty()

while True:
    with placeholder.container():
        st.write(f"⌛ Analizando mercado y enviando a Telegram: {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        c1, c2 = st.columns([2, 1])
        
        resultados = []
        for s in SIMBOLOS:
            try:
                res = analizar_precision(s)
                if res and res['Toques'] >= MIN_TOUCHES:
                    resultados.append(res)
            except: continue

        with c2:
            st.subheader("📡 Radar")
            for r in resultados:
                st.write(f"**{r['Par']}**: {r['Precio']:.5f} (M: {r['Toques']}T)")

        with c1:
            st.subheader("🔥 GATILLO DE OPERACIÓN")
            for d in resultados:
                if d['Confirmacion']:
                    ahora = datetime.datetime.now()
                    # Filtro para que no te mande el mismo mensaje cada 15 segundos
                    if d['Par'] not in st.session_state.ultima_alerta or (ahora - st.session_state.ultima_alerta[d['Par']]).seconds > 300:
                        msg = f"🎯 SNIPER ALERT!\nPar: {d['Par']}\nAcción: {d['Confirmacion']}\nPrecio: {d['Precio']}\n¡MÉTELA YA (1-2 MIN)!"
                        enviar_telegram(msg)
                        st.session_state.ultima_alerta[d['Par']] = ahora

                    st.markdown(f"""
                    <div class="gatillo-fuego">
                        <h1>¡{d['Confirmacion']}!</h1>
                        <h2>{d['Par']} @ {d['Precio']:.6f}</h2>
                    </div>
                    """, unsafe_allow_html=True)
            
            if not any(r['Confirmacion'] for r in resultados):
                st.info("Esperando que el precio limpie zona y confirme fuerza...")

    time.sleep(15)

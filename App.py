import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import time

st.set_page_config(page_title="Raúl Sniper Pro", layout="wide")

# --- ESTILO ---
st.markdown("""
    <style>
    .stProgress > div > div > div > div { background-color: #2ecc71; }
    .status-box { padding: 10px; border-radius: 5px; border: 1px solid #444; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Sniper Intelligence: Radar de Liquidez")

# --- SEGURIDAD ---
password = st.sidebar.text_input("Contraseña", type="password")
if password != "raul123":
    st.error("Introduce la clave, menor.")
    st.stop()

# --- CONFIGURACIÓN ---
SIMBOLOS = ["SOL-USD", "BTC-USD", "ETH-USD", "AUDCAD=X", "AUDJPY=X", "AUDUSD=X", "EURAUD=X", "GBPUSD=X", "GBPJPY=X"]
MIN_TOUCHES = 20 # Filtro de muralla

def analizar_par(s):
    df_15m = yf.download(s, interval="15m", period="5d", progress=False)
    df_1m = yf.download(s, interval="1m", period="1d", progress=False)
    
    actual = df_1m['Close'].iloc[-1]
    highs = df_15m['High']
    lows = df_15m['Low']
    
    # Lógica de Muralla
    precios = pd.concat([highs, lows])
    umbral = actual * 0.0005
    best_p = 0
    max_t = 0
    
    for p in precios.unique()[:50]: # Analizar niveles clave
        touches = ((highs >= p - umbral) & (lows <= p + umbral)).sum()
        if touches > max_t:
            max_t = touches
            best_p = p
            
    distancia = abs(actual - best_p)
    dist_pct = (distancia / best_p) * 100
    
    # Barra de Confianza (0 a 100)
    confianza = max(0, min(100, 100 - (dist_pct * 1000))) 
    
    estado = "Buscando Inercia"
    if dist_pct < 0.02:
        estado = "🔥 ZONA DE IMÁN (Barrido de Liquidez)"
    elif dist_pct < 0.1:
        estado = "⚡ Cerca del Objetivo"
        
    return {
        "Par": s, "Precio": actual, "Muralla": best_p, 
        "Toques": max_t, "Confianza": confianza, "Estado": estado,
        "Dist": dist_pct
    }

placeholder = st.empty()

while True:
    with placeholder.container():
        st.write(f"Refresco: {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        resultados = []
        for s in SIMBOLOS:
            try:
                res = analizar_par(s)
                resultados.append(res)
            except: continue
        
        # --- TABLA PRINCIPAL ---
        df_res = pd.DataFrame(resultados)
        
        cols = st.columns(3)
        for i, r in enumerate(resultados):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"### {r['Par']}")
                    st.metric("Precio Actual", f"{r['Precio']:.5f}")
                    st.write(f"**Estado:** {r['Estado']}")
                    st.progress(int(r['Confianza'])/100)
                    st.write(f"Distancia a Muralla: {r['Dist']:.4f}%")
                    st.divider()

        # --- SECCIÓN DE SEÑALES CRÍTICAS ---
        st.subheader("🚨 Señales en Tiempo Real (Fuego)")
        alertas = [r for r in resultados if r['Confianza'] > 80]
        if alertas:
            for a in alertas:
                st.warning(f"**{a['Par']}** está en la zona de toque ({a['Muralla']:.5f}). El precio está pendejeando ahí. ¡Atento al barrido!")
        else:
            st.info("No hay señales calientes todavía. El radar sigue escaneando...")
            
    time.sleep(30)

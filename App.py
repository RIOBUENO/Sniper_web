import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import time

st.set_page_config(page_title="Raúl Sniper Elite V3", layout="wide")

st.markdown("""
    <style>
    .gatillo-fuego { padding: 30px; border-radius: 15px; background-color: #00ff00; color: black; font-weight: bold; text-align: center; border: 4px solid #fff; animation: blinker 0.8s linear infinite; }
    @keyframes blinker { 50% { opacity: 0.2; } }
    .stInfo { background-color: #1e1e1e; color: #00ff00; border: 1px solid #00ff00; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Sniper Intelligence: Confirmación de Fuerza")

# --- SEGURIDAD ---
password = st.sidebar.text_input("Contraseña", type="password")
if password != "raul123":
    st.error("Introduce la clave, menor.")
    st.stop()

SIMBOLOS = ["SOL-USD", "PEPE-USD", "BTC-USD", "AUDUSD=X", "EURUSD=X", "GBPUSD=X", "GBPJPY=X"]
MIN_TOUCHES = 35 

def analizar_precision(s):
    # Traemos data de 1 minuto para ver el movimiento de las velas
    df_hist = yf.download(s, interval="15m", period="5d", progress=False)
    df_velas = yf.download(s, interval="1m", period="1h", progress=False)
    
    # Datos de las últimas dos velas cerradas
    v_actual = df_velas.iloc[-1]
    v_previa = df_velas.iloc[-2]
    precio_actual = v_actual['Close']
    
    # Buscador de Murallas (Igual a como lo teníamos)
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
    
    # --- LÓGICA DE GATILLO QUIRÚRGICO ---
    # 1. El precio debe haber estado o estar muy cerca de la muralla (Zona de Imán)
    if dist_pct < 0.02:
        # 2. CASO VENTA (PUT): El precio besó arriba y la vela actual cierra roja con fuerza
        # Verificamos que el cierre actual sea menor al de la vela anterior (Fuerza bajista)
        if v_actual['Close'] < v_actual['Open'] and v_actual['Close'] < v_previa['Close']:
            if precio_actual < best_p: # Ya empezó a bajar de la muralla
                confirmacion = "📉 VENTA (PUT) - FUERZA CONFIRMADA"
        
        # 3. CASO COMPRA (CALL): El precio besó abajo y la vela actual cierra verde con fuerza
        elif v_actual['Close'] > v_actual['Open'] and v_actual['Close'] > v_previa['Close']:
            if precio_actual > best_p: # Ya empezó a subir de la muralla
                confirmacion = "🚀 COMPRA (CALL) - FUERZA CONFIRMADA"
            
    return {
        "Par": s, "Precio": precio_actual, "Muralla": best_p, 
        "Toques": max_t, "Confirmacion": confirmacion, "Dist": dist_pct
    }

placeholder = st.empty()

while True:
    with placeholder.container():
        st.write(f"⌛ Analizando velas de 1min: {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        c1, c2 = st.columns([2, 1])
        
        resultados = []
        for s in SIMBOLOS:
            try:
                res = analizar_precision(s)
                if res['Toques'] >= MIN_TOUCHES:
                    resultados.append(res)
            except: continue

        with col2: # Panel de monitoreo
            st.subheader("📡 Radar")
            for r in resultados:
                st.write(f"**{r['Par']}**: {r['Precio']:.5f} (M: {r['Toques']}T)")

        with col1: # Señales de ejecución
            st.subheader("🔥 GATILLO DE OPERACIÓN")
            disparos = [r for r in resultados if r['Confirmacion'] is not None]
            
            if disparos:
                for d in disparos:
                    st.markdown(f"""
                    <div class="gatillo-fuego">
                        <h1>¡{d['Confirmacion']}!</h1>
                        <h2>{d['Par']} @ {d['Precio']:.6f}</h2>
                        <p>LA LIMPIEZA TERMINÓ - ENTRA AHORA (1-2 MIN)</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Precio en zona de conflicto. Esperando confirmación de la vela de fuerza...")

    time.sleep(15)

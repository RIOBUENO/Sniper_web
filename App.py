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
    
    # LÓGICA DE GATILLO: Espera a que la vela actual confirme el giro después del toque
    if dist_pct < 0.02:
        # VENTA (PUT): Vela actual roja y cerrando por debajo de la anterior tras tocar muralla
        if v_actual['Close'] < v_actual['Open'] and v_actual['Close'] < v_previa['Close']:
            if precio_actual < best_p:
                confirmacion = "📉 VENTA (PUT) - FUERZA CONFIRMADA"
        
        # COMPRA (CALL): Vela actual verde y cerrando por arriba de la anterior tras tocar muralla
        elif v_actual['Close'] > v_actual['Open'] and v_actual['Close'] > v_previa['Close']:
            if precio_actual > best_p:
                confirmacion = "🚀 COMPRA (CALL) - FUERZA CONFIRMADA"
            
    return {
        "Par": s, "Precio": precio_actual, "Muralla": best_p, 
        "Toques": max_t, "Confirmacion": confirmacion, "Dist": dist_pct
    }

placeholder = st.empty()

while True:
    with placeholder.container():
        st.write(f"⌛ Analizando velas de 1min: {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        c1, c2 = st.columns([2, 1]) # Aquí estaba el detalle, ya está igualito abajo
        
        resultados = []
        for s in SIMBOLOS:
            try:
                res = analizar_precision(s)
                if res and res['Toques'] >= MIN_TOUCHES:
                    resultados.append(res)
            except: continue

        with c2: # Ahora sí dice c2 igual que arriba
            st.subheader("📡 Radar")
            for r in resultados:
                st.write(f"**{r['Par']}**: {r['Precio']:.5f} (M: {r['Toques']}T)")

        with c1: # Ahora sí dice c1
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
                st.info("Esperando que el precio deje de pendejear y confirme dirección...")

    time.sleep(15)

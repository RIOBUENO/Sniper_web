import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import time

# Configuración de página ancha para ver todo claro
st.set_page_config(page_title="Raúl Sniper Pro Max", layout="wide")

st.markdown("""
    <style>
    .stProgress > div > div > div > div { background-color: #00ff00; }
    .status-box { padding: 15px; border-radius: 10px; background-color: #1e1e1e; border: 1px solid #333; }
    .signal-card { border-left: 5px solid #ff4b4b; background-color: #262626; padding: 10px; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Sniper Intelligence: Radar de Liquidez Pro")

# --- SEGURIDAD ---
password = st.sidebar.text_input("Contraseña de Acceso", type="password")
if password != "raul123":
    st.error("Introduce la clave para ver el mercado, menor.")
    st.stop()

# --- CONFIGURACIÓN DE ACTIVOS ---
# Añadimos PEPE-USD para máxima volatilidad
SIMBOLOS = ["SOL-USD", "PEPE-USD", "BTC-USD", "AUDUSD=X", "EURUSD=X", "GBPUSD=X", "GBPJPY=X"]
MIN_TOUCHES = 35 # Solo murallas de concreto

def analizar_par(s):
    # Estudiamos 240 velas de 15min (aprox 2.5 días de data)
    df_hist = yf.download(s, interval="15m", period="5d", progress=False)
    # Precio actual en tiempo real
    df_now = yf.download(s, interval="1m", period="1d", progress=False)
    
    actual = df_now['Close'].iloc[-1]
    highs = df_hist['High']
    lows = df_hist['Low']
    
    # Buscador de Murallas (Zonas de alta concentración de toques)
    precios = pd.concat([highs, lows])
    umbral = actual * 0.0003 # Margen de error mínimo para precisión quirúrgica
    best_p = 0
    max_t = 0
    
    # Escaneo de niveles con más rebotes
    for p in precios.unique()[:70]: 
        touches = ((highs >= p - umbral) & (lows <= p + umbral)).sum()
        if touches > max_t:
            max_t = touches
            best_p = p
            
    distancia = abs(actual - best_p)
    dist_pct = (distancia / best_p) * 100
    
    # Barra de Confianza basada en cercanía al imán
    confianza = max(0, min(100, 100 - (dist_pct * 1500))) 
    
    estado = "Analizando Inercia..."
    if dist_pct < 0.01: # El precio está encima de la muralla
        estado = "🚨 ZONA DE BARRIDO (OPERAR YA)"
    elif dist_pct < 0.05:
        estado = "⚡ Imán Activo (Precio Atrayendo)"
        
    return {
        "Par": s, "Precio": actual, "Muralla": best_p, 
        "Toques": max_t, "Confianza": confianza, "Estado": estado,
        "Dist": dist_pct
    }

placeholder = st.empty()

# Bucle de actualización automática
while True:
    with placeholder.container():
        st.write(f"🟢 Radar Activo - Última actualización: {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        resultados = []
        for s in SIMBOLOS:
            try:
                res = analizar_par(s)
                if res['Toques'] >= MIN_TOUCHES: # Solo mostramos si es muralla real
                    resultados.append(res)
            except: continue
        
        # Grid de Tarjetas de Monitoreo
        cols = st.columns(min(len(resultados), 3) if resultados else 1)
        for i, r in enumerate(resultados):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="status-box">
                    <h2 style='margin:0;'>{r['Par']}</h2>
                    <h3 style='color:#00ff00; margin:0;'>{r['Precio']:.6f}</h3>
                    <p><b>Muralla:</b> {r['Muralla']:.6f} ({r['Toques']} toques)</p>
                    <p style='color:#ffaa00;'><b>{r['Estado']}</b></p>
                </div>
                """, unsafe_allow_html=True)
                st.progress(int(r['Confianza'])/100)
                st.write(f"Distancia: {r['Dist']:.4f}%")

        # SECCIÓN DE SEÑALES CONFIRMADAS
        st.markdown("---")
        st.subheader("🚨 Señales Sniper Confirmadas")
        
        alertas = [r for r in resultados if r['Confianza'] > 85]
        if alertas:
            for a in alertas:
                st.markdown(f"""
                <div class="signal-card">
                    <h3>🔥 ENTRADA EN {a['Par']}</h3>
                    <p>El precio está pendejeando en la muralla de {a['Muralla']:.6f}. 
                    Posible barrido de liquidez. Prepara el gatillo para reversión o rotura fuerte.</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Escaneando murallas de concreto... Sin señales de alta probabilidad ahorita.")
            
    time.sleep(30) # Refresca cada 30 segundos

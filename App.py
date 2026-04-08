import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Raúl Francotirador Web", layout="wide")
st.title("🎯 Panel de Control: Inercia & Murallas")

# --- SEGURIDAD ---
# Mantengo tu clave raul123
contraseña = st.sidebar.text_input("Contraseña de Acceso", type="password")

if contraseña != "raul123":
    st.error("Introduce la clave para ver el mercado, menor.")
    st.stop()

# --- PARÁMETROS ---
SIMBOLOS = ["SOL-USD", "AUDCAD=X", "AUDJPY=X", "AUDUSD=X", "EURAUD=X", "GBPUSD=X", "GBPJPY=X"]
MIN_TOQUES = 35 # El filtro de fuerza que pediste

def obtener_murallas(df, min_t):
    # Umbral de sensibilidad para detectar toques en la muralla
    umbral = df['Close'].std() * 0.15
    # Combinamos altos y bajos para buscar zonas de rebote
    precios = pd.concat([df['High'], df['Low']]).unique()
    niveles = []
    
    for p in precios:
        # Contamos cuántas velas tocaron o estuvieron cerca de ese precio p
        toques = ((df['High'] >= p - umbral) & (df['Low'] <= p + umbral)).sum()
        
        if toques >= min_t:
            # Evitamos duplicar niveles que estén muy pegados
            if not any(abs(p - l['p']) < umbral * 2 for l in niveles):
                niveles.append({'p': p, 't': toques})
    
    return niveles

# --- MONITOR EN VIVO ---
placeholder = st.empty()

# Bucle principal
while True:
    with placeholder.container():
        st.write(f"🛰️ Radar Raúl Sniper - Actualizado: {datetime.datetime.now().strftime('%H:%M:%S')}")
        datos_tabla = []
        
        for s in SIMBOLOS:
            try:
                # Descarga de datos: 15m para murallas, 1m para el precio actual
                d15 = yf.download(s, interval="15m", period="5d", progress=False)
                d1 = yf.download(s, interval="1m", period="1d", progress=False)
                
                if d15.empty or d1.empty:
                    continue
                
                precio_cierre = d1['Close'].iloc[-1]
                murallas = obtener_murallas(d15, MIN_TOQUES)
                
                if murallas:
                    # Encontrar la muralla más cercana al precio actual
                    m_cercana = min(murallas, key=lambda x: abs(precio_cierre - x['p']))
                    dist = abs(precio_cierre - m_cercana['p'])
                    dist_pct = (dist / m_cercana['p']) * 100
                    
                    # Lógica de estados
                    estado = "⚪ Neutral"
                    if 0.01 < dist_pct < 0.09:
                        estado = "🔥 ¡IMÁN ACTIVO!"
                    elif dist_pct <= 0.01:
                        estado = "🎯 EN MURALLA (REBOTE)"
                    
                    datos_tabla.append({
                        "Activo": s,
                        "Precio": f"{precio_cierre:.5f}",
                        "Muralla": f"{m_cercana['p']:.5f}",
                        "Toques": m_cercana['t'],
                        "Distancia %": f"{dist_pct:.3f}%",
                        "Estado": estado
                    })
            except Exception as e:
                continue

        if datos_tabla:
            # Mostramos la tabla de datos corregida
            st.table(pd.DataFrame(datos_tabla))
        else:
            st.warning("Buscando murallas de 35 toques... (Mercado con poca volatilidad)")
            
    # Esperar 60 segundos para la siguiente actualización
    time.sleep(60)

import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Raúl Sniper Web", layout="wide")
st.title("🎯 Panel de Control: Inercia & Murallas")

# --- SEGURIDAD ---
password = st.sidebar.text_input("Contraseña de Acceso", type="password")
if password != "raul123": # <--- ESTA ES TU CLAVE, PUEDES CAMBIARLA
    st.error("Introduce la clave para ver el mercado, menor.")
    st.stop()

# --- PARÁMETROS ---
SIMBOLOS = ["SOL-USD", "AUDCAD=X", "AUDJPY=X", "AUDUSD=X", "EURAUD=X", "GBPUSD=X", "GBPJPY=X"]
MIN_TOUCHES = 35

def get_murallas(df, min_t):
    umbral = df['Close'].std() * 0.15
    prices = pd.concat([df['High'], df['Low']]).unique()
    levels = []
    for p in prices:
        touches = ((df['High'] >= p - umbral) & (df['Low'] <= p + umbral)).sum()
        if touches >= min_t:
            if not any(abs(p - l['p']) < umbral * 2 for l in levels):
                levels.append({'p': p, 't': touches})
    return levels

placeholder = st.empty()

while True:
    with placeholder.container():
        st.write(f"Última actualización: {datetime.datetime.now().strftime('%H:%M:%S')}")
        datos_tabla = []
        for s in SIMBOLOS:
            try:
                d15 = yf.download(s, interval="15m", period="5d", progress=False)
                d1 = yf.download(s, interval="1m", period="1d", progress=False)
                close = d1['Close'].iloc[-1]
                murallas = get_murallas(d15, MIN_TOUCHES)
                if murallas:
                    m_cercana = min(murallas, key=lambda x: abs(close - x['p']))
                    dist = abs(close - m_cercana['p'])
                    dist_pct = (dist / m_cercana['p']) * 100
                    estado = "⚪ Neutral"
                    if 0.01 < dist_pct < 0.09: estado = "🔥 ¡IMÁN ACTIVO!"
                    datos_tabla.append({
                        "Activo": s, "Precio": f"{close:.5f}",
                        "Muralla": f"{m_cercana['p']:.5f}", "Toques": m_cercana['t'],
                        "Distancia %": f"{dist_pct:.3f}%", "Estado": estado
                    })
            except: continue
        if datos_tabla:
            st.table(pd.DataFrame(datos_tabla))
        time.sleep(60)

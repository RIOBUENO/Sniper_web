import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Raúl Sniper Pro", layout="wide")
st.title("🏹 Raúl Sniper Pro+ (Estable)")

# Creamos un ÚNICO contenedor fuera del bucle para evitar el error de Nodos
monitor = st.empty()

# --- MOTOR DE ESCANEO ---
SIMBOLOS = ["EURUSD=X", "GBPUSD=X", "AUDUSD=X", "BTC-USD", "SOL-USD"]

while True:
    try:
        resumen_datos = []
        
        for s in SIMBOLOS:
            # Descarga rápida
            df = yf.download(s, interval="1m", period="1d", progress=False)
            if df.empty: continue
            
            # Indicadores base
            precio = df['Close'].iloc[-1]
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            
            estado = "⚪ NEUTRO"
            if rsi > 70: estado = "🔴 SOBRECOMPRA"
            if rsi < 30: estado = "🟢 SOBREVENTA"
            
            resumen_datos.append({
                "Activo": s,
                "Precio": f"{precio:.5f}",
                "RSI": f"{rsi:.2f}",
                "Estado": estado
            })

        # ACTUALIZACIÓN SEGURA: 
        # Usamos 'with monitor.container()' para sobrescribir el mismo nodo
        with monitor.container():
            st.write(f"⏳ Última actualización: {datetime.now().strftime('%H:%M:%S')}")
            # Usamos dataframe en lugar de table, que es más estable en móviles
            st.dataframe(pd.DataFrame(resumen_datos), use_container_width=True)
            
        time.sleep(60) # Esperamos 1 minuto para no saturar el navegador

    except Exception as e:
        st.error(f"Error en el ciclo: {e}")
        time.sleep(10)

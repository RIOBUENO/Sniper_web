import streamlit as st
import time
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime

# ======================================================
# 1. CONFIGURACIÓN DE CREDENCIALES
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

# Las 15 divisas de Forex
SIMBOLOS = [
    "EURAUD=X", "EURCAD=X", "EURCHF=X", "GBPAUD=X", "GBPCAD=X",
    "GBPJPY=X", "AUDUSD=X", "AUDCAD=X", "AUDJPY=X", "EURUSD=X",
    "GBPUSD=X", "USDJPY=X", "USDCAD=X", "USDCHF=X", "NZDUSD=X"
]

# Inicializar cooldown en el estado de la sesión
if 'cooldown' not in st.session_state:
    st.session_state.cooldown = {}

# ======================================================
# 2. MOTOR DE ANÁLISIS TÉCNICO
# ======================================================
def analizar_sniper(s):
    try:
        # Descarga de datos de 1 minuto
        df = yf.download(s, interval="1m", period="1d", progress=False)
        if df.empty or len(df) < 60: return None

        # Indicadores Técnicos
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        # Análisis de Muralla (Sensibilidad 25 toques)
        df_reciente = df.tail(150)
        soporte_h = df_reciente['Low'].min()
        resistencia_h = df_reciente['High'].max()
        
        margen = soporte_h * 0.0003 
        toques = ((df_reciente['Low'] - soporte_h).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = float(v_act['Close'])

        # GATILLO 1: MURALLA (REBOTE)
        # Distancia de activación: 0.05%
        distancia_zona = abs(precio - soporte_h) <= (precio * 0.0005)
        if distancia_zona and toques >= 25:
            rsi_val = v_act['RSI']
            veredicto = "🔥 REBOTE PROBABLE" if rsi_val < 42 else "👀 VIGILAR ZONA"
            enviar_alerta(s, precio, toques, f"🧱 MURALLA 25x\n{veredicto}")

        # GATILLO 2: TRAYECTORIA (FIBO 50-70%)
        rango = resistencia_h - soporte_h
        fibo_50 = resistencia_h - (0.50 * rango)
        fibo_70 = resistencia_h - (0.70 * rango)
        
        en_fibo = fibo_70 <= precio <= fibo_50
        tendencia_ok = v_act['EMA20'] > v_ant['EMA20']
        cruce_3_9 = v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']

        if tendencia_ok and en_fibo and cruce_3_9:
            enviar_alerta(s, precio, toques, "🚀 IMPULSO TENDENCIAL")
            
        return f"{s}: {precio:.4f} | T:{toques}"
    except:
        return None

def enviar_alerta(s, precio, toques, tipo):
    clave = f"{s}_{tipo}"
    ahora = time.time()
    # Cooldown de 10 minutos para evitar spam
    if clave not in st.session_state.cooldown or (ahora - st.session_state.cooldown[clave] > 600):
        msg = (f"🎯 *RAÚL SNIPER V10*\n\n"
               f"💎 *Activo:* {s}\n"
               f"💰 *Precio:* {precio:.5f}\n"
               f"🧱 *Toques:* {toques}\n"
               f"📡 *Alerta:* {tipo}\n"
               f"⏰ *Hora:* {datetime.now().strftime('%H:%M:%S')}")
        try:
            bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
            st.session_state.cooldown[clave] = ahora
        except:
            pass

# ======================================================
# 3. INTERFAZ Y BUCLE DE EJECUCIÓN (USANDO FRAGMENT)
# ======================================================
st.set_page_config(page_title="Raúl Sniper V10", page_icon="🏹")
st.title("🏹 Raúl Sniper Pro V10")

# Fragmento que se auto-ejecuta cada 20 segundos de forma aislada
@st.fragment(run_every=20)
def monitor_de_mercado():
    status_ui = st.empty()
    log_ui = st.empty()
    
    status_ui.success(f"📡 Escaneando divisas... Última vuelta: {datetime.now().strftime('%H:%M:%S')}")
    
    resultados = []
    for s in SIMBOLOS:
        res = analizar_sniper(s)
        if res:
            resultados.append(res)
    
    if resultados:
        log_ui.code("\n".join(resultados))
    else:
        log_ui.warning("Esperando respuesta de los mercados...")

# Verificación de mercado abierto (Lunes a Viernes)
if datetime.now().weekday() < 5:
    monitor_de_mercado()
else:
    st.error("💤 Mercado Cerrado (Fin de semana). El bot se activará el lunes.")

import time
import datetime
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import telebot
from datetime import datetime, timedelta

# ======================================================
# 1. CONFIGURACIÓN MAESTRA (DATOS DEL USUARIO)
# ======================================================
TOKEN = "8264571722:AAEP0Za-6ateXX8eE6OEhRxv9HgeVhwVWg4"
CHAT_ID = "5785324442"
bot = telebot.TeleBot(TOKEN)

SIMBOLOS = [
    "EURUSD=X", "GBPUSD=X", "EURCHF=X", "GBPJPY=X", 
    "BTC-USD", "ETH-USD", "SOL-USD", "AUDUSD=X"
]

# Parámetros Estratégicos V8.2
TOLERANCIA_MURO = 0.0005  # Flexibilidad del 0.05%
MIN_TOQUES = 35           # Filtro de calidad Sniper
COOLDOWN = {}             # Evita spam de señales

# ======================================================
# 2. FUNCIONES DEL COPILOTO (SEGURIDAD Y ANÁLISIS)
# ======================================================

def es_horario_seguro():
    """Bloquea el bot 30 min antes/después de aperturas de sesión"""
    ahora_utc = datetime.utcnow()
    hora_actual = ahora_utc.strftime("%H:%M")
    # Ventanas de alta volatilidad (Londres y NY)
    bloqueos = [("06:30", "07:30"), ("12:30", "13:30"), ("15:30", "16:30")]
    for inicio, fin in bloqueos:
        if inicio <= hora_actual <= fin:
            return False
    return True

def analizar_uniformidad(df_camino):
    """El Copiloto revisa si la tendencia es limpia para Fibonacci"""
    if len(df_camino) < 10: return False
    desviacion = df_camino['Close'].std()
    promedio = df_camino['Close'].mean()
    # Una tendencia uniforme no tiene gaps ni velas erráticas
    return desviacion < (promedio * 0.01)

def predecir_movimiento(toques, rsi):
    """Analiza si la zona de choque aguantará o romperá"""
    if toques > 40 and rsi > 70: return "REBOTE PROBABLE (Agotamiento) 📉"
    if toques < 15 and rsi < 60: return "POSIBLE RUPTURA (Fuerza nueva) 💥"
    return "ZONA DE CHOQUE (Respetando nivel) 🛡️"

def enviar_alerta(titulo, msg):
    """Envío de señales con formato profesional"""
    texto = f"⚠️ *{titulo}*\n\n{msg}"
    try:
        bot.send_message(CHAT_ID, texto, parse_mode="Markdown")
    except Exception as e:
        print(f"Error de envío: {e}")

# ======================================================
# 3. MOTOR LÓGICO (SNIPER & COPILOTO)
# ======================================================

def procesar_sniper(s):
    try:
        # Descarga de datos en tiempo real
        df = yf.download(s, interval="1m", period="1d", progress=False)
        if df.empty or len(df) < 50: return

        # Indicadores Técnicos Sniper
        df['EMA3'] = ta.ema(df['Close'], length=3)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # Detección de Muralla (Soporte de las últimas 50 velas)
        zona_soporte = df['Low'].rolling(window=50).min().iloc[-1]
        
        # Conteo histórico de toques
        margen = zona_soporte * 0.0003
        toques = ((df['Low'] - zona_soporte).abs() <= margen).sum()

        v_act = df.iloc[-1]
        v_ant = df.iloc[-2]
        precio = v_act['Close']

        # --- A. FUNCIÓN COPILOTO (RADAR) ---
        distancia = abs(precio - zona_soporte) / precio
        if 0.0008 <= distancia <= 0.0025: # El precio está entrando al área de radar
            if s not in COOLDOWN or (time.time() - COOLDOWN[s] > 900): # Cooldown de 15 min
                uniforme = analizar_uniformidad(df.tail(10))
                pred = predecir_movimiento(toques, v_act['RSI'])
                info = (f"Activo: {s}\nTarget: {zona_soporte:.5f}\n"
                        f"Toques detectados: {toques}\nFibo Apto: {'SÍ ✅' if uniforme else 'NO ⚠️'}\n"
                        f"Copiloto dice: *{pred}*")
                enviar_alerta("AVISO DE RADAR", info)
                COOLDOWN[s] = time.time()

        # --- B. FUNCIÓN SNIPER (DISPARO) ---
        # Filtros: EMA 20 para tendencia + Muralla + Tolerancia 0.05%
        t_alcista = v_act['EMA20'] > v_ant['EMA20']
        cerca_muro = abs(precio - zona_soporte) <= (precio * TOLERANCIA_MURO)

        if t_alcista and cerca_muro and toques >= MIN_TOQUES:
            # Gatillo de entrada: Cruce de EMA 3 vs 9 al cierre de vela
            if v_act['EMA3'] > v_act['EMA9'] and v_ant['EMA3'] <= v_ant['EMA9']:
                msg_final = (f"🔥 *¡DISPARA SNIPER!* 🔥\n\n"
                             f"Activo: {s}\n"
                             f"OPERACIÓN: *COMPRA (1-2 min)*\n"
                             f"Precio entrada: {precio:.5f}\n"
                             f"Confirmación: Cruce 3/9 + Muralla {toques}T")
                enviar_alerta("SEÑAL CONFIRMADA", msg_final)
                COOLDOWN[s] = time.time() + 600 # Bloqueo de 10 min por par

    except Exception as e:
        print(f"Error procesando {s}: {e}")

# ======================================================
# 4. INICIO DE OPERACIONES (EJECUCIÓN CONTINUA)
# ======================================================

print("🕵️ Raúl Sniper Elite V8.2 - ONLINE")
enviar_alerta("SISTEMA ACTIVO", "Radar y Sniper configurados. Esperando zona de choque...")

while True:
    try:
        # Solo opera si no estamos en apertura o cierre de sesión
        if es_horario_seguro():
            for s in SIMBOLOS:
                procesar_sniper(s)
        else:
            print("Pausa de seguridad: Mercado en apertura/cierre de sesión.")
        
        time.sleep(15) # Ciclo de escaneo
    except Exception as e:
        print(f"Falla crítica: {e}")
        time.sleep(30)

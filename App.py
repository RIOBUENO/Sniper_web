importar streamlit como st
Importar yfinance como yf
importar pandas como pd
importar fecha y hora
hora de importación

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Raúl Francotirador Web", layout="wide")
st.title("ðŸŽ¯ Panel de Control: Inercia & Murallas")

# --- SEGURIDAD ---
contraseña = st.sidebar.text_input("Contraseña de Acceso", type="password")
if contraseña != "raul123": # <--- ESTA ES TU CLAVE, PUEDES CAMBIARLA
    st.error("Introduce la clave para ver el mercado, menor.")
    st.stop()

# --- PARÃ METROS ---
SIMBOLOS = ["SOL-USD", "AUDCAD=X", "AUDJPY=X", "AUDUSD=X", "EURAUD=X", "GBPUSD=X", "GBPJPY=X"]
MIN_TOQUES = 35

def obtener_murallas(df, min_t):
    umbral = df['Close'].std() * 0.15
    precios = pd.concat([df['Máximo'], df['Mínimo']]).unique()
    niveles = []
    para p en precios:
        toques = ((df['Alto'] >= p - umbral) & (df['Bajo'] <= p + umbral)).sum()
        Si los toques son mayores o iguales a min_t:
            si no hay ninguno(abs(p - l['p']) < umbral * 2 para l en niveles):
                niveles.append({'p': p, 't': toques})
    niveles de retorno

marcador de posición = st.empty()

mientras que verdadero:
    con placeholder.container():
        st.write(f"Última actualización: {datetime.datetime.now().strftime('%H:%M:%S')}")
        datos_tabla = []
        para s en SÍMBOLOS:
            intentar:
                d15 = yf.download(s, interval="15m", period="5d", progress=False)
                d1 = yf.download(s, interval="1m", period="1d", progress=False)
                cerrar = d1['Cerrar'].iloc[-1]
                murallas = get_murallas(d15, MIN_TOUCHES)
                si murallas:
                    m_cercana = min(murallas, key=lambda x: abs(close - x['p']))
                    dist = abs(close - m_cercana['p'])
                    dist_pct = (dist / m_cercana['p']) * 100
                    estado = "âšª Neutral"
                    if 0.01 < dist_pct < 0.09: estado = "ðŸ”¥ Â¡IMÃ N ACTIVO!"
                    datos_tabla.append({
                        "Activo": s, "Precio": f"{close:.5f}",
                        "Muralla": f"{m_cercana['p']:.5f}", "Toques": m_cercana['t'],
                        "Distancia %": f"{dist_pct:.3f}%", "Estado": estado
                    })
            excepto: continuar
        si datos_tabla:
            st.table(pd.DataFrame(datos_tabla))
        tiempo.dormir(60)

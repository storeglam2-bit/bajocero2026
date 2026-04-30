import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Bajo Cero Cloud", page_icon="❄️", layout="wide")

# Estilo para el logo y métricas
st.markdown("""<style>
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebarNav"] { background-image: none; }
</style>""", unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
# En la nube, el link se configura en los "Secrets"
conn = st.connection("gsheets", type=GSheetsConnection)

# Intentar cargar el logo con seguridad para evitar el error de la imagen
try:
    st.sidebar.image("logo.png", use_container_width=True)
except:
    st.sidebar.title("❄️ BAJO CERO")

choice = st.sidebar.radio("MENÚ", ["📊 Dashboard", "🛒 Ventas", "📥 Entradas", "🥤 Productos", "🏢 Clientes"])

# --- FUNCIONES DE AYUDA ---
def get_data(sheet):
    return conn.read(worksheet=sheet, ttl="0") # ttl=0 para que actualice al instante

# --- MÓDULOS ---
if choice == "📊 Dashboard":
    st.title("📊 Resumen en Tiempo Real")
    df = get_data("productos")
    
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Stock Total", int(df['stock'].sum()))
        val = int((df['stock'] * df['precio']).sum())
        c3.metric("Valor Inventario", f"$ {val:,}".replace(",", "."))
        
        st.subheader("📦 Estado actual")
        df['Alerta'] = df['stock'].apply(lambda x: '🚨 BAJO' if x <= 4 else '✅ OK')
        st.dataframe(df[['nombre', 'tipo', 'stock', 'precio', 'Alerta']], use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos en Google Sheets.")

elif choice == "📥 Entradas":
    st.title("📥 Registro de Producción")
    df_p = get_data("productos")
    
    with st.form("ingreso"):
        prod = st.selectbox("Sabor", df_p['nombre'] + " (" + df_p['tipo'] + ")")
        cant = st.number_input("Botellas nuevas", min_value=1, step=1)
        if st.form_submit_button("Confirmar Entrada"):
            # Lógica para actualizar Google Sheets
            idx = df_p[df_p['nombre'] + " (" + df_p['tipo'] + ")" == prod].index[0]
            df_p.at[idx, 'stock'] += cant
            conn.update(worksheet="productos", data=df_p)
            st.success("Actualizado en Google Sheets")
            st.rerun()

# ... (El resto de módulos siguen la misma lógica de conn.update)
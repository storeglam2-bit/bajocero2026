import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Bajo Cero Pro", page_icon="❄️", layout="wide")

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    try:
        df = conn.read(worksheet=pestana, ttl=0)
        return df.dropna(how='all') # Elimina filas vacías
    except Exception as e:
        return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.title("❄️ BAJO CERO")
    st.markdown("---")
    menu = st.radio("MENÚ", ["📊 Dashboard", "🛒 Ventas", "📥 Entradas", "🥤 Productos", "🏢 Clientes"])

# --- MÓDULO PRODUCTOS (¡Empieza por aquí para llenar la lista!) ---
if menu == "🥤 Productos":
    st.title("🥤 Catálogo de Productos")
    df_p = cargar_datos("productos")
    
    with st.expander("✨ Añadir Primer Producto", expanded=df_p.empty):
        with st.form("nuevo_p"):
            n = st.text_input("Nombre del Sabor")
            t = st.selectbox("Tipo", ["Sin Licor", "Con Licor"])
            p = st.number_input("Precio Unitario", min_value=0, step=1000)
            if st.form_submit_button("Guardar Producto"):
                # Crear estructura si está vacío
                nueva_fila = pd.DataFrame([{"nombre": n, "color": "#000", "tipo": t, "precio": p, "stock": 0}])
                df_final = pd.concat([df_p, nueva_fila], ignore_index=True) if not df_p.empty else nueva_fila
                conn.update(worksheet="productos", data=df_final)
                st.success("¡Producto guardado! Ya aparecerá en el Dashboard.")
                st.rerun()
    
    if not df_p.empty:
        st.dataframe(df_p[['nombre', 'tipo', 'precio', 'stock']], use_container_width=True, hide_index=True)

# --- DASHBOARD ---
elif menu == "📊 Dashboard":
    st.title("📊 Resumen de Inventario")
    df_p = cargar_datos("productos")
    
    if df_p.empty or 'stock' not in df_p.columns:
        st.info("👋 ¡Bienvenido! Ve al módulo '🥤 Productos' para registrar tu primer sabor.")
    else:
        # Forzar números
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Sabores", len(df_p))
        c2.metric("Total Botellas", int(df_p['stock'].sum()))
        val = int((df_p['stock'] * df_p['precio']).sum())
        c3.metric("Valor Inventario", f"$ {val:,}".replace(",", "."))
        
        st.subheader("📦 Stock Actual")
        df_p['Sabor'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
        st.dataframe(
            df_p[['Sabor', 'stock', 'precio']].style.format({
                "precio": lambda x: f"$ {int(x):,}".replace(",", "."),
                "stock": "{:.0f}"
            }), use_container_width=True, hide_index=True
        )

# --- ENTRADAS ---
elif menu == "📥 Entradas":
    st.title("📥 Registro de Producción")
    df_p = cargar_datos("productos")
    if not df_p.empty:
        with st.form("ingreso"):
            df_p['display'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
            prod = st.selectbox("Sabor", df_p['display'])
            cant = st.number_input("Cantidad nueva", min_value=1, step=1)
            if st.form_submit_button("Actualizar Stock"):
                idx = df_p[df_p['display'] == prod].index[0]
                df_p.at[idx, 'stock'] = int(df_p.at[idx, 'stock']) + cant
                conn.update(worksheet="productos", data=df_p[['nombre', 'color', 'tipo', 'precio', 'stock']])
                st.success("Stock actualizado en la nube.")
                st.rerun()
    else:
        st.warning("Primero crea productos.")

# --- CLIENTES ---
elif menu == "🏢 Clientes":
    st.title("🏢 Clientes")
    df_c = cargar_datos("clientes")
    with st.form("cli"):
        nom = st.text_input("Nombre Empresa")
        if st.form_submit_button("Registrar"):
            nueva = pd.DataFrame([{"empresa": nom}])
            df_final = pd.concat([df_c, nueva], ignore_index=True) if not df_c.empty else nueva
            conn.update(worksheet="clientes", data=df_final)
            st.rerun()
    if not df_c.empty:
        st.table(df_c)
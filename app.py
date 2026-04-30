import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Bajo Cero - Sistema", page_icon="❄️", layout="wide")

# Estilo para mejorar la visualización en móvil
st.markdown("""
    <style>
    .stMetric { background-color: #1e2130; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    try:
        # Intentamos leer la pestaña. ttl=0 evita que guarde basura en memoria.
        return conn.read(worksheet=pestana, ttl=0)
    except Exception as e:
        st.error(f"⚠️ No se encontró la pestaña '{pestana}'. Revisa que el nombre en Google Sheets esté en minúsculas.")
        return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.header("❄️ BAJO CERO")
    
    st.markdown("---")
    menu = st.radio("NAVEGACIÓN", ["📊 Panel Principal", "🛒 Registrar Venta", "📥 Entrada Stock", "🥤 Productos", "🏢 Clientes"])

# --- PANEL PRINCIPAL ---
if menu == "📊 Panel Principal":
    st.title("📊 Resumen de Inventario")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # Validamos que existan las columnas necesarias
        columnas_req = ['nombre', 'tipo', 'stock', 'precio']
        if all(col in df_p.columns for col in columnas_req):
            # Métricas
            c1, c2, c3 = st.columns(3)
            stock_total = int(pd.to_numeric(df_p['stock']).sum())
            valor_inv = int((pd.to_numeric(df_p['stock']) * pd.to_numeric(df_p['precio'])).sum())
            
            c1.metric("Sabores", len(df_p))
            c2.metric("Total Unidades", stock_total)
            c3.metric("Valor Inventario", f"$ {valor_inv:,}".replace(",", "."))
            
            st.markdown("---")
            
            # Alerta Stock Bajo
            bajos = df_p[pd.to_numeric(df_p['stock']) <= 4]
            if not bajos.empty:
                st.warning(f"🚨 Tienes {len(bajos)} sabores con stock crítico (4 o menos).")
            
            # Tabla
            df_p['Sabor'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
            st.dataframe(
                df_p[['Sabor', 'stock', 'precio']].style.format({
                    "precio": lambda x: f"$ {int(x):,}".replace(",", "."),
                    "stock": "{:.0f}"
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.error(f"Error: La pestaña 'productos' debe tener estas columnas: {columnas_req}")
    else:
        st.info("Configura tu Google Sheet para empezar. Asegúrate de que el link en Secrets sea correcto.")

# --- ENTRADA STOCK ---
elif menu == "📥 Entrada Stock":
    st.title("📥 Registro de Producción")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        with st.form("form_entrada"):
            df_p['display'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
            sel = st.selectbox("Producto", df_p['display'])
            cant = st.number_input("Cantidad nueva", min_value=1, step=1)
            
            if st.form_submit_button("Actualizar Inventario"):
                idx = df_p[df_p['display'] == sel].index[0]
                df_p.at[idx, 'stock'] = int(df_p.at[idx, 'stock']) + cant
                # Guardar
                conn.update(worksheet="productos", data=df_p[['nombre', 'color', 'tipo', 'precio', 'stock']])
                st.success("¡Datos actualizados!")
                st.rerun()

# --- PRODUCTOS ---
elif menu == "🥤 Productos":
    st.title("🥤 Catálogo")
    df_p = cargar_datos("productos")
    with st.expander("Crear Nuevo Producto"):
        n = st.text_input("Nombre")
        t = st.selectbox("Tipo", ["Sin Licor", "Con Licor"])
        p = st.number_input("Precio", min_value=0, step=1000)
        if st.button("Guardar"):
            nueva = pd.DataFrame([{"nombre": n, "color": "#000", "tipo": t, "precio": p, "stock": 0}])
            conn.update(worksheet="productos", data=pd.concat([df_p, nueva], ignore_index=True))
            st.success("Producto creado")
            st.rerun()
    st.dataframe(df_p, use_container_width=True)

# --- CLIENTES ---
elif menu == "🏢 Clientes":
    st.title("🏢 Clientes")
    df_c = cargar_datos("clientes")
    with st.form("c"):
        nom = st.text_input("Empresa")
        if st.form_submit_button("Registrar"):
            n_cli = pd.DataFrame([{"empresa": nom}])
            conn.update(worksheet="clientes", data=pd.concat([df_c, n_cli], ignore_index=True))
            st.rerun()
    st.table(df_c)
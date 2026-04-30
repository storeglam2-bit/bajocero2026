import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Bajo Cero - Gestión de Inventario",
    page_icon="❄️",
    layout="wide"
)

# --- CONEXIÓN A GOOGLE SHEETS ---
# Utiliza la Service Account configurada en Secrets para permisos de Editor
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    try:
        # ttl=0 asegura que siempre veamos los datos reales de la nube
        df = conn.read(worksheet=pestana, ttl=0)
        return df.dropna(how='all')
    except Exception:
        return pd.DataFrame()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    try:
        # Intenta cargar el logo desde el repositorio
        st.image("logo.png", use_container_width=True)
    except:
        st.title("❄️ BAJO CERO")
    
    st.markdown("---")
    menu = st.radio(
        "MENÚ DE NAVEGACIÓN",
        ["📊 Panel Principal", "🛒 Registrar Venta", "📥 Entrada Producción", "🥤 Catálogo Productos", "🏢 Gestión Clientes"]
    )
    st.markdown("---")
    if st.button("🔄 Refrescar Datos"):
        st.cache_data.clear()
        st.rerun()

# --- MÓDULO 1: PANEL PRINCIPAL (DASHBOARD) ---
if menu == "📊 Panel Principal":
    st.title("📊 Resumen de Inventario")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # Limpieza de datos: asegurar que sean números enteros
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
        
        # Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("Sabores Activos", len(df_p))
        c2.metric("Total Líquidos (3L)", int(df_p['stock'].sum()))
        
        valor_total = (df_p['stock'] * df_p['precio']).sum()
        c3.metric("Valor Inventario", f"$ {int(valor_total):,}".replace(",", "."))
        
        st.markdown("---")
        
        # Alertas de Stock Bajo
        bajos = df_p[df_p['stock'] <= 4]
        if not bajos.empty:
            st.error(f"🚨 **ALERTA DE REABASTECIMIENTO:** Tienes {len(bajos)} sabor(es) en nivel crítico.")
            st.caption(f"Revisar: {', '.join(bajos['nombre'].tolist())}")
        
        # Tabla de Existencias
        st.subheader("📦 Estado del Stock")
        df_show = df_p.copy()
        df_show['Sabor'] = df_show['nombre'] + " (" + df_show['tipo'] + ")"
        
        st.dataframe(
            df_show[['Sabor', 'stock', 'precio']].style.format({
                "precio": lambda x: f"$ {int(x):,}".replace(",", "."),
                "stock": "{:d}"
            }),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No hay productos. Empieza por el menú '🥤 Catálogo Productos'.")

# --- MÓDULO 4: CATÁLOGO PRODUCTOS (Corregido) ---
elif menu == "🥤 Catálogo Productos":
    st.title("🥤 Gestión de Productos")
    df_p = cargar_datos("productos")
    
    with st.expander("✨ Añadir Nuevo Sabor"):
        with st.form("form_nuevo_p"):
            n = st.text_input("Nombre del Sabor")
            t = st.selectbox("Categoría", ["Sin Licor", "Con Licor"])
            p = st.number_input("Precio de Venta", min_value=0, step=1000)
            
            if st.form_submit_button("Guardar en Catálogo"):
                if n:
                    # Crear nueva fila con formatos forzados
                    nueva_f = pd.DataFrame([{
                        "nombre": str(n), 
                        "color": "#000", 
                        "tipo": str(t), 
                        "precio": int(p), 
                        "stock": 0
                    }])
                    
                    # Definir df_res antes de intentar el update para evitar NameError
                    if df_p.empty:
                        df_res = nueva_f
                    else:
                        df_res = pd.concat([df_p, nueva_f], ignore_index=True).fillna(0)
                    
                    try:
                        conn.update(worksheet="productos", data=df_res)
                        st.success(f"✅ {n} añadido correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error de permisos: {e}")
                else:
                    st.warning("Por favor, ingresa un nombre para el producto.")
    
    if not df_p.empty:
        st.dataframe(df_p[['nombre', 'tipo', 'precio', 'stock']], use_container_width=True, hide_index=True)

# (Los módulos de Ventas, Entradas y Clientes seguirían una lógica similar)

# --- MÓDULO 5: GESTIÓN CLIENTES ---
elif menu == "🏢 Gestión Clientes":
    st.title("🏢 Base de Datos de Clientes")
    df_c = cargar_datos("clientes")
    
    with st.form("form_cli"):
        nombre_c = st.text_input("Nombre del Cliente o Empresa")
        if st.form_submit_button("Registrar"):
            nueva_c = pd.DataFrame([{"empresa": nombre_c}])
            df_res_c = pd.concat([df_c, nueva_c], ignore_index=True)
            conn.update(worksheet="clientes", data=df_res_c)
            st.success("Cliente guardado.")
            st.rerun()
            
    if not df_c.empty:
        st.table(df_c)
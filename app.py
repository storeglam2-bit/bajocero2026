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
        st.rerun()

# --- MÓDULO 1: PANEL PRINCIPAL (DASHBOARD) ---
if menu == "📊 Panel Principal":
    st.title("📊 Resumen de Inventario")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # Limpieza de datos: asegurar que sean números enteros sin decimales .0000
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
        
        # Tabla de Existencias con formato limpio
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

# --- MÓDULO 2: REGISTRAR VENTA ---
elif menu == "🛒 Registrar Venta":
    st.title("🛒 Nueva Venta")
    df_p = cargar_datos("productos")
    df_c = cargar_datos("clientes")
    
    if not df_p.empty and not df_c.empty:
        with st.form("form_venta"):
            col1, col2 = st.columns(2)
            cli = col1.selectbox("Cliente", df_c['empresa'])
            
            df_p['display'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
            prod_sel = col1.selectbox("Producto", df_p['display'])
            cant = col2.number_input("Cantidad", min_value=1, step=1)
            
            if st.form_submit_button("Confirmar Venta"):
                idx = df_p[df_p['display'] == prod_sel].index[0]
                stock_act = int(df_p.at[idx, 'stock'])
                
                if stock_act >= cant:
                    # Actualizar stock en el DataFrame
                    df_p.at[idx, 'stock'] = stock_act - cant
                    # Guardar cambios
                    conn.update(worksheet="productos", data=df_p[['nombre', 'color', 'tipo', 'precio', 'stock']])
                    st.success("✅ Venta registrada con éxito.")
                    st.rerun()
                else:
                    st.error(f"❌ Stock insuficiente (Disponible: {stock_act})")
    else:
        st.warning("Se requiere configurar productos y clientes primero.")

# --- MÓDULO 3: ENTRADA PRODUCCIÓN ---
elif menu == "📥 Entrada Producción":
    st.title("📥 Registro de Producción")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        with st.form("form_entrada"):
            df_p['display'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
            prod_sel = st.selectbox("Sabor Producido", df_p['display'])
            cantidad = st.number_input("Cantidad de botellas", min_value=1, step=1)
            
            if st.form_submit_button("Sumar al Inventario"):
                idx = df_p[df_p['display'] == prod_sel].index[0]
                df_p.at[idx, 'stock'] = int(df_p.at[idx, 'stock']) + cantidad
                
                conn.update(worksheet="productos", data=df_p[['nombre', 'color', 'tipo', 'precio', 'stock']])
                st.success("✅ Stock actualizado en la nube.")
                st.rerun()

# --- MÓDULO 4: CATÁLOGO PRODUCTOS ---
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
                    # Crear nueva fila con formatos forzados para evitar errores de Google Sheets
                    nueva_f = pd.DataFrame([{
                        "nombre": str(n), 
                        "color": "#000", 
                        "tipo": str(t), 
                        "precio": int(p), 
                        "stock": 0
                    }])
                    df_res = pd.concat([df_p, nueva_f], ignore_index=True)
                    
                    try:
                        conn.update(worksheet="productos", data=df_res)
                        st.success(f"✅ {n} añadido correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error("❌ Error de permisos: Verifica que la Service Account sea Editor en el archivo.")
    
    if not df_p.empty:
        st.dataframe(df_p[['nombre', 'tipo', 'precio', 'stock']], use_container_width=True, hide_index=True)

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
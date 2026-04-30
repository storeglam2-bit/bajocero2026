import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Bajo Cero - Sistema de Control",
    page_icon="❄️",
    layout="wide"
)

# --- CONEXIÓN ---
# Se conecta usando la URL y credenciales de tus Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    try:
        # ttl=0 para datos frescos. Limpiamos espacios en nombres de columnas.
        df = conn.read(worksheet=pestana, ttl=0)
        df.columns = df.columns.str.strip().str.lower()
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"⚠️ Error en pestaña '{pestana}': {e}")
        return pd.DataFrame()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    # Si logo.png falla, no bloquea la app
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.title("❄️ BAJO CERO")
    
    st.markdown("---")
    menu = st.radio(
        "MENÚ DE NAVEGACIÓN",
        ["📊 Dashboard", "🛒 Ventas", "📥 Entradas", "🥤 Productos", "🏢 Clientes"]
    )
    st.markdown("---")
    if st.button("🔄 Forzar Actualización"):
        st.cache_data.clear()
        st.rerun()

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Resumen en Tiempo Real")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # Asegurar que las columnas existan antes de operar
        cols_necesarias = ['nombre', 'precio', 'stock']
        if all(col in df_p.columns for col in cols_necesarias):
            df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
            df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Sabores", len(df_p))
            c2.metric("Stock Total", int(df_p['stock'].sum()))
            val_total = (df_p['stock'] * df_p['precio']).sum()
            c3.metric("Valor Total", f"$ {int(val_total):,}".replace(",", "."))
            
            st.subheader("📦 Inventario Actual")
            st.dataframe(df_p[['nombre', 'tipo', 'stock', 'precio']], use_container_width=True, hide_index=True)
        else:
            st.warning("Revisa que el Excel tenga las columnas: nombre, tipo, precio, stock")

# --- 2. PRODUCTOS (CATÁLOGO) ---
elif menu == "🥤 Productos":
    st.title("🥤 Catálogo de Sabores")
    df_p = cargar_datos("productos")
    
    with st.expander("✨ Registrar Nuevo Sabor", expanded=df_p.empty):
        with st.form("form_nuevo_producto"):
            nombre = st.text_input("Nombre del Sabor")
            tipo = st.selectbox("Categoría", ["Sin Licor", "Con Licor"])
            precio = st.number_input("Precio de Venta", min_value=0, step=1000)
            
            if st.form_submit_button("Guardar en Google Sheets"):
                if nombre:
                    nueva_fila = pd.DataFrame([{
                        "nombre": str(nombre),
                        "color": "#000",
                        "tipo": str(tipo),
                        "precio": int(precio),
                        "stock": 0
                    }])
                    
                    # Unimos asegurando que el DataFrame no sea nulo
                    df_actualizado = pd.concat([df_p, nueva_fila], ignore_index=True) if not df_p.empty else nueva_fila
                    
                    try:
                        conn.update(worksheet="productos", data=df_actualizado)
                        st.success(f"✅ {nombre} añadido con éxito.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error de permisos: {e}")
                else:
                    st.warning("El nombre es obligatorio.")

    if not df_p.empty:
        st.subheader("Listado")
        st.write(df_p[['nombre', 'tipo', 'precio']])

# --- 3. ENTRADAS (PRODUCCIÓN) ---
elif menu == "📥 Entradas":
    st.title("📥 Entrada de Producción")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        with st.form("form_stock"):
            sabor_sel = st.selectbox("Seleccionar Sabor", df_p['nombre'].tolist())
            cantidad = st.number_input("Cantidad producida", min_value=1, step=1)
            
            if st.form_submit_button("Actualizar Stock"):
                idx = df_p[df_p['nombre'] == sabor_sel].index[0]
                df_p.at[idx, 'stock'] = int(df_p.at[idx, 'stock']) + cantidad
                
                try:
                    conn.update(worksheet="productos", data=df_p)
                    st.success("✅ Inventario actualizado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# --- 4. CLIENTES ---
elif menu == "🏢 Clientes":
    st.title("🏢 Registro de Clientes")
    df_c = cargar_datos("clientes")
    
    with st.form("form_clientes"):
        empresa = st.text_input("Nombre de la Empresa / Cliente")
        if st.form_submit_button("Registrar"):
            if empresa:
                nueva_c = pd.DataFrame([{"empresa": empresa}])
                df_final_c = pd.concat([df_c, nueva_c], ignore_index=True) if not df_c.empty else nueva_c
                conn.update(worksheet="clientes", data=df_final_c)
                st.success("✅ Cliente registrado.")
                st.rerun()

# --- 5. VENTAS (LÓGICA BÁSICA) ---
elif menu == "🛒 Ventas":
    st.title("🛒 Registro de Ventas")
    st.info("Módulo en desarrollo. Aquí podrás descontar stock automáticamente.")
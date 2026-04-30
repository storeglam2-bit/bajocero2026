import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Bajo Cero - Gestión de Inventario",
    page_icon="❄️",
    layout="wide"
)

# --- CONEXIÓN A GOOGLE SHEETS ---
# Se utiliza la URL de la hoja definida en tus Secrets de Streamlit
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    try:
        # ttl=0 asegura que los datos se lean en tiempo real sin caché
        df = conn.read(worksheet=pestana, ttl=0)
        # Limpiamos nombres de columnas: elimina espacios y convierte a minúsculas
        df.columns = df.columns.str.strip().str.lower()
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"⚠️ Error en pestaña '{pestana}': {e}")
        return pd.DataFrame()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    # Solución al MediaFileStorageError: Si logo.png no existe, muestra texto
    try:
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
        # Formateo de datos: asegurar que sean números enteros sin decimales
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
        
        # Métricas principales
        c1, c2, c3 = st.columns(3)
        c1.metric("Sabores Activos", len(df_p))
        c2.metric("Total Botellas (3L)", int(df_p['stock'].sum()))
        
        valor_total = (df_p['stock'] * df_p['precio']).sum()
        c3.metric("Valor Inventario", f"$ {int(valor_total):,}".replace(",", "."))
        
        st.markdown("---")
        
        # Tabla de Existencias con formato limpio
        st.subheader("📦 Estado del Stock")
        st.dataframe(
            df_p[['nombre', 'tipo', 'stock', 'precio']].style.format({
                "precio": lambda x: f"$ {int(x):,}".replace(",", "."),
                "stock": "{:d}"
            }),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No se encontraron datos en la pestaña 'productos'.")

# --- MÓDULO 2: REGISTRAR VENTA ---
elif menu == "🛒 Registrar Venta":
    st.title("🛒 Nueva Venta")
    df_p = cargar_datos("productos")
    df_c = cargar_datos("clientes")
    
    if not df_p.empty and not df_c.empty:
        with st.form("form_venta"):
            col1, col2 = st.columns(2)
            cli = col1.selectbox("Seleccionar Cliente", df_c['empresa'].tolist() if 'empresa' in df_c.columns else [])
            prod_sel = col1.selectbox("Seleccionar Sabor", df_p['nombre'].tolist())
            cant = col2.number_input("Cantidad", min_value=1, step=1)
            
            if st.form_submit_button("Confirmar Venta"):
                idx = df_p[df_p['nombre'] == prod_sel].index[0]
                stock_act = int(df_p.at[idx, 'stock'])
                
                if stock_act >= cant:
                    df_p.at[idx, 'stock'] = stock_act - cant
                    try:
                        conn.update(worksheet="productos", data=df_p)
                        st.success("✅ Venta registrada y stock actualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar: {e}")
                else:
                    st.error(f"❌ Stock insuficiente (Disponible: {stock_act})")

# --- MÓDULO 3: ENTRADA PRODUCCIÓN ---
elif menu == "📥 Entrada Producción":
    st.title("📥 Ingreso de Producción")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        with st.form("form_entrada"):
            prod_sel = st.selectbox("Sabor Producido", df_p['nombre'].tolist())
            cantidad = st.number_input("Botellas nuevas", min_value=1, step=1)
            
            if st.form_submit_button("Sumar al Inventario"):
                idx = df_p[df_p['nombre'] == prod_sel].index[0]
                df_p.at[idx, 'stock'] = int(df_p.at[idx, 'stock']) + cantidad
                
                try:
                    conn.update(worksheet="productos", data=df_p)
                    st.success("✅ Stock actualizado en la nube.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error de permisos: {e}")

# --- MÓDULO 4: CATÁLOGO PRODUCTOS (Solución a UnsupportedOperationError) ---
elif menu == "🥤 Catálogo Productos":
    st.title("🥤 Gestión de Productos")
    df_p = cargar_datos("productos")
    
    with st.expander("✨ Añadir Nuevo Sabor"):
        with st.form("form_nuevo_p"):
            n = st.text_input("Nombre del Sabor")
            t = st.selectbox("Categoría", ["Sin Licor", "Con Licor"])
            p = st.number_input("Precio de Venta", min_value=0, step=1000)
            
            if st.form_submit_button("Guardar Producto"):
                if n:
                    nueva_f = pd.DataFrame([{
                        "nombre": str(n), 
                        "color": "#000", 
                        "tipo": str(t), 
                        "precio": int(p), 
                        "stock": 0
                    }])
                    # Unir datos asegurando que no haya errores de referencia
                    df_res = pd.concat([df_p, nueva_f], ignore_index=True) if not df_p.empty else nueva_f
                    
                    try:
                        conn.update(worksheet="productos", data=df_res)
                        st.success(f"✅ {n} añadido correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al guardar. Verifica los permisos de Editor en el Excel.")
                else:
                    st.warning("El nombre es obligatorio.")
    
    if not df_p.empty:
        st.dataframe(df_p[['nombre', 'tipo', 'precio', 'stock']], use_container_width=True, hide_index=True)

# --- MÓDULO 5: GESTIÓN CLIENTES ---
elif menu == "🏢 Gestión Clientes":
    st.title("🏢 Base de Datos de Clientes")
    df_c = cargar_datos("clientes")
    
    with st.form("form_cli"):
        nombre_c = st.text_input("Nombre del Cliente o Empresa")
        if st.form_submit_button("Registrar Cliente"):
            if nombre_c:
                nueva_c = pd.DataFrame([{"empresa": nombre_c}])
                df_res_c = pd.concat([df_c, nueva_c], ignore_index=True) if not df_c.empty else nueva_c
                try:
                    conn.update(worksheet="clientes", data=df_res_c)
                    st.success("✅ Cliente guardado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            
    if not df_c.empty:
        st.table(df_c)
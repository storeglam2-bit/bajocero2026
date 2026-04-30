import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Bajo Cero - Gestión Pro",
    page_icon="❄️",
    layout="wide"
)

# --- CONEXIÓN A GOOGLE SHEETS ---
# Utiliza la Service Account configurada en tus Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    try:
        # ttl=0 fuerza la lectura en tiempo real de la nube
        df = conn.read(worksheet=pestana, ttl=0)
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"Error al conectar con la pestaña '{pestana}': {e}")
        return pd.DataFrame()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    # Solución al MediaFileStorageError: Intentar cargar imagen, si falla mostrar texto
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
        # Limpieza de datos: asegurar que sean números enteros sin decimales
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Sabores Activos", len(df_p))
        c2.metric("Total Líquidos (3L)", int(df_p['stock'].sum()))
        
        valor_total = (df_p['stock'] * df_p['precio']).sum()
        c3.metric("Valor Inventario", f"$ {int(valor_total):,}".replace(",", "."))
        
        st.markdown("---")
        
        # Alertas de Stock Bajo
        bajos = df_p[df_p['stock'] <= 4]
        if not bajos.empty:
            st.error(f"🚨 **ALERTA:** {len(bajos)} sabores necesitan producción inmediata.")
        
        # Tabla de Existencias
        st.subheader("📦 Estado del Stock")
        st.dataframe(
            df_p[['nombre', 'tipo', 'stock', 'precio']].style.format({
                "precio": lambda x: f"$ {int(x):,}".replace(",", "."),
                "stock": "{:d}"
            }),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No se encontraron datos. Revisa la conexión con Google Sheets.")

# --- MÓDULO 4: CATÁLOGO PRODUCTOS (Solución a errores de escritura) ---
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
                    # Crear nueva fila con formatos forzados para evitar el error 400/404
                    nueva_f = pd.DataFrame([{
                        "nombre": str(n), 
                        "color": "#000", 
                        "tipo": str(t), 
                        "precio": int(p), 
                        "stock": 0
                    }])
                    
                    # Definir df_res correctamente para evitar NameError
                    df_res = pd.concat([df_p, nueva_f], ignore_index=True) if not df_p.empty else nueva_f
                    
                    try:
                        # Guardar en la hoja "productos"
                        conn.update(worksheet="productos", data=df_res)
                        st.success(f"✅ {n} guardado con éxito.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error de permisos: Asegúrate de que la Service Account sea Editor.")
                else:
                    st.warning("El nombre es obligatorio.")
    
    if not df_p.empty:
        st.dataframe(df_p[['nombre', 'tipo', 'precio', 'stock']], use_container_width=True, hide_index=True)

# --- MÓDULO 3: ENTRADA PRODUCCIÓN ---
elif menu == "📥 Entrada Producción":
    st.title("📥 Ingreso de Mercancía")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        with st.form("form_entrada"):
            prod_sel = st.selectbox("Sabor producido", df_p['nombre'].tolist())
            cantidad = st.number_input("Cantidad de botellas nuevas", min_value=1, step=1)
            
            if st.form_submit_button("Actualizar Inventario"):
                idx = df_p[df_p['nombre'] == prod_sel].index[0]
                df_p.at[idx, 'stock'] = int(df_p.at[idx, 'stock']) + cantidad
                
                try:
                    conn.update(worksheet="productos", data=df_p)
                    st.success("✅ Stock actualizado en la nube.")
                    st.rerun()
                except:
                    st.error("Error al actualizar. Verifica los permisos de Editor.")

# --- MÓDULO 5: GESTIÓN CLIENTES ---
elif menu == "🏢 Gestión Clientes":
    st.title("🏢 Base de Clientes")
    df_c = cargar_datos("clientes")
    
    with st.form("form_cli"):
        nombre_c = st.text_input("Nombre de la Empresa / Cliente")
        if st.form_submit_button("Registrar Cliente"):
            nueva_c = pd.DataFrame([{"empresa": nombre_c}])
            df_res_c = pd.concat([df_c, nueva_c], ignore_index=True) if not df_c.empty else nueva_c
            conn.update(worksheet="clientes", data=df_res_c)
            st.success("Cliente guardado.")
            st.rerun()
            
    if not df_c.empty:
        st.table(df_c)
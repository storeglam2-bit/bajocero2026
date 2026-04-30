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

# --- MÓDULO 1: PANEL PRINCIPAL (TAMAÑO ORIGINAL CON COLORES REFINADOS) ---
if menu == "📊 Panel Principal":
    st.title("📊 Resumen de Inventario")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # Asegurar datos numéricos
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
        
        # Cálculos
        df_sin = df_p[df_p['tipo'].str.contains("Sin", case=False, na=False)]
        df_con = df_p[df_p['tipo'].str.contains("Con", case=False, na=False)]
        
        total_stock_sin = int(df_sin['stock'].sum())
        total_stock_con = int(df_con['stock'].sum())
        valor_inventario = int((df_p['stock'] * df_p['precio']).sum())

        # --- MÉTRICAS SUPERIORES ---
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 Valor Total", f"$ {valor_inventario:,}".replace(",", "."))
        m2.metric("🥤 Total Sin Licor", f"{total_stock_sin} und")
        m3.metric("🍸 Total Con Licor", f"{total_stock_con} und")
        
        # --- SECCIÓN DE ALERTAS (TAMAÑO AMPLIO - COLORES ELEGANTES) ---
        df_alerta = df_p[df_p['stock'] <= 4].sort_values('stock')
        
        if not df_alerta.empty:
            st.markdown("---")
            st.markdown("<h3 style='color: #ff4b4b; font-size: 20px;'>🚨 Disponibilidad Crítica</h3>", unsafe_allow_html=True)
            
            # Usamos 4 columnas para mantener el tamaño grande de las tarjetas
            cols_alerta = st.columns(4)
            
            for i, (_, fila) in enumerate(df_alerta.iterrows()):
                # Diseño: Fondo oscuro premium, borde coral, tamaño cómodo
                badge_html = f"""
                <div style="
                    background-color: #1a1a1a; 
                    color: #ffffff; 
                    padding: 20px; 
                    border-radius: 12px; 
                    border: 1px solid #ff4b4b;
                    margin-bottom: 15px;
                    text-align: center;
                    box-shadow: 2px 2px 10px rgba(0,0,0,0.5);">
                    <p style="margin: 0; font-size: 18px; font-weight: bold; color: #ff4b4b;">{fila['nombre']}</p>
                    <p style="margin: 5px 0 0 0; font-size: 16px; opacity: 0.9;">{fila['stock']} unidades restantes</p>
                    <p style="margin: 0; font-size: 12px; opacity: 0.6; text-transform: uppercase;">{fila['tipo']}</p>
                </div>
                """
                with cols_alerta[i % 4]:
                    st.markdown(badge_html, unsafe_allow_html=True)
        
        st.markdown("---")

        # --- TABLAS DETALLADAS ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥤 Detalle Sin Licor")
            st.dataframe(df_sin[['nombre', 'stock', 'precio']], use_container_width=True, hide_index=True)

        with col2:
            st.subheader("🍸 Detalle Con Licor")
            st.dataframe(df_con[['nombre', 'stock', 'precio']], use_container_width=True, hide_index=True)
            
    else:
        st.info("No hay productos registrados.")

# --- MÓDULO 3: ENTRADA PRODUCCIÓN (CORREGIDO) ---
elif menu == "📥 Entrada Producción":
    st.title("📥 Ingreso de Producción")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # 1. CREAMOS UNA IDENTIFICACIÓN ÚNICA (Nombre + Tipo)
        # Esto evita que 'Fresa' (Sin Licor) se sume en 'Fresa' (Con Licor)
        df_p['id_unico'] = df_p['nombre'].astype(str) + " - " + df_p['tipo'].astype(str)
        
        with st.form("form_entrada"):
            st.info("Selecciona el sabor específico para asegurar que el stock se sume correctamente.")
            
            # El selector ahora muestra el nombre y el tipo claramente
            seleccion = st.selectbox(
                "Sabor y Categoría", 
                options=df_p['id_unico'].tolist()
            )
            
            cantidad = st.number_input("Botellas nuevas producidas", min_value=1, step=1)
            
            if st.form_submit_button("Actualizar Inventario"):
                # 2. LOCALIZAMOS LA FILA EXACTA usando el ID ÚNICO
                idx = df_p[df_p['id_unico'] == seleccion].index[0]
                
                # Realizamos la suma
                stock_actual = int(df_p.at[idx, 'stock'])
                df_p.at[idx, 'stock'] = stock_actual + cantidad
                
                # 3. LIMPIEZA ANTES DE GUARDAR
                # Eliminamos la columna temporal 'id_unico' para no ensuciar el Excel
                df_para_enviar = df_p.drop(columns=['id_unico'])
                
                try:
                    conn.update(worksheet="productos", data=df_para_enviar)
                    st.success(f"✅ Se sumaron {cantidad} unidades a: {seleccion}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al conectar con Google Sheets: {e}")
    else:
        st.warning("⚠️ No hay productos en el catálogo para actualizar.")

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
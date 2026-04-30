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

# --- MÓDULO 1: PANEL PRINCIPAL (VERSIÓN PROFESIONAL) ---
if menu == "📊 Panel Principal":
    st.title("📊 Resumen de Inventario")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # Asegurar datos numéricos
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
        
        # Cálculos de inventario
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
        
        # --- SECCIÓN DE ALERTAS ESTÉTICAS ---
        df_alerta = df_p[df_p['stock'] <= 4].sort_values('stock')
        
        if not df_alerta.empty:
            st.markdown("#### 🚨 Disponibilidad Crítica")
            # Creamos una fila de "badges" o etiquetas pequeñas
            cols_alerta = st.columns(len(df_alerta) if len(df_alerta) <= 4 else 4)
            
            for i, (_, fila) in enumerate(df_alerta.iterrows()):
                # Usamos HTML para un diseño tipo "píldora" profesional
                badge_html = f"""
                <div style="
                    background-color: #4a1111; 
                    color: #ff4b4b; 
                    padding: 8px 12px; 
                    border-radius: 10px; 
                    border: 1px solid #ff4b4b;
                    margin-bottom: 10px;
                    font-size: 14px;
                    text-align: center;">
                    <strong>{fila['nombre']}</strong><br>
                    {fila['stock']} unidades
                </div>
                """
                with cols_alerta[i % 4]:
                    st.markdown(badge_html, unsafe_allow_html=True)
        
        st.markdown("---")

        # --- TABLAS DETALLADAS ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥤 Detalle Sin Licor")
            st.metric("Variedades", len(df_sin))
            st.dataframe(df_sin[['nombre', 'stock', 'precio']], use_container_width=True, hide_index=True)

        with col2:
            st.subheader("🍸 Detalle Con Licor")
            st.metric("Variedades", len(df_con))
            st.dataframe(df_con[['nombre', 'stock', 'precio']], use_container_width=True, hide_index=True)
            
    else:
        st.info("No hay productos registrados.")

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
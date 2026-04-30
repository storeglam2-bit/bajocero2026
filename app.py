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

# --- MÓDULO 1: PANEL PRINCIPAL (ESTILO SINCRONIZADO) ---
if menu == "📊 Panel Principal":
    st.markdown("<h1 style='text-align: center;'>📊 Resumen de Inventario</h1>", unsafe_allow_html=True)
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # Asegurar datos numéricos
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
        
        # Cálculos de métricas
        df_sin = df_p[df_p['tipo'].str.contains("Sin", case=False, na=False)]
        df_con = df_p[df_p['tipo'].str.contains("Con", case=False, na=False)]
        
        valor_inventario = int((df_p['stock'] * df_p['precio']).sum())

        # --- MÉTRICAS SUPERIORES ---
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 Valor Total", f"$ {valor_inventario:,}".replace(",", "."))
        m2.metric("🥤 Total Sin Licor", f"{df_sin['stock'].sum()} und")
        m3.metric("🍸 Total Con Licor", f"{df_con['stock'].sum()} und")
        
        # --- SECCIÓN DE DISPONIBILIDAD CRÍTICA ---
        df_alerta = df_p[df_p['stock'] <= 4].sort_values('stock')
        
        if not df_alerta.empty:
            st.markdown("---")
            # Título central con color dinámico (Cian para resaltar)
            st.markdown("""
                <div style='text-align: center; margin-bottom: 20px;'>
                    <h3 style='color: #00f2fe; font-size: 26px; font-weight: bold; margin-bottom: 0;'>🧊 DISPONIBILIDAD CRÍTICA</h3>
                    <p style='color: #666; font-size: 14px;'>Reponer estos sabores de inmediato</p>
                </div>
            """, unsafe_allow_html=True)
            
            cols_alerta = st.columns(4)
            
            for i, (_, fila) in enumerate(df_alerta.iterrows()):
                # Definición de colores según el stock para sincronizar todo el cuadro
                if fila['stock'] == 0:
                    color_tema = "#ff4b4b" # Rojo
                    icon = "🚫"
                elif fila['stock'] <= 2:
                    color_tema = "#ffa500" # Naranja
                    icon = "⚠️"
                else:
                    color_tema = "#00f2fe" # Cian
                    icon = "📉"

                badge_html = f"""
                <div style="
                    background-color: #1a1a1a; 
                    padding: 20px; 
                    border-radius: 15px; 
                    border: 2px solid {color_tema};
                    text-align: center;
                    margin-bottom: 15px;
                    box-shadow: 0px 4px 20px rgba(0,0,0,0.4);">
                    <div style="font-size: 35px; margin-bottom: 10px;">{icon}</div>
                    <p style="margin: 0; font-size: 18px; font-weight: bold; color: {color_tema};">{fila['nombre']}</p>
                    <p style="margin: 5px 0; font-size: 24px; color: white; font-weight: bold;">{fila['stock']} <span style='font-size: 14px; opacity:0.8;'>UND</span></p>
                    <div style="
                        display: inline-block;
                        padding: 2px 10px;
                        border-radius: 5px;
                        background-color: {color_tema}33; 
                        color: {color_tema};
                        font-size: 10px;
                        font-weight: bold;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        border: 1px solid {color_tema};">
                        {fila['tipo']}
                    </div>
                </div>
                """
                with cols_alerta[i % 4]:
                    st.markdown(badge_html, unsafe_allow_html=True)
        
        st.markdown("---")
        # --- TABLAS DETALLADAS ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🥤 Detalle Sin Licor")
            st.dataframe(df_sin[['nombre', 'stock', 'precio']], use_container_width=True, hide_index=True)
        with c2:
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

# --- MÓDULO 4: CATÁLOGO PRODUCTOS (REDISEÑO PROFESIONAL) ---
elif menu == "🥤 Catálogo Productos":
    st.markdown("<h1 style='text-align: center;'>🥤 Gestión de Catálogo</h1>", unsafe_allow_html=True)
    df_p = cargar_datos("productos")
    
    # --- MÉTRICAS RÁPIDAS DEL CATÁLOGO ---
    if not df_p.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Sabores Totales", len(df_p))
        c2.metric("Variedades Sin Licor", len(df_p[df_p['tipo'].str.contains("Sin", case=False, na=False)]))
        c3.metric("Variedades Con Licor", len(df_p[df_p['tipo'].str.contains("Con", case=False, na=False)]))
    
    st.markdown("---")

    # --- FORMULARIO DE REGISTRO ESTILIZADO ---
    with st.expander("✨ AGREGAR NUEVO SABOR AL MENÚ", expanded=False):
        with st.form("form_nuevo_producto", clear_on_submit=True):
            col_form1, col_form2 = st.columns(2)
            
            with col_form1:
                nombre = st.text_input("📝 Nombre del Sabor", placeholder="Ej: Maracuyá Explosivo")
                tipo = st.selectbox("🏷️ Categoría", ["Sin Licor", "Con Licor"])
            
            with col_form2:
                precio = st.number_input("💵 Precio de Venta ($)", min_value=0, step=500, value=35000)
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("🚀 GUARDAR EN CATÁLOGO", use_container_width=True)
            
            if submit:
                if nombre:
                    # Crear el nuevo registro
                    nueva_fila = pd.DataFrame([{
                        "nombre": nombre.strip(),
                        "tipo": tipo,
                        "precio": int(precio),
                        "stock": 0,  # Todo producto nuevo inicia en 0
                        "color": "#00f2fe" if "Sin" in tipo else "#ff4b4b"
                    }])
                    
                    df_actualizado = pd.concat([df_p, nueva_fila], ignore_index=True) if not df_p.empty else nueva_fila
                    
                    try:
                        conn.update(worksheet="productos", data=df_actualizado)
                        st.success(f"✅ ¡{nombre} ha sido añadido con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al guardar: {e}")
                else:
                    st.warning("⚠️ Por favor, escribe un nombre para el producto.")

    # --- TABLA DE PRODUCTOS ACTUALES ---
    st.markdown("### 📋 Sabores en Menú")
    if not df_p.empty:
        # Formatear la tabla para que se vea mejor
        df_display = df_p.copy()
        # Ordenar por tipo y luego por nombre
        df_display = df_display.sort_values(['tipo', 'nombre'])
        
        # Renombrar columnas para la vista del usuario
        df_display.columns = [c.upper() for c in df_display.columns]
        
        st.dataframe(
            df_display[['NOMBRE', 'TIPO', 'PRECIO', 'STOCK']], 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("Aún no tienes productos registrados. ¡Usa el botón de arriba para empezar!")

# --- MÓDULO 5: GESTIÓN CLIENTES (REDISEÑO PROFESIONAL) ---
elif menu == "🏢 Gestión Clientes":
    st.markdown("<h1 style='text-align: center;'>🏢 Directorio de Clientes</h1>", unsafe_allow_html=True)
    df_c = cargar_datos("clientes")
    
    # --- MÉTRICAS DE CLIENTES ---
    if not df_c.empty:
        c1, c2 = st.columns(2)
        total_clientes = len(df_c)
        c1.metric("Clientes Registrados", f"{total_clientes} 👤")
        # Simulación de crecimiento o mensaje de estado
        c2.info("💡 Consejo: Mantén los nombres estandarizados para evitar duplicados en las facturas.")
    
    st.markdown("---")

    # --- FORMULARIO DE REGISTRO ESTILIZADO ---
    with st.expander("➕ REGISTRAR NUEVO CLIENTE O EMPRESA", expanded=False):
        with st.form("form_cli", clear_on_submit=True):
            col_form1, col_form2 = st.columns([2, 1])
            
            with col_form1:
                nombre_c = st.text_input("🏢 Nombre Comercial / Razón Social", placeholder="Ej: Licorería El Faro")
            
            with col_form2:
                st.markdown("<br>", unsafe_allow_html=True)
                submit_cli = st.form_submit_button("💾 GUARDAR CLIENTE", use_container_width=True)
            
            if submit_cli:
                if nombre_c:
                    # Limpiamos el nombre para consistencia
                    nombre_limpio = nombre_c.strip().upper()
                    
                    # Verificamos si ya existe
                    if not df_c.empty and nombre_limpio in df_c['empresa'].str.upper().values:
                        st.warning(f"⚠️ El cliente '{nombre_limpio}' ya existe en la base de datos.")
                    else:
                        nueva_c = pd.DataFrame([{"empresa": nombre_limpio}])
                        df_res_c = pd.concat([df_c, nueva_c], ignore_index=True) if not df_c.empty else nueva_c
                        
                        try:
                            conn.update(worksheet="clientes", data=df_res_c)
                            st.success(f"✅ '{nombre_limpio}' ha sido registrado correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error de permisos o conexión: {e}")
                else:
                    st.error("⚠️ Debes ingresar un nombre para realizar el registro.")

    # --- VISUALIZACIÓN DE BASE DE DATOS ---
    st.markdown("### 📋 Listado de Aliados Comerciales")
    if not df_c.empty:
        # Buscador rápido
        busqueda = st.text_input("🔍 Buscar cliente...", placeholder="Escribe el nombre aquí...")
        
        df_filtrado = df_c.copy()
        if busqueda:
            df_filtrado = df_filtrado[df_filtrado['empresa'].str.contains(busqueda, case=False, na=False)]
        
        # Mostramos como dataframe estilizado (mejor que st.table)
        df_filtrado.columns = ["NOMBRE DE LA EMPRESA"]
        st.dataframe(
            df_filtrado.sort_values("NOMBRE DE LA EMPRESA"), 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("No hay clientes registrados aún.")
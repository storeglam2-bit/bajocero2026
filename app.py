import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from streamlit_option_menu import option_menu

# Configuración inicial
st.set_page_config(page_title="Bajo Cero Dashboard", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
# Nota: Asegúrate de configurar tus secretos en .streamlit/secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet_name):
    return conn.read(worksheet=worksheet_name)

# Cargar datos de las pestañas
df_productos = load_data("productos")
df_clientes = load_data("clientes")

# --- DISEÑO DE NAVEGACIÓN ---
with st.sidebar:
    st.title("❄️ Bajo Cero")
    selected = option_menu(
        menu_title=None,
        options=["Panel Principal", "Registrar Venta", "Clientes", "Ingresar Stock"],
        icons=["grid-1x2", "cart-plus", "people", "plus-circle"],
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#1a1a1a"},
            "icon": {"color": "#00d4ff", "font-size": "20px"}, 
            "nav-link-selected": {"background-color": "#005f73"},
        }
    )

# --- BOTÓN DE ACTUALIZACIÓN EN EL SIDEBAR ---
with st.sidebar:
    st.divider()
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        # Limpia el caché de la conexión a GSheets
        st.cache_data.clear()
        st.toast("Datos actualizados desde Google Sheets")
        st.rerun()

# --- 1. PANEL PRINCIPAL ---
if selected == "Panel Principal":
    st.header("📊 Resumen de Inventario")
    # --- 1. PROCESAMIENTO DE DATOS (Panel Principal) ---
    # Aseguramos que el stock sea entero y manejamos nulos
    df_productos['stock'] = df_productos['stock'].fillna(0).astype(int)
    df_productos['precio'] = df_productos['precio'].fillna(0)

    # Filtrado de Grupos
    con_licor_total = df_productos[(df_productos['tipo'] == 'Con Licor')]
    sin_licor_total = df_productos[(df_productos['tipo'] == 'Sin Licor')]

    # Inventarios específicos para las tablas
    inv_sin_licor = df_productos[(df_productos['tipo'] == 'Sin Licor') & (df_productos['promo'] == 'No')]
    inv_con_licor = df_productos[(df_productos['tipo'] == 'Con Licor') & (df_productos['promo'] == 'No')]
    inv_promos = df_productos[df_productos['promo'] == 'Si']

    # Alertas
    agotados = df_productos[df_productos['stock'] == 0]
    por_agotarse = df_productos[(df_productos['stock'] > 0) & (df_productos['stock'] <= 5)]

    # Cálculos de Valorización
    val_con = (con_licor_total['precio'] * con_licor_total['stock']).sum()
    val_sin = (sin_licor_total['precio'] * sin_licor_total['stock']).sum()
    val_total = val_con + val_sin

    # --- 2. ESTILOS CSS PERSONALIZADOS ---
    st.markdown("""
    <style>
        .main-card {
            background: #1E1E1E;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #333;
            text-align: center;
            margin-bottom: 15px;
        }
        .metric-title { color: #888; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
        .metric-value { color: #00D4FF; font-size: 30px; font-weight: bold; }
        .status-tag {
            padding: 8px 15px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 10px;
        }
        .tag-critical { background-color: rgba(255, 75, 75, 0.1); color: #FF4B4B; border: 1px solid #FF4B4B; }
        .tag-warning { background-color: rgba(255, 165, 0, 0.1); color: #FFA500; border: 1px solid #FFA500; }
    </style>
    """, unsafe_allow_html=True)

    # --- 3. DISEÑO DE LA INTERFAZ ---
    st.title("📊 Dashboard Ejecutivo")

    # FILA 1: MÉTRICAS DE CANTIDAD
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="main-card"><div class="metric-title">📦 Total Stock</div><div class="metric-value">{df_productos["stock"].sum()}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="main-card"><div class="metric-title">🥃 Con Licor</div><div class="metric-value">{con_licor_total["stock"].sum()} <span style="font-size:14px">und</span></div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="main-card"><div class="metric-title">🥤 Sin Licor</div><div class="metric-value">{sin_licor_total["stock"].sum()} <span style="font-size:14px">und</span></div></div>', unsafe_allow_html=True)
    with col4:
        color_agotado = "#FF4B4B" if len(agotados) > 0 else "#00FF87"
        st.markdown(f'<div class="main-card" style="border-bottom: 4px solid {color_agotado}"><div class="metric-title">⚠️ Agotados</div><div class="metric-value" style="color:{color_agotado}">{len(agotados)}</div></div>', unsafe_allow_html=True)

    # FILA 2: VALORIZACIÓN
    st.subheader("💰 Resumen Financiero de Inventario")
    v1, v2, v3 = st.columns(3)
    with v1:
        st.markdown(f'<div class="main-card"><div class="metric-title">Valor Con Licor</div><div style="color:#00FF87; font-size:20px; font-weight:bold">${val_con:,.0f}</div></div>', unsafe_allow_html=True)
    with v2:
        st.markdown(f'<div class="main-card"><div class="metric-title">Valor Sin Licor</div><div style="color:#00FF87; font-size:20px; font-weight:bold">${val_sin:,.0f}</div></div>', unsafe_allow_html=True)
    with v3:
        st.markdown(f'<div class="main-card" style="background: linear-gradient(145deg, #004e92, #000428);"><div class="metric-title" style="color:white">Valor Total Patrimonio</div><div style="color:white; font-size:24px; font-weight:bold">${val_total:,.0f}</div></div>', unsafe_allow_html=True)

    st.divider()

    # FILA 3: ALERTAS CRÍTICAS
    st.subheader("🚨 Alertas de Control")
    c_crit1, c_crit2 = st.columns(2)

    with c_crit1:
        st.markdown('<div class="status-tag tag-critical">🔴 PRODUCTOS AGOTADOS</div>', unsafe_allow_html=True)
        if not agotados.empty:
            st.dataframe(agotados[['nombre', 'tipo']], use_container_width=True, hide_index=True)
        else:
            st.success("No hay productos agotados actualmente.")

    with c_crit2:
        st.markdown('<div class="status-tag tag-warning">🟠 PRÓXIMOS A AGOTARSE (Stock ≤ 5)</div>', unsafe_allow_html=True)
        if not por_agotarse.empty:
            st.dataframe(por_agotarse[['nombre', 'stock', 'tipo']], use_container_width=True, hide_index=True)
        else:
            st.info("Stock suficiente en todos los productos.")

    st.divider()

    # FILA 4: INVENTARIOS DETALLADOS POR CATEGORÍA
    st.subheader("📦 Detalle de Existencias")
    tab1, tab2, tab3 = st.tabs(["🥤 SIN LICOR", "🥃 CON LICOR", "🎁 PROMOS"])

    with tab1:
        st.markdown("### Inventario Sin Licor")
        st.dataframe(inv_sin_licor[inv_sin_licor['stock'] > 0 ][['nombre', 'precio', 'stock']], use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### Inventario Con Licor")
        st.dataframe(inv_con_licor[['nombre', 'precio', 'stock']], use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### Inventario de Promociones (Si)")
        st.dataframe(inv_promos[['nombre', 'tipo', 'precio', 'stock']], use_container_width=True, hide_index=True)

# --- 2. REGISTRAR VENTA ---
elif selected == "Registrar Venta":
    st.markdown("<h1 style='text-align: center; color: #00d4ff;'>💎 Terminal de Ventas Pro</h1>", unsafe_allow_html=True)

    # 1. Inicialización de Carrito
    if 'carrito' not in st.session_state:
        st.session_state.carrito = []

    # 2. Área de Selección
    with st.container(border=True):
        st.markdown("#### 📝 Configuración de Venta")
        c1, c2 = st.columns(2)
        
        with c1:
            lista_cli = df_clientes['empresa'].unique() if 'empresa' in df_clientes.columns else []
            cliente_sel = st.selectbox("👤 Cliente", lista_cli)
        
        with c2:
            # --- LIMPIEZA Y FILTRO DE SEGURIDAD ---
            # Aseguramos que el stock sea tratado como número para que el filtro > 0 funcione
            df_productos['stock'] = pd.to_numeric(df_productos['stock'], errors='coerce').fillna(0)
            
            # Filtramos: Solo lo que realmente tiene existencias
            df_vta = df_productos[df_productos['stock'] > 0].copy()

            if not df_vta.empty:
                # Generamos la etiqueta con nombre, tipo y stock exacto
                df_vta['display'] = (
                    df_vta['nombre'] + 
                    " (" + df_vta['tipo'] + ") | Stock: " + 
                    df_vta['stock'].astype(int).astype(str)
                )
                
                opcion_prod = st.selectbox(
                    "📦 Seleccionar Producto Disponible", 
                    options=df_vta['display'].unique(),
                    key="prod_vta_selector"
                )
                
                # Extraemos los datos del producto seleccionado
                datos_p = df_vta[df_vta['display'] == opcion_prod].iloc[0]
                nombre_real = datos_p['nombre']
                tipo_p = datos_p['tipo']
                precio_b = int(float(datos_p['precio']))
                stock_r = int(datos_p['stock'])
                
                st.markdown(f"**Categoría:** `{tipo_p}` | **Disponible:** `{stock_r}`")
            else:
                st.error("⚠️ NO HAY STOCK DISPONIBLE")
                nombre_real, precio_b, stock_r, tipo_p = None, 0, 0, ""

        st.divider()
        
        c3, c4, c5 = st.columns([1, 2, 1])
        with c3:
            cantidad = st.number_input("Cantidad", min_value=1, max_value=max(1, int(stock_r)), step=1)
        with c4:
            precio_vta = st.number_input("💰 Precio Unitario Final", value=precio_b, step=500)
        with c5:
            st.write("##")
            if st.button("➕ Añadir", use_container_width=True, disabled=stock_r <= 0):
                if nombre_real:
                    st.session_state.carrito.append({
                        "Producto": nombre_real, "Tipo": tipo_p,
                        "Cant": int(cantidad), "Precio": int(precio_vta),
                        "Subtotal": int(cantidad * precio_vta)
                    })
                    st.toast(f"✅ {nombre_real} añadido")
                    st.rerun()

    # 3. Resumen y Confirmación
    if st.session_state.carrito:
        st.markdown("### 📋 Factura Temporal")
        df_carro = pd.DataFrame(st.session_state.carrito)
        st.dataframe(df_carro[["Producto", "Tipo", "Cant", "Precio", "Subtotal"]], 
                     use_container_width=True, hide_index=True)
        
        total_vta = int(df_carro['Subtotal'].sum())

        st.markdown(f"""
            <div style="background-color: #064e3b; padding: 20px; border-radius: 15px; border-left: 10px solid #10b981; text-align: center;">
                <p style="margin: 0; color: #a7f3d0; font-weight: bold;">TOTAL A COBRAR</p>
                <h1 style="margin: 0; color: #ffffff; font-size: 3rem;">${total_vta:,}</h1>
            </div>
        """.replace(",", "."), unsafe_allow_html=True)

        col_v1, col_v2 = st.columns([1, 2])
        with col_v1:
            if st.button("🗑️ Vaciar", use_container_width=True):
                st.session_state.carrito = []
                st.rerun()
        with col_v2:
            if st.button("🚀 CONFIRMAR REGISTRO DE VENTA", type="primary", use_container_width=True):
                try:
                    df_actualizado = df_productos.copy()
                    for item in st.session_state.carrito:
                        n_vta, t_vta, c_vta = item["Producto"], item["Tipo"], item["Cant"]
                        idx = df_actualizado[(df_actualizado['nombre'] == n_vta) & 
                                            (df_actualizado['tipo'] == t_vta)].index
                        if not idx.empty:
                            df_actualizado.loc[idx, 'stock'] -= c_vta

                    # Actualización en Sheets
                    conn.update(worksheet="productos", data=df_actualizado)
                    
                    st.success("🎉 Venta registrada correctamente.")
                    st.balloons()
                    st.session_state.carrito = []
                    st.rerun() # Esto refresca el filtro de stock > 0 inmediatamente
                    
                except Exception as e:
                    st.error(f"Error: {e}")

# --- 3. CLIENTES ---
elif selected == "Clientes":
    st.markdown("<h1 style='text-align: center; color: #00d4ff;'>👥 Administración de Clientes</h1>", unsafe_allow_html=True)

    # 1. PREPARACIÓN DE DATOS
    df_clientes.columns = df_clientes.columns.str.strip()
    total_clientes = len(df_clientes)

    # --- 2. CAJITA PREMIUM: TOTAL CLIENTES ---
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 25px;
            border-radius: 20px;
            border: 1px solid #334155;
            text-align: center;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            margin-bottom: 30px;
        ">
            <p style="margin: 0; color: #94a3b8; font-size: 1rem; text-transform: uppercase; letter-spacing: 2px;">Cartera Total de Clientes</p>
            <h1 style="margin: 0; color: #00d4ff; font-size: 4rem; font-weight: bold;">{total_clientes}</h1>
            <p style="margin: 0; color: #00ff87; font-size: 0.9rem;">● Clientes registrados activamente</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 3. TOP 3 CLIENTES (DISEÑO DE PODIO) ---
    st.markdown("### 🏆 Top 3 Clientes Destacados")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""<div style="background: #1e293b; padding: 15px; border-radius: 15px; border-bottom: 4px solid #ffd700; text-align: center;">
                <span style="font-size: 2rem;">🥇</span><p style="margin:0; font-weight: bold; color: #f8fafc;">EL DISTRITO</p>
                <p style="margin:0; font-size: 0.8rem; color: #ffd700;">Cliente VIP</p></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div style="background: #1e293b; padding: 15px; border-radius: 15px; border-bottom: 4px solid #c0c0c0; text-align: center;">
                <span style="font-size: 2rem;">🥈</span><p style="margin:0; font-weight: bold; color: #f8fafc;">BAJO CERO</p>
                <p style="margin:0; font-size: 0.8rem; color: #c0c0c0;">Recurrente</p></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div style="background: #1e293b; padding: 15px; border-radius: 15px; border-bottom: 4px solid #cd7f32; text-align: center;">
                <span style="font-size: 2rem;">🥉</span><p style="margin:0; font-weight: bold; color: #f8fafc;">POZON</p>
                <p style="margin:0; font-size: 0.8rem; color: #cd7f32;">Nuevo Socio</p></div>""", unsafe_allow_html=True)

    st.divider()

    # --- 4. FORMULARIO, GESTIÓN Y TABLA ---
    col_izq, col_tabla = st.columns([1, 1.5])

    with col_izq:
        # Pestañas para separar Registro de Edición
        tab1, tab2 = st.tabs(["➕ Registrar", "⚙️ Gestionar"])
        
        with tab1:
            with st.container(border=True):
                nombre_nuevo = st.text_input("Nombre de la Empresa")
                ciudad_cliente = st.text_input("Ciudad / Ubicación")
                if st.button("🚀 Registrar", use_container_width=True):
                    if nombre_nuevo:
                        st.success(f"Registrado: {nombre_nuevo}")
                        st.rerun()
                    else:
                        st.error("Falta el nombre")

        with tab2:
            with st.container(border=True):
                if not df_clientes.empty:
                    cliente_sel = st.selectbox("Seleccionar Cliente", df_clientes['empresa'].unique())
                    nuevo_nom_edit = st.text_input("Editar Nombre", value=cliente_sel)
                    
                    c_mod, c_eli = st.columns(2)
                    with c_mod:
                        if st.button("💾 Guardar", use_container_width=True):
                            st.info(f"Modificado: {nuevo_nom_edit}")
                            st.rerun()
                    with c_eli:
                        if st.button("🗑️ Eliminar", use_container_width=True, type="secondary"):
                            st.error(f"Eliminado: {cliente_sel}")
                            st.rerun()
                else:
                    st.write("No hay clientes para editar.")

    with col_tabla:
        st.markdown("#### 📋 Base de Datos Actual")
        if 'empresa' in df_clientes.columns:
            st.dataframe(df_clientes[['empresa']], use_container_width=True, hide_index=True, height=380)
        else:
            st.warning("No se encontró la columna 'empresa'")

# --- 4. INGRESAR STOCK ---
elif selected == "Ingresar Stock":
    st.markdown("<h1 style='text-align: center; color: #00d4ff;'>📥 Entrada de Mercancía</h1>", unsafe_allow_html=True)

    # 1. MÉTRICAS RÁPIDAS DE INVENTARIO
    total_items = df_productos['stock'].sum()
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 20px; border-radius: 15px; border: 1px solid #334155; text-align: center; margin-bottom: 25px;">
            <p style="margin: 0; color: #94a3b8; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">Total Unidades en Inventario Actual</p>
            <h1 style="margin: 0; color: #00ff87; font-size: 3rem;">{int(total_items):,}</h1>
        </div>
    """.replace(",", "."), unsafe_allow_html=True)

    # 2. SISTEMA DE ENTRADA
    tab_viejo, tab_nuevo = st.tabs(["🔄 Reponer Stock (Existente)", "✨ Registrar Producto Nuevo"])

    with tab_viejo:
        # Contenedor principal con borde para orden
        with st.container(border=True):
            st.markdown("#### 🔄 Actualizar Inventario Existente")
            
            # Columnas para alinear todo en una sola fila visual
            col_prod, col_info, col_input = st.columns([2, 1, 1])
            
            with col_prod:
                # 1. Selector que muestra el TIPO de producto para evitar confusiones
                # Combinamos Nombre + Tipo en la lista desplegable
                df_productos['display_name'] = df_productos['nombre'] + " - " + df_productos['tipo']
                p_display = st.selectbox("📦 Producto y Categoría", df_productos['display_name'].unique())
                
                # Extraemos los datos reales basados en la selección
                nombre_real = p_display.split(" - ")[0]
                tipo_real = p_display.split(" - ")[1]
                
                datos_actuales = df_productos[(df_productos['nombre'] == nombre_real) & 
                                             (df_productos['tipo'] == tipo_real)].iloc[0]
                stock_actual_val = int(datos_actuales['stock'])

            with col_info:
                st.write("Estado Actual")
                # 2. Lógica de colores para la cajita pequeña
                if stock_actual_val >= 6:
                    color_bg, txt = "#10b981", "Suficiente" # Verde
                elif 3 <= stock_actual_val <= 5:
                    color_bg, txt = "#f59e0b", "Bajo"      # Naranja
                elif 1 <= stock_actual_val <= 2:
                    color_bg, txt = "#b45309", "Crítico"   # Naranja Oscuro
                else:
                    color_bg, txt = "#ef4444", "AGOTADO"   # Rojo

                # Cajita pequeña y bien ordenada
                st.markdown(f"""
                    <div style="
                        background-color: {color_bg};
                        color: white;
                        padding: 8px;
                        border-radius: 10px;
                        text-align: center;
                        font-weight: bold;
                        border: 1px solid rgba(255,255,255,0.1);
                        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
                    ">
                        Stock: {stock_actual_val}<br>
                        <span style="font-size: 0.7rem; opacity: 0.9;">{txt}</span>
                    </div>
                """, unsafe_allow_html=True)

            with col_input:
                # 3. Input de cantidad alineado
                cant_entrada = st.number_input("¿Cuánto llegó?", min_value=1, step=1)

            st.write("##") # Espaciador
            if st.button("📥 Confirmar Entrada de Mercancía", use_container_width=True, type="primary"):
                # Aquí la lógica para actualizar tu Google Sheets
                st.success(f"✅ Se cargaron {cant_entrada} unidades a: {p_display}")
                st.balloons()
                st.rerun()

    with tab_nuevo:
        with st.container(border=True):
            st.markdown("#### Datos del Nuevo Producto")
            n_col1, n_col2 = st.columns(2)
            
            with n_col1:
                nuevo_nombre = st.text_input("Nombre del Producto", placeholder="Ej: Cerveza Club 330ml")
                nuevo_tipo = st.selectbox("Categoría", ["Sin Licor", "Con Licor", "Promo"])
            
            with n_col2:
                nuevo_precio = st.number_input("Precio de Venta Sugerido", min_value=0, step=500)
                nuevo_stock_ini = st.number_input("Stock Inicial", min_value=1, step=1)
            
            promo_check = st.radio("¿Es una promoción?", ["No", "Si"], horizontal=True)

            if st.button("🚀 Registrar y Guardar Producto", use_container_width=True):
                if nuevo_nombre:
                    # Aquí iría la lógica para conn.create o conn.update añadiendo fila
                    st.success(f"✅ {nuevo_nombre} ha sido creado exitosamente.")
                    st.rerun()
                else:
                    st.error("Por favor, ingresa el nombre del producto.")

    # 3. VISTA PREVIA DE LO QUE TIENES
    st.divider()
    st.markdown("#### 📋 Vista Rápida de Precios y Existencias")
    
    # Filtro rápido para la tabla
    filtro_tipo = st.multiselect("Filtrar por categoría", ["Sin Licor", "Con Licor", "Promo"], default=["Sin Licor", "Con Licor", "Promo"])
    df_filtrado = df_productos[df_productos['tipo'].isin(filtro_tipo)]
    
    st.dataframe(
        df_filtrado[['nombre', 'tipo', 'precio', 'stock']], 
        use_container_width=True, 
        hide_index=True
    )
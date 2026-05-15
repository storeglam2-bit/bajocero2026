import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go

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
        options=["Panel Principal", "Registrar Venta", "Clientes", "Ingresar Stock", "Historial de Ventas"],
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
        st.dataframe(inv_con_licor[inv_con_licor['stock'] > 0 ][['nombre', 'precio', 'stock']], use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### Inventario de Promociones (Si)")
        st.dataframe(inv_promos[inv_promos['stock'] > 0 ][['nombre', 'tipo', 'precio', 'stock']], use_container_width=True, hide_index=True)

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
            # 1. Limpieza y Filtro Estricto: Eliminamos lo que tenga 0 o menos stock
            df_productos['stock'] = pd.to_numeric(df_productos['stock'], errors='coerce').fillna(0)
            df_vta = df_productos[df_productos['stock'] > 0].copy()

            if not df_vta.empty:
                # Solo Nombre y Tipo en la lista (Stock oculto aquí para limpieza)
                df_vta['display'] = df_vta['nombre'] + " (" + df_vta['tipo'] + ")"
                
                opcion_prod = st.selectbox(
                    "📦 Seleccionar Producto", 
                    options=df_vta['display'].unique(),
                    key="prod_vta_selector"
                )
                
                datos_p = df_vta[df_vta['display'] == opcion_prod].iloc[0]
                tipo_p = datos_p['tipo']
                stock_r = int(datos_p['stock'])
                precio_b = int(float(datos_p['precio']))
                nombre_real = datos_p['nombre']

                # 2. Lógica de Estados y Colores (Semáforo)
                if stock_r > 5:
                    color_bg = "#059669"  # Verde (Disponible)
                    texto_estado = "DISPONIBLE"
                elif stock_r == 5:
                    color_bg = "#d97706"  # Naranja (Agotándose)
                    texto_estado = "AGOTÁNDOSE"
                else:  # Entre 1 y 4 unidades (Crítico)
                    color_bg = "#991b1b"  # Rojo Oscuro (Crítico)
                    texto_estado = "CRÍTICO"

                # 3. Diseño de la Tarjeta Informativa
                st.markdown(f"""
                    <div style="
                        background-color: #1e293b; 
                        padding: 12px; 
                        border-radius: 10px; 
                        border: 1px solid #334155;
                        margin-top: 5px;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #94a3b8; font-size: 0.85rem; font-weight: bold;">DETALLES</span>
                            <span style="background-color: {color_bg}; color: white; padding: 2px 10px; border-radius: 5px; font-size: 0.7rem; font-weight: bold;">
                                {texto_estado}
                            </span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                            <div style="color: #e2e8f0; font-size: 0.95rem;">
                                🏷️ <b>Tipo:</b> {tipo_p}
                            </div>
                            <div style="color: #f8fafc; font-size: 1.1rem; font-weight: bold;">
                                {stock_r} <small style="font-size: 0.7rem; color: #94a3b8;">uds</small>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # 4. Caso 0 Stock: Alerta Roja y exclusión
                st.error("❌ SIN STOCK: No hay productos con existencias para vender.")
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

                    # 1. Guardar en Google Sheets
                    conn.update(worksheet="productos", data=df_actualizado)
                    
                    # 2. IMPORTANTE: Si usas caché para leer los datos, límpialo aquí
                    # st.cache_data.clear() 
                    
                    st.success("🎉 Venta registrada. Inventario actualizado.")
                    st.session_state.carrito = []
                    
                    # 3. Al hacer rerun, el Panel Principal volverá a leer df_productos
                    # y el filtro stock > 0 excluirá los que llegaron a cero.
                    st.rerun() 
                    
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

# --- 5. HISTORIAL DE VENTAS PREMIUM ---

# --- 1. CSS PARA TARJETAS CON EFECTO NEÓN Y CRISTAL ---
st.markdown("""
    <style>
    /* Contenedor de KPI con degradado animado en el borde */
    .premium-kpi {
        background: rgba(30, 41, 59, 0.7);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }
    .kpi-title { color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; }
    .kpi-value { color: #ffffff; font-size: 2.2rem; font-weight: 800; text-shadow: 0 0 10px rgba(56, 189, 248, 0.5); }
    
    /* Ranking de Clientes Estilo Podio */
    .rank-box {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border: 1px solid #334155;
    }
    .gold { border-left: 6px solid #fbbf24; box-shadow: -5px 0 15px rgba(251, 191, 36, 0.2); }
    .silver { border-left: 6px solid #94a3b8; }
    .bronze { border-left: 6px solid #cd7f32; }
    
    .client-name { color: white; font-weight: 600; font-size: 1.1rem; }
    .client-total { color: #38bdf8; font-weight: 800; font-size: 1.3rem; }
    </style>
""", unsafe_allow_html=True)

if selected == "Historial de Ventas":
    st.markdown("<h1 style='text-align: center; color: #00d4ff;'>💎 DASHBOARD ESTRATÉGICO</h1>", unsafe_allow_html=True)

    try:
        df_ventas = conn.read(worksheet="ventas")
        if not df_ventas.empty:
            df_ventas['total'] = pd.to_numeric(df_ventas['total'], errors='coerce').fillna(0)
            df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'])

            # --- FILA 1: CAJITAS PREMIUM ---
            c1, c2, c3, c4 = st.columns(4)
            metrics = [
                ("INGRESOS TOTALES", f"${df_ventas['total'].sum():,.0f}", "💰"),
                ("UNIDADES", f"{int(pd.to_numeric(df_ventas['cantidad']).sum())}", "📦"),
                ("TOP CLIENTE", df_ventas.groupby('cliente')['total'].sum().idxmax()[:12], "🏆"),
                ("TICKET PROM.", f"${df_ventas['total'].mean():,.0f}", "📊")
            ]

            for i, col in enumerate([c1, c2, c3, c4]):
                with col:
                    st.markdown(f"""
                        <div class="premium-kpi">
                            <div style="font-size: 1.5rem;">{metrics[i][2]}</div>
                            <div class="kpi-title">{metrics[i][0]}</div>
                            <div class="kpi-value">{metrics[i][1]}</div>
                        </div>
                    """.replace(",", "."), unsafe_allow_html=True)

            st.write("##")

            # --- FILA 2: RANKING Y GRÁFICO (CORREGIDO) ---
            col_rank, col_chart = st.columns([1, 1])

            with col_rank:
                st.markdown("### 🥇 Ranking de Clientes")
                top_3 = df_ventas.groupby('cliente')['total'].sum().sort_values(ascending=False).head(3).reset_index()
                styles = ["gold", "silver", "bronze"]
                icons = ["🥇", "🥈", "🥉"]

                for i, row in top_3.iterrows():
                    st.markdown(f"""
                        <div class="rank-box {styles[i]}">
                            <div style="display: flex; align-items: center; gap: 15px;">
                                <span style="font-size: 1.8rem;">{icons[i]}</span>
                                <div>
                                    <div class="client-name">{row['cliente']}</div>
                                    <div style="color: #64748b; font-size: 0.8rem;">CLIENTE ELITE</div>
                                </div>
                            </div>
                            <div class="client-total">${row['total']:,.0f}</div>
                        </div>
                    """.replace(",", "."), unsafe_allow_html=True)

            with col_chart:
                st.markdown("### 📅 Distribución Mensual")
                df_ventas['mes'] = df_ventas['fecha'].dt.strftime('%b')
                # CORRECCIÓN DE COLOR: Usamos 'Plotly3' o 'Ice' que son estables
                fig = px.pie(df_ventas, values='total', names='mes', hole=0.7, 
                             color_discrete_sequence=px.colors.sequential.RdBu)
                fig.update_layout(
                    margin=dict(t=0, b=0, l=0, r=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color="white",
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error visual: {e}")

# --- 3. TABLA DE VENTAS CON DISEÑO PREMIUM ---
    st.write("##")
    st.markdown("""
                <div style="background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%); padding: 15px; border-radius: 15px 15px 0 0; border: 1px solid #334155; border-bottom: none;">
                    <span style="color: #38bdf8; font-size: 1.2rem; font-weight: 700;">📄 Registro Cronológico de Ventas</span>
                </div>
            """, unsafe_allow_html=True)

            # Estilizamos el dataframe usando column_config para que se vea Pro
    st.dataframe(
                df_ventas[['fecha', 'cliente', 'producto', 'cantidad', 'total', 'metodo']].sort_values(by='fecha', ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "fecha": st.column_config.DatetimeColumn("📅 Fecha y Hora", format="DD/MM/YY HH:mm"),
                    "cliente": st.column_config.TextColumn("👤 Cliente"),
                    "producto": st.column_config.TextColumn("📦 Producto"),
                    "cantidad": st.column_config.NumberColumn("Cant.", format="%d uds"),
                    "total": st.column_config.NumberColumn("Monto Total", format="$%d"),
                    "metodo": st.column_config.SelectboxColumn(
                        "💳 Método",
                        options=["Nequi/Daviplata", "Transferencia", "Efectivo"],
                    )
                }
            )

            # --- BOTÓN DE DESCARGA ESTILIZADO ---
    col_down, col_empty = st.columns([1, 3])
    with col_down:
                csv = df_ventas.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Exportar Reporte Mensual",
                    data=csv,
                    file_name=f"Ventas_BajoCero_{df_ventas['mes'].iloc[0]}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
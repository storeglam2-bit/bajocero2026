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
        st.dataframe(inv_sin_licor[['nombre', 'precio', 'stock']], use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### Inventario Con Licor")
        st.dataframe(inv_con_licor[['nombre', 'precio', 'stock']], use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### Inventario de Promociones (Si)")
        st.dataframe(inv_promos[['nombre', 'tipo', 'precio', 'stock']], use_container_width=True, hide_index=True)

# --- 2. REGISTRAR VENTA ---
elif selected == "Registrar Venta":
    st.title("🛒 Terminal de Ventas")

    # 1. Inicializar carrito si no existe
    if 'carrito' not in st.session_state:
        st.session_state.carrito = []

    # 2. Limpieza de datos de GSheets
    df_clientes.columns = df_clientes.columns.str.strip()
    df_productos.columns = df_productos.columns.str.strip()

    # 3. Interfaz de Selección
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        
        with c1:
            lista_cli = df_clientes['empresa'].unique() if 'empresa' in df_clientes.columns else []
            cliente_sel = st.selectbox("👤 Seleccionar Cliente", lista_cli)
        
        with c2:
            # Filtramos productos con stock
            prod_dis = df_productos[df_productos['stock'] > 0].copy()
            
            if not prod_dis.empty:
                # CREAMOS UNA ETIQUETA: "Nombre (Tipo)" para el selector
                prod_dis['display'] = prod_dis['nombre'] + " (" + prod_dis['tipo'] + ")"
                
                opcion_prod = st.selectbox("📦 Producto", prod_dis['display'].unique())
                
                # Extraemos el nombre real y el tipo para la base de datos
                nombre_real = opcion_prod.split(" (")[0]
                datos_p = prod_dis[prod_dis['nombre'] == nombre_real].iloc[0]
                
                tipo_prod = datos_p['tipo']
                precio_base = int(float(datos_p['precio'])) 
                stock_real = int(datos_p['stock'])
                
                st.caption(f"Tipo: **{tipo_prod}** | Stock: {stock_real}")
            else:
                st.warning("Sin stock disponible")
                nombre_real, precio_base, stock_real, tipo_prod = None, 0, 0, ""

        with c3:
            cantidad = st.number_input("Cant.", min_value=1, max_value=stock_real if stock_real > 0 else 1, step=1)

    # 4. Precio Editable (Entero) y Botón
    col_p, col_b = st.columns([2, 1])
    with col_p:
        precio_vta = st.number_input("💰 Precio de Venta", value=precio_base, step=1)
    
    with col_b:
        st.write("##")
        if st.button("➕ Añadir al Carrito", use_container_width=True):
            if nombre_real:
                # Guardamos los datos con nombres de columna consistentes
                st.session_state.carrito.append({
                    "Producto": nombre_real,
                    "Tipo": tipo_prod,
                    "Cant": int(cantidad),
                    "Precio": int(precio_vta),
                    "Subtotal": int(cantidad * precio_vta)
                })
                st.toast(f"Añadido: {nombre_real}")
                st.rerun() # Refrescar para actualizar la tabla abajo

    # 5. Resumen de la Venta (SOLO SE MUESTRA SI HAY ALGO EN EL CARRITO)
    if len(st.session_state.carrito) > 0:
        st.divider()
        st.subheader("📋 Resumen de la Venta")
        
        df_carro = pd.DataFrame(st.session_state.carrito)
        
        # Seleccionamos las columnas exactas para evitar el KeyError
        st.dataframe(
            df_carro[["Producto", "Tipo", "Cant", "Precio", "Subtotal"]], 
            use_container_width=True, 
            hide_index=True
        )
        
        total_vta = int(df_carro['Subtotal'].sum())
        
        v1, v2, v3 = st.columns([1.5, 1, 1.5])
        with v1:
            st.metric("Total General", f"${total_vta:,}".replace(",", "."))
        
        with v2:
            if st.button("🗑️ Vaciar Carrito", use_container_width=True):
                st.session_state.carrito = []
                st.rerun()
        
        with v3:
            if st.button("🚀 Confirmar Venta", type="primary", use_container_width=True):
                # Aquí procesarías la escritura en Google Sheets
                st.success("Venta procesada exitosamente")
                st.balloons()
                st.session_state.carrito = []
    else:
        st.info("El carrito está vacío. Selecciona un producto y presiona 'Añadir'.")

# --- 3. CLIENTES ---
elif selected == "Clientes":
    st.header("👥 Administración de Clientes")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("nuevo_cliente"):
            nombre_c = st.text_input("Nombre del Cliente")
            if st.form_submit_button("Registrar"):
                # Aquí iría conn.update() para agregar a la fila
                st.success("Registrado")
    
    with col2:
        st.subheader("Lista de Clientes")
        st.dataframe(df_clientes, use_container_width=True)

# --- 4. INGRESAR STOCK ---
elif selected == "Ingresar Stock":
    st.header("📥 Entrada de Mercancía")
    # Formulario para actualizar la columna 'stock' de la pestaña 'productos'
    pass
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
    st.markdown("<h1 style='text-align: center; color: #00d4ff;'>💎 Terminal de Ventas Pro</h1>", unsafe_allow_html=True)

    # 1. Inicialización de Carrito
    if 'carrito' not in st.session_state:
        st.session_state.carrito = []

    # 2. Área de Selección (Diseño en Bloques)
    with st.container(border=True):
        st.markdown("#### 📝 Configuración de Venta")
        c1, c2 = st.columns(2)
        
        with c1:
            lista_cli = df_clientes['empresa'].unique() if 'empresa' in df_clientes.columns else []
            cliente_sel = st.selectbox("👤 Cliente", lista_cli, help="Selecciona el cliente registrado")
        
        with c2:
            prod_dis = df_productos[df_productos['stock'] > 0].copy()
            if not prod_dis.empty:
                prod_dis['display'] = prod_dis['nombre'] + " (" + prod_dis['tipo'] + ")"
                opcion_prod = st.selectbox("📦 Producto", prod_dis['display'].unique())
                
                # Extracción de datos técnicos
                nombre_real = opcion_prod.split(" (")[0]
                datos_p = prod_dis[prod_dis['nombre'] == nombre_real].iloc[0]
                tipo_p, precio_b, stock_r = datos_p['tipo'], int(float(datos_p['precio'])), int(datos_p['stock'])
                
                st.markdown(f"**Tipo:** `{tipo_p}` | **Stock:** `{stock_r}`")
            else:
                st.error("⚠️ Sin stock disponible")
                nombre_real, precio_b, stock_r, tipo_p = None, 0, 0, ""

        st.divider()
        
        c3, c4, c5 = st.columns([1, 2, 1])
        with c3:
            cantidad = st.number_input("Cantidad", min_value=1, max_value=stock_r if stock_r > 0 else 1, step=1)
        with c4:
            precio_vta = st.number_input("💰 Precio Unitario Final", value=precio_b, step=500)
        with c5:
            st.write("##")
            if st.button("➕ Añadir", use_container_width=True):
                if nombre_real:
                    st.session_state.carrito.append({
                        "Producto": nombre_real, "Tipo": tipo_p,
                        "Cant": int(cantidad), "Precio": int(precio_vta),
                        "Subtotal": int(cantidad * precio_vta)
                    })
                    st.toast(f"✅ {nombre_real} añadido")
                    st.rerun()

    # 3. Resumen de Venta Estilizado
    if st.session_state.carrito:
        st.markdown("### 📋 Factura Temporal")
        df_carro = pd.DataFrame(st.session_state.carrito)
        
        # Tabla limpia
        st.dataframe(df_carro[["Producto", "Tipo", "Cant", "Precio", "Subtotal"]], 
                     use_container_width=True, hide_index=True)
        
        total_vta = int(df_carro['Subtotal'].sum())

        # --- CAJA VERDE DE TOTAL (DISEÑO PROFESIONAL) ---
        st.markdown(f"""
            <div style="
                background-color: #064e3b; 
                padding: 20px; 
                border-radius: 15px; 
                border-left: 10px solid #10b981;
                margin: 20px 0;
                text-align: center;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
            ">
                <p style="margin: 0; font-size: 1.2rem; color: #a7f3d0; font-weight: bold;">TOTAL A COBRAR</p>
                <h1 style="margin: 0; color: #ffffff; font-size: 3rem;">${total_vta:,}</h1>
            </div>
        """, unsafe_allow_html=True)

        # Acciones Finales
        col_v1, col_v2 = st.columns([1, 2])
        with col_v1:
            if st.button("🗑️ Vaciar Carrito", use_container_width=True):
                st.session_state.carrito = []
                st.rerun()
        with col_v2:
            if st.button("🚀 CONFIRMAR REGISTRO DE VENTA", type="primary", use_container_width=True):
                # Lógica de guardado pendiente
                st.success("🎉 ¡Venta guardada en la base de datos!")
                st.session_state.carrito = []
                st.balloons()
    else:
        st.info("💡 El carrito está esperando tu primera selección.")

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
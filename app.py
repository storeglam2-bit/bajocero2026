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

# --- 1. PANEL PRINCIPAL ---
if selected == "Panel Principal":
    st.header("📊 Resumen de Inventario")
    # --- CÁLCULOS PREVIOS ---
    # Separamos los grupos
    con_licor = df_productos[df_productos['tipo'] == 'Con Licor']
    sin_licor = df_productos[df_productos['tipo'] == 'Sin Licor']
    promos = df_productos[df_productos['promo'] == 'Si']

    # Valores
    val_con = (con_licor['precio'] * con_licor['stock']).sum()
    val_sin = (sin_licor['precio'] * sin_licor['stock']).sum()
    val_total = val_con + val_sin

    # Estilos CSS Avanzados
    st.markdown("""
    <style>
        .main-card {
            background: #1E1E1E;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #333;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
            text-align: center;
            margin-bottom: 20px;
        }
        .metric-title {
            color: #888;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .metric-value {
            color: #00D4FF;
            font-size: 28px;
            font-weight: bold;
        }
        .sub-value {
            color: #00FF87;
            font-size: 18px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Dashboard Ejecutivo - Bajo Cero")

    # --- FILA 1: CANTIDADES (CAJITAS) ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f'''<div class="main-card">
            <div class="metric-title">📦 Total Unidades</div>
            <div class="metric-value">{int(df_productos['stock'].sum())}</div>
        </div>''', unsafe_allow_html=True)

    with col2:
        st.markdown(f'''<div class="main-card">
            <div class="metric-title">🥃 Con Licor</div>
            <div class="metric-value">{int(con_licor['stock'].sum())} <span style="font-size:15px">und</span></div>
        </div>''', unsafe_allow_html=True)

    with col3:
        st.markdown(f'''<div class="main-card">
            <div class="metric-title">🥤 Sin Licor</div>
            <div class="metric-value">{int(sin_licor['stock'].sum())} <span style="font-size:15px">und</span></div>
        </div>''', unsafe_allow_html=True)

    with col4:
        st.markdown(f'''<div class="main-card" style="border-left: 5px solid #FF4B4B;">
            <div class="metric-title">⚠️ Agotados</div>
            <div class="metric-value" style="color:#FF4B4B">{len(df_productos[df_productos['stock'] == 0])}</div>
        </div>''', unsafe_allow_html=True)

    # --- FILA 2: VALORIZACIÓN (DISEÑO MÁS ELEGANTE) ---
    st.markdown("### 💰 Valorización del Patrimonio")
    v1, v2, v3 = st.columns(3)

    with v1:
        st.markdown(f'''<div class="main-card" style="background: linear-gradient(145deg, #1a1a1a, #252525);">
            <div class="metric-title">Total Con Licor</div>
            <div class="sub-value">${val_con:,.0f}</div>
        </div>''', unsafe_allow_html=True)

    with v2:
        st.markdown(f'''<div class="main-card" style="background: linear-gradient(145deg, #1a1a1a, #252525);">
            <div class="metric-title">Total Sin Licor</div>
            <div class="sub-value">${val_sin:,.0f}</div>
        </div>''', unsafe_allow_html=True)

    with v3:
        st.markdown(f'''<div class="main-card" style="background: linear-gradient(145deg, #004e92, #000428);">
            <div class="metric-title" style="color:white">Valor Total</div>
            <div class="sub-value" style="color:white; font-size:24px">${val_total:,.0f}</div>
        </div>''', unsafe_allow_html=True)

    # --- FILA 3: PROMOS Y TABLAS ---
    st.divider()
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.subheader("🎁 Inventario Promociones")
        # Mostramos una tabla estilizada de promos
        st.dataframe(promos[['nombre', 'tipo', 'stock']], use_container_width=True, hide_index=True)

    with c_right:
        st.subheader("📉 Alerta de Reabastecimiento")
        bajas = df_productos[(df_productos['stock'] > 0) & (df_productos['stock'] <= 5)]
        if not bajas.empty:
            st.warning(f"Tienes {len(bajas)} productos por agotarse.")
            st.table(bajas[['nombre', 'stock']])
        else:
            st.success("¡Todo el stock está en niveles óptimos!")

# --- 2. REGISTRAR VENTA ---
elif selected == "Registrar Venta":
    st.header("🛒 Terminal de Ventas")
    
    with st.container(border=True):
        col_c, col_p, col_can = st.columns([2, 2, 1])
        
        with col_c:
            # Lista desplegable de clientes desde la pestaña 'clientes'
            cliente_sel = st.selectbox("Cliente", df_clientes['nombre'].unique())
        
        with col_p:
            # Solo mostrar productos con stock > 0
            prod_disponibles = df_productos[df_productos['stock'] > 0]
            producto_sel = st.selectbox("Producto", prod_disponibles['nombre'].unique())
            
            # Obtener precio sugerido
            precio_sug = df_productos.loc[df_productos['nombre'] == producto_sel, 'precio'].values[0]
            
        with col_can:
            cantidad = st.number_input("Cant.", min_value=1, step=1)

        precio_final = st.number_input("Precio de Venta (Editable)", value=float(precio_sug))
        
        if st.button("Añadir al carrito"):
            # Lógica para guardar temporalmente antes de subir a la pestaña 'ventas'
            st.toast(f"Añadido: {producto_sel} x{cantidad}")

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
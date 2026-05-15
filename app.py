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
    
    # Cálculos dinámicos basados en tu imagen
    total_unidades = df_productos['stock'].sum()
    con_licor = df_productos[df_productos['tipo'] == 'Con Licor']
    sin_licor = df_productos[df_productos['tipo'] == 'Sin Licor']
    
    # Métricas de Dinero (Precio * Stock)
    valor_con_licor = (con_licor['precio'] * con_licor['stock']).sum()
    valor_sin_licor = (sin_licor['precio'] * sin_licor['stock']).sum()

    # Fila 1: Cantidades
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Unidades", f"{total_unidades}")
    m2.metric("Con Licor", f"{con_licor['stock'].sum()} und")
    m3.metric("Sin Licor", f"{sin_licor['stock'].sum()} und")
    m4.metric("Agotados", f"{len(df_productos[df_productos['stock'] == 0])}")

    # Fila 2: Dinero y Promos
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("💰 Valorización de Inventario")
        st.write(f"**Con Licor:** ${valor_con_licor:,.0f}")
        st.write(f"**Sin Licor:** ${valor_sin_licor:,.0f}")
    
    with c2:
        st.subheader("🎁 Promociones Activas")
        promos = df_productos[df_productos['promo'] == 'Si']
        st.dataframe(promos[['nombre', 'tipo', 'stock']], hide_index=True)

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
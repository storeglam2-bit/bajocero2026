import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Bajo Cero | Inventario Pro",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO CSS PERSONALIZADO ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #31333f; }
    div[data-testid="stExpander"] { border: 1px solid #31333f; border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2e7bcf; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
def conectar():
    return sqlite3.connect('inventario_liquidos.db')

def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY, nombre TEXT, color TEXT, tipo TEXT, precio REAL, stock INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY, empresa TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY, producto_id INTEGER, cliente TEXT, cantidad INTEGER, fecha TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS ingresos (id INTEGER PRIMARY KEY, producto_id INTEGER, cantidad INTEGER, fecha TEXT)')
    conn.commit()
    conn.close()

crear_tablas()

# --- SIDEBAR PROFESIONAL ---
with st.sidebar:
    st.image("logo.png", use_container_width=True)
    st.title("❄️ BAJO CERO")
    st.caption("Control de Inventario Líquidos 3L")
    st.markdown("---")
    
    choice = st.radio(
        "NAVEGACIÓN",
        ["📊 Panel Principal", "🛒 Registrar Venta", "📥 Entrada Producción", "📋 Historial", "🥤 Sabores", "🏢 Clientes"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("🔄 Refrescar Datos"):
        st.rerun()

conn = conectar()

# --- 📊 PANEL PRINCIPAL (VERSIÓN FINAL COP) ---
if choice == "📊 Panel Principal":
    st.title("📊 Resumen de Inventario")
    
    # Consulta de datos
    df_prod = pd.read_sql_query("SELECT nombre, tipo, stock, precio FROM productos", conn)
    
    if not df_prod.empty:
        # 1. CÁLCULO DE MÉTRICAS
        val_total = int((df_prod['stock'] * df_prod['precio']).sum())
        total_botellas = int(df_prod['stock'].sum())
        
        # Fila de métricas visuales
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Sabores en Catálogo", len(df_prod))
        with c2:
            st.metric("Total Líquidos (3L)", total_botellas)
        with c3:
            # Formato moneda COP para el valor total
            st.metric("Valor Inventario", f"$ {val_total:,}".replace(",", "."))
        
        st.markdown("---")
        
        # 2. SECCIÓN DE ALERTAS CRÍTICAS (Stock <= 4)
        criticos = df_prod[df_prod['stock'] <= 4]
        if not criticos.empty:
            st.error(f"⚠️ **ALERTA DE REABASTECIMIENTO:** Tienes {len(criticos)} sabor(es) en nivel crítico.")
            # Opcional: lista corta de qué sabores faltan
            sabores_bajos = ", ".join([f"{r['nombre']} ({r['tipo']})" for _, r in criticos.iterrows()])
            st.caption(f"Revisar: {sabores_bajos}")
        
        st.subheader("📦 Estado del Stock")

        # 3. PREPARACIÓN DE LA TABLA PARA MOSTRAR
        # Creamos una columna combinada para evitar confusión entre Con/Sin Licor
        df_prod['Sabor / Tipo'] = df_prod['nombre'] + " (" + df_prod['tipo'] + ")"
        
        # Seleccionamos y renombramos columnas para el usuario
        df_display = df_prod[['Sabor / Tipo', 'stock', 'precio']].copy()
        df_display.columns = ['Sabor', 'Existencias', 'Precio Unit.']

        # Función para aplicar color rojo al stock bajo
        def color_stock(val):
            color = '#ff4b4b' if val <= 4 else '#09ab3b' # Rojo si es 4 o menos, Verde si es más
            return f'color: {color}; font-weight: bold'

        # 4. RENDERIZADO DE LA TABLA CON FORMATO COP
        st.dataframe(
            df_display.style.applymap(color_stock, subset=['Existencias'])
            .format({
                # Aquí ocurre la magia: quita decimales, pone $ y usa puntos para miles
                "Precio Unit.": lambda x: f"$ {int(x):,}".replace(",", ".")
            }),
            use_container_width=True, 
            hide_index=True
        )
        
    else:
        st.info("👋 ¡Bienvenido! El inventario está vacío. Comienza registrando tus productos en el módulo '🥤 Sabores'.")

# --- 🛒 REGISTRAR VENTA ---
elif choice == "🛒 Registrar Venta":
    st.title("🛒 Nueva Venta")
    prods = pd.read_sql_query("SELECT id, nombre, tipo, stock FROM productos", conn)
    clis = pd.read_sql_query("SELECT empresa FROM clientes", conn)
    
    if prods.empty or clis.empty:
        st.warning("Debes registrar productos y clientes antes de vender.")
    else:
        with st.form("venta_form"):
            c1, c2 = st.columns(2)
            cliente = c1.selectbox("Empresa Cliente", clis['empresa'])
            prods['disp'] = prods['nombre'] + " (" + prods['tipo'] + ")"
            p_sel = c1.selectbox("Sabor seleccionado", prods['disp'])
            
            cant = c2.number_input("Cantidad a despachar", min_value=1, step=1)
            p_idx = prods[prods['disp'] == p_sel].index[0]
            stock_act = prods.iloc[p_idx]['stock']
            
            c2.info(f"Stock disponible: {stock_act}")
            
            if st.form_submit_button("Confirmar y Restar del Stock"):
                if stock_act >= cant:
                    p_id = int(prods.iloc[p_idx]['id'])
                    cur = conn.cursor()
                    cur.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cant, p_id))
                    cur.execute("INSERT INTO ventas (producto_id, cliente, cantidad, fecha) VALUES (?,?,?,?)", 
                                (p_id, cliente, cant, datetime.now().strftime("%d/%m/%Y %H:%M")))
                    conn.commit()
                    st.success(f"Venta registrada. Quedan {stock_act - cant} unidades.")
                else:
                    st.error("No hay suficiente stock.")

# --- 📥 ENTRADA PRODUCCIÓN ---
elif choice == "📥 Entrada Producción":
    st.title("📥 Ingreso de Mercancía")
    prods = pd.read_sql_query("SELECT id, nombre, tipo FROM productos", conn)
    
    with st.container(border=True):
        prods['disp'] = prods['nombre'] + " (" + prods['tipo'] + ")"
        p_ing = st.selectbox("¿Qué sabor entró a bodega?", prods['disp'])
        cant_in = st.number_input("Cantidad de botellas nuevas", min_value=1, step=1)
        
        if st.button("Sumar al Inventario"):
            p_id = int(prods[prods['disp'] == p_ing].iloc[0]['id'])
            cur = conn.cursor()
            cur.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cant_in, p_id))
            cur.execute("INSERT INTO ingresos (producto_id, cantidad, fecha) VALUES (?,?,?)", 
                        (p_id, cant_in, datetime.now().strftime("%d/%m/%Y %H:%M")))
            conn.commit()
            st.success(f"¡Listo! Se agregaron {cant_in} unidades.")

# --- 📋 HISTORIAL ---
elif choice == "📋 Historial":
    st.title("📋 Registro Histórico")
    df_h = pd.read_sql_query('''SELECT i.fecha as Fecha, p.nombre || ' (' || p.tipo || ')' as Sabor, i.cantidad as Cantidad 
                               FROM ingresos i JOIN productos p ON i.producto_id = p.id ORDER BY i.id DESC''', conn)
    st.dataframe(df_h, use_container_width=True, hide_index=True)

# --- 🥤 SABORES ---
elif choice == "🥤 Sabores":
    st.title("🥤 Catálogo de Sabores")
    with st.expander("✨ Crear Nuevo Sabor"):
        nom = st.text_input("Nombre")
        c1, c2 = st.columns(2)
        tip = c1.selectbox("Tipo", ["Sin Licor", "Con Licor"])
        pre = c2.number_input("Precio", min_value=0, step=100)
        col = st.color_picker("Color guía")
        if st.button("Guardar Producto"):
            conn.execute("INSERT INTO productos (nombre, color, tipo, precio, stock) VALUES (?,?,?,?,?)", (nom, col, tip, pre, 0))
            conn.commit()
            st.rerun()
    
    df_l = pd.read_sql_query("SELECT nombre, tipo, precio, stock FROM productos", conn)
    st.table(df_l)

# --- 🏢 CLIENTES ---
elif choice == "🏢 Clientes":
    st.title("🏢 Gestión de Clientes")
    with st.form("cli_form"):
        n_cli = st.text_input("Nombre de la Empresa")
        if st.form_submit_button("Registrar Cliente"):
            conn.execute("INSERT INTO clientes (empresa) VALUES (?)", (n_cli,))
            conn.commit()
            st.rerun()
    
    df_c = pd.read_sql_query("SELECT empresa FROM clientes", conn)
    st.dataframe(df_c, use_container_width=True)

conn.close()
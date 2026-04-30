import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Bajo Cero - Gestión", page_icon="❄️", layout="wide")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- SIDEBAR ---
# Intentamos cargar el logo. Si falla, ponemos texto para evitar el error MediaFileStorageError
try:
    st.sidebar.image("logo.png", use_container_width=True)
except Exception:
    st.sidebar.title("❄️ BAJO CERO")

menu = st.sidebar.radio("MENÚ", ["📊 Dashboard", "🛒 Ventas", "📥 Entradas", "🥤 Productos", "🏢 Clientes"])

# --- FUNCIÓN PARA CARGAR DATOS ---
def load_data(sheet_name):
    # ttl="0" permite ver los cambios realizados por otros usuarios o el celular al instante
    return conn.read(worksheet=sheet_name, ttl="0")

# --- MÓDULO: DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Resumen de Inventario")
    df_p = load_data("productos")
    
    if not df_p.empty:
        # Métricas principales sin decimales
        val_total = int((df_p['stock'] * df_p['precio']).sum())
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Sabores", len(df_p))
        c2.metric("Total Líquidos (3L)", int(df_p['stock'].sum()))
        c3.metric("Valor Inventario", f"$ {val_total:,}".replace(",", "."))
        
        # Alertas de stock bajo (4 o menos)
        criticos = df_p[df_p['stock'] <= 4]
        if not criticos.empty:
            st.error(f"⚠️ Alerta: {len(criticos)} productos con poco stock.")
        
        # Tabla de stock formateada
        st.subheader("Existencias Actuales")
        df_p['Sabor'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
        
        # Estilo para destacar stock bajo en rojo
        def highlight_low_stock(s):
            return ['color: #ff4b4b; font-weight: bold' if v <= 4 else 'color: #09ab3b' for v in s]

        st.dataframe(
            df_p[['Sabor', 'stock', 'precio']].style
            .apply(highlight_low_stock, subset=['stock'])
            .format({"precio": lambda x: f"$ {int(x):,}".replace(",", ".")}),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("La base de datos está vacía.")

# --- MÓDULO: VENTAS ---
elif menu == "🛒 Ventas":
    st.title("🛒 Registrar Venta")
    df_p = load_data("productos")
    df_c = load_data("clientes")
    
    if not df_p.empty and not df_c.empty:
        with st.form("venta_form"):
            cliente = st.selectbox("Cliente", df_c['empresa'])
            df_p['display'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
            prod_sel = st.selectbox("Sabor", df_p['display'])
            cantidad = st.number_input("Cantidad", min_value=1, step=1)
            
            if st.form_submit_button("Finalizar Venta"):
                idx = df_p[df_p['display'] == prod_sel].index[0]
                if df_p.at[idx, 'stock'] >= cantidad:
                    df_p.at[idx, 'stock'] -= cantidad
                    # Actualizar productos
                    conn.update(worksheet="productos", data=df_p[['nombre', 'color', 'tipo', 'precio', 'stock']])
                    
                    # Registrar historial de venta
                    df_v = load_data("ventas")
                    nueva_v = pd.DataFrame([{"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), 
                                            "producto": prod_sel, "cliente": cliente, "cantidad": cantidad}])
                    conn.update(worksheet="ventas", data=pd.concat([df_v, nueva_v], ignore_index=True))
                    
                    st.success("Venta guardada correctamente.")
                    st.rerun()
                else:
                    st.error("Stock insuficiente.")

# --- MÓDULO: ENTRADAS ---
elif menu == "📥 Entradas":
    st.title("📥 Ingreso de Producción")
    df_p = load_data("productos")
    
    with st.form("entrada_form"):
        df_p['display'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
        prod_sel = st.selectbox("Sabor que ingresa", df_p['display'])
        cantidad = st.number_input("Cantidad de botellas", min_value=1, step=1)
        
        if st.form_submit_button("Registrar Ingreso"):
            idx = df_p[df_p['display'] == prod_sel].index[0]
            df_p.at[idx, 'stock'] += cantidad
            conn.update(worksheet="productos", data=df_p[['nombre', 'color', 'tipo', 'precio', 'stock']])
            st.success("Stock actualizado en la nube.")
            st.rerun()

# --- MÓDULO: PRODUCTOS ---
elif menu == "🥤 Productos":
    st.title("🥤 Catálogo")
    df_p = load_data("productos")
    with st.expander("Crear Nuevo Producto"):
        n = st.text_input("Nombre")
        t = st.selectbox("Tipo", ["Sin Licor", "Con Licor"])
        p = st.number_input("Precio", min_value=0, step=500)
        if st.button("Añadir"):
            new_p = pd.DataFrame([{"nombre": n, "color": "#000", "tipo": t, "precio": p, "stock": 0}])
            conn.update(worksheet="productos", data=pd.concat([df_p, new_p], ignore_index=True))
            st.rerun()
    st.dataframe(df_p, use_container_width=True)

# --- MÓDULO: CLIENTES ---
elif menu == "🏢 Clientes":
    st.title("🏢 Clientes")
    df_c = load_data("clientes")
    with st.form("cli"):
        nom = st.text_input("Nombre Empresa")
        if st.form_submit_button("Guardar"):
            new_c = pd.DataFrame([{"empresa": nom}])
            conn.update(worksheet="clientes", data=pd.concat([df_c, new_c], ignore_index=True))
            st.rerun()
    st.table(df_c)
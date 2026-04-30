import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Bajo Cero - Inventario Pro",
    page_icon="❄️",
    layout="wide"
)

# --- 2. CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    try:
        # ttl="0" asegura que lea los datos reales de la nube cada vez que refrescas
        return conn.read(worksheet=pestana, ttl="0")
    except Exception as e:
        st.error(f"Error en pestaña '{pestana}': {e}")
        return pd.DataFrame()

# --- 3. DISEÑO DE LA BARRA LATERAL ---
with st.sidebar:
    try:
        # Intenta cargar el logo local
        st.image("logo.png", use_container_width=True)
    except:
        st.title("❄️ BAJO CERO")
    
    st.markdown("---")
    menu = st.radio(
        "MENÚ DE NAVEGACIÓN",
        ["📊 Panel Principal", "🛒 Registrar Venta", "📥 Entrada Producción", "🥤 Catálogo Productos", "🏢 Gestión Clientes"]
    )
    st.markdown("---")
    st.caption("Versión Cloud 2.0 - Google Sheets")

# --- 4. MÓDULO: PANEL PRINCIPAL (DASHBOARD) ---
if menu == "📊 Panel Principal":
    st.title("📊 Resumen de Inventario")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # Cálculo de métricas
        total_botellas = int(df_p['stock'].sum())
        valor_inv = int((df_p['stock'] * df_p['precio']).sum())
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Sabores en Catálogo", len(df_p))
        c2.metric("Stock Total (Botellas)", total_botellas)
        c3.metric("Valor Inventario", f"$ {valor_inv:,}".replace(",", "."))
        
        st.markdown("---")
        
        # Alertas de Stock Bajo
        criticos = df_p[df_p['stock'] <= 4]
        if not criticos.empty:
            st.error(f"⚠️ **ATENCIÓN:** Tienes {len(criticos)} sabores con 4 unidades o menos.")
        
        # Tabla Principal Formateada
        st.subheader("📦 Estado Actual del Stock")
        df_show = df_p.copy()
        df_show['Producto'] = df_show['nombre'] + " (" + df_show['tipo'] + ")"
        
        # Aplicar colores al stock
        def color_stock(val):
            color = '#ff4b4b' if val <= 4 else '#09ab3b'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df_show[['Producto', 'stock', 'precio']].style
            .applymap(color_stock, subset=['stock'])
            .format({
                "precio": lambda x: f"$ {int(x):,}".replace(",", "."),
                "stock": "{:.0f}"
            }),
            use_container_width=True, hide_index=True
        )
    else:
        st.warning("No se encontraron datos. Revisa la conexión con Google Sheets.")

# --- 5. MÓDULO: REGISTRAR VENTA ---
elif menu == "🛒 Registrar Venta":
    st.title("🛒 Nueva Venta")
    df_p = cargar_datos("productos")
    df_c = cargar_datos("clientes")
    
    if not df_p.empty and not df_c.empty:
        with st.form("venta_form"):
            col1, col2 = st.columns(2)
            cliente = col1.selectbox("Seleccione Cliente", df_c['empresa'])
            
            df_p['display'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
            prod_sel = col1.selectbox("Producto a vender", df_p['display'])
            
            cant = col2.number_input("Cantidad de botellas", min_value=1, step=1)
            
            if st.form_submit_button("Finalizar Venta"):
                idx = df_p[df_p['display'] == prod_sel].index[0]
                stock_actual = df_p.at[idx, 'stock']
                
                if stock_actual >= cant:
                    # 1. Descontar de productos
                    df_p.at[idx, 'stock'] -= cant
                    conn.update(worksheet="productos", data=df_p[['nombre', 'color', 'tipo', 'precio', 'stock']])
                    
                    # 2. Registrar en historial de ventas
                    df_v = cargar_datos("ventas")
                    nueva_v = pd.DataFrame([{
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "producto": prod_sel,
                        "cliente": cliente,
                        "cantidad": cant
                    }])
                    conn.update(worksheet="ventas", data=pd.concat([df_v, nueva_v], ignore_index=True))
                    
                    st.success(f"✅ Venta exitosa. Quedan {int(stock_actual - cant)} unidades.")
                    st.rerun()
                else:
                    st.error(f"❌ Stock insuficiente. Solo tienes {int(stock_actual)} unidades.")
    else:
        st.error("Error: Debes tener productos y clientes creados.")

# --- 6. MÓDULO: ENTRADA PRODUCCIÓN ---
elif menu == "📥 Entrada Producción":
    st.title("📥 Registro de Ingreso")
    df_p = cargar_datos("productos")
    
    with st.form("entrada_form"):
        df_p['display'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
        prod_sel = st.selectbox("Sabor que ingresa a bodega", df_p['display'])
        cant = st.number_input("Cantidad de botellas nuevas", min_value=1, step=1)
        
        if st.form_submit_button("Registrar Entrada"):
            idx = df_p[df_p['display'] == prod_sel].index[0]
            df_p.at[idx, 'stock'] += cant
            
            # Guardar actualización
            conn.update(worksheet="productos", data=df_p[['nombre', 'color', 'tipo', 'precio', 'stock']])
            
            # Registrar historial de ingresos
            df_i = cargar_datos("ingresos")
            nuevo_i = pd.DataFrame([{
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "producto": prod_sel,
                "cantidad": cant
            }])
            conn.update(worksheet="ingresos", data=pd.concat([df_i, nuevo_i], ignore_index=True))
            
            st.success("✅ Stock actualizado correctamente.")
            st.rerun()

# --- 7. MÓDULO: CATÁLOGO PRODUCTOS ---
elif menu == "🥤 Catálogo Productos":
    st.title("🥤 Gestión de Productos")
    df_p = cargar_datos("productos")
    
    with st.expander("✨ Crear Nuevo Sabor"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nombre del Líquido")
        t = c1.selectbox("Tipo", ["Sin Licor", "Con Licor"])
        p = c2.number_input("Precio de Venta (COP)", min_value=0, step=500)
        
        if st.button("Guardar Producto"):
            new_row = pd.DataFrame([{"nombre": n, "color": "#000", "tipo": t, "precio": p, "stock": 0}])
            conn.update(worksheet="productos", data=pd.concat([df_p, new_row], ignore_index=True))
            st.success("Sabor añadido.")
            st.rerun()
            
    st.subheader("Listado Actual")
    st.dataframe(df_p[['nombre', 'tipo', 'precio', 'stock']], use_container_width=True)

# --- 8. MÓDULO: GESTIÓN CLIENTES ---
elif menu == "🏢 Gestión Clientes":
    st.title("🏢 Clientes Registrados")
    df_c = cargar_datos("clientes")
    
    with st.form("cli_form"):
        nuevo_c = st.text_input("Nombre de la Empresa / Cliente")
        if st.form_submit_button("Registrar Cliente"):
            new_row = pd.DataFrame([{"empresa": nuevo_c}])
            conn.update(worksheet="clientes", data=pd.concat([df_c, new_row], ignore_index=True))
            st.success("Cliente guardado.")
            st.rerun()
            
    st.table(df_c)
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Bajo Cero - Gestión de Inventario",
    page_icon="❄️",
    layout="wide"
)

# Estilo visual para métricas y tablas
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; }
    .stDataFrame { border: 1px solid #30333d; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    try:
        # ttl=0 para que siempre lea los datos más recientes de la nube
        df = conn.read(worksheet=pestana, ttl=0)
        return df.dropna(how='all')
    except Exception:
        return pd.DataFrame()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
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
        st.rerun()

# --- MÓDULO 1: PANEL PRINCIPAL (DASHBOARD) ---
if menu == "📊 Panel Principal":
    st.title("📊 Resumen de Inventario")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # Asegurar tipos de datos numéricos y sin decimales
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
        
        # Métricas principales
        c1, c2, c3 = st.columns(3)
        c1.metric("Sabores Activos", len(df_p))
        c2.metric("Total Botellas (3L)", int(df_p['stock'].sum()))
        
        valor_total = (df_p['stock'] * df_p['precio']).sum()
        c3.metric("Valor Inventario", f"$ {int(valor_total):,}".replace(",", "."))
        
        st.markdown("---")
        
        # Alertas de Stock Bajo
        bajos = df_p[df_p['stock'] <= 4]
        if not bajos.empty:
            nombres_bajos = ", ".join(bajos['nombre'].tolist())
            st.error(f"⚠️ **STOCK CRÍTICO:** Reabastecer: {nombres_bajos}")
        
        # Tabla de Existencias
        st.subheader("📦 Estado del Stock")
        df_show = df_p.copy()
        df_show['Sabor'] = df_show['nombre'] + " (" + df_show['tipo'] + ")"
        
        # Formateo de la tabla (Color rojo si stock <= 4)
        def highlight_stock(val):
            color = '#ff4b4b' if val <= 4 else '#09ab3b'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df_show[['Sabor', 'stock', 'precio']].style
            .applymap(highlight_stock, subset=['stock'])
            .format({
                "precio": lambda x: f"$ {int(x):,}".replace(",", "."),
                "stock": "{:d}"
            }),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No hay productos registrados. Ve a '🥤 Catálogo Productos' para empezar.")

# --- MÓDULO 2: REGISTRAR VENTA ---
elif menu == "🛒 Registrar Venta":
    st.title("🛒 Nueva Venta")
    df_p = cargar_datos("productos")
    df_c = cargar_datos("clientes")
    
    if not df_p.empty and not df_c.empty:
        with st.form("form_venta"):
            col1, col2 = st.columns(2)
            cli = col1.selectbox("Cliente", df_c['empresa'])
            
            df_p['display'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
            prod_sel = col1.selectbox("Producto", df_p['display'])
            
            cant = col2.number_input("Cantidad", min_value=1, step=1)
            
            if st.form_submit_button("Confirmar Venta"):
                idx = df_p[df_p['display'] == prod_sel].index[0]
                stock_actual = int(df_p.at[idx, 'stock'])
                
                if stock_actual >= cant:
                    # 1. Restar stock
                    df_p.at[idx, 'stock'] = stock_actual - cant
                    conn.update(worksheet="productos", data=df_p[['nombre', 'color', 'tipo', 'precio', 'stock']])
                    
                    # 2. Registrar historial
                    df_v = cargar_datos("ventas")
                    nueva_v = pd.DataFrame([{
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "producto": prod_sel,
                        "cliente": cli,
                        "cantidad": cant
                    }])
                    conn.update(worksheet="ventas", data=pd.concat([df_v, nueva_v], ignore_index=True))
                    
                    st.success(f"✅ Venta registrada. Stock restante: {stock_actual - cant}")
                    st.rerun()
                else:
                    st.error(f"❌ Error: Stock insuficiente (Disponible: {stock_actual})")
    else:
        st.warning("Se requieren productos y clientes para realizar ventas.")

# --- MÓDULO 3: ENTRADA PRODUCCIÓN ---
elif menu == "📥 Entrada Producción":
    st.title("📥 Ingreso de Mercancía")
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        with st.form("form_entrada"):
            df_p['display'] = df_p['nombre'] + " (" + df_p['tipo'] + ")"
            prod_sel = st.selectbox("Sabor producido", df_p['display'])
            cantidad = st.number_input("Cantidad de botellas", min_value=1, step=1)
            
            if st.form_submit_button("Cargar a Inventario"):
                idx = df_p[df_p['display'] == prod_sel].index[0]
                df_p.at[idx, 'stock'] = int(df_p.at[idx, 'stock']) + cantidad
                
                conn.update(worksheet="productos", data=df_p[['nombre', 'color', 'tipo', 'precio', 'stock']])
                st.success("✅ Stock actualizado en Google Sheets.")
                st.rerun()

# --- MÓDULO 4: CATÁLOGO PRODUCTOS ---
elif menu == "🥤 Catálogo Productos":
    st.title("🥤 Gestión de Productos")
    df_p = cargar_datos("productos")
    
    with st.expander("✨ Crear Nuevo Sabor"):
        with st.form("form_nuevo_p"):
            n = st.text_input("Nombre del Sabor")
            t = st.selectbox("Categoría", ["Sin Licor", "Con Licor"])
            p = st.number_input("Precio de Venta", min_value=0, step=1000)
            if st.form_submit_button("Añadir al Catálogo"):
                # Limpiamos los datos antes de enviar
                nueva_f = pd.DataFrame([{
                    "nombre": str(n),
                    "color": "#000",
                    "tipo": str(t),
                    "precio": int(p),
                    "stock": 0
                }])
    
            # Unimos y nos aseguramos de que no haya valores nulos
            df_res = pd.concat([df_p, nueva_f], ignore_index=True).fillna(0)
    
            try:
                conn.update(worksheet="productos", data=df_res)
                st.success("✅ Sabor guardado con éxito.")
                st.rerun()
            except Exception as e:
                st.error(f"Error de permisos: Asegúrate de que la Service Account sea Editor en el Excel.")
    
    if not df_p.empty:
        st.dataframe(df_p[['nombre', 'tipo', 'precio', 'stock']], use_container_width=True, hide_index=True)

# --- MÓDULO 5: GESTIÓN CLIENTES ---
elif menu == "🏢 Gestión Clientes":
    st.title("🏢 Base de Clientes")
    df_c = cargar_datos("clientes")
    
    with st.form("form_cli"):
        nombre_c = st.text_input("Nombre de la Empresa / Cliente")
        if st.form_submit_button("Registrar Cliente"):
            nueva_c = pd.DataFrame([{"empresa": nombre_c}])
            df_res = pd.concat([df_c, nueva_c], ignore_index=True) if not df_c.empty else nueva_c
            conn.update(worksheet="clientes", data=df_res)
            st.success("Cliente guardado.")
            st.rerun()
            
    if not df_c.empty:
        st.table(df_c)
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Bajo Cero - Gestión de Inventario",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONEXIÓN A GOOGLE SHEETS ---
# Se utiliza la URL de la hoja definida en tus Secrets de Streamlit
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos(pestana):
    try:
        # ttl=0 asegura que los datos se lean en tiempo real sin caché
        df = conn.read(worksheet=pestana, ttl=0)
        # Limpiamos nombres de columnas: elimina espacios y convierte a minúsculas
        df.columns = df.columns.str.strip().str.lower()
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"⚠️ Error en pestaña '{pestana}': {e}")
        return pd.DataFrame()

from streamlit_option_menu import option_menu

# --- CONFIGURACIÓN DE ESTILO (Inyectar en el inicio de la app) ---
st.markdown("""
    <style>
        /* Estilo para que el sidebar se sienta más moderno */
        [data-testid="stSidebar"] {
            background-color: #0e1117;
            border-right: 1px solid #333;
        }
        /* Ajuste de logo */
        .sidebar-logo {
            display: flex;
            justify-content: center;
            padding: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    # Contenedor de Logo
    st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    try:
        st.image("logo.png", width=150)
    except:
        st.markdown("<h2 style='text-align: center; color: #00f2fe;'>❄️ BAJO CERO</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # MENÚ PROFESIONAL CON AUTO-OCULTADO
    # Al cambiar de opción, Streamlit refresca la página, y al tener 'initial_sidebar_state="collapsed"' 
    # en st.set_page_config, se cerrará solo.
    menu = option_menu(
        menu_title="NAVEGACIÓN",
        options=["Panel Principal", "Registrar Venta", "Entrada Producción", "Catálogo Productos", "Gestión Clientes", "Historial de Ventas"],
        icons=["speedometer2", "cart3", "box-seam", "cup-straw", "building", "clipboard-data"], 
        menu_icon="cast", 
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "transparent"},
            "icon": {"color": "#00f2fe", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "14px", 
                "text-align": "left", 
                "margin":"5px", 
                "--hover-color": "#1e1e1e",
                "color": "white"
            },
            "nav-link-selected": {
                "background-color": "#1a1a1a", 
                "border-left": "4px solid #00f2fe",
                "font-weight": "bold"
            },
        }
    )

    st.markdown("---")
    
    # Botón de refresco con mejor diseño
    if st.button("🔄 Actualizar Sistema", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- TRUCO CRUCIAL PARA EL AUTO-OCULTADO ---
# Asegúrate de que al inicio de todo tu archivo app.py tengas esto:
# st.set_page_config(initial_sidebar_state="collapsed", ...)

# --- MÓDULO 1: PANEL PRINCIPAL (RESTAURADO + PROMO DETALLADA) ---
if menu == "Panel Principal":
    st.markdown("<h1 style='text-align: center; color: #00f2fe;'>📊 Resumen de Inventario</h1>", unsafe_allow_html=True)
    df_p = cargar_datos("productos")

    if not df_p.empty:
        # 1. LIMPIEZA Y COLUMNA INVISIBLE
        # 1. PREPARACIÓN DE DATOS Y LÓGICA INVISIBLE
        if 'promo' not in df_p.columns:
            df_p['promo'] = "No"

        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)

        # Función para determinar el precio real basado en si es promo
        def obtener_precio_final(row):
            if str(row['tipo']).strip() == "Sin Licor" and str(row['promo']).strip() == "Si":
                return 30000
            return row['precio']

        df_p['precio_display'] = df_p.apply(obtener_precio_final, axis=1)
        df_p['valor_total_fila'] = df_p['stock'] * df_p['precio_display']

        # SEPARACIÓN DE GRUPOS
        df_sin_reg = df_p[(df_p['tipo'].str.contains("Sin", case=False)) & (df_p['promo'] != "Si")]
        df_sin_pro = df_p[(df_p['tipo'].str.contains("Sin", case=False)) & (df_p['promo'] == "Si")]
        df_con_lic = df_p[df_p['tipo'].str.contains("Con", case=False)]

        # --- DISEÑO DE TARJETAS (4 COLUMNAS) ---
        # 2. TARJETAS DE INDICADORES (KPIs)
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(f'''<div style="background-color:#1a1a1a;padding:12px;border-radius:10px;border-left:5px solid #ff4b4b;text-align:center;">
                <p style="margin:0;font-size:11px;color:#888;">🥤 SIN LICOR (REG)</p>
                <h3 style="margin:0;color:white;font-size:20px;">{df_sin_reg["stock"].sum()} <span style="font-size:10px;">UND</span></h3>
                <p style="margin:0;color:#ff4b4b;font-size:14px;font-weight:bold;">$ {int(df_sin_reg["valor_total_fila"].sum()):,}</p>
            </div>''', unsafe_allow_html=True)

        with c2:

            color_promo = "#f1c40f" if not df_sin_pro.empty else "#333"
            st.markdown(f'''<div style="background-color:#1a1a1a;padding:12px;border-radius:10px;border-left:5px solid {color_promo};text-align:center;">
                <p style="margin:0;font-size:11px;color:#888;">🔥 SIN LICOR (PROMO)</p>
                <h3 style="margin:0;color:white;font-size:20px;">{df_sin_pro["stock"].sum()} <span style="font-size:10px;">UND</span></h3>
                <p style="margin:0;color:{color_promo};font-size:14px;font-weight:bold;">$ {int(df_sin_pro["valor_total_fila"].sum()):,}</p>
            </div>''', unsafe_allow_html=True)

        with c3:
            st.markdown(f'''<div style="background-color:#1a1a1a;padding:12px;border-radius:10px;border-left:5px solid #00f2fe;text-align:center;">
                <p style="margin:0;font-size:11px;color:#888;">🍸 CON LICOR</p>
                <h3 style="margin:0;color:white;font-size:20px;">{df_con_lic["stock"].sum()} <span style="font-size:10px;">UND</span></h3>
                <p style="margin:0;color:#00f2fe;font-size:14px;font-weight:bold;">$ {int(df_con_lic["valor_total_fila"].sum()):,}</p>
            </div>''', unsafe_allow_html=True)

        with c4:
        # --- ALERTAS (Mantenemos tu diseño original) ---
            total_valor = df_p['valor_total_fila'].sum()
            st.markdown(f'''<div style="background-color:#1a1a1a;padding:12px;border-radius:10px;border-left:5px solid #2ecc71;text-align:center;">
                <p style="margin:0;font-size:11px;color:#888;">💰 VALOR TOTAL</p>
                <h3 style="margin:0;color:white;font-size:20px;">{df_p["stock"].sum()} <span style="font-size:10px;">UND</span></h3>
                <p style="margin:0;color:#2ecc71;font-size:14px;font-weight:bold;">$ {int(total_valor):,}</p>
            </div>''', unsafe_allow_html=True)

        # 3. ALERTAS DE REPOSICIÓN
        df_alerta = df_p[df_p['stock'] <= 4].sort_values('stock')
        if not df_alerta.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            cols_alerta = st.columns(5)
            st.markdown("<br><p style='text-align:center; color:#888; font-size:13px;'>⚠️ NECESITAN REPOSICIÓN</p>", unsafe_allow_html=True)
            cols = st.columns(5)
            for i, (_, fila) in enumerate(df_alerta.iterrows()):
                color_a = "#ff4b4b" if fila['stock'] == 0 else ("#ffa500" if fila['stock'] <= 2 else "#00f2fe")
                with cols[i % 5]:
                    st.markdown(f'''<div style="background-color:#0e1117;padding:8px;border-radius:8px;border:1px solid {color_a};text-align:center;margin-bottom:5px;">
                        <p style="margin:0;font-size:11px;font-weight:bold;color:white;white-space:nowrap;overflow:hidden;">{fila["nombre"]}</p>
                        <p style="margin:0;font-size:15px;color:{color_a};font-weight:bold;">{fila["stock"]} <span style="font-size:10px;">UND</span></p>
                    </div>''', unsafe_allow_html=True)

        st.markdown("---")

        # 4. TABLAS DETALLADAS POR CATEGORÍA
        # Fila 1: Regulares vs Con Licor
        col_left, col_right = st.columns(2)

        # --- TABLAS DETALLADAS (Ocultando la columna promo visualmente) ---
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            st.markdown("### 🥤 Sin Licor")
            # Mostramos 'precio_visual' en lugar de 'precio'
        with col_left:
            st.subheader("🥤 Sin Licor (Regulares)")
            st.dataframe(df_sin_reg[['nombre', 'stock', 'precio_display']].rename(columns={'precio_display': 'precio'}), 
                         use_container_width=True, hide_index=True)

        with col_right:
            st.subheader("🍸 Con Licor")
            st.dataframe(df_con_lic[['nombre', 'stock', 'precio']], 
                         use_container_width=True, hide_index=True)

        with c_t2:
            st.markdown("### 🍸 Con Licor")
        # Fila 2: Solo si existen Promociones
        if not df_sin_pro.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🔥 Promociones Activas (Sin Licor)")
            st.dataframe(df_sin_pro[['nombre', 'stock', 'precio_display']].rename(columns={'precio_display': 'precio'}), 
                         use_container_width=True, hide_index=True)

    else:
        st.info("No hay productos registrados en la base de datos.")

## --- MÓDULO 2: REGISTRAR VENTA (INTERFAZ POS PREMIUM) ---
elif menu == "Registrar Venta":
    st.markdown("<h1 style='text-align: center; color: #00f2fe;'>🛒 Punto de Venta Premium</h1>", unsafe_allow_html=True)
    
    if 'carrito' not in st.session_state:
        st.session_state.carrito = []

    df_p = cargar_datos("productos")
    df_c = cargar_datos("clientes")
    
    if not df_p.empty:
        # Limpieza y preparación
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
        df_p['id_unico'] = df_p['nombre'] + " - " + df_p['tipo']

        # --- PASO 1: SELECCIÓN ---
        st.markdown("### 1️⃣ Selección de Productos")
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            
            with c1:
                # Añadimos las opciones de PROMO manualmente al selectbox o pueden estar en tu Excel
                opciones_base = df_p['id_unico'].tolist()
                promos = ["🎁 PROMO - Con Licor ($36k)", "🎁 PROMO - Sin Licor ($30k)"]
                prod_sel = st.selectbox("Buscar Producto o Promo:", opciones_base + promos)

            with c2:
                # Lógica de Stock para Promos
                es_promo = "🎁 PROMO" in prod_sel
                if es_promo:
                    tipo_a_descontar = "Con Licor" if "Con Licor" in prod_sel else "Sin Licor"
                    # El stock disponible para la promo es la suma de todo lo que sea de ese tipo
                    stock_disp = df_p[df_p['tipo'] == tipo_a_descontar]['stock'].sum()
                    precio_sugerido = 36000 if "Con Licor" in prod_sel else 30000
                else:
                    info_p = df_p[df_p['id_unico'] == prod_sel].iloc[0]
                    stock_disp = info_p['stock']
                    precio_sugerido = int(info_p['precio'])
                
                cant_v = st.number_input("Cantidad:", min_value=1, max_value=max(1, stock_disp), step=1)
                st.caption(f"Stock Disponible: {stock_disp} und")

            with c3:
                precio_final = st.number_input("Precio Unitario ($):", value=precio_sugerido, step=500)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Agregar", use_container_width=True):
                    if stock_disp >= cant_v:
                        nombre_item = prod_sel if not es_promo else f"PROMO {tipo_a_descontar}"
                        st.session_state.carrito.append({
                            "id": prod_sel,
                            "nombre": nombre_item,
                            "tipo": "Promo" if es_promo else info_p['tipo'],
                            "tipo_descuento": tipo_a_descontar if es_promo else None,
                            "cantidad": cant_v,
                            "precio_u": precio_final,
                            "subtotal": cant_v * precio_final
                        })
                        st.toast(f"Añadido: {nombre_item}")
                    else:
                        st.error("Existencias insuficientes")

        # --- PASO 2: CARRITO Y CLIENTE ---
        if st.session_state.carrito:
            st.markdown("### 2️⃣ Resumen de Venta")
            
            col_tabla, col_card = st.columns([2, 1])
            
            with col_tabla:
                df_carrito = pd.DataFrame(st.session_state.carrito)
                st.dataframe(df_carrito[['nombre', 'cantidad', 'precio_u', 'subtotal']], 
                             use_container_width=True, hide_index=True)
                
                if st.button("🗑️ Vaciar Carrito", type="secondary"):
                    st.session_state.carrito = []
                    st.rerun()

            with col_card:
                total_v = df_carrito['subtotal'].sum()
                st.markdown(f"""
                    <div style="background-color: #1e1e1e; padding: 20px; border-radius: 15px; border: 2px solid #2ecc71; text-align: center;">
                        <p style="margin:0; color: #888;">TOTAL A COBRAR</p>
                        <h1 style="margin:0; color: #2ecc71;">$ {total_v:,}</h1>
                        <p style="margin:0; color: #555;">{df_carrito['cantidad'].sum()} unidades</p>
                    </div>
                """, unsafe_allow_html=True)

            # --- PASO 3: FINALIZAR ---
            st.markdown("### 3️⃣ Finalizar Transacción")
            with st.container(border=True):
                f1, f2, f3 = st.columns(3)
                with f1:
                    cliente_v = st.selectbox("Cliente:", df_c['empresa'].tolist()) if not df_c.empty else st.text_input("Cliente:")
                with f2:
                    metodo_p = st.selectbox("Método de Pago:", ["Transferencia", "Efectivo", "Nequi/Daviplata"])
                with f3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🚀 CONFIRMAR Y COBRAR", type="primary", use_container_width=True):
                        try:
                            # --- LÓGICA DE DESCUENTO DE INVENTARIO INTELIGENTE ---
                            for item in st.session_state.carrito:
                                if item['tipo'] == "Promo":
                                    # Descontamos del primero que encuentre con stock de ese tipo
                                    # O puedes elegir un producto específico 'Base' para esto
                                    tipo_target = item['tipo_descuento']
                                    idx = df_p[df_p['tipo'] == tipo_target].index[0]
                                    df_p.at[idx, 'stock'] -= item['cantidad']
                                else:
                                    idx = df_p[df_p['id_unico'] == item['id']].index[0]
                                    df_p.at[idx, 'stock'] -= item['cantidad']

                            # Guardar en Historial
                            df_hist = cargar_datos("ventas")
                            nuevos = pd.DataFrame([{
                                "fecha": datetime.now().strftime("%Y-%m-%d"),
                                "cliente": cliente_v,
                                "producto": item['nombre'],
                                "cantidad": item['cantidad'],
                                "precio_unitario": item['precio_u'],
                                "total": item['subtotal'],
                                "metodo": metodo_p
                            } for item in st.session_state.carrito])
                            
                            conn.update(worksheet="productos", data=df_p.drop(columns=['id_unico']))
                            conn.update(worksheet="ventas", data=pd.concat([df_hist, nuevos], ignore_index=True))
                            
                            st.cache_data.clear()
                            st.success("¡Venta Exitosa!")
                            st.balloons()
                            st.session_state.carrito = []
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.info("👋 El carrito está esperando productos.")

# --- MÓDULO 3: ENTRADA PRODUCCIÓN (REDISEÑO PREMIUM) ---
elif menu == "Entrada Producción":
    st.markdown("<h1 style='text-align: center;'>📥 Ingreso de Producción</h1>", unsafe_allow_html=True)
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # Asegurar tipos de datos para evitar errores de cálculo
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['id_unico'] = df_p['nombre'].astype(str) + " - " + df_p['tipo'].astype(str)
        
        # --- SECCIÓN DE VISTA PREVIA ---
        st.markdown("### 🔍 Estado Actual del Sabor")
        col_sel, col_info = st.columns([2, 1])
        
        with col_sel:
            seleccion = st.selectbox(
                "Busca y selecciona el sabor que acabas de producir:", 
                options=df_p['id_unico'].tolist(),
                help="Elige el sabor exacto para actualizar su inventario."
            )
            
        # Extraer info del sabor seleccionado para mostrar una tarjeta visual
        datos_sabor = df_p[df_p['id_unico'] == seleccion].iloc[0]
        stock_hoy = datos_sabor['stock']
        tipo_sabor = datos_sabor['tipo']
        
        with col_info:
            # Tarjeta visual del stock actual antes de la carga
            color_tarjeta = "#00f2fe" if "Sin" in tipo_sabor else "#ff4b4b"
            st.markdown(f"""
                <div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; border-left: 5px solid {color_tarjeta}; text-align: center;">
                    <p style="margin: 0; font-size: 14px; color: #888;">STOCK ACTUAL</p>
                    <h2 style="margin: 0; color: white;">{stock_hoy} <span style="font-size: 15px;">und</span></h2>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # --- FORMULARIO DE CARGA ---
        with st.form("form_entrada_pro", clear_on_submit=True):
            st.markdown("### 📦 Registro de Nueva Tanda")
            c1, c2 = st.columns(2)
            
            with c1:
                cantidad = st.number_input("Cantidad de botellas producidas:", min_value=1, step=1, help="Ingresa solo el número de botellas nuevas.")
            
            with c2:
                st.markdown("<br>", unsafe_allow_html=True)
                confirmar = st.form_submit_button("🚀 ACTUALIZAR INVENTARIO", use_container_width=True)
            
            if confirmar:
                idx = df_p[df_p['id_unico'] == seleccion].index[0]
                nuevo_total = stock_hoy + cantidad
                df_p.at[idx, 'stock'] = nuevo_total
                
                # Limpieza de columna temporal
                df_para_enviar = df_p.drop(columns=['id_unico'])
                
                try:
                    with st.spinner("Sincronizando con la nube..."):
                        conn.update(worksheet="productos", data=df_para_enviar)
                    st.balloons()
                    st.success(f"✅ ¡Inventario Actualizado! {seleccion} ahora tiene {nuevo_total} unidades.")
                    # Pequeña pausa para que el usuario vea el mensaje antes de recargar
                    import time
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error de conexión: {e}")
    else:
        st.warning("⚠️ No hay productos en el catálogo. Primero registra sabores en 'Catálogo Productos'.")


# --- MÓDULO 4: CATÁLOGO PRODUCTOS (DISEÑO MINI TARJETAS) ---
elif menu == "Catálogo Productos":
    st.markdown("<h1 style='text-align: center; color: #00f2fe; font-size: 24px;'>🥤 Catálogo Maestro</h1>", unsafe_allow_html=True)
    df_p = cargar_datos("productos")
    
    # 1. NORMALIZACIÓN DE DATOS (Prevención de errores)
    if not df_p.empty:
        # Mapeo de columna 'Oferta' si existe en Google Sheets
        if 'Oferta' in df_p.columns:
            df_p = df_p.rename(columns={'Oferta': 'promo'})
        
        # Asegurar columnas críticas
        cols_req = ['nombre', 'tipo', 'precio', 'stock', 'promo']
        for c in cols_req:
            if c not in df_p.columns:
                df_p[c] = "No" if c == 'promo' else 0
                
        # Limpieza de tipos de datos
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)

    # --- 2. FORMULARIO DE REGISTRO (Estilizado) ---
    with st.expander("✨ AÑADIR NUEVA REFERENCIA", expanded=False):
        with st.form("nuevo_sabor", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                n = st.text_input("Nombre Sabor")
                t = st.selectbox("Tipo", ["Sin Licor", "Con Licor"])
            with c2:
                promo_val = st.selectbox("¿Es Promo?", ["No", "Si"])
                # Precio sugerido inteligente
                sug = 30000 if (t == "Sin Licor" and promo_val == "Si") else 36000 if t == "Sin Licor" else 40000
                p = st.number_input("Precio ($)", value=sug, step=500)
            
            if st.form_submit_button("🚀 GUARDAR EN CATÁLOGO", use_container_width=True):
                if n:
                    # Guardamos con el nombre original 'Oferta' para Google Sheets
                    nueva_fila = pd.DataFrame([{"nombre": n.strip(), "tipo": t, "precio": p, "stock": 0, "Oferta": promo_val}])
                    # Renombramos 'promo' de vuelta a 'Oferta' antes de concatenar para subir datos
                    df_subir = df_p.rename(columns={'promo': 'Oferta'})
                    df_final = pd.concat([df_subir, nueva_fila], ignore_index=True)
                    try:
                        conn.update(worksheet="productos", data=df_final)
                        st.cache_data.clear()
                        st.success(f"{n} guardado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.markdown("---")

    # --- 3. VISTA DE MINI TARJETAS ---
    if not df_p.empty:
        busqueda = st.text_input("🔍 Buscar sabor...", placeholder="Escribe el sabor")
        df_show = df_p[df_p['nombre'].str.contains(busqueda, case=False, na=False)] if busqueda else df_p

        # Usamos 4 columnas para que sean más pequeñas
        cols = st.columns(4)
        
        for i, (_, fila) in enumerate(df_show.iterrows()):
            with cols[i % 4]:
                # Estilo dinámico
                es_promo = str(fila['promo']).strip().lower() == "si"
                color = "#f1c40f" if es_promo else "#00f2fe"
                badge = "🔥 PROMO" if es_promo else fila['tipo'].upper()
                
                # HTML MINI TARJETA (Ajustado y Espectacular)
                st.markdown(f"""
                    <div style="
                        background-color: #1a1a1a; 
                        padding: 12px; 
                        border-radius: 10px; 
                        border-top: 4px solid {color};
                        margin-bottom: 15px;
                        height: 140px;
                        position: relative;
                        overflow: hidden;
                    ">
                        <div style="
                            position: absolute;
                            top: 5px;
                            right: 5px;
                            background: {color};
                            color: black;
                            padding: 1px 4px;
                            border-radius: 3px;
                            font-size: 8px;
                            font-weight: bold;
                        ">{badge}</div>
                        
                        <h4 style="color: white; font-size: 14px; margin: 15px 0 5px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            {fila['nombre']}
                        </h4>
                        <hr style="border: 0.1px solid #333; margin: 5px 0;">
                        
                        <div style="display: flex; justify-content: space-between; align-items: end; margin-top:10px;">
                            <div>
                                <p style="color: #888; font-size: 10px; margin: 0;">Precio</p>
                                <p style="color: {color}; font-size: 16px; font-weight: bold; margin: 0;">
                                    ${int(fila['precio']):,}
                                </p>
                            </div>
                            <div style="text-align: right;">
                                <p style="color: #888; font-size: 10px; margin: 0;">Stock</p>
                                <p style="color: white; font-size: 18px; font-weight: bold; margin: 0;">
                                    {int(fila['stock'])}
                                </p>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("El catálogo está vacío.")


# --- MÓDULO 5: GESTIÓN CLIENTES (DISEÑO CRM PRO) ---
elif menu == "Gestión Clientes":
    st.markdown("<h1 style='text-align: center; color: #00f2fe;'>🏢 Directorio de Aliados</h1>", unsafe_allow_html=True)
    df_c = cargar_datos("clientes")
    
    # --- 1. INDICADORES SUPERIORES (KPIs) ---
    c1, c2, c3 = st.columns([1, 1, 2])
    
    with c1:
        total_clientes = len(df_c) if not df_c.empty else 0
        st.markdown(f'''
            <div style="background-color:#1a1a1a;padding:15px;border-radius:15px;border-left:5px solid #00f2fe;text-align:center;">
                <p style="margin:0;font-size:12px;color:#888;">CLIENTES ACTIVOS</p>
                <h2 style="margin:0;color:white;">{total_clientes}</h2>
            </div>
        ''', unsafe_allow_html=True)
    
    with c2:
        st.markdown(f'''
            <div style="background-color:#1a1a1a;padding:15px;border-radius:15px;border-left:5px solid #2ecc71;text-align:center;">
                <p style="margin:0;font-size:12px;color:#888;">ESTADO SISTEMA</p>
                <h2 style="margin:0;color:#2ecc71; font-size:20px;">SINCRO ✅</h2>
            </div>
        ''', unsafe_allow_html=True)

    with c3:
        st.info("⚡ **Acción Rápida:** Para actualizar un nombre comercial, utiliza la pestaña de eliminación y regístralo con el nuevo dato.")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2. ACCIONES DINÁMICAS (Pestañas Modernas) ---
    tab_lista, tab_registro, tab_peligro = st.tabs(["📋 Base de Datos", "➕ Nuevo Aliado", "⚠️ Zona de Control"])

    # PESTAÑA: LISTADO CON BUSCADOR DINÁMICO
    with tab_lista:
        if not df_c.empty:
            col_search1, col_search2 = st.columns([2, 1])
            with col_search1:
                busqueda = st.text_input("🔍 Filtrar por Nombre Comercial...", placeholder="Escribe para buscar...")
            
            df_display = df_c.copy()
            if busqueda:
                df_display = df_display[df_display['empresa'].str.contains(busqueda, case=False, na=False)]
            
            # Tabla estilizada
            st.dataframe(
                df_display.sort_values("empresa").rename(columns={"empresa": "NOMBRE DEL ALIADO COMERCIAL"}),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay aliados registrados aún.")

    # PESTAÑA: REGISTRO PROFESIONAL
    with tab_registro:
        st.markdown("### 🖋️ Registrar Nuevo Aliado")
        with st.container(border=True):
            nombre_c = st.text_input("Nombre de la Empresa o Persona", placeholder="Ej: RESTAURANTE EL MUELLE")
            confirmar_reg = st.checkbox("Confirmo que los datos son correctos")
            
            if st.button("🚀 VINCULAR CLIENTE AL SISTEMA", use_container_width=True):
                if nombre_c and confirmar_reg:
                    nombre_limpio = nombre_c.strip().upper()
                    if not df_c.empty and nombre_limpio in df_c['empresa'].str.upper().values:
                        st.error(f"El cliente '{nombre_limpio}' ya existe en la base de datos.")
                    else:
                        nueva_c = pd.DataFrame([{"empresa": nombre_limpio}])
                        df_res_c = pd.concat([df_c, nueva_c], ignore_index=True) if not df_c.empty else nueva_c
                        try:
                            conn.update(worksheet="clientes", data=df_res_c)
                            st.balloons()
                            st.success(f"¡{nombre_limpio} ha sido vinculado exitosamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Falla de conexión: {e}")
                else:
                    st.warning("Por favor ingresa un nombre y marca la casilla de confirmación.")

    # PESTAÑA: ZONA DE PELIGRO (Eliminación con doble validación)
    with tab_peligro:
        if not df_c.empty:
            st.markdown("<h3 style='color: #ff4b4b;'>🚨 Gestión de Bajas</h3>", unsafe_allow_html=True)
            st.write("Selecciona un cliente para revocar su acceso al sistema de facturación.")
            
            cliente_a_borrar = st.selectbox("Cliente a eliminar:", ["--- SELECCIONAR ---"] + df_c['empresa'].sort_values().tolist())
            
            if cliente_a_borrar != "--- SELECCIONAR ---":
                st.warning(f"¿Estás seguro de eliminar a **{cliente_a_borrar}**? Esta acción no se puede deshacer.")
                
                # Input de seguridad
                check_delete = st.text_input(f"Escribe 'ELIMINAR' para confirmar")
                
                if st.button("🔥 EJECUTAR BAJA DEFINITIVA", use_container_width=True):
                    if check_delete == "ELIMINAR":
                        df_nuevo_c = df_c[df_c['empresa'] != cliente_a_borrar]
                        try:
                            conn.update(worksheet="clientes", data=df_nuevo_c)
                            st.success(f"El registro de '{cliente_a_borrar}' ha sido borrado.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error técnico: {e}")
                    else:
                        st.error("Palabra de confirmación incorrecta.")
        else:
            st.info("No hay datos para gestionar.")

# --- MÓDULO 6: CENTRO DE INTELIGENCIA (ORGANIZACIÓN PROFESIONAL) ---
elif menu == "Historial de Ventas":
    st.markdown("""
        <h1 style='text-align: center; color: #00f2fe; margin-bottom: 20px;'>
            📋 Centro de Inteligencia de Ventas
        </h1>
    """, unsafe_allow_html=True)
    
    df_v = cargar_datos("ventas")
    
    if not df_v.empty:
        # Procesamiento de datos
        df_v['total'] = pd.to_numeric(df_v['total'], errors='coerce').fillna(0)
        df_v['cantidad'] = pd.to_numeric(df_v['cantidad'], errors='coerce').fillna(0).astype(int)
        df_v['fecha'] = pd.to_datetime(df_v['fecha']).dt.date
        
        # --- ÁREA DE CONTROL ---
        with st.expander("🛠️ HERRAMIENTAS DE FILTRADO", expanded=False):
            f1, f2, f3 = st.columns(3)
            with f1:
                filtro_cliente = st.multiselect("👤 Filtrar Cliente", options=sorted(df_v['cliente'].unique()))
            with f2:
                filtro_metodo = st.multiselect("💳 Método de Pago", options=df_v['metodo'].unique())
            with f3:
                rango = st.date_input("📅 Rango de Fechas", [df_v['fecha'].min(), df_v['fecha'].max()])

        # Aplicar Filtros
        df_f = df_v.copy()
        if filtro_cliente: df_f = df_f[df_f['cliente'].isin(filtro_cliente)]
        if filtro_metodo: df_f = df_f[df_f['metodo'].isin(filtro_metodo)]
        if len(rango) == 2:
            df_f = df_f[(df_f['fecha'] >= rango[0]) & (df_f['fecha'] <= rango[1])]

        # --- KPI DASHBOARD (DISEÑO GLASSMISM) ---
        m1, m2, m3, m4 = st.columns(4)
        
        def draw_kpi(label, value, color, icon):
            st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.03); padding: 15px; border-radius: 12px; 
                            border-top: 3px solid {color}; text-align: center;">
                    <p style="margin:0; font-size: 11px; color: #888; text-transform: uppercase;">{icon} {label}</p>
                    <h2 style="margin:0; color: white; font-size: 22px;">{value}</h2>
                </div>
            """, unsafe_allow_html=True)

        total_d = df_f['total'].sum()
        total_u = df_f['cantidad'].sum()
        promedio = total_d / len(df_f) if len(df_f) > 0 else 0
        
        with m1: draw_kpi("Ingresos", f"$ {total_d:,.0f}", "#2ecc71", "💰")
        with m2: draw_kpi("Unidades", f"{total_u:,}", "#00f2fe", "🍦")
        with m3: draw_kpi("Ticket Prom.", f"$ {promedio:,.0f}", "#f1c40f", "📈")
        with m4: draw_kpi("Órdenes", f"{len(df_f)}", "#9b59b6", "🧾")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- SECCIÓN CENTRAL: RANKING DE CLIENTES ---
        st.markdown("#### 🏆 Top Clientes (Mayor Inversión)")
        ventas_cli = df_f.groupby('cliente')['total'].sum().reset_index().sort_values('total', ascending=False).head(10)
        
        st.dataframe(
            ventas_cli, 
            column_config={
                "cliente": "Nombre del Cliente / Empresa",
                "total": st.column_config.ProgressColumn(
                    "Volumen de Compra", 
                    format="$ %d", 
                    min_value=0, 
                    max_value=float(ventas_cli['total'].max() if not ventas_cli.empty else 100)
                )
            },
            hide_index=True, 
            use_container_width=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # --- SECCIÓN FINAL: LOG DE TRANSACCIONES DETALLADO ---
        st.markdown("#### 📄 Registro Detallado de Movimientos")
        st.dataframe(
            df_f.sort_values('fecha', ascending=False),
            column_config={
                "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "cliente": "Cliente",
                "producto": "Sabor Vendido",
                "cantidad": st.column_config.NumberColumn("Und", format="%d"),
                "precio_unitario": st.column_config.NumberColumn("P. Unit", format="$ %d"),
                "total": st.column_config.NumberColumn("Subtotal", format="$ %d"),
                "metodo": "Pago"
            },
            use_container_width=True,
            hide_index=True
        )

        # Botón de exportación minimalista
        csv = df_f.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Historial Completo (CSV)",
            data=csv,
            file_name=f'ventas_bajo_cero.csv',
            mime='text/csv',
            use_container_width=True
        )

    else:
        st.info("🕒 No se han detectado ventas registradas para mostrar el análisis.")
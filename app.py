import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Bajo Cero - Gestión de Inventario",
    page_icon="❄️",
    layout="wide"
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

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    # Solución al MediaFileStorageError: Si logo.png no existe, muestra texto
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.title("❄️ BAJO CERO")
    
    st.markdown("---")
    menu = st.radio(
        "MENÚ DE NAVEGACIÓN",
        ["📊 Panel Principal", "🛒 Registrar Venta", "📥 Entrada Producción", "🥤 Catálogo Productos", "🏢 Gestión Clientes", "📋 Historial de Ventas"]
    )
    st.markdown("---")
    if st.button("🔄 Refrescar Datos"):
        st.cache_data.clear()
        st.rerun()

# --- MÓDULO 1: PANEL PRINCIPAL (RESTAURADO + PROMO) ---
if menu == "📊 Panel Principal":
    st.markdown("<h1 style='text-align: center; color: #00f2fe;'>📊 Resumen de Inventario</h1>", unsafe_allow_html=True)
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # 1. SOLUCIÓN AL ERROR: Asegurar que existe la columna 'promo' internamente
        if 'promo' not in df_p.columns:
            df_p['promo'] = "No"
            
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
        
        # 2. CÁLCULO DE VALORIZACIÓN DINÁMICA
        # Si es 'Sin Licor' y 'Si' es promo, el valor es $30.000 x stock
        def calcular_valor_real(row):
            tipo = str(row['tipo']).strip()
            es_promo = str(row['promo']).strip()
            if tipo == "Sin Licor" and es_promo == "Si":
                return row['stock'] * 30000
            return row['stock'] * row['precio']

        df_p['valor_total_item'] = df_p.apply(calcular_valor_real, axis=1)
        
        # 3. FILTROS PARA TARJETAS
        df_sin = df_p[df_p['tipo'].str.contains("Sin", case=False, na=False)]
        df_con = df_p[df_p['tipo'].str.contains("Con", case=False, na=False)]
        
        valor_sin = int(df_sin['valor_total_item'].sum())
        valor_con = int(df_con['valor_total_item'].sum())
        total_global = valor_sin + valor_con

        # --- TARJETAS DE VALOR (TUS TARJETAS ORIGINALES) ---
        c_val1, c_val2, c_val3 = st.columns(3)
        
        with c_val1:
            st.markdown(f"""
                <div style="background-color: #1a1a1a; padding: 10px; border-radius: 10px; border-left: 5px solid #ff4b4b; text-align: center;">
                    <p style="margin:0; font-size:12px; color:#888;">🥤 SIN LICOR</p>
                    <h3 style="margin:0; color:white; font-size:18px;">{df_sin['stock'].sum()} <span style="font-size:10px;">UND</span></h3>
                    <p style="margin:0; color:#ff4b4b; font-size:14px; font-weight:bold;">$ {valor_sin:,}</p>
                </div>
            """, unsafe_allow_html=True)

        with c_val2:
            st.markdown(f"""
                <div style="background-color: #1a1a1a; padding: 10px; border-radius: 10px; border-left: 5px solid #00f2fe; text-align: center;">
                    <p style="margin:0; font-size:12px; color:#888;">🍸 CON LICOR</p>
                    <h3 style="margin:0; color:white; font-size:18px;">{df_con['stock'].sum()} <span style="font-size:10px;">UND</span></h3>
                    <p style="margin:0; color:#00f2fe; font-size:14px; font-weight:bold;">$ {valor_con:,}</p>
                </div>
            """, unsafe_allow_html=True)

        with c_val3:
            st.markdown(f"""
                <div style="background-color: #1a1a1a; padding: 10px; border-radius: 10px; border-left: 5px solid #2ecc71; text-align: center;">
                    <p style="margin:0; font-size:12px; color:#888;">💰 VALOR TOTAL</p>
                    <h3 style="margin:0; color:white; font-size:18px;">{df_p['stock'].sum()} <span style="font-size:10px;">UND</span></h3>
                    <p style="margin:0; color:#2ecc71; font-size:14px; font-weight:bold;">$ {total_global:,}</p>
                </div>
            """, unsafe_allow_html=True)
        
        # --- ALERTAS DE REPOSICIÓN (TUS ALERTAS ORIGINALES) ---
        df_alerta = df_p[df_p['stock'] <= 4].sort_values('stock')
        
        if not df_alerta.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#666; font-size:13px; margin-bottom:5px;'>⚠️ ALERTAS DE REPOSICIÓN</p>", unsafe_allow_html=True)
            cols_alerta = st.columns(5)
            
            for i, (_, fila) in enumerate(df_alerta.iterrows()):
                color_t = "#ff4b4b" if fila['stock'] == 0 else ("#ffa500" if fila['stock'] <= 2 else "#00f2fe")
                icon = "🚫" if fila['stock'] == 0 else ("⚠️" if fila['stock'] <= 2 else "📉")
                badge_html = f"""
                <div style="background-color: #0e1117; padding: 8px; border-radius: 8px; border: 1px solid {color_t}; text-align: center; margin-bottom: 5px;">
                    <div style="font-size: 14px;">{icon}</div>
                    <p style="margin: 0; font-size: 11px; font-weight: bold; color: white;">{fila['nombre']}</p>
                    <p style="margin: 0; font-size: 14px; color: {color_t}; font-weight: bold;">{fila['stock']} <span style='font-size: 9px;'>UND</span></p>
                </div>
                """
                with cols_alerta[i % 5]:
                    st.markdown(badge_html, unsafe_allow_html=True)
        
        st.markdown("---")
        # --- TABLAS DETALLADAS CON COLUMNA PROMO ---
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<p style='font-size:14px; font-weight:bold; margin-bottom:0;'>🥤 Detalle Sin Licor</p>", unsafe_allow_html=True)
            # Mostramos la columna promo para que veas cuáles son
            st.dataframe(df_sin[['nombre', 'promo', 'stock', 'precio']], use_container_width=True, hide_index=True)
        with c2:
            st.markdown("<p style='font-size:14px; font-weight:bold; margin-bottom:0;'>🍸 Detalle Con Licor</p>", unsafe_allow_html=True)
            st.dataframe(df_con[['nombre', 'stock', 'precio']], use_container_width=True, hide_index=True)
    else:
        st.info("No hay productos registrados.")

## --- MÓDULO 2: REGISTRAR VENTA (INTERFAZ POS PREMIUM) ---
elif menu == "🛒 Registrar Venta":
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
elif menu == "📥 Entrada Producción":
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

# --- MÓDULO 4: CATÁLOGO PRODUCTOS (CON OPCIÓN PROMO) ---
elif menu == "🥤 Catálogo Productos":
    st.title("🥤 Gestión de Catálogo")
    df_p = cargar_datos("productos")
    
    with st.expander("✨ AÑADIR NUEVO SABOR", expanded=False):
        with st.form("nuevo"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("Nombre del Sabor")
            t = c1.selectbox("Tipo", ["Sin Licor", "Con Licor"])
            # Si es Sin Licor, preguntamos si es Promo
            promo_opt = c2.selectbox("¿Es Promoción?", ["No", "Si"])
            
            # Precio sugerido automático
            precio_defecto = 36000
            if t == "Sin Licor" and promo_opt == "Si":
                precio_defecto = 30000
                
            p = c3.number_input("Precio de Venta ($)", min_value=0, step=500, value=precio_defecto)
            
            if st.form_submit_button("Guardar Sabor"):
                if n:
                    # Guardamos la columna 'promo' en el Excel
                    nueva = pd.DataFrame([{"nombre": n.strip(), "tipo": t, "precio": p, "stock": 0, "promo": promo_opt}])
                    df_f = pd.concat([df_p, nueva], ignore_index=True)
                    conn.update(worksheet="productos", data=df_f)
                    st.cache_data.clear()
                    st.rerun()

    if not df_p.empty:
        # Mostramos la tabla con la columna Promo
        st.dataframe(
            df_p[['nombre', 'tipo', 'promo', 'precio', 'stock']].sort_values(['tipo', 'promo']), 
            column_config={
                "promo": st.column_config.SelectboxColumn("Oferta", options=["Si", "No"]),
                "precio": st.column_config.NumberColumn("Precio", format="$ %d")
            },
            use_container_width=True, 
            hide_index=True
        )
# --- MÓDULO 5: GESTIÓN CLIENTES (VERSIÓN COMPLETA CON ELIMINACIÓN) ---
elif menu == "🏢 Gestión Clientes":
    st.markdown("<h1 style='text-align: center;'>🏢 Directorio de Clientes</h1>", unsafe_allow_html=True)
    df_c = cargar_datos("clientes")
    
    # --- MÉTRICAS ---
    if not df_c.empty:
        c1, c2 = st.columns(2)
        c1.metric("Clientes Registrados", f"{len(df_c)} 👤")
        c2.info("💡 Tip: Para editar un nombre, elíminalo y regístralo nuevamente.")
    
    st.markdown("---")

    # --- PESTAÑAS DE ACCIÓN ---
    tab_registro, tab_eliminar = st.tabs(["➕ Registrar Cliente", "🗑️ Eliminar Cliente"])

    # PESTAÑA 1: REGISTRO
    with tab_registro:
        with st.form("form_cli", clear_on_submit=True):
            col_form1, col_form2 = st.columns([2, 1])
            with col_form1:
                nombre_c = st.text_input("🏢 Nombre Comercial / Razón Social", placeholder="Ej: Licorería El Faro")
            with col_form2:
                st.markdown("<br>", unsafe_allow_html=True)
                submit_cli = st.form_submit_button("💾 GUARDAR CLIENTE", use_container_width=True)
            
            if submit_cli:
                if nombre_c:
                    nombre_limpio = nombre_c.strip().upper()
                    if not df_c.empty and nombre_limpio in df_c['empresa'].str.upper().values:
                        st.warning(f"⚠️ El cliente '{nombre_limpio}' ya existe.")
                    else:
                        nueva_c = pd.DataFrame([{"empresa": nombre_limpio}])
                        df_res_c = pd.concat([df_c, nueva_c], ignore_index=True) if not df_c.empty else nueva_c
                        try:
                            conn.update(worksheet="clientes", data=df_res_c)
                            st.success(f"✅ '{nombre_limpio}' registrado.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")

    # PESTAÑA 2: ELIMINACIÓN (ZONA DE PELIGRO)
    with tab_eliminar:
        if not df_c.empty:
            st.markdown("<p style='color: #ff4b4b; font-weight: bold;'>⚠️ ZONA DE PELIGRO</p>", unsafe_allow_html=True)
            with st.form("form_eliminar_cli"):
                cliente_a_borrar = st.selectbox("Selecciona el cliente que deseas eliminar:", df_c['empresa'].sort_values().tolist())
                
                st.write(f"¿Estás seguro de que deseas eliminar a **{cliente_a_borrar}**?")
                confirmar = st.form_submit_button("🔥 ELIMINAR DEFINITIVAMENTE", use_container_width=True)
                
                if confirmar:
                    # Filtrar el dataframe para quitar el cliente seleccionado
                    df_nuevo_c = df_c[df_c['empresa'] != cliente_a_borrar]
                    try:
                        conn.update(worksheet="clientes", data=df_nuevo_c)
                        st.success(f"🗑️ Cliente '{cliente_a_borrar}' eliminado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ No se pudo eliminar: {e}")
        else:
            st.info("No hay clientes para eliminar.")

    st.markdown("---")

    # --- LISTADO VISUAL ---
    st.markdown("### 📋 Aliados Comerciales Actuales")
    if not df_c.empty:
        busqueda = st.text_input("🔍 Buscar cliente...")
        df_filtrado = df_c.copy()
        if busqueda:
            df_filtrado = df_filtrado[df_filtrado['empresa'].str.contains(busqueda, case=False, na=False)]
        
        df_filtrado.columns = ["NOMBRE DE LA EMPRESA"]
        st.dataframe(df_filtrado.sort_values("NOMBRE DE LA EMPRESA"), use_container_width=True, hide_index=True)

# --- MÓDULO 6: CENTRO DE INTELIGENCIA (ORGANIZACIÓN PROFESIONAL) ---
elif menu == "📋 Historial de Ventas":
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
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

# --- MÓDULO 1: PANEL PRINCIPAL (ULTRA COMPACTO & DETALLADO) ---
if menu == "📊 Panel Principal":
    st.markdown("<h1 style='text-align: center;'>📊 Resumen de Inventario</h1>", unsafe_allow_html=True)
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # Limpieza de datos
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
        
        # Cálculos específicos
        df_sin = df_p[df_p['tipo'].str.contains("Sin", case=False, na=False)]
        df_con = df_p[df_p['tipo'].str.contains("Con", case=False, na=False)]
        
        valor_sin = int((df_sin['stock'] * df_sin['precio']).sum())
        valor_con = int((df_con['stock'] * df_con['precio']).sum())
        total_global = valor_sin + valor_con

        # --- NUEVAS TARJETAS DE VALOR INDIVIDUAL ---
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
        
        # --- SECCIÓN DE DISPONIBILIDAD CRÍTICA (MÁS PEQUEÑA) ---
        df_alerta = df_p[df_p['stock'] <= 4].sort_values('stock')
        
        if not df_alerta.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#666; font-size:13px; margin-bottom:5px;'>⚠️ ALERTAS DE REPOSICIÓN</p>", unsafe_allow_html=True)
            
            cols_alerta = st.columns(5) # 5 columnas para que sean más pequeñas
            
            for i, (_, fila) in enumerate(df_alerta.iterrows()):
                color_t = "#ff4b4b" if fila['stock'] == 0 else ("#ffa500" if fila['stock'] <= 2 else "#00f2fe")
                icon = "🚫" if fila['stock'] == 0 else ("⚠️" if fila['stock'] <= 2 else "📉")

                badge_html = f"""
                <div style="
                    background-color: #0e1117; 
                    padding: 8px; 
                    border-radius: 8px; 
                    border: 1px solid {color_t};
                    text-align: center;
                    margin-bottom: 5px;">
                    <div style="font-size: 14px;">{icon}</div>
                    <p style="margin: 0; font-size: 11px; font-weight: bold; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{fila['nombre']}</p>
                    <p style="margin: 0; font-size: 14px; color: {color_t}; font-weight: bold;">{fila['stock']} <span style='font-size: 9px;'>UND</span></p>
                </div>
                """
                with cols_alerta[i % 5]:
                    st.markdown(badge_html, unsafe_allow_html=True)
        
        st.markdown("---")
        # --- TABLAS DETALLADAS ---
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<p style='font-size:14px; font-weight:bold; margin-bottom:0;'>🥤 Detalle Sin Licor</p>", unsafe_allow_html=True)
            st.dataframe(df_sin[['nombre', 'stock', 'precio']], use_container_width=True, hide_index=True)
        with c2:
            st.markdown("<p style='font-size:14px; font-weight:bold; margin-bottom:0;'>🍸 Detalle Con Licor</p>", unsafe_allow_html=True)
            st.dataframe(df_con[['nombre', 'stock', 'precio']], use_container_width=True, hide_index=True)
    else:
        st.info("No hay productos registrados.")

## --- MÓDULO 2: REGISTRAR VENTA (MULTI-PRODUCTO Y PRECIOS FLEXIBLES) ---
elif menu == "🛒 Registrar Venta":
    st.markdown("<h1 style='text-align: center;'>🛒 Registro de Ventas</h1>", unsafe_allow_html=True)
    
    # Inicializar el carrito en la sesión si no existe
    if 'carrito' not in st.session_state:
        st.session_state.carrito = []

    df_p = cargar_datos("productos")
    df_c = cargar_datos("clientes")
    
    if not df_p.empty:
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
        df_p['id_unico'] = df_p['nombre'] + " - " + df_p['tipo']

        # --- ÁREA DE SELECCIÓN DE PRODUCTOS ---
        with st.expander("➕ Añadir Productos a la Venta", expanded=True):
            col_sel, col_cant, col_prec = st.columns([2, 1, 1])
            
            with col_sel:
                prod_sel = st.selectbox("Producto:", df_p['id_unico'].tolist())
                info_p = df_p[df_p['id_unico'] == prod_sel].iloc[0]
                stock_disp = info_p['stock']
                st.caption(f"Stock disponible: {stock_disp} unidades")

            with col_cant:
                cant_v = st.number_input("Cantidad:", min_value=1, max_value=stock_disp if stock_disp > 0 else 1, step=1)
            
            with col_prec:
                # Aquí permitimos editar el precio sugerido
                precio_sugerido = int(info_p['precio'])
                precio_final = st.number_input("Precio Unitario ($):", value=precio_sugerido, step=500)

            if st.button("🛒 Agregar al Carrito", use_container_width=True):
                if stock_disp >= cant_v:
                    # Añadir al carrito (lista de diccionarios)
                    item = {
                        "id": prod_sel,
                        "nombre": info_p['nombre'],
                        "tipo": info_p['tipo'],
                        "cantidad": cant_v,
                        "precio_u": precio_final,
                        "subtotal": cant_v * precio_final
                    }
                    st.session_state.carrito.append(item)
                    st.toast(f"Agregado: {info_p['nombre']}")
                else:
                    st.error("No hay suficiente stock")

        # --- VISUALIZACIÓN DEL CARRITO Y TOTAL ---
        if st.session_state.carrito:
            st.markdown("### 📋 Resumen de la Venta")
            df_carrito = pd.DataFrame(st.session_state.carrito)
            
            # Mostrar tabla del carrito
            st.table(df_carrito[['nombre', 'tipo', 'cantidad', 'precio_u', 'subtotal']])
            
            total_venta = df_carrito['subtotal'].sum()
            
            c_cliente, c_pago, c_final = st.columns([1.5, 1, 1])
            
            with c_cliente:
                cliente_v = st.selectbox("Cliente / Empresa:", df_c['empresa'].tolist()) if not df_c.empty else st.text_input("Cliente:")
            
            with c_pago:
                metodo_p = st.selectbox("Método de Pago:", ["Transferencia", "Efectivo", "Nequi/Daviplata"])
            
            with c_final:
                st.markdown(f"### Total: ${total_venta:,}")
                
                col_b1, col_b2 = st.columns(2)
                if col_b1.button("🗑️ Vaciar", use_container_width=True):
                    st.session_state.carrito = []
                    st.rerun()
                
                if col_b2.button("✅ Cobrar", type="primary", use_container_width=True):
                    try:
                        # 1. ACTUALIZAR STOCK EN DATAFRAME DE PRODUCTOS
                        for item in st.session_state.carrito:
                            idx = df_p[df_p['id_unico'] == item['id']].index[0]
                            df_p.at[idx, 'stock'] -= item['cantidad']
                        
                        # 2. PREPARAR REGISTROS PARA EL HISTORIAL DE VENTAS
                        from datetime import datetime
                        df_ventas_hist = cargar_datos("ventas")
                        
                        nuevos_registros = []
                        for item in st.session_state.carrito:
                            nuevos_registros.append({
                                "fecha": datetime.now().strftime("%Y-%m-%d"),
                                "cliente": cliente_v,
                                "producto": item['id'],
                                "cantidad": item['cantidad'],
                                "precio_unitario": item['precio_u'],
                                "total": item['subtotal'],
                                "metodo": metodo_p
                            })
                        
                        df_actualizado_v = pd.concat([df_ventas_hist, pd.DataFrame(nuevos_registros)], ignore_index=True)
                        
                        # 3. SUBIR A GOOGLE SHEETS
                        conn.update(worksheet="productos", data=df_p.drop(columns=['id_unico']))
                        conn.update(worksheet="ventas", data=df_actualizado_v)
                        
                        # --- EL TRUCO PARA DATOS REALES INMEDIATOS ---
                        st.cache_data.clear() # Esto borra la memoria vieja y obliga a leer el stock nuevo
                        
                        st.success("¡Venta procesada con éxito!")
                        st.balloons()
                        st.session_state.carrito = [] # Limpiar carrito
                        
                        import time
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
        else:
            st.info("El carrito está vacío. Agrega productos arriba.")

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

# --- MÓDULO 4: CATÁLOGO PRODUCTOS ---
elif menu == "🥤 Catálogo Productos":
    st.title("🥤 Gestión de Catálogo")
    df_p = cargar_datos("productos")
    
    with st.expander("✨ AÑADIR NUEVO SABOR", expanded=False):
        with st.form("nuevo"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nombre")
            t = c1.selectbox("Tipo", ["Sin Licor", "Con Licor"])
            p = c2.number_input("Precio", min_value=0, step=500, value=36000)
            if st.form_submit_button("Guardar"):
                if n:
                    nueva = pd.DataFrame([{"nombre": n.strip(), "tipo": t, "precio": p, "stock": 0}])
                    df_f = pd.concat([df_p, nueva], ignore_index=True)
                    conn.update(worksheet="productos", data=df_f)
                    st.rerun()

    if not df_p.empty:
        st.dataframe(df_p[['nombre', 'tipo', 'precio', 'stock']].sort_values('tipo'), use_container_width=True, hide_index=True)

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
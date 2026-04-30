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

# --- MÓDULO 1: PANEL PRINCIPAL (ESTILO SINCRONIZADO) ---
if menu == "📊 Panel Principal":
    st.markdown("<h1 style='text-align: center;'>📊 Resumen de Inventario</h1>", unsafe_allow_html=True)
    df_p = cargar_datos("productos")
    
    if not df_p.empty:
        # Asegurar datos numéricos
        df_p['stock'] = pd.to_numeric(df_p['stock'], errors='coerce').fillna(0).astype(int)
        df_p['precio'] = pd.to_numeric(df_p['precio'], errors='coerce').fillna(0).astype(int)
        
        # Cálculos de métricas
        df_sin = df_p[df_p['tipo'].str.contains("Sin", case=False, na=False)]
        df_con = df_p[df_p['tipo'].str.contains("Con", case=False, na=False)]
        
        valor_inventario = int((df_p['stock'] * df_p['precio']).sum())

        # --- MÉTRICAS SUPERIORES ---
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 Valor Total", f"$ {valor_inventario:,}".replace(",", "."))
        m2.metric("🥤 Total Sin Licor", f"{df_sin['stock'].sum()} und")
        m3.metric("🍸 Total Con Licor", f"{df_con['stock'].sum()} und")
        
        # --- SECCIÓN DE DISPONIBILIDAD CRÍTICA ---
        df_alerta = df_p[df_p['stock'] <= 4].sort_values('stock')
        
        if not df_alerta.empty:
            st.markdown("---")
            # Título central con color dinámico (Cian para resaltar)
            st.markdown("""
                <div style='text-align: center; margin-bottom: 20px;'>
                    <h3 style='color: #00f2fe; font-size: 26px; font-weight: bold; margin-bottom: 0;'>🧊 DISPONIBILIDAD CRÍTICA</h3>
                    <p style='color: #666; font-size: 14px;'>Reponer estos sabores de inmediato</p>
                </div>
            """, unsafe_allow_html=True)
            
            cols_alerta = st.columns(4)
            
            for i, (_, fila) in enumerate(df_alerta.iterrows()):
                # Definición de colores según el stock para sincronizar todo el cuadro
                if fila['stock'] == 0:
                    color_tema = "#ff4b4b" # Rojo
                    icon = "🚫"
                elif fila['stock'] <= 2:
                    color_tema = "#ffa500" # Naranja
                    icon = "⚠️"
                else:
                    color_tema = "#00f2fe" # Cian
                    icon = "📉"

                badge_html = f"""
                <div style="
                    background-color: #1a1a1a; 
                    padding: 20px; 
                    border-radius: 15px; 
                    border: 2px solid {color_tema};
                    text-align: center;
                    margin-bottom: 15px;
                    box-shadow: 0px 4px 20px rgba(0,0,0,0.4);">
                    <div style="font-size: 35px; margin-bottom: 10px;">{icon}</div>
                    <p style="margin: 0; font-size: 18px; font-weight: bold; color: {color_tema};">{fila['nombre']}</p>
                    <p style="margin: 5px 0; font-size: 24px; color: white; font-weight: bold;">{fila['stock']} <span style='font-size: 14px; opacity:0.8;'>UND</span></p>
                    <div style="
                        display: inline-block;
                        padding: 2px 10px;
                        border-radius: 5px;
                        background-color: {color_tema}33; 
                        color: {color_tema};
                        font-size: 10px;
                        font-weight: bold;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        border: 1px solid {color_tema};">
                        {fila['tipo']}
                    </div>
                </div>
                """
                with cols_alerta[i % 4]:
                    st.markdown(badge_html, unsafe_allow_html=True)
        
        st.markdown("---")
        # --- TABLAS DETALLADAS ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🥤 Detalle Sin Licor")
            st.dataframe(df_sin[['nombre', 'stock', 'precio']], use_container_width=True, hide_index=True)
        with c2:
            st.subheader("🍸 Detalle Con Licor")
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

# --- MÓDULO 6: HISTORIAL DE VENTAS (CENTRO DE CONTROL) ---
elif menu == "📋 Historial de Ventas":
    st.markdown("<h1 style='text-align: center;'>📋 Registro Histórico de Ventas</h1>", unsafe_allow_html=True)
    
    df_v = cargar_datos("ventas")
    
    if not df_v.empty:
        # Asegurar formatos de datos
        df_v['total'] = pd.to_numeric(df_v['total'], errors='coerce').fillna(0)
        df_v['fecha'] = pd.to_datetime(df_v['fecha']).dt.date
        
        # --- FILTROS INTELIGENTES ---
        st.markdown("### 🔍 Filtros de Búsqueda")
        f1, f2, f3 = st.columns(3)
        
        with f1:
            filtro_cliente = st.multiselect("Filtrar por Cliente:", options=df_v['cliente'].unique())
        with f2:
            filtro_metodo = st.multiselect("Método de Pago:", options=df_v['metodo'].unique())
        with f3:
            # Rango de fechas
            fecha_min = df_v['fecha'].min()
            fecha_max = df_v['fecha'].max()
            rango = st.date_input("Rango de Fechas:", [fecha_min, fecha_max])

        # Aplicar Filtros
        df_filtrado = df_v.copy()
        if filtro_cliente:
            df_filtrado = df_filtrado[df_filtrado['cliente'].isin(filtro_cliente)]
        if filtro_metodo:
            df_filtrado = df_filtrado[df_filtrado['metodo'].isin(filtro_metodo)]
        if len(rango) == 2:
            df_filtrado = df_filtrado[(df_filtrado['fecha'] >= rango[0]) & (df_filtrado['fecha'] <= rango[1])]

        st.markdown("---")

        # --- MÉTRICAS DE VENTAS FILTRADAS ---
        m1, m2, m3 = st.columns(3)
        total_dinero = df_filtrado['total'].sum()
        total_unidades = df_filtrado['cantidad'].sum()
        ticket_promedio = total_dinero / len(df_filtrado) if len(df_filtrado) > 0 else 0

        m1.metric("💰 Ingresos Totales", f"$ {total_dinero:,.0f}".replace(",", "."))
        m2.metric("📦 Unidades Vendidas", f"{total_unidades} und")
        m3.metric("📈 Ticket Promedio", f"$ {ticket_promedio:,.0f}".replace(",", "."))

        # --- TABLA DE DATOS ESTILIZADA ---
        st.markdown("### 📄 Detalle de Movimientos")
        
        # Formatear columnas para la vista
        df_v_style = df_filtrado.copy()
        df_v_style.columns = [c.upper() for c in df_v_style.columns]
        
        st.dataframe(
            df_v_style.sort_values(by="FECHA", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        # --- BOTÓN PARA DESCARGAR ---
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte en CSV",
            data=csv,
            file_name='ventas_bajo_cero.csv',
            mime='text/csv',
        )

    else:
        st.info("Aún no se han registrado ventas en el sistema.")
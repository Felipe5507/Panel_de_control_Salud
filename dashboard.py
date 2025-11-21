import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Monitor de Salud Colombia", layout="wide", page_icon="🏥")

# --- ESTILOS CSS MEJORADOS ---
st.markdown("""
    <style>
    /* Color de fondo general con gradiente */
    .main { 
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        background-attachment: fixed;
    }
    
    /* Contenedor principal */
    .block-container {
        padding-top: 2rem;
    }
    
    /* Títulos principales */
    h1 { 
        color: #0A5F6D;
        font-size: 2.5em;
        font-weight: 700;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
    }
    
    h2 {
        color: #0A9396;
        border-bottom: 3px solid #0A9396;
        padding-bottom: 0.5rem;
    }
    
    h3 { 
        color: #0A9396;
    }
    
    /* Métricas mejoradas */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
        border: 2px solid #0A9396;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(10, 147, 150, 0.15);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 25px rgba(10, 147, 150, 0.25);
    }

    /* --- PERSONALIZACIÓN DE PESTAÑAS (TABS) --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        width: 100%;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        flex-grow: 1;
        background-color: #E8EAF6;
        border-radius: 10px;
        color: #404040;
        font-weight: 600;
        border: 2px solid #D1D5DB;
        transition: all 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0A9396 0%, #07777A 100%);
        color: #FFFFFF;
        border: 2px solid #0A9396;
        box-shadow: 0 4px 12px rgba(10, 147, 150, 0.3);
    }
    
    /* Divisores */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, #0A9396, transparent);
    }
    
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS DESDE GOOGLE DRIVE ---
import requests
import io

@st.cache_data
def load_data():
    # URL de descarga directa desde Google Drive (archivo Excel compartido)
    # ID del archivo: 1k_L9iafaaJm5eWJnqhy6961tiIzDEGab
    file_id = "1k_L9iafaaJm5eWJnqhy6961tiIzDEGab"
    drive_url = f"https://drive.google.com/uc?id={file_id}&export=download"
    
    try:
        # Descargar el archivo con sesión para manejar redirects
        session = requests.Session()
        response = session.get(drive_url, stream=True)
        
        # Si Google Drive redirige, seguir el redirect
        if "drive.google.com" in response.url:
            # Obtener el token de confirmación
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    drive_url += f"&confirm={value}"
            response = session.get(drive_url, stream=True)
        
        response.raise_for_status()
        
        # Leer como Excel desde bytes
        excel_file = io.BytesIO(response.content)
        
        # Cargar datos por departamento
        df_dept = pd.read_excel(excel_file, sheet_name='CoberturaDepartamento', header=1)
        df_dept = df_dept.dropna(subset=['Departamento'])
        df_dept = df_dept[df_dept['Departamento'] != 'Total general'].copy()
        df_dept = df_dept[['Departamento', 'Contributivo', 'Subsidiado', 'Excepción & Especiales', 'Afiliados']].copy()
        df_dept = df_dept.rename(columns={'Departamento': 'Región', 'Afiliados': 'Total', 'Excepción & Especiales': 'Excepción'})
        df_dept['Contributivo'] = pd.to_numeric(df_dept['Contributivo'], errors='coerce')
        df_dept['Subsidiado'] = pd.to_numeric(df_dept['Subsidiado'], errors='coerce')
        df_dept['Excepción'] = pd.to_numeric(df_dept['Excepción'], errors='coerce')
        df_dept['Total'] = pd.to_numeric(df_dept['Total'], errors='coerce')
        df_dept['% Contributivo'] = (df_dept['Contributivo'] / df_dept['Total'] * 100).round(2)
        df_dept['% Subsidiado'] = (df_dept['Subsidiado'] / df_dept['Total'] * 100).round(2)
        df_dept['% Excepción'] = (df_dept['Excepción'] / df_dept['Total'] * 100).round(2)
        
        # Cargar datos de EPS
        df_eps = pd.read_excel(excel_file, sheet_name='EPS', header=2)
        df_eps = df_eps.dropna(subset=['EPS'])
        df_eps = df_eps[df_eps['EPS'] != 'Total general'].copy()
        df_eps = df_eps[['EPS', 'TOTAL AFILIADOS', 'PORCENTAJE(%)', '% Contributivo', '% Subsidiado', '% Especiales/Excep']].copy()
        df_eps = df_eps.rename(columns={
            'TOTAL AFILIADOS': 'Total Afiliados',
            'PORCENTAJE(%)': 'Market Share (%)',
            '% Contributivo': '% Contributivo',
            '% Subsidiado': '% Subsidiado',
            '% Especiales/Excep': '% Excepción'
        })
        for col in ['Total Afiliados', 'Market Share (%)', '% Contributivo', '% Subsidiado', '% Excepción']:
            df_eps[col] = pd.to_numeric(df_eps[col], errors='coerce')
        df_eps = df_eps.dropna(subset=['Total Afiliados'])
        
        return df_dept, df_eps
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return None, None

# Cargar los datos
df_dept, df_eps = load_data()

# --- SIDEBAR MEJORADO ---
st.sidebar.image("https://www.uniremington.edu.co/wp-content/uploads/2023/06/Logo-Uniremington-2023-H-C.png", width=200)

# Estilos mejorados para botones
st.sidebar.markdown("""
    <style>
    /* Contenedor de selección */
    .selector-container {
        background: linear-gradient(135deg, #E8F4F8 0%, #F0F8FB 100%);
        border: 2px solid #0A9396;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
    }
    
    /* Título del selector */
    .selector-title {
        color: #0A5F6D;
        font-size: 1.1em;
        font-weight: 700;
        margin-bottom: 15px;
        display: block;
    }
    
    /* Contenedor de botones */
    .button-group {
        display: flex;
        gap: 10px;
        width: 100%;
    }
    
    /* Botones de selección */
    .selector-btn {
        flex: 1;
        padding: 12px;
        border-radius: 8px;
        border: 2px solid #D1D5DB;
        background-color: #FFFFFF;
        color: #404040;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        font-size: 0.95em;
    }
    
    .selector-btn:hover {
        border-color: #0A9396;
        background-color: #F0F8FB;
        transform: translateY(-2px);
    }
    
    .selector-btn.active {
        background: linear-gradient(135deg, #0A9396 0%, #07777A 100%);
        color: #FFFFFF;
        border-color: #0A9396;
        box-shadow: 0 4px 12px rgba(10, 147, 150, 0.3);
    }
    
    /* Slider mejorado */
    .slider-label {
        color: #0A5F6D;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    
    /* Info box mejorado */
    .info-box {
        background: linear-gradient(135deg, #FFF3CD 0%, #FFFAED 100%);
        border-left: 4px solid #FFC107;
        padding: 12px;
        border-radius: 6px;
        margin-top: 20px;
        font-size: 0.9em;
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.markdown("<span class='selector-title'>📊 Tipo de Análisis</span>", unsafe_allow_html=True)

# Botones estilizados uno debajo del otro
if st.sidebar.button("📊 Departamento", key="btn_dept", use_container_width=True):
    st.session_state.analysis_mode = "📊 Por Departamento"

if st.sidebar.button("🏥 EPS", key="btn_eps", use_container_width=True):
    st.session_state.analysis_mode = "🏥 Por EPS"

# Obtener modo de análisis con persistencia
if 'analysis_mode' not in st.session_state:
    st.session_state.analysis_mode = "📊 Por Departamento"

analysis_mode = st.session_state.analysis_mode

st.sidebar.divider()

st.sidebar.markdown("<span class='slider-label'>🔝 Principales entidades a visualizar</span>", unsafe_allow_html=True)
top_n = st.sidebar.slider("Selecciona la cantidad:", 5, 35, 10, label_visibility="collapsed")

# --- TÍTULO PRINCIPAL ---
st.markdown("<h1>🏥 Monitor Integrado de Salud en Colombia</h1>", unsafe_allow_html=True)
st.markdown("""
**Fuente:** [Ministerio de Salud - CIFRAS OCTUBRE 2025](https://www.minsalud.gov.co/proteccionsocial/paginas/cifras-aseguramiento-salud.aspx) 
| **Cobertura:** Nacional (32 Departamentos + 46 EPS)
""")
st.markdown("---")

# ==========================================
# ANÁLISIS POR DEPARTAMENTO
# ==========================================
if analysis_mode == "📊 Por Departamento":
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 VISIÓN GENERAL", "💼 R. CONTRIBUTIVO", "🤝 R. SUBSIDIADO", "⚠️ R. EXCEPCIÓN", "📋 DATOS"])
    
    # --- PESTAÑA 1: VISIÓN GENERAL ---
    with tab1:
        st.markdown("## Panorama Nacional por Región")
        
        # KPIs
        total_sistema = df_dept['Total'].sum()
        total_contributivo = df_dept['Contributivo'].sum()
        total_subsidiado = df_dept['Subsidiado'].sum()
        total_excepcion = df_dept['Excepción'].sum()
        pct_subsidiado = (total_subsidiado / total_sistema * 100)
        pct_contributivo = (total_contributivo / total_sistema * 100)
        pct_excepcion = (total_excepcion / total_sistema * 100)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("🇨🇴 Total Afiliados País", f"{total_sistema:,.0f}")
        with col2:
            st.metric("💼 Régimen Contributivo", f"{pct_contributivo:.1f}%")
        with col3:
            st.metric("🤝 Régimen Subsidiado", f"{pct_subsidiado:.1f}%")
        with col4:
            st.metric("⚠️ Régimen Excepción", f"{pct_excepcion:.1f}%")
        with col5:
            region_lider = df_dept.loc[df_dept['Total'].idxmax(), 'Región']
            total_lider = df_dept['Total'].max()
            st.metric("🏆 Región Líder", region_lider, f"{total_lider:,.0f}")
        
        st.divider()
        
        # Gráficos
        col_g1, col_g2 = st.columns([1.5, 1])
        
        with col_g1:
            st.subheader(f"🏆 Ranking de los {top_n} Departamentos")
            df_top = df_dept.sort_values(by="Total", ascending=False).head(top_n)
            fig_bar = px.bar(
                df_top, x="Total", y="Región", orientation='h',
                text_auto='.2s', color="Total", color_continuous_scale="Viridis",
                hover_data={'% Contributivo': ':.1f', '% Subsidiado': ':.1f'}
            )
            fig_bar.update_layout(
                yaxis=dict(autorange="reversed"), 
                plot_bgcolor="white",
                xaxis_title="Afiliados",
                yaxis_title="",
                height=450
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col_g2:
            st.subheader("📍 Distribución por Régimen (Top 5)")
            df_top5 = df_dept.sort_values(by="Total", ascending=False).head(5)
            fig_pie = px.pie(
                df_top5, values='Total', names='Región',
                color_discrete_sequence=px.colors.sequential.Teal
            )
            fig_pie.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=450)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Gráfico stacked
        st.subheader("⚖️ Composición de Afiliación (Mix de 3 Regímenes)")
        df_top_stack = df_dept.sort_values(by="Total", ascending=False).head(top_n)
        df_melted = df_top_stack[["Región", "Contributivo", "Subsidiado", "Excepción"]].melt(
            id_vars=["Región"], value_vars=["Contributivo", "Subsidiado", "Excepción"], 
            var_name="Régimen", value_name="Cantidad"
        )
        fig_stack = px.bar(
            df_melted, x="Cantidad", y="Región", color="Régimen", orientation='h', barmode='stack',
            color_discrete_map={"Contributivo": "#005F73", "Subsidiado": "#94D2BD", "Excepción": "#E76F51"}
        )
        fig_stack.update_layout(
            yaxis=dict(autorange="reversed"), 
            plot_bgcolor="white",
            xaxis_title="Cantidad de Afiliados",
            yaxis_title="",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig_stack, use_container_width=True)
    
    # --- PESTAÑA 2: RÉGIMEN CONTRIBUTIVO ---
    with tab2:
        st.markdown("## 💼 Comparacion Regimenes")
        st.markdown("*Afiliados vinculados laboralmente o con capacidad de pago*")
        
        col_c1, col_c2 = st.columns([2, 1])
        
        with col_c1:
            df_contrib = df_dept.sort_values(by="Contributivo", ascending=False).head(top_n)
            fig_c = px.bar(
                df_contrib, x="Contributivo", y="Región", orientation='h', text_auto='.2s',
                color="% Contributivo", color_continuous_scale="Blues",
                title=f"Top {top_n} Departamentos - Régimen Contributivo"
            )
            fig_c.update_layout(yaxis=dict(autorange="reversed"), plot_bgcolor="white", height=500)
            st.plotly_chart(fig_c, use_container_width=True)
        
        with col_c2:
            st.write("**Market Share Top 5**")
            df_contrib5 = df_dept.sort_values(by="Contributivo", ascending=False).head(5)
            fig_pie_c = px.pie(
                df_contrib5, values='Contributivo', names='Región', hole=0.4,
                color_discrete_sequence=px.colors.sequential.Blues
            )
            fig_pie_c.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=500)
            st.plotly_chart(fig_pie_c, use_container_width=True)
    
    # --- PESTAÑA 3: RÉGIMEN SUBSIDIADO ---
    with tab3:
        st.markdown("## 🤝 Análisis: Régimen Subsidiado")
        st.markdown("*Población sin capacidad de pago, cubierta por el Estado*")
        
        col_s1, col_s2 = st.columns([2, 1])
        
        with col_s1:
            df_subsid = df_dept.sort_values(by="Subsidiado", ascending=False).head(top_n)
            fig_s = px.bar(
                df_subsid, x="Subsidiado", y="Región", orientation='h', text_auto='.2s',
                color="% Subsidiado", color_continuous_scale="Greens",
                title=f"Top {top_n} Departamentos - Régimen Subsidiado"
            )
            fig_s.update_layout(yaxis=dict(autorange="reversed"), plot_bgcolor="white", height=500)
            st.plotly_chart(fig_s, use_container_width=True)
        
        with col_s2:
            st.write("**Market Share Top 5**")
            df_subsid5 = df_dept.sort_values(by="Subsidiado", ascending=False).head(5)
            fig_pie_s = px.pie(
                df_subsid5, values='Subsidiado', names='Región', hole=0.4,
                color_discrete_sequence=px.colors.sequential.Greens
            )
            fig_pie_s.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=500)
            st.plotly_chart(fig_pie_s, use_container_width=True)
    
    # --- PESTAÑA 4: RÉGIMEN EXCEPCIÓN ---
    with tab4:
        st.markdown("## ⚠️ Régimen Excepción & Especiales")
        st.markdown("*Población en situación especial cubierta con régimen de excepción*")
        
        st.divider()
        
        # KPI Total Excepción
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            st.metric("⚠️ Total Régimen Excepción", f"{total_excepcion:,.0f}")
        with col_e2:
            st.metric("📊 % del Total Nacional", f"{pct_excepcion:.1f}%")
        with col_e3:
            promedio_excep = total_excepcion / len(df_dept)
            st.metric("📈 Promedio por Depto", f"{promedio_excep:,.0f}")
        
        st.divider()
        
        # Gráfico: Comparativa de 3 regímenes
        st.subheader("Comparativa de los 3 Regímenes Nacionales")
        data_regimenes = {
            'Régimen': ['Contributivo', 'Subsidiado', 'Excepción'],
            'Afiliados': [total_contributivo, total_subsidiado, total_excepcion],
            'Porcentaje': [pct_contributivo, pct_subsidiado, pct_excepcion]
        }
        df_regimenes = pd.DataFrame(data_regimenes)
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            fig_bar_reg = px.bar(
                df_regimenes, x='Régimen', y='Afiliados', text_auto='.2s',
                color='Régimen', color_discrete_map={'Contributivo': '#005F73', 'Subsidiado': '#94D2BD', 'Excepción': '#E76F51'},
                title="Total de Afiliados por Régimen"
            )
            fig_bar_reg.update_layout(plot_bgcolor="white", height=400, showlegend=False)
            st.plotly_chart(fig_bar_reg, use_container_width=True)
        
        with col_g2:
            fig_pie_reg = px.pie(
                df_regimenes, values='Afiliados', names='Régimen',
                color_discrete_map={'Contributivo': '#005F73', 'Subsidiado': '#94D2BD', 'Excepción': '#E76F51'},
                title="Distribución por Régimen"
            )
            fig_pie_reg.update_layout(height=400)
            st.plotly_chart(fig_pie_reg, use_container_width=True)
    
    # --- PESTAÑA 5: DATOS ---
    with tab5:
        st.markdown("## 📋 Base de Datos Completa - Departamentos")
        
        df_display = df_dept.sort_values(by="Total", ascending=False).copy()
        st.dataframe(
            df_display.style.format({
                'Contributivo': "{:,.0f}",
                'Subsidiado': "{:,.0f}",
                'Excepción': "{:,.0f}",
                'Total': "{:,.0f}",
                '% Contributivo': "{:.1f}",
                '% Subsidiado': "{:.1f}",
                '% Excepción': "{:.1f}"
            }),
            use_container_width=True,
            height=500
        )
        
        col_dwn1, col_dwn2 = st.columns(2)
        with col_dwn1:
            st.download_button(
                label="📥 Descargar Datos - Departamentos",
                data=df_dept.to_csv(index=False).encode('utf-8'),
                file_name='datos_departamentos_oct2025.csv',
                mime='text/csv'
            )

# ==========================================
# ANÁLISIS POR EPS
# ==========================================
elif analysis_mode == "🏥 Por EPS":
    tab1, tab2, tab3 = st.tabs(["🏥 VISIÓN GENERAL EPS", "⚖️ COMPARACIÓN DE REGÍMENES", "📋 DATOS"])
    
    # --- PESTAÑA 1: VISIÓN GENERAL EPS ---
    with tab1:
        st.markdown("## Panorama de las EPS en Colombia")
        
        total_eps = df_eps['Total Afiliados'].sum()
        top_eps = df_eps.sort_values(by="Total Afiliados", ascending=False).iloc[0]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏥 Total Afiliados EPS", f"{total_eps:,.0f}")
        with col2:
            st.metric("🏆 EPS Líder", top_eps['EPS'], f"{top_eps['Total Afiliados']:,.0f}")
        with col3:
            num_eps = len(df_eps)
            st.metric("🏢 Total de EPS", num_eps)
        
        st.divider()
        
        # Gráficos principales
        col_g1, col_g2 = st.columns([1.5, 1])
        
        with col_g1:
            st.subheader(f"🏥 Top {top_n} EPS por Total de Afiliados")
            df_eps_top = df_eps.sort_values(by="Total Afiliados", ascending=False).head(top_n)
            fig_eps_bar = px.bar(
                df_eps_top, x="Total Afiliados", y="EPS", orientation='h',
                text_auto='.2s', color="Total Afiliados", color_continuous_scale="Blues",
                hover_data={'Market Share (%)': ':.2f', '% Contributivo': ':.1f', '% Subsidiado': ':.1f'}
            )
            fig_eps_bar.update_layout(
                yaxis=dict(autorange="reversed"),
                plot_bgcolor="white",
                xaxis_title="Total Afiliados",
                yaxis_title="",
                height=500
            )
            st.plotly_chart(fig_eps_bar, use_container_width=True)
        
        with col_g2:
            st.subheader("📍 Participación Top 10")
            df_eps_top10 = df_eps.sort_values(by="Total Afiliados", ascending=False).head(10)
            fig_pie_eps = px.pie(
                df_eps_top10, values='Total Afiliados', names='EPS',
                color_discrete_sequence=px.colors.sequential.Blues
            )
            fig_pie_eps.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=500)
            st.plotly_chart(fig_pie_eps, use_container_width=True)
    
    # --- PESTAÑA 2: COMPARACIÓN DE REGÍMENES ---
    with tab2:
        st.markdown("## ⚖️ Comparación de Regímenes (Contributivo, Subsidiado y Excepción)")
        st.markdown("*Distribución de afiliados por tipo de régimen en cada EPS*")
        
        st.subheader(f"Top {top_n} EPS - Distribución por Régimen")
        df_eps_top = df_eps.sort_values(by="Total Afiliados", ascending=False).head(top_n)
        
        # Calcular afiliados contributivos, subsidiados y excepción
        df_eps_top_calc = df_eps_top.copy()
        df_eps_top_calc['Contrib'] = (df_eps_top_calc['Total Afiliados'] * df_eps_top_calc['% Contributivo']).astype(int)
        df_eps_top_calc['Subsid'] = (df_eps_top_calc['Total Afiliados'] * df_eps_top_calc['% Subsidiado']).astype(int)
        df_eps_top_calc['Excep'] = (df_eps_top_calc['Total Afiliados'] * df_eps_top_calc['% Excepción']).astype(int)
        
        df_melted_eps = df_eps_top_calc[["EPS", "Contrib", "Subsid", "Excep"]].melt(
            id_vars=["EPS"], value_vars=["Contrib", "Subsid", "Excep"],
            var_name="Régimen", value_name="Cantidad"
        )
        df_melted_eps['Régimen'] = df_melted_eps['Régimen'].map({'Contrib': 'Contributivo', 'Subsid': 'Subsidiado', 'Excep': 'Excepción'})
        
        fig_stack_eps = px.bar(
            df_melted_eps, x="Cantidad", y="EPS", color="Régimen", orientation='h', barmode='stack',
            color_discrete_map={"Contributivo": "#005F73", "Subsidiado": "#94D2BD", "Excepción": "#E76F51"}
        )
        
        # Agregar porcentajes como anotaciones
        annotations = []
        for idx, row in df_eps_top_calc.iterrows():
            contrib_pct = row['% Contributivo'] * 100
            subsid_pct = row['% Subsidiado'] * 100
            excep_pct = row['% Excepción'] * 100
            contrib_val = row['Contrib']
            subsid_val = row['Subsid']
            excep_val = row['Excep']
            
            # Anotación para Contributivo
            if contrib_val > 100000:  # Solo si es visible
                annotations.append(
                    dict(
                        x=contrib_val/2,
                        y=row['EPS'],
                        text=f"{contrib_pct:.1f}%",
                        showarrow=False,
                        font=dict(color="white", size=11, family="Arial Black"),
                        xanchor="center",
                        yanchor="middle"
                    )
                )
            
            # Anotación para Subsidiado
            if subsid_val > 100000:  # Solo si es visible
                annotations.append(
                    dict(
                        x=contrib_val + subsid_val/2,
                        y=row['EPS'],
                        text=f"{subsid_pct:.1f}%",
                        showarrow=False,
                        font=dict(color="white", size=11, family="Arial Black"),
                        xanchor="center",
                        yanchor="middle"
                    )
                )
            
            # Anotación para Excepción
            if excep_val > 50000:  # Mostrar si es visible
                annotations.append(
                    dict(
                        x=contrib_val + subsid_val + excep_val/2,
                        y=row['EPS'],
                        text=f"{excep_pct:.1f}%",
                        showarrow=False,
                        font=dict(color="white", size=10, family="Arial Black"),
                        xanchor="center",
                        yanchor="middle"
                    )
                )
            else:
                # Si es muy pequeño, mostrar solo la cantidad
                annotations.append(
                    dict(
                        x=contrib_val + subsid_val + excep_val/2,
                        y=row['EPS'],
                        text=f"{excep_val:,.0f}",
                        showarrow=False,
                        font=dict(color="white", size=9, family="Arial Black"),
                        xanchor="center",
                        yanchor="middle"
                    )
                )
        
        fig_stack_eps.update_layout(
            yaxis=dict(autorange="reversed"),
            plot_bgcolor="white",
            xaxis_title="Cantidad de Afiliados",
            yaxis_title="",
            height=500,
            hovermode='closest',
            annotations=annotations
        )
        st.plotly_chart(fig_stack_eps, use_container_width=True)
    
    # --- PESTAÑA 3: DATOS EPS ---
    with tab3:
        st.markdown("## 📋 Base de Datos Completa - EPS")
        
        df_eps_display = df_eps.sort_values(by="Total Afiliados", ascending=False).copy()
        st.dataframe(
            df_eps_display.style.background_gradient(subset=['Total Afiliados'], cmap="Blues").format({
                'Total Afiliados': "{:,.0f}",
                'Market Share (%)': "{:.2f}",
                '% Contributivo': "{:.1f}",
                '% Subsidiado': "{:.1f}",
                '% Excepción': "{:.1f}"
            }),
            use_container_width=True,
            height=500
        )
        
        st.download_button(
            label="📥 Descargar Datos - EPS",
            data=df_eps.to_csv(index=False).encode('utf-8'),
            file_name='datos_eps_oct2025.csv',
            mime='text/csv'
        )

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9em; margin-top: 2rem;">
    <p> Dashboard Desarrollado para Analítica de Datos </p>
    <p> Felipe Ramirez Florez |  Octubre 2025</p>
    </div>
    """, unsafe_allow_html=True)

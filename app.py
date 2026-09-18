import streamlit as st
import pandas as pd
from datetime import datetime
import anthropic

st.set_page_config(page_title="Oracle Sales AI", page_icon="📊", layout="wide")

# Taxa de câmbio (USD para BRL)
TAXA_USD_BRL = 5.0

@st.cache_data
def load_data():
    try:
        clientes = pd.read_csv('clientes_oracle.csv')
        vendas = pd.read_csv('vendas_negociacoes_oracle.csv')
        mercado = pd.read_csv('mercado_tendencias_oracle.csv')
        cases = pd.read_csv('cases_oracle.csv')
        agenda = pd.read_csv('agenda_reunioes.csv')
        historico_compras = pd.read_csv('historico_compras.csv')
        market_insights = pd.read_csv('market_insights.csv')
        return clientes, vendas, mercado, cases, agenda, historico_compras, market_insights
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None, None, None, None, None, None

dados = load_data()
if dados[0] is None:
    st.stop()

clientes_df, vendas_df, mercado_df, cases_df, agenda_df, historico_df, insights_df = dados

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.vendedor = None
    st.session_state.chat_history = []
    st.session_state.cliente_selecionado = None

def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 🤖 Oracle Sales AI")
        st.markdown("**Inteligência para Reuniões Comerciais**")
        st.markdown("---")

        vendedor = st.selectbox("👤 Selecione seu nome:",
            ["João Silva", "Maria Santos", "Carlos Mendes", "Ana Costa", "Pedro Oliveira"])

        password = st.text_input("🔐 Senha:", type="password")

        if st.button("🚀 Entrar", use_container_width=True):
            if password == "oracle2024":
                st.session_state.logged_in = True
                st.session_state.vendedor = vendedor
                st.success(f"Bem-vindo, {vendedor}! 🎉")
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")

def dashboard_page():
    with st.sidebar:
        st.markdown("## Oracle Sales AI")
        st.write(f"👤 {st.session_state.vendedor}")
        if st.button("🚪 Sair"):
            st.session_state.logged_in = False
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("# 📊 Oracle Sales AI Assistant")
    st.markdown(f"**Vendedor:** {st.session_state.vendedor} | **Data:** {datetime.now().strftime('%d/%m/%Y')}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 Agenda", "👥 Cliente", "💬 Chat", "📋 Briefing", "🎯 Farol"])

    # TAB 1: AGENDA
    with tab1:
        st.markdown("## 📅 Reuniões Agendadas - Próximos 3 Meses")
        
        today = datetime.now().strftime('%Y-%m-%d')
        reunioes = agenda_df[agenda_df['data'] >= today].sort_values('data')

        if len(reunioes) > 0:
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.selectbox("Filtrar por status:", 
                    ["Todos"] + list(reunioes['status'].unique()))
            with col2:
                cliente_filter = st.selectbox("Filtrar por cliente:",
                    ["Todos"] + list(reunioes['cliente_nome'].unique()))

            filtered = reunioes
            if status_filter != "Todos":
                filtered = filtered[filtered['status'] == status_filter]
            if cliente_filter != "Todos":
                filtered = filtered[filtered['cliente_nome'] == cliente_filter]

            for idx, row in filtered.iterrows():
                col1, col2, col3, col4 = st.columns([1, 3, 1.5, 1])
                with col1:
                    st.write(f"📅 {row['data']}")
                    st.caption(f"⏰ {row['hora_inicio']}")
                with col2:
                    status_emoji = "✅" if row['status'] == "Confirmada" else "📌" if row['status'] == "Agendada" else "⏳"
                    st.markdown(f"**{status_emoji} {row['cliente_nome']}**")
                    st.caption(f"{row['tipo_reuniao']} | {row['produto_foco']}")
                    st.caption(f"📝 {row['observacoes']}")
                with col3:
                    st.metric("Duração", f"{row['duracao_minutos']}min")
                with col4:
                    if st.button("📌 Lembrete", key=f"lem_{idx}", use_container_width=True):
                        st.success(f"✅ Lembrete criado para {row['cliente_nome']}")

                st.divider()
        else:
            st.info("Nenhuma reunião agendada para hoje.")

    # TAB 2: PERFIL DO CLIENTE
    with tab2:
        st.markdown("## 👥 Perfil do Cliente")
        cliente = st.selectbox("Selecione um cliente:", clientes_df['nome'].tolist(), key="perfil")
        st.session_state.cliente_selecionado = cliente

        info = clientes_df[clientes_df['nome'] == cliente].iloc[0]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Receita Anual", f"${info['receita_anual_usd']/1e6:.1f}M")
        with col2:
            st.metric("Tamanho", info['tamanho'])
        with col3:
            st.metric("Localização", info['localizacao'])

        st.markdown("---")
        
        st.markdown("### 🏢 Informações Gerais")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Segmento:** {info['segmento']}")
            st.write(f"**Stack Tecnológico:** {info['stack_tecnologico']}")
            st.write(f"**Website:** {info['website']}")
        with col2:
            st.write(f"**Dores Identificadas:** {info['dores_identificadas']}")
            st.write(f"**Contato Principal:** {info['contato_principal']}")
            st.write(f"**Email:** {info['email_contato']}")

        st.markdown("---")

        st.markdown("### 📰 Notícias & Tendências do Segmento")
        insights_segmento = insights_df[insights_df['segmento'] == info['segmento']]
        
        if len(insights_segmento) > 0:
            for idx, insight in insights_segmento.iterrows():
                impact_color = "🔴" if insight['impacto'] == "Muito Alto" else "🟠" if insight['impacto'] == "Alto" else "🟡"
                with st.expander(f"{impact_color} {insight['titulo']} ({insight['tipo']})"):
                    st.write(insight['descricao'])
                    st.caption(f"📅 {insight['data']} | Impacto: {insight['impacto']}")
        else:
            st.info("Nenhuma notícia específica para este segmento no momento.")

        st.markdown("---")

        st.markdown("### 🏆 Concorrentes Principais")
        st.write(f"**{', '.join(info['concorrentes_principais'].split(','))}**")

        st.markdown("---")

        st.markdown("### 💳 Histórico de Compras com Oracle")
        historico_cliente = historico_df[historico_df['cliente_id'] == info['id']].sort_values('data_contrato', ascending=False)

        if len(historico_cliente) > 0:
            for idx, compra in historico_cliente.iterrows():
                status_color = "🟢" if compra['status_contrato'] == "Ativo" else "⚫"
                with st.expander(f"{status_color} {compra['produto']} - ${compra['valor_usd']:,.0f} USD"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Valor USD", f"${compra['valor_usd']:,.0f}")
                    with col2:
                        st.metric("Valor BRL", f"R$ {compra['valor_usd'] * TAXA_USD_BRL:,.0f}")
                    with col3:
                        st.metric("Duração", f"{compra['duracao_meses']} meses")
                    with col4:
                        st.metric("Status", compra['status_contrato'])
                    
                    st.caption(f"📅 Contrato: {compra['data_contrato']}")
                    if compra['status_contrato'] == 'Ativo':
                        st.caption(f"🔄 Próxima renovação: {compra['data_renovacao_proxima']}")
                    else:
                        st.caption(f"❌ Contrato expirado em: {compra['data_renovacao_proxima']}")
        else:
            st.info("Nenhuma compra anterior registrada.")

    # TAB 3: CHAT
    with tab3:
        st.markdown("## 💬 Chat Inteligente")
        cliente_chat = st.selectbox("Sobre qual cliente?", clientes_df['nome'].tolist(), key="chat")

        st.markdown("### 💡 Tipos de perguntas:")
        st.markdown("""
        - "Quais são as principais dores?"
        - "Qual produto recomendar?"
        - "Como este cliente se compara?"
        """)

        for msg in st.session_state.chat_history:
            with st.chat_message(msg['role']):
                st.write(msg['content'])

        user_input = st.chat_input("Faça uma pergunta...")

        if user_input:
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            st.info("💡 Resposta com IA (configure ANTHROPIC_API_KEY para ativar)")

    # TAB 4: BRIEFING
    with tab4:
        st.markdown("## 📋 Gerador de Briefing")

        col1, col2 = st.columns(2)
        with col1:
            cliente_brief = st.selectbox("Cliente:", clientes_df['nome'].tolist(), key="brief")
        with col2:
            produto = st.selectbox("Produto:",
                ["Oracle OCI Migration", "Oracle Database Optimization",
                 "Oracle NetSuite Implementation", "Autonomous Database Premium"])

        if st.button("📄 Gerar Briefing", use_container_width=True):
            cliente_info = clientes_df[clientes_df['nome'] == cliente_brief].iloc[0]

            st.markdown("### 📋 BRIEFING EXECUTIVO")
            st.write(f"**Cliente:** {cliente_brief}")
            st.write(f"**Produto:** {produto}")
            st.write(f"**Data:** {datetime.now().strftime('%d/%m/%Y')}")

            st.markdown("---")
            st.markdown("### 1️⃣ DIAGNÓSTICO")
            st.write(f"**Dores Identificadas:** {cliente_info['dores_identificadas']}")
            st.write(f"**Stack Atual:** {cliente_info['stack_tecnologico']}")

            st.markdown("### 2️⃣ SOLUÇÃO PROPOSTA")
            st.write(f"O produto {produto} resolve os principais desafios de
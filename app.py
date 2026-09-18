import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Oracle Sales AI", page_icon="📊", layout="wide")

@st.cache_data
def load_data():
    try:
        clientes = pd.read_csv('clientes_oracle.csv')
        vendas = pd.read_csv('vendas_negociacoes_oracle.csv')
        mercado = pd.read_csv('mercado_tendencias_oracle.csv')
        cases = pd.read_csv('cases_oracle.csv')
        agenda = pd.read_csv('agenda_reunioes.csv')
        return clientes, vendas, mercado, cases, agenda
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None, None, None, None

dados = load_data()
if dados[0] is None:
    st.stop()

clientes_df, vendas_df, mercado_df, cases_df, agenda_df = dados

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.vendedor = None
    st.session_state.chat_history = []

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
    
    with tab1:
        st.markdown("## 📅 Reuniões Agendadas")
        today = datetime.now().strftime('%Y-%m-%d')
        reunioes = agenda_df[agenda_df['data'] >= today].head(10)
        
        if len(reunioes) > 0:
            for idx, row in reunioes.iterrows():
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.write(f"⏰ {row['hora_inicio']}")
                with col2:
                    st.write(f"**{row['cliente_nome']}**")
                    st.caption(f"{row['tipo_reuniao']} | {row['produto_foco']}")
                with col3:
                    st.write(f"{row['duracao_minutos']}min")
                st.divider()
        else:
            st.info("Nenhuma reunião agendada para hoje.")
    
    with tab2:
        st.markdown("## 👥 Perfil do Cliente")
        cliente = st.selectbox("Selecione um cliente:", clientes_df['nome'].tolist(), key="perfil")
        
        info = clientes_df[clientes_df['nome'] == cliente].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Receita Anual", f"${info['receita_anual_usd']/1e6:.1f}M")
        with col2:
            st.metric("Tamanho", info['tamanho'])
        with col3:
            st.metric("Localização", info['localizacao'])
        
        st.markdown("---")
        st.markdown("### Informações Gerais")
        st.write(f"**Segmento:** {info['segmento']}")
        st.write(f"**Stack:** {info['stack_tecnologico']}")
        st.write(f"**Dores:** {info['dores_identificadas']}")
        
        st.markdown("### 📈 Oportunidades Abertas")
        vendas_cliente = vendas_df[vendas_df['cliente_id'] == info['id']]
        
        if len(vendas_cliente) > 0:
            for idx, venda in vendas_cliente.iterrows():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**{venda['produto_principal']}**")
                    st.caption(f"Status: {venda['etapa_funil']} | Prob: {venda['probabilidade_fechamento']}")
                with col2:
                    st.metric("Valor", f"${venda['valor_proposta_usd']/1e3:.0f}K")
                st.divider()
        else:
            st.info("Nenhuma venda aberta para este cliente.")
    
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
            st.write(f"O produto {produto} resolve os principais desafios de {cliente_brief}")
            
            st.markdown("### 3️⃣ CASOS SIMILARES")
            casos_similares = cases_df[cases_df['segmento'].str.contains(cliente_info['segmento'].split()[0], case=False, na=False)]
            if len(casos_similares) > 0:
                for idx, caso in casos_similares.iterrows():
                    with st.expander(f"📈 {caso['titulo']}"):
                        st.write(f"**Resultado:** {caso['resultado_metrica']}")
                        st.write(f"**Impacto:** {caso['resultado_valor']}")
            
            st.markdown("### 4️⃣ PERGUNTAS INVESTIGATIVAS")
            st.markdown("""
            - Qual é o atual tempo de ciclo de vendas?
            - Quais são os principais bloqueadores?
            - Qual é o orçamento disponível?
            - Qual é a prioridade desta implementação?
            """)
    
    with tab5:
        st.markdown("## 🎯 Farol Preditivo")
        
        vendas_abertas = vendas_df[vendas_df['etapa_funil'] != 'Fechado']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Oportunidades", len(vendas_abertas))
        with col2:
            st.metric("Pipeline", f"${vendas_abertas['valor_proposta_usd'].sum()/1e6:.2f}M")
        with col3:
            st.metric("Ciclo Médio", f"{vendas_abertas['tempo_ciclo_dias'].mean():.0f} dias")
        with col4:
            prob = vendas_abertas['probabilidade_fechamento'].str.rstrip('%').astype(float).mean()
            st.metric("Taxa Conversão", f"{prob:.0f}%")
        
        st.markdown("---")
        st.markdown("### ⚠️ Oportunidades em Risco (> 45 dias)")
        
        oportunidades_risco = vendas_abertas[vendas_abertas['tempo_ciclo_dias'] > 45]
        
        if len(oportunidades_risco) > 0:
            for idx, oport in oportunidades_risco.iterrows():
                st.warning(f"🚨 {oport['cliente_nome']} - {oport['produto_principal']} ({oport['tempo_ciclo_dias']} dias)")
        else:
            st.success("✅ Nenhuma oportunidade em risco!")
        
        st.markdown("---")
        st.markdown("### 📊 Status por Etapa do Funil")
        etapas = vendas_abertas.groupby('etapa_funil')['valor_proposta_usd'].sum().reset_index()
        etapas.columns = ['Etapa', 'Valor (USD)']
        etapas['Valor (M)'] = (etapas['Valor (USD)'] / 1e6).round(2)
        st.dataframe(etapas[['Etapa', 'Valor (M)']], use_container_width=True)

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        dashboard_page()

if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import anthropic

st.set_page_config(page_title="Oracle Sales AI", layout="wide")

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
        st.markdown("# Oracle Sales AI")
        st.markdown("**Sistema Inteligente de Vendas**")
        st.markdown("---")

        vendedor = st.selectbox("Selecione seu nome:",
            ["João Silva", "Maria Santos", "Carlos Mendes", "Ana Costa", "Pedro Oliveira"])

        password = st.text_input("Senha:", type="password")

        if st.button("Entrar", use_container_width=True):
            if password == "oracle2024":
                st.session_state.logged_in = True
                st.session_state.vendedor = vendedor
                st.success(f"Bem-vindo, {vendedor}")
                st.rerun()
            else:
                st.error("Senha incorreta")

def get_action_items(agenda_df, vendas_df, clientes_df, historico_df):
    """Identifica ações estratégicas prioritárias"""
    hoje = datetime.now()
    today_str = hoje.strftime('%Y-%m-%d')
    
    acoes = []
    
    proximo_14d = (hoje + timedelta(days=14)).strftime('%Y-%m-%d')
    reunioes_proximas = agenda_df[(agenda_df['data'] >= today_str) & (agenda_df['data'] <= proximo_14d)]
    
    for idx, reuniao in reunioes_proximas.iterrows():
        cliente_id = reuniao['cliente_id']
        cliente_nome = reuniao['cliente_nome']
        
        oporcl = vendas_df[vendas_df['cliente_id'] == cliente_id]
        hist = historico_df[historico_df['cliente_id'] == cliente_id]
        
        score = 0
        motivo = ""
        acao = ""
        prioridade = "Normal"
        
        assinatura = oporcl[oporcl['etapa_funil'] == 'Assinatura de Contrato']
        if len(assinatura) > 0:
            score = 100
            valor = assinatura.iloc[0]['valor_proposta_usd']
            motivo = f"Contrato pendente de assinatura - USD {valor:,.0f}"
            acao = "Confirmar Assinatura"
            prioridade = "Crítica"
        
        elif len(oporcl[oporcl['etapa_funil'] == 'Negociação']) > 0:
            negociacao = oporcl[oporcl['etapa_funil'] == 'Negociação'].iloc[0]
            prob = float(negociacao['probabilidade_fechamento'].rstrip('%'))
            if prob >= 80:
                score = 90
                valor = negociacao['valor_proposta_usd']
                motivo = f"Negociação em estágio avançado ({negociacao['probabilidade_fechamento']}) - USD {valor:,.0f}"
                acao = "Avançar Negociação"
                prioridade = "Alta"
        
        if len(hist) > 0:
            contratos_ativos = hist[hist['status_contrato'] == 'Ativo'].sort_values('data_renovacao_proxima')
            if len(contratos_ativos) > 0:
                proximo_contrato = contratos_ativos.iloc[0]
                data_renovacao = datetime.strptime(proximo_contrato['data_renovacao_proxima'], '%Y-%m-%d')
                dias_para_renovacao = (data_renovacao - hoje).days
                
                if 0 <= dias_para_renovacao <= 30:
                    if score < 80:
                        score = 80
                        motivo = f"Contrato {proximo_contrato['produto']} vence em {dias_para_renovacao} dias"
                        acao = "Iniciar Renovação"
                        prioridade = "Alta"
        
        if reuniao['data'] == today_str:
            score += 20
            prioridade = "Crítica"
        
        if score > 50:
            acoes.append({
                'score': score,
                'cliente': cliente_nome,
                'motivo': motivo,
                'acao': acao,
                'tipo_reuniao': reuniao['tipo_reuniao'],
                'data': reuniao['data'],
                'hora': reuniao['hora_inicio'],
                'prioridade': prioridade
            })
    
    acoes.sort(key=lambda x: x['score'], reverse=True)
    return acoes[:8]

def get_deals_em_risco(vendas_df):
    """Identifica deals em risco"""
    hoje = datetime.now()
    riscos = []
    
    for idx, venda in vendas_df.iterrows():
        if venda['etapa_funil'] == 'Assinatura de Contrato':
            continue
        
        score_risco = 0
        motivos_risco = []
        
        prob = float(venda['probabilidade_fechamento'].rstrip('%'))
        if prob < 50:
            score_risco += 50
            motivos_risco.append(f"Baixa probabilidade de fechamento ({venda['probabilidade_fechamento']})")
        elif prob < 65:
            score_risco += 25
            motivos_risco.append(f"Probabilidade moderada ({venda['probabilidade_fechamento']})")
        
        data_fech = datetime.strptime(venda['data_fechamento_esperada'], '%Y-%m-%d')
        dias_falta = (data_fech - hoje).days
        
        if dias_falta <= 7 and prob < 70:
            score_risco += 40
            motivos_risco.append(f"Fecha em {dias_falta} dias com probabilidade {venda['probabilidade_fechamento']}")
        
        if venda['tempo_ciclo_dias'] > 45:
            score_risco += 20
            motivos_risco.append(f"Ciclo estendido ({venda['tempo_ciclo_dias']} dias)")
        
        data_atu = datetime.strptime(venda['data_atualizacao'], '%Y-%m-%d')
        dias_sem_atu = (hoje - data_atu).days
        
        if dias_sem_atu > 10 and prob < 75:
            score_risco += 30
            motivos_risco.append(f"Sem atualização há {dias_sem_atu} dias")
        
        if score_risco > 50:
            riscos.append({
                'score': score_risco,
                'cliente': venda['cliente_nome'],
                'produto': venda['produto_principal'],
                'valor': venda['valor_proposta_usd'],
                'etapa': venda['etapa_funil'],
                'prob': venda['probabilidade_fechamento'],
                'data_fech': venda['data_fechamento_esperada'],
                'motivos': motivos_risco
            })
    
    riscos.sort(key=lambda x: x['score'], reverse=True)
    return riscos[:10]

def dashboard_page():
    with st.sidebar:
        st.markdown("## Oracle Sales AI")
        st.write(f"Usuário: {st.session_state.vendedor}")
        if st.button("Sair"):
            st.session_state.logged_in = False
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("# Oracle Sales AI Assistant")
    st.markdown(f"**Vendedor:** {st.session_state.vendedor} | **Data:** {datetime.now().strftime('%d/%m/%Y')}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Agenda", "Cliente", "Chat", "Briefing", "Farol"])

    with tab1:
        st.markdown("## Agenda Estratégica")
        
        st.markdown("### Ações Prioritárias")
        
        acoes = get_action_items(agenda_df, vendas_df, clientes_df, historico_df)
        
        if len(acoes) > 0:
            for acao in acoes:
                col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1])
                
                with col1:
                    st.markdown(f"**{acao['cliente']}**")
                    st.caption(f"{acao['motivo']}")
                    st.caption(f"{acao['tipo_reuniao']} - {acao['data']} às {acao['hora']}")
                
                with col2:
                    if acao['prioridade'] == "Crítica":
                        st.markdown(f"<span style='background-color: #ff4444; color: white; padding: 5px 10px; border-radius: 3px;'>CRÍTICA</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='background-color: #ffaa00; color: white; padding: 5px 10px; border-radius: 3px;'>ALTA</span>", unsafe_allow_html=True)
                
                with col3:
                    st.write(f"Pontuação: {acao['score']}")
                
                with col4:
                    if st.button(acao['acao'], key=f"acao_{acao['cliente']}", use_container_width=True):
                        st.success(f"{acao['acao']} iniciado para {acao['cliente']}")
                
                st.divider()
        else:
            st.info("Nenhuma ação prioritária neste momento")
        
        st.markdown("---")
        
        st.markdown("### Agenda Completa")
        
        today = datetime.now().strftime('%Y-%m-%d')
        reunioes = agenda_df[agenda_df['data'] >= today].sort_values('data')

        if len(reunioes) > 0:
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.selectbox("Filtrar por status:",
                    ["Todos"] + list(reunioes['status'].unique()), key="status_filter")
            with col2:
                cliente_filter = st.selectbox("Filtrar por cliente:",
                    ["Todos"] + list(reunioes['cliente_nome'].unique()), key="cliente_filter")

            filtered = reunioes
            if status_filter != "Todos":
                filtered = filtered[filtered['status'] == status_filter]
            if cliente_filter != "Todos":
                filtered = filtered[filtered['cliente_nome'] == cliente_filter]

            for idx, row in filtered.iterrows():
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.write(f"**{row['data']}**")
                with col2:
                    status_texto = "Confirmada" if row['status'] == "Confirmada" else "Agendada"
                    st.markdown(f"**{row['cliente_nome']}** - {row['tipo_reuniao']}")
                    st.caption(f"{row['produto_foco']} | {row['hora_inicio']} | Status: {status_texto}")
                with col3:
                    if st.button("Lembrete", key=f"lem_{idx}", use_container_width=True):
                        st.success(f"Lembrete criado")
                st.divider()
        else:
            st.info("Nenhuma reunião agendada")

    with tab2:
        st.markdown("## Perfil do Cliente")
        cliente = st.selectbox("Selecione um cliente:", clientes_df['nome'].tolist(), key="perfil")
        st.session_state.cliente_selecionado = cliente

        info = clientes_df[clientes_df['nome'] == cliente].iloc[0]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Receita Anual", f"USD {info['receita_anual_usd']/1e6:.1f}M")
        with col2:
            st.metric("Tamanho", info['tamanho'])
        with col3:
            st.metric("Localização", info['localizacao'])

        st.markdown("---")

        st.markdown("### Informações Gerais")
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

        st.markdown("### Notícias & Tendências do Segmento")
        insights_segmento = insights_df[insights_df['segmento'] == info['segmento']]

        if len(insights_segmento) > 0:
            for idx, insight in insights_segmento.iterrows():
                with st.expander(f"{insight['titulo']} ({insight['tipo']}) - Impacto: {insight['impacto']}"):
                    st.write(insight['descricao'])
                    st.caption(f"{insight['data']}")
        else:
            st.info("Nenhuma notícia específica para este segmento")

        st.markdown("---")

        st.markdown("### Concorrentes Principais")
        st.write(f"{', '.join(info['concorrentes_principais'].split(','))}")

        st.markdown("---")

        st.markdown("### Histórico de Compras")
        historico_cliente = historico_df[historico_df['cliente_id'] == info['id']].sort_values('data_contrato', ascending=False)

        if len(historico_cliente) > 0:
            for idx, compra in historico_cliente.iterrows():
                status_texto = "Ativo" if compra['status_contrato'] == "Ativo" else "Expirado"
                with st.expander(f"{compra['produto']} - USD {compra['valor_usd']:,.0f} ({status_texto})"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Valor USD", f"USD {compra['valor_usd']:,.0f}")
                    with col2:
                        st.metric("Valor BRL", f"R$ {compra['valor_usd'] * TAXA_USD_BRL:,.0f}")
                    with col3:
                        st.metric("Duração", f"{compra['duracao_meses']} meses")
                    with col4:
                        st.metric("Status", status_texto)

                    st.caption(f"Contrato: {compra['data_contrato']}")
                    if compra['status_contrato'] == 'Ativo':
                        st.caption(f"Próxima renovação: {compra['data_renovacao_proxima']}")
                    else:
                        st.caption(f"Expirado em: {compra['data_renovacao_proxima']}")
        else:
            st.info("Nenhuma compra anterior registrada")

    with tab3:
        st.markdown("## Chat Inteligente")
        cliente_chat = st.selectbox("Sobre qual cliente?", clientes_df['nome'].tolist(), key="chat")

        st.markdown("### Tipos de perguntas:")
        st.markdown("""
        - Quais são as principais dores?
        - Qual produto recomendar?
        - Como este cliente se compara?
        """)

        for msg in st.session_state.chat_history:
            with st.chat_message(msg['role']):
                st.write(msg['content'])

        user_input = st.chat_input("Faça uma pergunta...")

        if user_input:
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            st.info("Resposta com IA (configure ANTHROPIC_API_KEY para ativar)")

    with tab4:
        st.markdown("## Gerador de Briefing")

        col1, col2 = st.columns(2)
        with col1:
            cliente_brief = st.selectbox("Cliente:", clientes_df['nome'].tolist(), key="brief")
        with col2:
            produto = st.selectbox("Produto:",
                ["Oracle OCI Migration", "Oracle Database Optimization",
                 "Oracle NetSuite Implementation", "Autonomous Database Premium"])

        if st.button("Gerar Briefing", use_container_width=True):
            cliente_info = clientes_df[clientes_df['nome'] == cliente_brief].iloc[0]

            st.markdown("### BRIEFING EXECUTIVO")
            st.write(f"**Cliente:** {cliente_brief}")
            st.write(f"**Produto:** {produto}")
            st.write(f"**Data:** {datetime.now().strftime('%d/%m/%Y')}")

            st.markdown("---")
            st.markdown("### 1. DIAGNÓSTICO")
            st.write(f"**Dores Identificadas:** {cliente_info['dores_identificadas']}")
            st.write(f"**Stack Atual:** {cliente_info['stack_tecnologico']}")

            st.markdown("### 2. SOLUÇÃO PROPOSTA")
            msg = f"O produto {produto} resolve os principais desafios de {cliente_brief}"
            st.write(msg)

            st.markdown("### 3. CASOS SIMILARES")
            casos_similares = cases_df[cases_df['segmento'].str.contains(cliente_info['segmento'].split()[0], case=False, na=False)]
            if len(casos_similares) > 0:
                for idx, caso in casos_similares.iterrows():
                    with st.expander(f"{caso['titulo']}"):
                        st.write(f"**Resultado:** {caso['resultado_metrica']}")
                        st.write(f"**Impacto:** {caso['resultado_valor']}")

            st.markdown("### 4. PERGUNTAS INVESTIGATIVAS")
            st.markdown("""
            - Qual é o atual tempo de ciclo de vendas?
            - Quais são os principais bloqueadores?
            - Qual é o orçamento disponível?
            - Qual é a prioridade desta implementação?
            """)

    with tab5:
        st.markdown("## Farol Preditivo de Vendas")

        if st.session_state.cliente_selecionado:
            st.info(f"Mostrando dados do cliente selecionado: **{st.session_state.cliente_selecionado}**")
            cliente_info_farol = clientes_df[clientes_df['nome'] == st.session_state.cliente_selecionado].iloc[0]
            vendas_farol = vendas_df[vendas_df['cliente_id'] == cliente_info_farol['id']]
        else:
            st.warning("Selecione um cliente na aba 'Cliente' para ver o Farol específico")
            vendas_farol = vendas_df

        vendas_abertas = vendas_farol[vendas_farol['etapa_funil'] != 'Assinatura de Contrato']

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Oportunidades Abertas", len(vendas_abertas))
        with col2:
            pipeline_usd = vendas_abertas['valor_proposta_usd'].sum()
            st.metric("Pipeline (USD)", f"USD {pipeline_usd/1e6:.2f}M")
        with col3:
            pipeline_brl = pipeline_usd * TAXA_USD_BRL
            st.metric("Pipeline (BRL)", f"R$ {pipeline_brl/1e6:.2f}M")
        with col4:
            if len(vendas_abertas) > 0:
                prob = vendas_abertas['probabilidade_fechamento'].str.rstrip('%').astype(float).mean()
                st.metric("Prob. Fechamento Média", f"{prob:.0f}%")

        st.markdown("---")
        
        st.markdown("### Deals em Risco")
        
        deals_risco = get_deals_em_risco(vendas_df)
        
        if len(deals_risco) > 0:
            for deal in deals_risco:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**{deal['cliente']} - {deal['produto']}**")
                    st.caption(f"Etapa: {deal['etapa']} | Probabilidade: {deal['prob']}")
                    st.caption(f"Valor: USD {deal['valor']:,.0f}")
                    for motivo in deal['motivos']:
                        st.caption(f"• {motivo}")
                
                with col2:
                    st.markdown(f"<span style='background-color: #ff6666; color: white; padding: 5px; border-radius: 3px; display: block; text-align: center;'>RISCO {deal['score']}</span>", unsafe_allow_html=True)
                
                with col3:
                    if st.button("Agir", key=f"risco_{deal['cliente']}", use_container_width=True):
                        st.success(f"Ação iniciada para {deal['cliente']}")
                
                st.divider()
        else:
            st.success("Nenhum deal em risco crítico no momento")
        
        st.markdown("---")
        st.markdown("### Oportunidades por Etapa do Funil")

        st.markdown("""
        **Etapas do Funil:**
        - Qualificação: Validação inicial da oportunidade
        - Demonstração: Apresentação técnica
        - Proposta: Proposta comercial apresentada
        - Negociação: Discussão de termos
        - Assinatura de Contrato: Contrato assinado
        """)

        if len(vendas_abertas) > 0:
            etapas = vendas_abertas.groupby('etapa_funil').agg({
                'valor_proposta_usd': 'sum',
                'id': 'count'
            }).reset_index()
            etapas.columns = ['Etapa', 'Valor (USD)', 'Quantidade']
            etapas['Valor (BRL)'] = etapas['Valor (USD)'] * TAXA_USD_BRL
            etapas['Valor (USD)'] = etapas['Valor (USD)'].apply(lambda x: f"USD {x/1e3:.0f}K")
            etapas['Valor (BRL)'] = etapas['Valor (BRL)'].apply(lambda x: f"R$ {x/1e3:.0f}K")

            st.dataframe(etapas[['Etapa', 'Quantidade', 'Valor (USD)', 'Valor (BRL)']], use_container_width=True)

        st.markdown("---")
        st.markdown("### Oportunidades com Datas de Fechamento")

        if len(vendas_abertas) > 0:
            for idx, oport in vendas_abertas.iterrows():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{oport['produto_principal']}**")
                    st.caption(f"Etapa: {oport['etapa_funil']} | Prob: {oport['probabilidade_fechamento']}")
                with col2:
                    st.metric("USD", f"USD {oport['valor_proposta_usd']/1e3:.0f}K")
                with col3:
                    st.metric("BRL", f"R$ {oport['valor_proposta_usd'] * TAXA_USD_BRL/1e3:.0f}K")
                with col4:
                    st.metric("Fechamento", oport['data_fechamento_esperada'])
        else:
            st.success("Nenhuma oportunidade aberta no momento")

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        dashboard_page()

if __name__ == "__main__":
    main()
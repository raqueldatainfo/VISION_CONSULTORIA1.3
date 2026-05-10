# app.py - Sistema Modular de Gestão Vision IA Consultoria
import json
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import hashlib
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

from services.acessos import (
    init_db,
    generate_fake_data,
    load_df,
    authenticate,
    log_audit,
    get_db_connection,
    Pessoa,
)

BASE_DIR = Path(__file__).resolve().parent
PLANTA_FILE = BASE_DIR / 'Planta_CNAK.json'
DEFAULT_PLANTA_TYPES = [
    'Sala Comercial',
    'Loja',
    'Vaga de Estacionamento',
    'Praça de Alimentação',
    'Hall de Entrada',
    'Suporte de Usuário',
    'Brigada de Segurança',
]


def generate_default_planta():
    itens = []
    itens.append({'id': 'H1', 'tipo': 'Hall de Entrada', 'nome': 'Hall de Entrada'})
    itens.append({'id': 'S1', 'tipo': 'Suporte de Usuário', 'nome': 'Suporte de Usuário'})
    itens.append({'id': 'B1', 'tipo': 'Brigada de Segurança', 'nome': 'Brigada de Segurança'})
    itens.append({'id': 'F1', 'tipo': 'Praça de Alimentação', 'nome': 'Praça de Alimentação'})

    for i in range(1, 51):
        itens.append({'id': f'C{i}', 'tipo': 'Sala Comercial', 'nome': f'Sala Comercial {i}'})
    for i in range(1, 51):
        itens.append({'id': f'L{i}', 'tipo': 'Loja', 'nome': f'Loja {i}'})
    for i in range(1, 201):
        itens.append({'id': f'P{i}', 'tipo': 'Vaga de Estacionamento', 'nome': f'Vaga {i}'})

    return {
        'predios': [
            {'id': idx, 'nome': f'Prédio {idx}', 'itens': [item.copy() for item in itens]}
            for idx in range(1, 5)
        ]
    }


def load_planta_data():
    if PLANTA_FILE.exists():
        try:
            with PLANTA_FILE.open('r', encoding='utf-8') as file:
                data = json.load(file)
        except (json.JSONDecodeError, IOError):
            data = generate_default_planta()
    else:
        data = generate_default_planta()

    if 'predios' not in data or not isinstance(data['predios'], list):
        data = generate_default_planta()

    existing = {predio.get('id'): predio for predio in data['predios'] if isinstance(predio, dict) and predio.get('id')}
    for idx in range(1, 5):
        predio = existing.get(idx)
        if predio is None:
            data['predios'].append({'id': idx, 'nome': f'Prédio {idx}', 'itens': [item.copy() for item in generate_default_planta()['predios'][0]['itens']]})
        elif not predio.get('itens'):
            predio['itens'] = [item.copy() for item in generate_default_planta()['predios'][0]['itens']]

    data['predios'] = sorted(data['predios'], key=lambda x: x['id'])
    return data


def save_planta_data(data):
    with PLANTA_FILE.open('w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

st.set_page_config(page_title="Vision IA Consultoria", page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
        :root {
            --bg: #020917;
            --surface: rgba(7, 25, 55, 0.92);
            --accent: #5de4ff;
            --accent-strong: #1bd7ff;
            --text: #f5f9ff;
            --muted: #8fb8d8;
            --border: rgba(94, 220, 255, 0.18);
        }

        .stApp {
            background-image: url('static/images/vision_bg.jpg');
            background-size: cover;
            background-position: center center;
            background-attachment: fixed;
            background-repeat: no-repeat;
            background-color: #020917;
            background-blend-mode: overlay;
            color: var(--text);
        }

        .stApp::before {
            content: '';
            position: fixed;
            inset: 0;
            background: radial-gradient(circle at top left, rgba(10, 76, 164, 0.28), transparent 22%),
                        radial-gradient(circle at bottom right, rgba(5, 183, 255, 0.18), transparent 18%);
            pointer-events: none;
        }

        .css-1v3fvcr {
            padding-top: 1.25rem;
        }

        .hero-banner {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 3rem 1rem;
            margin-bottom: 1.5rem;
            min-height: 360px;
            color: var(--text);
        }

        .hero-card {
            width: 100%;
            max-width: 1140px;
            padding: 2rem 2.5rem;
            border-radius: 30px;
            background: rgba(2, 9, 23, 0.86);
            border: 1px solid rgba(94, 220, 255, 0.18);
            box-shadow: 0 28px 80px rgba(0, 0, 0, 0.35);
        }

        .hero-header {
            display: flex;
            align-items: center;
            gap: 1.5rem;
            flex-wrap: wrap;
        }

        .hero-logo {
            width: 108px;
            height: 108px;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.18);
            padding: 1rem;
            background: rgba(255,255,255,0.08);
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        .hero-title {
            margin: 0;
            font-size: 3rem;
            font-weight: 900;
            letter-spacing: 0.18rem;
            text-transform: uppercase;
            color: #ffffff;
        }

        .hero-subtitle {
            margin: 0.75rem 0 0;
            font-size: 1.05rem;
            line-height: 1.85;
            color: #c6e9ff;
            max-width: 780px;
        }

        .hero-note {
            margin-top: 1.75rem;
            font-size: 0.88rem;
            color: #94cfff;
            opacity: 0.88;
            max-width: 840px;
        }

        .hero-small-text {
            font-size: 0.84rem;
            color: #a6d7ff;
            line-height: 1.75;
        }

        .stApp header {
            background-color: transparent;
        }

        .css-18e3th9 {
            background: transparent;
        }

        .block-container {
            padding: 2rem 2rem 3rem;
            border-radius: 24px;
            background: rgba(6, 16, 36, 0.88);
            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
            border: 1px solid rgba(94, 220, 255, 0.12);
        }

        .sidebar .sidebar-content {
            background: linear-gradient(180deg, #021121 0%, #061c35 100%);
            border-right: 1px solid rgba(94, 220, 255, 0.15);
        }

        .stButton>button {
            background: linear-gradient(135deg, #16b2ff 0%, #3fe5ff 100%) !important;
            color: #02101c !important;
            border: none;
            box-shadow: 0 12px 24px rgba(8, 129, 178, 0.28);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }

        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 16px 28px rgba(8, 129, 178, 0.32);
        }

        .stTextInput>div>div>input,
        .stSelectbox>div>div>div>div>span {
            background: rgba(255,255,255,0.04) !important;
            color: var(--text) !important;
            border: 1px solid rgba(94, 220, 255, 0.18) !important;
        }

        .stDataFrame table {
            background: rgba(1, 17, 35, 0.9);
            color: var(--text);
        }

        .stDataFrame th {
            background: rgba(9, 47, 86, 0.95);
            color: #d4f6ff;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 12px 12px 0 0;
            background-color: rgba(5, 17, 42, 0.85);
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #16b2ff 0%, #2fd5ff 100%);
            color: #02101c;
        }

        .stMetric, .stExpander {
            background: rgba(8, 17, 40, 0.82) !important;
            border: 1px solid rgba(94, 220, 255, 0.16);
            box-shadow: 0 16px 30px rgba(0, 0, 0, 0.24);
        }

        .glow {
            animation: glow 3.4s ease-in-out infinite;
        }

        @keyframes glow {
            0%, 100% { box-shadow: 0 0 16px rgba(29, 211, 255, 0.2); }
            50% { box-shadow: 0 0 32px rgba(29, 211, 255, 0.35); }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


class BaseModule:
    def __init__(self, role, user_id):
        self.role = role
        self.user_id = user_id

    def guard(self, allowed_roles, message="Acesso restrito."):
        if self.role not in allowed_roles:
            st.warning(f"⚠️ {message}")
            return False
        return True

    def audit(self, action):
        log_audit(self.user_id, action)

    def empty_state(self, title, text):
        st.info(f"{title}\n{text}")


class AccessControlModule(BaseModule):
    def show(self):
        st.subheader("1. Módulo Gerenciamento de Controle de Acesso")
        st.write("Gerencie usuários, módulos do sistema e ambientes prediais com controle centralizado e visibilidade segura.")
        tabs = st.tabs(["1.1 CRUD Usuários", "1.2 CRUD Módulos", "1.3 CRUD Ambientes"])
        with tabs[0]:
            self.render_users()
        with tabs[1]:
            self.render_system_modules()
        with tabs[2]:
            self.render_buildings()

    def render_users(self):
        if not self.guard(['admin'], "Somente administradores podem gerenciar usuários."):
            return
        st.markdown("**Controle de contas e perfis de acesso**")
        df = load_df('users')
        st.dataframe(df)

        with st.expander("➕ Criar novo usuário"):
            with st.form("create_user"):
                username = st.text_input("Nome de usuário")
                password = st.text_input("Senha", type="password")
                role = st.selectbox("Perfil", ['admin', 'user', 'guest'])
                submitted = st.form_submit_button("Criar usuário")
                if submitted:
                    if not username or not password:
                        st.error("Preencha usuário e senha.")
                    else:
                        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
                        try:
                            with get_db_connection() as conn:
                                conn.execute(
                                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                                    (username, pwd_hash, role),
                                )
                            st.success("Usuário cadastrado com sucesso.")
                            self.audit(f"Criou usuário: {username}")
                            st.rerun()
                        except Exception:
                            st.error("Não foi possível criar o usuário. Verifique se o nome já existe.")

        with st.expander("✏️ Atualizar / Excluir usuário"):
            users = df['username'].tolist()
            if users:
                selected = st.selectbox("Selecionar usuário", users)
                action = st.radio("Ação", ['Atualizar role', 'Excluir usuário'])
                if action == 'Atualizar role':
                    new_role = st.selectbox("Nova role", ['admin', 'user', 'guest'])
                    if st.button("Salvar alteração"):
                        with get_db_connection() as conn:
                            conn.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, selected))
                        st.success("Role atualizada.")
                        self.audit(f"Atualizou role de {selected} para {new_role}")
                        st.rerun()
                else:
                    if st.button("Excluir usuário"):
                        with get_db_connection() as conn:
                            conn.execute("DELETE FROM users WHERE username = ?", (selected,))
                        st.warning("Usuário excluído.")
                        self.audit(f"Excluiu usuário: {selected}")
                        st.rerun()
            else:
                st.info("Nenhum usuário encontrado.")

    def render_system_modules(self):
        st.markdown("**Estrutura de módulos do sistema**")
        df = load_df('system_modules')
        st.dataframe(df)

        with st.expander("➕ Adicionar módulo"):
            with st.form("create_module"):
                nome = st.text_input("Nome do módulo")
                descricao = st.text_area("Descrição")
                if st.form_submit_button("Salvar módulo"):
                    if not nome:
                        st.error("Nome do módulo é obrigatório.")
                    else:
                        with get_db_connection() as conn:
                            conn.execute(
                                "INSERT INTO system_modules (nome, descricao, criado_em) VALUES (?, ?, ?)",
                                (nome, descricao, datetime.now().strftime('%Y-%m-%d')),
                            )
                        st.success("Módulo salvo com sucesso.")
                        self.audit(f"Criou módulo do sistema: {nome}")
                        st.rerun()

        with st.expander("✏️ Atualizar / Excluir módulo"):
            modules = df['nome'].tolist()
            if modules:
                selected = st.selectbox("Selecionar módulo", modules)
                if st.button("Excluir módulo selecionado"):
                    with get_db_connection() as conn:
                        conn.execute("DELETE FROM system_modules WHERE nome = ?", (selected,))
                    st.warning("Módulo excluído.")
                    self.audit(f"Excluiu módulo: {selected}")
                    st.rerun()
            else:
                st.info("Nenhum módulo cadastrado.")

    def render_buildings(self):
        st.markdown("**Gerenciar ambientes (prédios)**")
        st.write("A seguir está a adaptação do código de planta CNAK para o módulo de CRUD de ambientes.")
        df = load_df('buildings')
        st.dataframe(df)

        with st.expander("➕ Novo ambiente"):
            with st.form("create_building"):
                nome = st.text_input("Nome do prédio")
                localizacao = st.text_input("Localização")
                capacidade = st.number_input("Capacidade", min_value=1, value=50)
                status = st.selectbox("Status", ['Ativo', 'Manutenção', 'Inativo'])
                if st.form_submit_button("Salvar ambiente"):
                    if not nome or not localizacao:
                        st.error("Preencha todos os campos.")
                    else:
                        with get_db_connection() as conn:
                            conn.execute(
                                "INSERT INTO buildings (nome, localizacao, capacidade, status) VALUES (?, ?, ?, ?)",
                                (nome, localizacao, capacidade, status),
                            )
                        st.success("Ambiente cadastrado.")
                        self.audit(f"Criou ambiente: {nome}")
                        st.rerun()

        with st.expander("✏️ Atualizar / Excluir ambiente"):
            environments = df['nome'].tolist()
            if environments:
                selected = st.selectbox("Selecionar ambiente", environments)
                new_status = st.selectbox("Novo status", ['Ativo', 'Manutenção', 'Inativo'])
                if st.button("Atualizar status"):
                    with get_db_connection() as conn:
                        conn.execute("UPDATE buildings SET status = ? WHERE nome = ?", (new_status, selected))
                    st.success("Status atualizado.")
                    self.audit(f"Atualizou status de {selected} para {new_status}")
                    st.rerun()
                if st.button("Excluir ambiente"):
                    with get_db_connection() as conn:
                        conn.execute("DELETE FROM buildings WHERE nome = ?", (selected,))
                    st.warning("Ambiente removido.")
                    self.audit(f"Excluiu ambiente: {selected}")
                    st.rerun()
            else:
                st.info("Nenhum ambiente encontrado.")

        st.markdown("---")
        st.markdown("### Planta CNAK")
        planta_data = load_planta_data()
        current_predio = st.selectbox(
            "Selecionar prédio para edição de itens",
            [f"{predio['id']} - {predio['nome']}" for predio in planta_data['predios']],
        )
        predio_id = int(current_predio.split(' - ')[0])
        predio = next(p for p in planta_data['predios'] if p['id'] == predio_id)

        st.markdown(f"**Itens cadastrados no {predio['nome']}**")
        st.dataframe(pd.DataFrame(predio['itens']))

        with st.expander("➕ Adicionar / Atualizar item da planta"):
            with st.form("upsert_planta_item"):
                original_id = st.text_input("ID original (deixe vazio para novo item)")
                item_id = st.text_input("ID do item", value=original_id or '')
                tipo = st.selectbox("Tipo", DEFAULT_PLANTA_TYPES)
                nome = st.text_input("Nome do item")
                submitted = st.form_submit_button("Salvar item")
                if submitted:
                    if not item_id or not tipo or not nome:
                        st.error("ID, tipo e nome são obrigatórios.")
                    else:
                        existing = next((item for item in predio['itens'] if item['id'] == item_id), None)
                        if original_id:
                            item_to_edit = next((item for item in predio['itens'] if item['id'] == original_id), None)
                            if not item_to_edit:
                                st.error("Item original não encontrado.")
                            else:
                                if item_id != original_id and existing:
                                    st.error("ID já existe.")
                                else:
                                    item_to_edit.update({'id': item_id, 'tipo': tipo, 'nome': nome})
                                    save_planta_data(planta_data)
                                    st.success("Item atualizado com sucesso.")
                                    self.audit(f"Atualizou item {original_id} para {item_id} no prédio {predio['nome']}")
                                    st.rerun()
                        else:
                            if existing:
                                st.error("ID já existe.")
                            else:
                                predio['itens'].append({'id': item_id, 'tipo': tipo, 'nome': nome})
                                save_planta_data(planta_data)
                                st.success("Item adicionado com sucesso.")
                                self.audit(f"Adicionou item {item_id} no prédio {predio['nome']}")
                                st.rerun()

        with st.expander("🗑️ Remover item da planta"):
            item_choices = [f"{item['id']} - {item['nome']}" for item in predio['itens']]
            if item_choices:
                selected_item = st.selectbox("Selecionar item", item_choices)
                if st.button("Excluir item selecionado"):
                    item_id_to_delete = selected_item.split(' - ')[0]
                    predio['itens'] = [item for item in predio['itens'] if item['id'] != item_id_to_delete]
                    save_planta_data(planta_data)
                    st.warning("Item removido com sucesso.")
                    self.audit(f"Removeu item {item_id_to_delete} do prédio {predio['nome']}")
                    st.rerun()
            else:
                st.info("Nenhum item disponível para exclusão.")


class EquipmentManagementModule(BaseModule):
    def show(self):
        st.subheader("2. Módulo de Gerenciamento de Equipamentos")
        st.write("Administre equipamentos e suas distribuições em ambientes de forma confiável.")
        tabs = st.tabs(["2.1 CRUD Equipamentos", "2.2 Distribuição"])
        with tabs[0]:
            self.render_equipments()
        with tabs[1]:
            self.render_distribution()

    def render_equipments(self):
        st.markdown("**Cadastro completo de equipamentos**")
        df = load_df('equipamentos')
        st.dataframe(df)

        with st.expander("➕ Novo equipamento"):
            with st.form("create_equipment"):
                nome = st.text_input("Nome do equipamento")
                tipo = st.text_input("Tipo")
                serial = st.text_input("Serial")
                status = st.selectbox("Status", ['Operando', 'Inativo', 'Manutenção'])
                if st.form_submit_button("Salvar equipamento"):
                    if not nome or not tipo or not serial:
                        st.error("Preencha todos os campos.")
                    else:
                        try:
                            with get_db_connection() as conn:
                                conn.execute(
                                    "INSERT INTO equipamentos (nome, tipo, serial, status) VALUES (?, ?, ?, ?)",
                                    (nome, tipo, serial, status),
                                )
                            st.success("Equipamento cadastrado.")
                            self.audit(f"Cadastrou equipamento: {nome}")
                            st.rerun()
                        except Exception:
                            st.error("Não foi possível cadastrar. Verifique se o serial já está em uso.")

        with st.expander("✏️ Alterar / Excluir equipamento"):
            equipments = df['serial'].tolist()
            if equipments:
                selected = st.selectbox("Selecionar serial", equipments)
                new_status = st.selectbox("Nova status", ['Operando', 'Inativo', 'Manutenção'])
                if st.button("Atualizar status do equipamento"):
                    with get_db_connection() as conn:
                        conn.execute("UPDATE equipamentos SET status = ? WHERE serial = ?", (new_status, selected))
                    st.success("Status atualizado.")
                    self.audit(f"Atualizou equipamento {selected} para {new_status}")
                    st.rerun()
                if st.button("Excluir equipamento"):
                    with get_db_connection() as conn:
                        conn.execute("DELETE FROM equipamentos WHERE serial = ?", (selected,))
                    st.warning("Equipamento excluído.")
                    self.audit(f"Excluiu equipamento serial: {selected}")
                    st.rerun()
            else:
                st.info("Nenhum equipamento registrado.")

    def render_distribution(self):
        st.markdown("**Distribuição de equipamentos nos ambientes**")
        df = load_df('equipamento_ambiente')
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("Ainda não há equipamentos alocados.")

        equipments = load_df('equipamentos')
        buildings = load_df('buildings')
        if not equipments.empty and not buildings.empty:
            with st.form("assign_equipment"):
                equip = st.selectbox("Equipamento", equipments['id'].astype(str) + ' - ' + equipments['nome'])
                ambiente = st.selectbox("Ambiente", buildings['id'].astype(str) + ' - ' + buildings['nome'])
                if st.form_submit_button("Alocar equipamento"):
                    equip_id = int(equip.split(' - ')[0])
                    ambiente_id = int(ambiente.split(' - ')[0])
                    with get_db_connection() as conn:
                        conn.execute(
                            "INSERT OR REPLACE INTO equipamento_ambiente (equipamento_id, ambiente_id, alocacao_data) VALUES (?, ?, ?)",
                            (equip_id, ambiente_id, datetime.now().strftime('%Y-%m-%d')),
                        )
                    st.success("Equipamento alocado com sucesso.")
                    self.audit(f"Alocou equipamento {equip_id} no ambiente {ambiente_id}")
                    st.rerun()
        else:
            st.info("Cadastre equipamentos e ambientes antes de alocar.")


class EnvironmentMonitoringModule(BaseModule):
    def show(self):
        st.subheader("3. Módulo de Monitoramento de Ambientes")
        st.write("Visualize condições de prédios e estacionamento com dados de temperatura, ocupação e status.")
        tabs = st.tabs(["3.1 Monitoramento Prédios", "3.2 Monitoramento Estacionamento"])
        with tabs[0]:
            self.render_building_monitoring()
        with tabs[1]:
            self.render_parking_monitoring()

    def render_building_monitoring(self):
        df = load_df('monitoramento')
        if df.empty:
            self.empty_state("Sem dados de monitoramento.", "Registre um novo evento para começar.")
            return
        st.dataframe(df)
        fig = px.bar(
            df,
            x='area',
            y='ocupacao',
            color='status',
            title='Ocupação por área',
            text='ocupacao',
            labels={'ocupacao': 'Pessoas', 'area': 'Área'},
        )
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    def render_parking_monitoring(self):
        df = load_df('monitoramento')
        if df.empty:
            self.empty_state("Sem dados de estacionamento.", "Adicione dados na origem do monitoramento.")
            return
        st.markdown("**Resumo de estacionamento e ocupação**")
        available = np.random.randint(12, 42)
        total = 50
        st.metric("Espaços disponíveis", f"{available}/{total}")
        st.progress(available / total)
        st.write("Dados simulados para demonstrar o status de estacionamento em tempo real.")


class AuditModule(BaseModule):
    def show(self):
        st.subheader("4. Módulo de Auditoria")
        st.write("Registre ações, consulte logs e extraia relatórios de auditoria de forma organizada.")
        tabs = st.tabs(["4.1 Registros", "4.2 Consultar Relatórios"])
        with tabs[0]:
            self.render_records()
        with tabs[1]:
            self.render_reports()

    def render_records(self):
        st.dataframe(load_df('audits'))

    def render_reports(self):
        df = load_df('audits')
        periodo = st.selectbox("Filtrar por período", ['Últimas 24h', 'Últimos 7 dias', 'Últimos 30 dias', 'Todos'])
        if periodo != 'Todos':
            st.info("Filtro de período está em modo de demonstração.")
        st.download_button("📥 Exportar auditoria CSV", df.to_csv(index=False).encode('utf-8'), "auditoria.csv", "text/csv")


class AnalysisModule(BaseModule):
    def show(self):
        st.subheader("5. Módulo de Análise")
        st.write("Painel de análise com mapa de calor e configuração de parâmetros estratégicos.")
        tabs = st.tabs(["5.1 Dashboard", "5.2 Configurações"])
        with tabs[0]:
            self.render_dashboard()
        with tabs[1]:
            self.render_settings()

    def render_dashboard(self):
        df = load_df('heatmap_data')
        if df.empty:
            self.empty_state("Sem dados de análise.", "Preencha heatmap_data para visualizar gráficos.")
            return
        st.dataframe(df)
        ambient_ids = df['ambiente_id'].astype(str) + ' - ' + df['tipo']
        fig = go.Figure(
            data=go.Heatmap(
                z=df['intensidade'],
                x=ambient_ids,
                y=['Intensity'] * len(df),
                colorscale='Blues',
            )
        )
        fig.update_layout(title='Mapa de Calor de Ocorrências', xaxis_title='Ambiente / Tipo', yaxis={'visible': False})
        st.plotly_chart(fig, use_container_width=True)

    def render_settings(self):
        st.markdown("**Parâmetros de análise e apresentações**")
        threshold = st.slider("Limite crítico de intensidade", 0.0, 1.0, 0.6)
        refresh = st.selectbox("Intervalo de atualização", ['1 min', '5 min', '15 min', '30 min'])
        st.success(f"Parâmetros salvos: limite {threshold} e atualização {refresh}.")
        self.audit(f"Alterou configurações de análise: limite {threshold}, refresh {refresh}")


def draw_intro():
    st.markdown("""
        <div class='hero-banner'>
            <div class='hero-card'>
                <div class='hero-header'>
                    <div class='hero-logo'>
                        <img src='static/images/logo_cnak_vision.svg' alt='Vision IA' style='width: 100%; height: 100%; object-fit: contain;'>
                    </div>
                    <div>
                        <h1 class='hero-title'>VISION IA CONSULTORIA</h1>
                        <p class='hero-subtitle'>Missão: Converter sistemas tradicionais em plataformas inteligentes que geram receita e reduzem custos.<br>
                        Visão: Liderar a transformação digital em empreendimentos comerciais, tornando-os mais rentáveis e sustentáveis.<br>
                        Valores: Sustentabilidade financeira, transparência, parceria estratégica, inovação acessível.</p>
                    </div>
                </div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.write('')


def main():
    if 'initialized' not in st.session_state:
        init_db()
        generate_fake_data()
        st.session_state.initialized = True

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.role = None

    st.sidebar.markdown("# Vision IA")
    st.sidebar.markdown("### Menu principal")
    if not st.session_state.logged_in:
        st.sidebar.markdown("---")
        with st.sidebar.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type='password')
            login_clicked = st.form_submit_button("Entrar")
            
            if login_clicked:
                uid, role = authenticate(username, password)
                if uid:
                    st.session_state.logged_in = True
                    st.session_state.user_id = uid
                    st.session_state.role = role
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        
        st.sidebar.markdown("<p style='font-size:0.82rem; color:#a4d8ff; line-height:1.72;'>Nossa história começou em 2026, no berço da educação profissional: Senac DF. Foi ali que aprendemos a transformar teoria em prática e sonhos em negócios.</p>", unsafe_allow_html=True)
        draw_intro()
        return

    menu = [
        "🏠 Dashboard",
        "1. Módulo Gerenciamento de Controle de Acesso",
        "2. Módulo de Gerenciamento de Equipamentos",
        "3. Módulo de Monitoramento de Ambientes",
        "4. Módulo de Auditoria",
        "5. Módulo de Análise",
    ]
    selection = st.sidebar.selectbox("Navegar", menu)
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        self_user = st.session_state.user_id
        log_audit(self_user, "Logout")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    draw_intro()

    if selection == "🏠 Dashboard":
        AnalysisModule(st.session_state.role, st.session_state.user_id).render_dashboard()
    elif selection == "1. Módulo Gerenciamento de Controle de Acesso":
        AccessControlModule(st.session_state.role, st.session_state.user_id).show()
    elif selection == "2. Módulo de Gerenciamento de Equipamentos":
        EquipmentManagementModule(st.session_state.role, st.session_state.user_id).show()
    elif selection == "3. Módulo de Monitoramento de Ambientes":
        EnvironmentMonitoringModule(st.session_state.role, st.session_state.user_id).show()
    elif selection == "4. Módulo de Auditoria":
        AuditModule(st.session_state.role, st.session_state.user_id).show()
    elif selection == "5. Módulo de Análise":
        AnalysisModule(st.session_state.role, st.session_state.user_id).show()


if __name__ == '__main__':
    main()
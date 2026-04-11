import streamlit as st
import pandas as pd
import io
import datetime
import json
import time
import os
import base64
import requests
import urllib.parse
from fpdf import FPDF
import string
import random
#from streamlit_gsheets import GSheetsConnection
from st_supabase_connection import SupabaseConnection
#import sqlite3
#import shutil

# --- 1. CONFIGURAÇÃO E ESTILO (LARANJA SS) ---
st.set_page_config(page_title="LOTO Digital | System Service", layout="wide", page_icon="logo_ss_inicio2.png")

st.markdown("""
    <style>
            
    /* 1. FORÇAR TEMA CLARO GLOBAL (SIDEBAR, CORPO E CABEÇALHO) */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"], .stApp {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
    }
    button[kind="primary"] {
        background-color: #FF6B00 !important;
        color: white !important;
        border-radius: 12px !important;
    }

    /* 2. BLINDAGEM DE CAMPOS (SELECTBOX, INPUT, TEXTAREA) - REMOVE O FUNDO PRETO */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div,
    input, textarea, select, .stSelectbox div {
        background-color: #F1F5F9 !important; /* Cinza bem claro */
        color: #1E293B !important;
        border: 1px solid #CBD5E1 !important;
    }
    
    /* Corrigir o texto dentro das listas de seleção que somem no modo dark */
    div[role="listbox"] div, div[role="option"] {
        color: #1E293B !important;
        background-color: white !important;
    }

    /* 3. FIX PARA LABELS DAS GUIAS (TÍTULOS QUE SUMIRAM NO PAINEL ADMIN) */
    [data-testid="stMarkdownContainer"] p, label, .st-ae {
        color: #1E293B !important;
    }

    /* 4. REESTRUTURAÇÃO DO CARD (TÍTULO EM CIMA E NÚMERO NO MEIO) */
    .metric-container {
        background-color: white !important;
        border: 1px solid #EDF2F7 !important;
        border-radius: 15px !important;
        padding: 20px 10px !important;
        text-align: center !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06) !important;
        height: 170px !important;
        display: flex !important;
        flex-direction: column !important; /* Força ordem vertical */
        justify-content: center !important;
        align-items: center !important;
    }

    /* 5. CORES DAS MÉTRICAS (GARANTIA DE VISIBILIDADE) */
    .card-total .metric-value-custom { color: #1E3A8A !important; }
    .card-exec .metric-value-custom { color: #3B82F6 !important; }
    .card-conc .metric-value-custom { color: #10B981 !important; }
    .card-canc .metric-value-custom { color: #EF4444 !important; }

    /* 6. TRANSPARÊNCIA DE IMAGENS */
    img, [data-testid="stImage"] {
        background-color: transparent !important;
        mix-blend-mode: multiply;
    }

    /* 7. ALERTA VIBRANTE CUSTOMIZADO */
    .alerta-vermelho {
        background-color: #FDE2E2 !important;
        color: #991B1B !important;
        padding: 15px !important;
        border-radius: 10px !important;
        border-left: 6px solid #EF4444 !important;
        margin-bottom: 10px !important;
        font-weight: bold !important;
    }

    /* 1. FORÇAR BOTÕES DA SIDEBAR A FICAREM VERTICAIS E IGUAIS */
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] {
        display: grid !important;
        grid-template-columns: 1fr !important; /* Força uma única coluna larga */
        gap: 8px !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button {
        width: 100% !important;
        justify-content: flex-start !important;
        text-align: left !important;
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
    }

    /* 2. REMOVER BORDAS DUPLAS E RETÂNGULOS EM INPUTS/LISTAS */
    div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox div, .stTextInput div {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        background-color: transparent !important;
    }
    
    /* Garante que o campo de digitação em si tenha uma borda limpa */
    input, textarea {
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        background-color: white !important;
    }   
            
    /* Card de Perfil Estilo Mobile */
    .profile-card {
        background-color: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        text-align: center;
        max-width: 400px;
        margin: auto;
    }
    .profile-avatar {
        width: 100px;
        height: 100px;
        background-color: #FEEBC8; /* Laranja bem clarinho */
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 15px;
        font-size: 40px;
        color: #FF6B00;
        border: 3px solid #FFF;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    /* Estilo para os cards das etapas do checklist */
    .step-card {
        background-color: #F8FAFC;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        margin-bottom: 10px;
    }
    .step-card-complete {
        background-color: #F0FDF4; /* Verde bem claro */
        border: 1px solid #BBF7D0;
    }
    .step-card-na {
        background-color: #F1F5F9; /* Cinza claro */
        opacity: 0.7;
    }
    iframe {
        border-radius: 10px;
        border: 1px solid #EEE;
        /* Aceleração de hardware para zoom mais fluido */
        transform: translateZ(0); 
        -webkit-transform: translateZ(0);
    }
    /* Ajuste de altura do botão Sugerir para alinhar com o input */
    [data-testid="column"]:nth-of-type(2) button[kind="secondary"] {
        height: 45px !important;
        margin-top: 28px !important; /* Compensa a altura do label 'Senha Inicial' */
    }
    /* Estilo para os novos botões de métrica */
    .metric-card-btn button {
        height: 140px !important;
    }
    .metric-card-btn div[data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
        line-height: 1.2 !important;
    }
    /* Estilo para os números grandes dentro dos botões */
    .metric-card-btn button div {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
    }        
    
     /* 1. RESTAURA OS NÚMEROS GRANDES E TÍTULOS NOS CARDS (Imagens 1 e 3) */
    .metric-value-custom { font-size: 3.5rem !important; font-weight: 800 !important; display: block !important; }
    .metric-label-custom { font-size: 1.1rem !important; font-weight: 600 !important; display: block !important; }
    .card-total .metric-value-custom { color: #1E3A8A !important; }
    .card-exec .metric-value-custom { color: #3B82F6 !important; }
    .card-conc .metric-value-custom { color: #10B981 !important; }
    .card-canc .metric-value-custom { color: #EF4444 !important; }

    /* 2. FORÇA VERTICALIZAÇÃO DA SIDEBAR (Imagem 1) */
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] {
        display: grid !important;
        grid-template-columns: 1fr !important;
        gap: 8px !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] [data-testid="stSegmentedControl"] button {
        width: 100% !important;
        justify-content: flex-start !important;
        text-align: left !important;
    }

    /* 3. REMOVE A BARRA VERTICAL NO CANTO DOS TEXTOS (Imagem 2) */
    div[data-baseweb="select"] div { border: none !important; box-shadow: none !important; }
    div[data-baseweb="input"] { border: none !important; box-shadow: none !important; }

    /* 4. AJUSTE DO BOTÃO LARANJA (Imagem 4) */
    button[kind="primary"] {
        background-color: #FF6B00 !important;
        height: 3rem !important; /* Reduz a altura para não ficar tão bruto */
        border-radius: 8px !important;
    }           

    /* Estilos de borda por status */
    .card-ativa { border-left: 6px solid #3B82F6 !important; }    /* Azul */
    .card-concluida { border-left: 6px solid #10B981 !important; } /* Verde */
    .card-cancelada { border-left: 6px solid #FF6B00 !important; } /* Laranja SS */

    .hist-card {
        background-color: white !important;
        padding: 15px !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        margin-bottom: 12px !important;
        display: block !important;
        text-align: left !important;
    }
    .hist-os { font-weight: bold !important; font-size: 1.1rem !important; color: #1E293B !important; }
    .hist-status { 
        background-color: #DEF7EC !important; color: #03543F !important; 
        padding: 2px 10px !important; border-radius: 15px !important; font-size: 0.8rem !important; font-weight: bold !important;
    }
    .hist-sub { color: #64748B !important; font-size: 0.9rem !important; margin-top: 4px !important; }
    .hist-status-cancel { 
        background-color: #FDE2E2 !important; 
        color: #9B1C1C !important; 
        padding: 2px 10px !important; 
        border-radius: 15px !important; 
        font-size: 0.8rem !important; 
        font-weight: bold !important;
        display: inline-block !important; /* Garante o mesmo formato do verde */
        line-height: 1.5 !important;
    }
            
    </style>
    """, unsafe_allow_html=True)

# --- 1. CONEXÃO OFICIAL SUPABASE ---
try:
    # Buscamos os valores dos Secrets e injetamos na conexão
    S_URL = st.secrets["connections"]["supabase"]["url"]
    S_KEY = st.secrets["connections"]["supabase"]["key"]
    
    conn = st.connection(
        "supabase", 
        type=SupabaseConnection,
        url=S_URL,
        key=S_KEY
    )
except Exception as e:
    st.error(f"Erro ao carregar credenciais do Supabase: {e}")
    st.stop()

# --- FERRAMENTAS DO BANCO DE DADOS ---
# --- 2. FUNÇÕES DO BANCO (SUPABASE) ---
def ler_sql(query_ou_tabela, params=None):
    tabelas = ['usuarios', 'equipamentos', 'historico_loto', 'solicitacoes', 'ativos_loto']
    tabela_alvo = next((t for t in tabelas if t.upper() in query_ou_tabela.upper()), query_ou_tabela)

    try:
        q = conn.table(tabela_alvo).select("*")
        
        # Filtro via SQL (quando usado)
        if "WHERE" in query_ou_tabela.upper():
            parte_filtro = query_ou_tabela.split("where")[1] if "where" in query_ou_tabela else query_ou_tabela.split("WHERE")[1]
            if "=" in parte_filtro:
                coluna = parte_filtro.split("=")[0].strip().lower()
                valor = parte_filtro.split("=")[1].strip().replace("'", "").replace('"', "")
                if valor == "?" and params: q = q.eq(coluna, params[0])
                else: q = q.eq(coluna, valor)

        res = q.execute()
        df_res = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        
        if not df_res.empty:
            # 1. Processa JSON se existir
            if 'dados_etapas' in df_res.columns:
                df_json = pd.json_normalize(df_res['dados_etapas'])
                # Remove do JSON colunas que já existem na tabela principal (evita o erro de duplicate labels)
                cols_duplicadas = [c for c in df_json.columns if c.upper() in [str(x).upper() for x in df_res.columns]]
                df_json = df_json.drop(columns=cols_duplicadas, errors='ignore')
                
                df_res = pd.concat([df_res.reset_index(drop=True), df_json.reset_index(drop=True)], axis=1)
                df_res = df_res.drop(columns=['dados_etapas'], errors='ignore')

            # 2. Padroniza colunas para MAIÚSCULO e remove duplicatas físicas
            df_res.columns = [str(c).strip().upper() for c in df_res.columns]
            df_res = df_res.loc[:, ~df_res.columns.duplicated()] # Mata duplicatas de nome
            
        return df_res
    except:
        return pd.DataFrame()

def salvar_dataframe_no_sql(df, tabela):
    try:
        df_save = df.copy()
        df_save.columns = [str(c).lower().strip() for c in df_save.columns]
        
        if tabela.lower() == "historico_loto":
            # --- ADICIONE 'empresa' NA LISTA ABAIXO ---
            colunas_fixas = [
                'data', 'hora_inicio', 'hora_fim', 'os', 'resp', 
                'setor', 'equip', 'tipo', 'status', 'obs_geral', 'empresa' # <--- AQUI
            ]
            
            cols_checklist = [c for c in df_save.columns if c not in colunas_fixas and c != 'id']
            lista_dict = df_save[cols_checklist].to_dict(orient='records')
            df_save['dados_etapas'] = [lista_dict[0]] if lista_dict else [{}]
            df_save = df_save.drop(columns=cols_checklist)

        dados_finais = df_save.to_dict(orient='records')
        conn.table(tabela).insert(dados_finais).execute()
        st.cache_data.clear() # Limpa o cache para atualizar as telas
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False
    
def executar_sql(query, params=()):
    query_up = query.upper()
    try:
        tabelas = ['usuarios', 'equipamentos', 'historico_loto', 'solicitacoes', 'ativos_loto']
        tabela_alvo = next((t for t in tabelas if t.upper() in query_up), None)
        if not tabela_alvo: return

        # --- CASO A: INSERÇÃO (INSERT) ---
        if "INSERT INTO" in query_up:
            dados = {}
            if tabela_alvo == "solicitacoes":
                dados = {"data": params[0], "email": params[1], "nome_empresa": params[2], "observacao": params[3], "status": params[4]}
            elif tabela_alvo == "usuarios":
                dados = {"email": params[0], "senha": params[1], "nome": params[2], "area": params[3], "perfil": params[4], "ativo": params[5], "empresa": params[6]}
            elif tabela_alvo == "equipamentos":
                # Watson, garanta que os nomes abaixo batam com o seu banco Supabase
                dados = {
                    "setor": params[0], 
                    "equipamento": params[1], 
                    "link_raiz": params[2], 
                    "link_mapa": params[3], 
                    "link_procedimento": params[4]
                }
            
            if dados:
                conn.table(tabela_alvo).insert(dados).execute()

        # --- CASO B: EXCLUSÃO (DELETE) ---
        elif "DELETE FROM" in query_up:
            if tabela_alvo == "usuarios":
                conn.table("usuarios").delete().eq("email", params[0]).execute()
            elif tabela_alvo == "equipamentos":
                conn.table("equipamentos").delete().eq("setor", params[0]).eq("equipamento", params[1]).execute()
            elif tabela_alvo == "ativos_loto":
                # Mudança: Usamos eq("resp", params[0]) para garantir a exclusão pelo nome do responsável
                conn.table("ativos_loto").delete().eq("resp", f"{params[0]}|{params[1]}|{params[2]}").execute()

        # --- CASO C: ATUALIZAÇÃO (UPDATE) ---
        elif "UPDATE" in query_up:
            if tabela_alvo == "solicitacoes":
                # Se enviarmos um parâmetro, usamos ele como ID para atualização individual
                if params:
                    conn.table("solicitacoes").update({"status": "Resolvido"}).eq("id", params[0]).execute()
                else:
                    # Se não houver parâmetro, mantém o comportamento de limpar tudo (botão geral)
                    conn.table("solicitacoes").update({"status": "Resolvido"}).eq("status", "Pendente").execute()
            elif tabela_alvo == "usuarios":
                if "SET SENHA" in query_up:
                    conn.table("usuarios").update({"senha": params[0]}).eq("email", params[1]).execute()
                else:
                    # Adicionado params[4] para empresa e o e-mail passou para params[5]
                    d_u = {"nome": params[0], "ativo": params[1], "area": params[2], "perfil": params[3], "empresa": params[4]}
                    conn.table("usuarios").update(d_u).eq("email", params[5]).execute()
            elif tabela_alvo == "equipamentos":
                d_e = {"setor": params[0], "equipamento": params[1], "link_raiz": params[2], "link_mapa": params[3], "link_procedimento": params[4]}
                conn.table("equipamentos").update(d_e).eq("setor", params[5]).eq("equipamento", params[6]).execute()

        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erro Sherlock Execução: {e}")

# --- FUNÇÕES DE ATIVOS (JSONB) ---
# --- (IDENTIFICADOR COMPOSTA) ---
def salvar_ativo_sql(resp, equip, tipo, dados_dict):
    pk_id = f"{resp}|{equip}|{tipo}"
    conn.table("ativos_loto").upsert({"resp": pk_id, "dados_json": dados_dict}).execute()

def ler_ativo_sql(resp, equip, tipo):
    pk_id = f"{resp}|{equip}|{tipo}"
    try:
        res = conn.table("ativos_loto").select("dados_json").eq("resp", pk_id).execute()
        return res.data[0]['dados_json'] if res.data else None
    except:
        return None

# --- 3. CARGA GLOBAL COM PROTEÇÃO (FIM DO KEYERROR) ---
def carregar_dados_seguro():
    df_temp = ler_sql("equipamentos")
    if df_temp.empty:
        # Retorna DataFrame com as colunas certas para evitar o KeyError 'SETOR'
        return pd.DataFrame(columns=['SETOR', 'EQUIPAMENTO', 'LINK_RAIZ', 'LINK_MAPA', 'LINK_PROCEDIMENTO'])
    # Padroniza nomes para maiúsculo
    df_temp.columns = [c.upper() for c in df_temp.columns]
    return df_temp

df = carregar_dados_seguro()
# Se o df ainda estiver vazio (ex: tabela nova no banco), garante as colunas
if df.empty:
    df = pd.DataFrame(columns=['SETOR', 'EQUIPAMENTO', 'LINK_RAIZ', 'LINK_MAPA', 'LINK_PROCEDIMENTO'])

# --- CARGA GLOBAL DE EQUIPAMENTOS (O SEGURO CONTRA ERRO) ---
df = ler_sql("SELECT * FROM equipamentos")
if df.empty:
    # Se o banco estiver vazio, criamos as colunas na memória para o site não dar KeyError
    df = pd.DataFrame(columns=['SETOR', 'EQUIPAMENTO', 'LINK_RAIZ', 'LINK_MAPA', 'LINK_PROCEDIMENTO'])

# --- 2. INICIALIZAÇÃO DE MEMÓRIA (GAVETAS) ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'pagina_ativa' not in st.session_state: st.session_state.pagina_ativa = "🏠 Início"
if 'id_os_detalhe' not in st.session_state: st.session_state.id_os_detalhe = None
if 'editando_agora' not in st.session_state: st.session_state.editando_agora = False
if 'hora_inicio_loto' not in st.session_state: st.session_state.hora_inicio_loto = None
if 'timestamps' not in st.session_state: st.session_state.timestamps = {}
if 'f_os' not in st.session_state: st.session_state.f_os = ""
if 'f_resp' not in st.session_state: st.session_state.f_resp = "Todos"
if 'f_setor' not in st.session_state: st.session_state.f_setor = "Todos"
if 'f_maq' not in st.session_state: st.session_state.f_maq = "Todas"
if 'f_data_de' not in st.session_state: 
    st.session_state.f_data_de = datetime.date.today().replace(day=1)
if 'f_data_ate' not in st.session_state: 
    st.session_state.f_data_ate = datetime.date.today()
if 'f_empresa' not in st.session_state: 
    st.session_state.f_empresa = "Todas"
if 'aba_admin_ativa' not in st.session_state: 
    st.session_state.aba_admin_ativa = "➕ Novo Usuário"

# Função para validar o login
# --- 2. CONTROLE DE NAVEGAÇÃO E ACESSO ---

def limpar_texto(valor):
    """Remove o 'nan' e limpa espaços de qualquer valor vindo do Excel"""
    v = str(valor).strip()
    if v.lower() in ['nan', 'none', 'n/a', '']:
        return ""
    return v

def sugerir_senha_forte():
    caracteres = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(random.choice(caracteres) for i in range(8))

def realizar_login(email, senha):
    # 1. Admin de Emergência
    if email == "admin@admin.com" and senha == "admin123":
        st.session_state.autenticado = True
        st.session_state.usuario = {
            "NOME": "Administrador Geral", 
            "EMAIL": email, 
            "AREA": "Perfil System", 
            "PERFIL": "Perfil System", 
            "ATIVO": "Sim",
            "EMPRESA": "System Service" # Adicionado para evitar KeyError
        }
        st.rerun()

    # Limpeza de campos
    email_limpo = str(email).strip().lower()
    senha_limpa = str(senha).strip()

    # 2. Busca no Banco de Dados APENAS pelo E-MAIL
    df_u = ler_sql("SELECT * FROM usuarios WHERE EMAIL = ?", (email_limpo,))
    if not df_u.empty:
        df_u = df_u[df_u['EMAIL'].astype(str).str.lower() == email_limpo.lower()]

    # --- VALIDAÇÃO NÍVEL 1: EXISTÊNCIA DO CADASTRO ---
    if df_u.empty:
        st.error("⚠️ **USUÁRIO NÃO CADASTRADO.** O e-mail informado não foi encontrado em nossa base. Verifique a digitação ou fale com o administrador.")
        return # Encerra aqui

    dados = df_u.iloc[0].to_dict()
    
    # --- VALIDAÇÃO NÍVEL 2: STATUS DO ACESSO ---
    status = str(dados.get('ATIVO', 'Sim')).strip().lower()
    if status in ["não", "nao"]:
        st.error("🚫 **ACESSO SUSPENSO.** Seu cadastro está inativo. Por favor, entre em contato com a administradora do software para regularizar sua situação.")
        return # Encerra aqui

    # --- VALIDAÇÃO NÍVEL 3: CONFERÊNCIA DE SENHA ---
    if str(dados.get('SENHA')) == senha_limpa:
        st.session_state.autenticado = True
        st.session_state.usuario = dados
        st.rerun()
    else:
        st.error("🔑 **SENHA INCORRETA.** A senha informada é inválida para este e-mail. Tente novamente ou use a recuperação de senha abaixo.")

# TELA DE LOGIN UI
if not st.session_state.autenticado:
    st.write("##")
    c_l1, c_l2, c_l3 = st.columns([1, 1.2, 1]) 
    with c_l2:
        if os.path.exists("logo_ss_inicio2.png"):
            st.image("logo_ss_inicio2.png", width=120)
        
        # Título com tipografia mais elegante
        st.markdown("""
            <h2 style='margin-top: -15px; color: #1E293B; font-family: sans-serif;'>
                Portal de Acesso
            </h2>
            <h4 style='margin-top: -15px; color: #FF6B00; font-family: sans-serif; font-weight: 400;'>
                LOTO DIGITAL
            </h4>
        """, unsafe_allow_html=True)
        
        st.caption("Insira suas credenciais para acessar o painel.")
        
        with st.container(border=True):
            email_in = st.text_input("E-mail", placeholder="seu@email.com")
            senha_in = st.text_input("Senha", type="password", placeholder="••••••••")
            
            if st.button("Entrar no Sistema", type="primary", use_container_width=True):
                realizar_login(email_in, senha_in)
            
            with st.expander("❓ Esqueci minha senha"):
                st.caption("Preencha os dados abaixo para solicitar o reset ao administrador.")
                
                # Campos separados
                f_nome = st.text_input("Nome Completo", key="f_nome", placeholder="Seu Nome")
                f_empresa_rec = st.text_input("Sua Empresa", key="f_empresa_rec", placeholder="Seu Empresa") 
                f_email = st.text_input("E-mail Utilizado", key="f_email", placeholder="seu@email.com")
                f_obs = st.text_area("Observações (Opcional)", key="f_obs")
                
                if st.button("Enviar Solicitação", use_container_width=True):
                    if f_email and f_nome and f_empresa_rec:
                        fuso_br = datetime.timezone(datetime.timedelta(hours=-3))
                        agora_sol = datetime.datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
                        
                        # params: (data, email, nome_empresa (pessoa), observacao, status, empresa (empresa))
                        query = "INSERT INTO solicitacoes (DATA, EMAIL, NOME_EMPRESA, OBSERVACAO, STATUS, EMPRESA) VALUES (?, ?, ?, ?, ?, ?)"
                        executar_sql(query, (agora_sol, f_email, f_nome, f_obs, "Pendente", f_empresa_rec))
                        
                        st.success("✅ Solicitação enviada!")
                    else:
                        st.error("⚠️ Preencha Nome, Empresa e E-mail.")
    st.stop()

# --- CONFIGURAÇÕES DE MENU (Só roda se estiver logado) ---
OPCOES_MENU = ["🏠 Início", "➕ Nova Execução", "📊 Visão Geral", "⚙️ Painel Admin"]
if 'pagina_ativa' not in st.session_state: st.session_state.pagina_ativa = "🏠 Início"
if 'timestamps' not in st.session_state: st.session_state.timestamps = {}

def navegar_para(pagina):
    st.session_state.pagina_ativa = pagina
    st.session_state.id_os_detalhe = None
    st.session_state.editando_agora = False
    st.rerun()

# --- 3. CARGA DE DADOS (AGORA VIA BANCO DE DADOS) ---
@st.cache_data(ttl=600) # Mantém em memória por 10 minutos para ser rápido
def carregar_dados():
    # Busca todos os equipamentos do banco sem distinção de empresa
    df_temp = ler_sql("equipamentos")
    if not df_temp.empty:
        # Padroniza as colunas para maiúsculo
        df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
        # Remove duplicatas de colunas se existirem
        df_temp = df_temp.loc[:, ~df_temp.columns.duplicated()]
        return df_temp.fillna("")
    
    # Se o banco estiver vazio, retorna a estrutura básica para não dar erro no código
    return pd.DataFrame(columns=['SETOR', 'EQUIPAMENTO', 'LINK_RAIZ', 'LINK_MAPA', 'LINK_PROCEDIMENTO'])

# Atualiza a variável global que alimenta os selectboxes do app
df = carregar_dados()

@st.cache_data(show_spinner="Baixando documento...")
def obter_pdf_base64(url_compartilhada):
    try:
        if str(url_compartilhada).lower() == "nan" or not url_compartilhada:
            return None
        
        # 1. Converte o link do OneDrive para o link de download direto
        data_bytes64 = base64.b64encode(bytes(url_compartilhada, 'utf-8'))
        data_encoded = data_bytes64.decode('utf-8').replace('/', '_').replace('+', '-').rstrip('=')
        link_direto = f"https://api.onedrive.com/v1.0/shares/u!{data_encoded}/root/content"
        
        # 2. O Python baixa o arquivo
        response = requests.get(link_direto)
        if response.status_code == 200:
            # Converte o conteúdo do PDF para uma string Base64
            base64_pdf = base64.b64encode(response.content).decode('utf-8')
            return base64_pdf
        return None
    except:
        return None

def exibir_pdf_no_quadro(link_original):
    pdf_base64 = obter_pdf_base64(link_original)
    if pdf_base64:
        # Cria o componente HTML que injeta o PDF direto no navegador
        pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Não foi possível carregar o documento. Verifique se o link permite 'Acesso Público'.")
        st.link_button("Abrir manualmente", link_original)

def gerar_pdf_loto_premium(dados_os, lista_itens):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    
    if os.path.exists("modelo_pdf.png"):
        pdf.image("modelo_pdf.png", x=0, y=0, w=210, h=297)

    # --- 1. CABEÇALHO (TEXTO BRANCO - COORDENADAS RESTAURADAS) ---
    pdf.set_text_color(255, 255, 255) 
    
    # OS no topo
    pdf.set_font("Helvetica", "B", 20)
    pdf.text(x=115, y=33.5, txt=limpar_texto(dados_os['OS']))
    
    # Dados da OS (Coordenadas originais do seu refino)
    pdf.set_font("Helvetica", "B", 10)
    pdf.text(x=52, y=43, txt=limpar_texto(dados_os['SETOR']))
    pdf.text(x=52, y=49.5, txt=limpar_texto(dados_os['EQUIP']))
    pdf.text(x=52, y=55.5, txt=limpar_texto(dados_os['RESP']))
    pdf.text(x=52, y=61.5, txt=limpar_texto(dados_os['DATA']))
    pdf.text(x=52, y=68, txt=limpar_texto(dados_os['HORA_INICIO']))
    pdf.text(x=52, y=74, txt=limpar_texto(dados_os['HORA_FIM']))
    
    #Duração
    try:
        h1 = datetime.datetime.strptime(str(dados_os['HORA_INICIO']), "%H:%M:%S")
        h2 = datetime.datetime.strptime(str(dados_os['HORA_FIM']), "%H:%M:%S")
        pdf.text(x=52, y=80, txt=str(h2 - h1))
    except:
        pdf.text(x=52, y=80, txt="---")

    # --- 2. TABELA (TEXTO CINZA ESCURO) ---
    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", "", 9)
    
    y_inicial_tabela = 117.2 # Coordenada original da linha 1
    altura_linha = 9.35      # Salto original calibrado por você

    for i, (_, nome_etapa) in enumerate(lista_itens):
        n_up = nome_etapa.upper()
        h = limpar_texto(dados_os.get(f"HORA_{n_up}", ""))
        obs = limpar_texto(dados_os.get(f"OBS_{n_up}", ""))
        na = dados_os.get(f"NA_{n_up}", False)
        
        y_atual = y_inicial_tabela + 1.2 + (i * altura_linha)
        
        # Horário
        txt_h = "N/A" if na else (h if h else "---")
        pdf.text(x=70, y=y_atual, txt=txt_h)
        
        # Observação da Etapa
        if obs:
            pdf.text(x=110, y=y_atual, txt=obs[:45])

    # --- 3. OBSERVAÇÕES GERAIS (CAIXA CINZA) ---
    obs_geral = limpar_texto(dados_os.get('OBS_GERAL', ''))
    if obs_geral:
        pdf.set_xy(40, 220) # Posição da caixa cinza
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(190, 5, txt=f"{obs_geral}")

    return bytes(pdf.output())

# Definimos a lista aqui fora para que o Histórico e a Execução consigam ler
itens_loto = [
    ("📢", "Preparação/Comunicação"), ("⚡", "Desligamento"),
    ("⛓️", "Isolamento da Energia"), ("🔒", "Aplicação de Bloqueio/Etiqueta"),
    ("🌫️", "Dissipar Energia Residual"), ("🧪", "Verificar Energia Zero"),
    ("🛠️", "Execução do trabalho"), ("🛡️", "Recompor Proteções"),
    ("🔓", "Retirar Bloqueios"), ("🔌", "Reenergizar/Teste")
]

def filtrar_por_periodo(df_input, data_inicio, data_fim):
    if df_input.empty or 'DATA' not in df_input.columns:
        return df_input
    # Converte a coluna DATA (string DD/MM/YYYY) para objeto de data do Pandas
    df_temp = df_input.copy()
    df_temp['DATA_DT'] = pd.to_datetime(df_temp['DATA'], format='%d/%m/%Y', errors='coerce').dt.date
    # Filtra entre o range selecionado
    mask = (df_temp['DATA_DT'] >= data_inicio) & (df_temp['DATA_DT'] <= data_fim)
    return df_temp[mask].drop(columns=['DATA_DT'])

# --- 4. SIDEBAR ---
with st.sidebar:

    col_sync, _ = st.columns([1.2, 1])
    with col_sync:
        if st.button("🔄 Atualizar", help="Sincronizar banco de dados"):
            st.cache_data.clear()
            st.toast("Sincronizado!")
            time.sleep(0.5)
            st.rerun()
    st.write("---")

    if os.path.exists("logo_ss.png"):
        st.image("logo_ss.png", width=180)
    
    st.markdown("### Menu")
    
    # Define o menu baseado no perfil
    user_p = st.session_state.usuario
    if user_p['PERFIL'] == 'Perfil System':
        OPCOES_MENU = ["🏠 Início", "➕ Nova Execução", "📊 Visão Geral", "⚙️ Painel Admin"]
    elif user_p['PERFIL'] == 'Perfil Gerencial Clientes':
        OPCOES_MENU = ["🏠 Início", "➕ Nova Execução", "📊 Visão Geral", "⚙️ Painel Admin"]
    else:
        OPCOES_MENU = ["🏠 Início", "➕ Nova Execução", "📊 Visão Geral"]

    # Renderiza botões verticais (Menu Nativo)
    for opcao in OPCOES_MENU:
        estilo = "primary" if st.session_state.pagina_ativa == opcao else "secondary"
        # Adicionamos um .strip() para garantir que espaços não quebrem a lógica
        if st.sidebar.button(opcao, key=f"btn_side_{opcao}", use_container_width=True, type=estilo):
            st.session_state.pagina_ativa = opcao
            st.session_state.id_os_detalhe = None
            st.rerun()

    st.write("---")
    if st.button("🚪 Sair da Conta", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario = None
        st.rerun()

# --- 5. TELA DE INÍCIO (DASHBOARD) ---
if st.session_state.pagina_ativa == "🏠 Início":
    # 1. Logo Centralizada (Preservando sua imagem)
    col_logo1, col_logo2, col_logo3 = st.columns([1, 0.6, 1])
    with col_logo2:
        if os.path.exists("logo_ss_inicio2.png"):
            #st.image("logo_ss_inicio2.png", use_container_width=True)
            st.image("logo_ss_inicio2.png", width=180)

    # 2. Título Profissional (Seguindo o padrão do Login)
    st.markdown("""
        <div style='text-align: center; margin-top: -20px;'>
            <h1 style='color: #1E293B; margin-bottom: 0; font-family: sans-serif; font-size: 2.5rem;'>
                LOTO DIGITAL
        </div>
    """, unsafe_allow_html=True)
    
    # --- LÓGICA DE SAUDAÇÃO INTELIGENTE (CORRIGIDA UTC-3 - Horário de Brasília por conta do Servidor em North Virginia US) ---
    fuso_br = datetime.timezone(datetime.timedelta(hours=-3))
    hora_agora = datetime.datetime.now(fuso_br).hour
    
    if 5 <= hora_agora < 12:
        txt_saudacao = "Bom dia"
    elif 12 <= hora_agora < 18:
        txt_saudacao = "Boa tarde"
    else:
        txt_saudacao = "Boa noite"
    
    # Pega apenas o primeiro nome para ser mais amigável
    primeiro_nome = st.session_state.usuario['NOME'].split()[0]
    
    st.markdown(f"""
        <p style='text-align: center; color: #666;'>
            Controle de Lockout/Tagout<br>
            {txt_saudacao}, <b style='color:#FF6B00'>{primeiro_nome}</b>!
        </p>
    """, unsafe_allow_html=True)

    # --- MÉTRICAS REAIS VIA SQL (FILTRADAS POR PERFIL) ---
    user_atual = st.session_state.usuario
    perfil_logado = user_atual['PERFIL']
    
    try:
        # Buscamos tudo do banco primeiro
        df_h_tudo = ler_sql("historico_loto").reset_index(drop=True)
        df_a_tudo = ler_sql("ativos_loto").reset_index(drop=True)
    except Exception as e:
        st.error(f"Erro ao conectar com o banco: {e}")
        df_h_tudo = pd.DataFrame()
        df_a_tudo = pd.DataFrame()

    # --- 2. FILTROS DE PERÍODO E EMPRESA (HOME) ---
    with st.expander("🔍 Filtros de Relatórios", expanded=False): # Começa fechado
        col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
        
        hoje = datetime.date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        
        with col_f1:
            data_de = st.date_input("📅 De:", key="f_data_de")
        with col_f2:
            data_ate = st.date_input("📅 Até:", key="f_data_ate")
            
        with col_f3:
            lista_empresas_filtro = ["Todas"]
            if not df_h_tudo.empty and 'EMPRESA' in df_h_tudo.columns:
                lista_empresas_filtro += sorted([str(x) for x in df_h_tudo['EMPRESA'].unique() if x and str(x).lower() != 'nan'])
            
            if perfil_logado == 'Perfil System':
                # Adicionamos a KEY aqui para sincronizar
                empresa_sel_home = st.selectbox("🏢 Empresa:", lista_empresas_filtro, key="f_empresa")
            else:
                empresa_sel_home = user_atual.get('EMPRESA', 'Não definida')
                st.session_state.f_empresa = empresa_sel_home # Garante que o filtro global saiba a empresa
                st.info(f"🏢 Empresa: {empresa_sel_home}")

    # --- 3. LÓGICA DE FILTRAGEM E CÁLCULO ---
    total_finalizados = total_cancelados = total_ativos = 0

    try:
        # A) Filtro por Perfil e Empresa
        if perfil_logado == 'Perfil System':
            df_h_base = df_h_tudo if empresa_sel_home == "Todas" else df_h_tudo[df_h_tudo['EMPRESA'] == empresa_sel_home]
            df_a_base = df_a_tudo if empresa_sel_home == "Todas" else df_a_tudo[df_a_tudo['EMPRESA'] == empresa_sel_home]
        elif perfil_logado == 'Perfil Gerencial Clientes':
            df_h_base = df_h_tudo[df_h_tudo['EMPRESA'] == empresa_sel_home]
            df_a_base = df_a_tudo[df_a_tudo['EMPRESA'] == empresa_sel_home]
        else:
            df_h_base = df_h_tudo[df_h_tudo['RESP'] == user_atual['NOME']]
            df_a_base = df_a_tudo[df_a_tudo['RESP'] == user_atual['NOME']]

        # B) Filtro por Data
        df_h_count = filtrar_por_periodo(df_h_base, data_de, data_ate)
        
        # C) Atribuição dos valores para os botões
        total_finalizados = len(df_h_count[df_h_count['STATUS'] == 'CONCLUÍDO']) if not df_h_count.empty else 0
        total_cancelados = len(df_h_count[df_h_count['STATUS'] == 'CANCELADO']) if not df_h_count.empty else 0
        total_ativos = len(df_a_base) if not df_a_base.empty else 0
        
    except Exception as e:
        st.error(f"Erro ao processar cálculos: {e}")

# --- 3. MÉTRICAS CLICÁVEIS (ESTILO DASHBOARD) ---
    st.write("##")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f'''
            <div class="metric-container">
                <span class="metric-label-custom">Total</span>
                <span class="metric-value-custom" style="color: #1E3A8A;">{total_finalizados + total_ativos + total_cancelados}</span>
            </div>
        ''', unsafe_allow_html=True)
        if st.button("Ver detalhes", key="btn_h_total", use_container_width=False):
            st.session_state.aba_desejada = "Todas"
            navegar_para("📊 Visão Geral")

    with c2:
        st.markdown(f'''
            <div class="metric-container">
                <span class="metric-label-custom">Em Execução</span>
                <span class="metric-value-custom" style="color: #3B82F6;">{total_ativos}</span>
            </div>
        ''', unsafe_allow_html=True)
        if st.button("Ver detalhes", key="btn_h_ativos", use_container_width=False):
            st.session_state.aba_desejada = "Ativas"
            navegar_para("📊 Visão Geral")

    with c3:
        st.markdown(f'''
            <div class="metric-container">
                <span class="metric-label-custom">Concluídas</span>
                <span class="metric-value-custom" style="color: #10B981;">{total_finalizados}</span>
            </div>
        ''', unsafe_allow_html=True)
        if st.button("Ver detalhes", key="btn_h_conc", use_container_width=False):
            st.session_state.aba_desejada = "Concluídas"
            navegar_para("📊 Visão Geral")

    with c4:
        st.markdown(f'''
            <div class="metric-container">
                <span class="metric-label-custom">Canceladas</span>
                <span class="metric-value-custom" style="color: #EF4444;">{total_cancelados}</span>
            </div>
        ''', unsafe_allow_html=True)
        if st.button("Ver detalhes", key="btn_h_canc", use_container_width=False):
            st.session_state.aba_desejada = "Canceladas"
            navegar_para("📊 Visão Geral")


    # --- BOTÕES DE AÇÃO (Lógica Inteligente de Retomada) ---
    st.write("##")
    
      # 1. Busca TODOS os registros ativos deste usuário (Sem cache para ser em tempo real)
    user_nome = st.session_state.usuario['NOME']
    user_area = st.session_state.usuario.get('AREA', 'Manutenção Mecânica')
    setor_sel = None
    maquina_sel = None
    os_n = ""
    resp_n = user_nome
    tipo = user_area
    obs_final = ""
    reg = None
    
    # --- BUSCA DE ATIVOS POR PERFIL (HOME) ---
    if perfil_logado == 'Perfil System':
        # 1. Master vê TUDO (Radar Global)
        res_at = conn.client.table("ativos_loto").select("*").execute()
        ativos_usuario = res_at.data if res_at.data else []

    elif perfil_logado == 'Perfil Gerencial Clientes':
        # 2. Supervisor vê apenas os registros ativos da sua EMPRESA
        res_bruto = conn.client.table("ativos_loto").select("*").execute()
        ativos_usuario = []
        if res_bruto.data:
            for r in res_bruto.data:
                d = r.get('dados_json') or r.get('DADOS_JSON')
                # Filtra apenas o que pertence à empresa do supervisor logado
                if d and d.get('EMPRESA') == user_atual.get('EMPRESA'):
                    ativos_usuario.append(r)
    else:
        # 3. Operador vê apenas o SEU trabalho
        res_at = conn.client.table("ativos_loto").select("*").ilike("resp", f"{user_nome}|%").execute()
        ativos_usuario = res_at.data if res_at.data else []

    c_b1, c_b2, c_b3 = st.columns([0.2, 2.6, 0.2])
    with c_b2:
        if ativos_usuario:
            st.info(f"Você possui **{len(ativos_usuario)}** execução(ões) em aberto.")
            # O loop abaixo vai criar um botão para CADA registro encontrado
            for reg_at in ativos_usuario:
                info_loto = reg_at.get('dados_json') or reg_at.get('DADOS_JSON')
                if not info_loto: continue
                
                tipo_at = info_loto.get('TIPO', 'Manutenção')
                maq_at = info_loto.get('EQUIP', 'Equipamento')
                os_at = info_loto.get('OS', 'N/A')
                
                # --- RECUPERAÇÃO DA NOTIFICAÇÃO 7/10 (HOME) ---
                progresso_h = 0
                timestamps_h = info_loto.get("TIMESTAMPS", {})
                na_etapas_h = info_loto.get("NA_ETAPAS", {})
                for i in range(7): 
                    n_it = itens_loto[i][1]
                    if timestamps_h.get(f"t_{n_it}") or na_etapas_h.get(f"na_{n_it}"):
                        progresso_h += 1

                # --- LÓGICA DE CÁLCULO DE TEMPO DECORRIDO (CORRIGIDA) ---
                tempo_formatado = "Calculando..."
                try:
                    fuso_br = datetime.timezone(datetime.timedelta(hours=-3))
                    h_ini_str = row.get('HORA_INICIO', '')
                    
                    if h_ini_str:
                        if len(h_ini_str) <= 8: # Apenas HH:MM:SS
                            hoje_str = datetime.datetime.now(fuso_br).strftime("%d/%m/%Y")
                            dt_ini = datetime.datetime.strptime(f"{hoje_str} {h_ini_str}", "%d/%m/%Y %H:%M:%S")
                        else: # DD/MM/YYYY HH:MM
                            dt_ini = datetime.datetime.strptime(h_ini_str, "%d/%m/%Y %H:%M")
                        
                        agora_br = datetime.datetime.now(fuso_br).replace(tzinfo=None)
                        # abs() garante que o intervalo seja sempre positivo (Módulo)
                        total_segundos = abs(int((agora_br - dt_ini).total_seconds()))
                        horas, resto = divmod(total_segundos, 3600)
                        minutos, _ = divmod(resto, 60)
                        tempo_formatado = f"{int(horas)}h {int(minutos)}min"
                except:
                    tempo_formatado = "---"

                # --- EXIBIÇÃO DOS ALERTAS ---
                if progresso_h >= 7:
                    st.markdown(f'<div class="alerta-vermelho">🚨 ALERTA: A máquina {maq_at} está FORA DE OPERAÇÃO há {tempo_formatado}.</div>', unsafe_allow_html=True)

                if info_loto.get('TIPO') == 'SESMT':
                    nome_exibir = info_loto.get('RESP') or info_loto.get('resp') or "Gestor SESMT"
                    st.markdown(f"""
                        <div style="background-color: #FEE2E2; padding: 15px; border-radius: 10px; border-left: 5px solid #EF4444; margin-bottom: 10px;">
                            <b style="color: #991B1B;">⚠️ INTERDIÇÃO SESMT: {maq_at}</b><br>
                            <span style="color: #B91C1C;">Tempo de Interdição: <b>{tempo_formatado}</b></span><br>
                            <small style="color: #B91C1C;">Responsável: {nome_exibir}</small>
                        </div>
                    """, unsafe_allow_html=True)
                    
                # Botão com chave única baseada no ID do banco
                if st.button(f"▶️ Continuar {tipo_at}: {maq_at} (OS: {os_at})", key=f"home_btn_{reg_at['resp']}", use_container_width=True):
                    # Injeta tudo na memória (Setor, Maquina, Tipo, etc.)
                    st.session_state["setor_exec"] = info_loto.get('SETOR')
                    st.session_state["maq_exec"] = maq_at
                    st.session_state["os_exec"] = os_at
                    st.session_state["tipo_exec"] = tipo_at
                    st.session_state["obs_final_exec"] = info_loto.get('OBS_GERAL', '')
                    st.session_state.hora_inicio_loto = info_loto.get('HORA_INICIO')
                    
                    # Restaura as memórias de etapas
                    st.session_state.timestamps = info_loto.get("TIMESTAMPS", {})
                    st.session_state.obs_etapas = info_loto.get("OBS_ETAPAS", {})
                    st.session_state.na_etapas = info_loto.get("NA_ETAPAS", {})
                    
                    # Sincroniza widgets
                    for _, n_it in itens_loto:
                        v_na = st.session_state.na_etapas.get(f"na_{n_it}", False)
                        st.session_state[f"na_{n_it}"] = v_na
                        st.session_state[f"check_{n_it}"] = (st.session_state.timestamps.get(f"t_{n_it}", "N/A") != "N/A") or v_na
                        st.session_state[f"input_{n_it}"] = st.session_state.obs_etapas.get(n_it, "")

                    st.session_state.editando_agora = True
                    st.session_state.pagina_ativa = "➕ Nova Execução"
                    st.rerun()
            st.write("")

        # BOTÃO NOVA EXECUÇÃO (Sempre visível ou muda de cor se houver pendente)
        if st.button("➕ Nova Execução", type="primary", use_container_width=True):
            navegar_para("➕ Nova Execução")
        
        st.write("") 
        
        if st.button("📊 Visão Geral", type="secondary", use_container_width=True):
            navegar_para("📊 Visão Geral")

# --- 6. TELA DE NOVA EXECUÇÃO ---
elif st.session_state.pagina_ativa == "➕ Nova Execução":
    st.title("➕ Nova Execução")
    
    # --- 1. NASCIMENTO DAS VARIÁVEIS ---
    user_nome = st.session_state.usuario['NOME']
    user_area = st.session_state.usuario.get('AREA', 'Manutenção Mecânica')
    setor_sel = None
    maquina_sel = None
    os_n = ""
    resp_n = user_nome
    tipo = user_area
    obs_final = ""
    reg = None

##trecho removido daqui

    # --- 3. PASSO 1: LOCALIZAÇÃO ---
    with st.container(border=True):
        st.subheader("📍 Passo 1: Localização")
        col1, col2 = st.columns(2)
        
        # SETOR com placeholder profissional
        setor_sel = col1.selectbox(
            "Setor *", 
            ["Selecione o setor"] + sorted(list(df['SETOR'].unique())), 
            key="setor_exec"
        )
        
        maquina_sel = None
        # Verifica se um setor real foi escolhido (e não o texto do placeholder)
        if setor_sel and setor_sel != "Selecione o setor":
            lista_maq = df[df['SETOR'] == setor_sel]['EQUIPAMENTO'].unique()
            
            # MÁQUINA com placeholder profissional
            maquina_sel = col2.selectbox(
                "Máquina *", 
                ["Selecione o equipamento"] + list(lista_maq), 
                key="maq_exec"
            )
            
            if maquina_sel == "Selecione o equipamento":
                maquina_sel = None # Mantém o Passo 2 escondido

            # --- Início da validação SESMT --- #
            # 1. Busca se existe interdição ativa
            res_sesmt = conn.client.table("ativos_loto").select("*").execute()
            interditada = False
            dados_interdicao = None
            id_registro_interdicao = None

            if res_sesmt.data:
                for reg in res_sesmt.data:
                    d = reg.get('dados_json') or reg.get('DADOS_JSON')
                    if d and str(d.get('EQUIP')).upper() == str(maquina_sel).upper():
                        if d.get('TIPO') == 'SESMT':
                            interditada = True
                            dados_interdicao = d
                            id_registro_interdicao = reg.get('resp')
                            break

            # 2. LÓGICA DE EXIBIÇÃO
            user_logado = st.session_state.usuario
            area_usuario = user_logado.get('AREA')

            if interditada:
                # Se a máquina está interditada, mostramos o aviso para TODOS
                st.error(f"🚫 **MÁQUINA INTERDITADA PELO SESMT**")
                # CORREÇÃO DO "NONE": Buscamos 'RESP' ou 'resp' do JSON
                #nome_responsavel = dados_interdicao.get('RESP') or dados_interdicao.get('resp') or id_registro_interdicao.split('|')[0]
                nome_responsavel = dados_interdicao.get('RESP') or dados_interdicao.get('resp') or str(id_registro_interdicao).split('|')[0] or "Não identificado"
                st.warning(f"Esta máquina foi suspensa por: **{nome_responsavel}**")
                
                # SE O USUÁRIO FOR SESMT: Ele pode LIBERAR
                if area_usuario == "SESMT":
                    st.info("Você tem permissão para liberar esta máquina.")
                    if st.button("🔓 LIBERAR MÁQUINA (Finalizar Interdição)", type="primary", use_container_width=True):
                        # Move para o histórico como CONCLUÍDO
                        agora_f = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
                        dados_h = {
                            "DATA": agora_f.strftime("%d/%m/%Y"),
                            "HORA_INICIO": dados_interdicao.get("HORA_INICIO"),
                            "HORA_FIM": agora_f.strftime("%H:%M:%S"),
                            "OS": dados_interdicao.get("OS"),
                            "RESP": user_logado['NOME'],
                            "EMPRESA": user_logado['EMPRESA'],
                            "SETOR": setor_sel,
                            "EQUIP": maquina_sel,
                            "TIPO": "SESMT",
                            "STATUS": "CONCLUÍDO",
                            "OBS_GERAL": "Interdição finalizada e máquina liberada pelo SESMT."
                        }
                        if salvar_dataframe_no_sql(pd.DataFrame([dados_h]), "historico_loto"):
                            conn.client.table("ativos_loto").delete().eq("resp", id_registro_interdicao).execute()
                            st.success("✅ Máquina liberada com sucesso!")
                            time.sleep(1)
                            st.rerun()
                    if st.button("⬅️ Voltar"): st.rerun()
                    st.stop()
                
                # SE NÃO FOR SESMT: Ele é bloqueado
                else:
                    st.info("Aguarde a liberação do SESMT para realizar manutenções nesta máquina.")
                    if st.button("⬅️ Voltar ao Início"): navegar_para("🏠 Início")
                    st.stop()

            # 3. SE NÃO ESTÁ INTERDITADA, MAS O USUÁRIO É SESMT (Ele pode INTERDITAR)
            elif area_usuario == "SESMT":
                st.subheader("🛠️ Painel de Interdição SESMT")
                os_sesmt = st.text_input("Número do Laudo/OS de Interdição *", placeholder="Ex: INT-2024-001")
                
                if os_sesmt:
                    if st.button("🚨 INTERDITAR MÁQUINA AGORA", type="primary", use_container_width=True):
                        agora_f = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
                        estado_interdicao = {
                            "SETOR": setor_sel, "EQUIP": maquina_sel, "OS": os_sesmt, "TIPO": "SESMT", 
                            "RESP": user_logado['NOME'], "EMPRESA": user_logado['EMPRESA'],
                            "HORA_INICIO": agora_f.strftime("%d/%m/%Y %H:%M:%S")
                        }
                        salvar_ativo_sql(user_logado['NOME'], maquina_sel, "SESMT", estado_interdicao)
                        st.error(f"🔴 Máquina {maquina_sel} interditada com sucesso!")
                        time.sleep(1)
                        navegar_para("🏠 Início")
                st.stop() # Impede o SESMT de ver o resto do checklist operacional

    # --- 4. PASSO 2: IDENTIFICAÇÃO ---
    if maquina_sel:
        if st.session_state.hora_inicio_loto is None:
            st.session_state.hora_inicio_loto = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M:%S")

        with st.container(border=True):
            st.subheader("📝 Passo 2: Identificação")
            
            # Pega a área do cadastro do usuário
            area_usuario = st.session_state.usuario.get('AREA', 'Manutenção Mecânica')
            
            # As opções agora são apenas estas 3
            opcoes_radio = ["Manutenção Mecânica", "Manutenção Elétrica", "SESMT"]

            st.radio(
                "Sua Área de Atuação:", 
                opcoes_radio, 
                # O index agora procura na lista de 3 opções
                index=opcoes_radio.index(area_usuario) if area_usuario in opcoes_radio else 0,
                horizontal=True, 
                key="tipo_exec_display",
                disabled=True 
            )
            tipo = area_usuario # Garante que o tipo gravado seja a área real
            
            # --- RADAR DE CONFLITO EMPRESARIAL (SENIOR DATA AUDIT) ---
            res_ativos = conn.client.table("ativos_loto").select("*").execute()
            lista_ativos = res_ativos.data if res_ativos.data else []
            
            conflito_v10 = None
            for reg in lista_ativos:
                d = reg.get('dados_json') or reg.get('DADOS_JSON')
                if d:
                    m_db = str(d.get('EQUIP', '')).strip().upper()
                    t_db = str(d.get('TIPO', '')).strip().upper()
                    e_db = str(d.get('EMPRESA', '')).strip().upper()
                    
                    m_at = str(maquina_sel).strip().upper()
                    t_at = str(tipo).strip().upper()
                    e_at = str(st.session_state.usuario.get('EMPRESA', '')).strip().upper()

                    if m_db == m_at and t_db == t_at and e_db == e_at:
                        conflito_v10 = reg
                        conflito_v10['DADOS_FIX'] = d
                        break

            # --- VALIDAÇÃO DE BLOQUEIO IMEDIATO ---
            if conflito_v10:
                dados_c = conflito_v10['DADOS_FIX']
                id_origem = conflito_v10.get('resp', '')
                dono = id_origem.split('|')[0] if '|' in id_origem else id_origem
                
                # Verificamos se a OS na tela é diferente da OS no banco para detectar tentativa de novo início
                os_banco = str(dados_c.get("OS", ""))
                os_atual = str(st.session_state.get("os_exec", ""))

                if os_atual != os_banco:
                    # 1. Alerta de Segurança 7/10
                    p_7 = sum(1 for i in range(7) if dados_c.get("TIMESTAMPS", {}).get(f"t_{itens_loto[i][1]}") or dados_c.get("NA_ETAPAS", {}).get(f"na_{itens_loto[i][1]}"))
                    if p_7 >= 7:
                        st.error(f"🚨 **ALERTA DE SEGURANÇA:** Máquina **{maquina_sel}** bloqueada em estágio avançado por {dono}.")

                    # CASO A: O bloqueio é do Hugo (Pode retomar ou descartar)
                    if dono == user_nome:
                        st.warning(f"⚠️ {user_nome}, você já possui este bloqueio de **{tipo}** ativo.")
                        c1, c2 = st.columns(2)
                        
                        if c1.button("▶️ Continuar Meu Trabalho", use_container_width=True, key="btn_ret_v10"):
                            # --- RESTAURAÇÃO INTEGRAL (Pulo do Gato) ---
                            st.session_state.os_exec = dados_c["OS"]
                            st.session_state.setor_exec = dados_c["SETOR"]
                            st.session_state.maq_exec = dados_c["EQUIP"]
                            st.session_state.tipo_exec = dados_c["TIPO"]
                            st.session_state.obs_final_exec = dados_c.get("OBS_GERAL", "")
                            st.session_state.hora_inicio_loto = dados_c["HORA_INICIO"]
                            st.session_state.timestamps = dados_c.get("TIMESTAMPS", {})
                            st.session_state.obs_etapas = dados_c.get("OBS_ETAPAS", {})
                            st.session_state.na_etapas = dados_c.get("NA_ETAPAS", {})
                            
                            # SINCRONIZAÇÃO VISUAL DOS WIDGETS
                            for _, n_it in itens_loto:
                                v_na = st.session_state.na_etapas.get(f"na_{n_it}", False)
                                st.session_state[f"na_{n_it}"] = v_na
                                h_v = st.session_state.timestamps.get(f"t_{n_it}", "N/A")
                                st.session_state[f"check_{n_it}"] = (h_v != "N/A") or v_na
                                st.session_state[f"input_{n_it}"] = st.session_state.obs_etapas.get(n_it, "")
                            
                            st.session_state.editando_agora = True
                            st.rerun()

                        if c2.button("➕ Iniciar Novo (Descarta antigo)", use_container_width=True, key="btn_nov_v10"):
                            # --- REGISTRO DE CANCELAMENTO E LIMPEZA TOTAL ---
                            dados_p_hist = {
                                "DATA": [datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%d/%m/%Y")],
                                "HORA_INICIO": [dados_c.get("HORA_INICIO", "N/A")],
                                "HORA_FIM": [datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%H:%M:%S")],
                                "OS": [dados_c.get("OS", "N/A")],
                                "RESP": [user_nome], "SETOR": [setor_sel], "EQUIP": [maquina_sel], "TIPO": [tipo],
                                "STATUS": ["CANCELADO"], "EMPRESA": [e_at],
                                "OBS_GERAL": ["Cancelamento Automático para início de nova execução"]
                            }
                            # Salva horários antigos no histórico antes de apagar
                            for _, n_it in itens_loto:
                                u_n = n_it.upper()
                                dados_p_hist[f"HORA_{u_n}"] = [dados_c.get('TIMESTAMPS', {}).get(f"t_{n_it}", "N/A")]
                                dados_p_hist[f"OBS_{u_n}"] = [dados_c.get('OBS_ETAPAS', {}).get(n_it, "")]
                                dados_p_hist[f"NA_{u_n}"] = [dados_c.get('NA_ETAPAS', {}).get(f"na_{n_it}", False)]

                            salvar_dataframe_no_sql(pd.DataFrame(dados_p_hist), "historico_loto")
                            conn.client.table("ativos_loto").delete().eq("resp", id_origem).execute()
                            
                            # LIMPEZA ABSOLUTA DA MEMÓRIA TÉCNICA
                            for k in ["os_exec", "obs_final_exec"]:
                                if k in st.session_state: del st.session_state[k]
                            st.session_state.timestamps = {}; st.session_state.obs_etapas = {}; st.session_state.na_etapas = {}
                            st.session_state.hora_inicio_loto = None
                            st.session_state.editando_agora = False # Volta para validação limpa
                            st.rerun()
                        st.stop()

                    # CASO B: O bloqueio é de um COLEGA (Trava Total)
                    else:
                        st.error(f"🚫 **BLOQUEIO POR COLEGA:** {dono} já possui um registro de {tipo} aqui.")
                        st.info(f"Aguarde a liberação da OS {dados_c.get('OS')} para intervir.")
                        if st.button("⬅️ Voltar ao Início"): navegar_para("🏠 Início")
                        st.stop()

            # --- FLUXO NORMAL (DESCONGELADO) ---
            c_os_col, c_info_col = st.columns(2)
            os_n = c_os_col.text_input("Número da OS *", placeholder="Ex: OS-2026-001", key="os_exec")
            c_info_col.info(f"Responsável: {resp_n}")

        # --- 5. PASSO 3: SEGURANÇA E DOCUMENTAÇÃO ---
        if os_n:
            if 'obs_etapas' not in st.session_state: st.session_state.obs_etapas = {}
            if 'na_etapas' not in st.session_state: st.session_state.na_etapas = {}

            with st.container(border=True):
                # 1. Busca todos os links do Banco de Dados
                linha_d = df[df['EQUIPAMENTO'] == maquina_sel].iloc[0]
                l_mapa = str(linha_d.get('LINK_MAPA', '')).strip()
                l_proc = str(linha_d.get('LINK_PROCEDIMENTO', '')).strip()
                l_raiz = str(linha_d.get('LINK_RAIZ', '')).strip()

                # 2. ABAS DE DOCUMENTAÇÃO COM EXPANDIR (ZOOM)
                t_map, t_tec, t_pasta = st.tabs(["🗺️ Mapa de Bloqueio", "🛠️ Procedimento Técnico", "📂 Pasta Completa"])
                
                with t_map:
                    f_m = st.toggle("🔍 Expandir visualização", key="f_m")
                    h_m = 1000 if f_m else 600
                    st.markdown(f'<iframe src="{l_mapa}" width="100%" height="{h_m}" style="border:none;" allowfullscreen></iframe>', unsafe_allow_html=True)
                
                with t_tec:
                    f_p = st.toggle("🔍 Expandir visualização", key="f_p")
                    h_p = 1000 if f_p else 600
                    st.markdown(f'<iframe src="{l_proc}" width="100%" height="{h_p}" style="border:none;" allowfullscreen></iframe>', unsafe_allow_html=True)
                
                with t_pasta:
                    st.info("Acesse a pasta original no OneDrive para outros arquivos:")
                    st.link_button("📂 Abrir Pasta de Procedimentos", l_raiz, use_container_width=True)
                
                st.write("---")
                st.write("### Itens de Segurança")
                
                status_etapas, progresso = [], 0
                
                # 3. LOOP DO CHECKLIST COM CONTADOR X/10
                for i, (icone, nome) in enumerate(itens_loto, 1):
                    k_ch, k_na = f"check_{nome}", f"na_{nome}"
                    if st.session_state.get(k_na, False): st.session_state[k_ch] = True
                    
                    is_ch = st.session_state.get(k_ch, False)
                    is_na = st.session_state.get(k_na, False)
                    card_c = "step-card-complete" if is_ch else "step-card"
                    
                    with st.container():
                        st.markdown(f'<div class="{card_c}">', unsafe_allow_html=True)
                        c_chk, c_txt, c_act = st.columns([0.5, 4, 1.5])
                        with c_chk: 
                            check = st.checkbox(" ", key=k_ch, disabled=is_na, label_visibility="collapsed")
                            if check and f"t_{nome}" not in st.session_state.timestamps:
                                st.session_state.timestamps[f"t_{nome}"] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%H:%M:%S")
                        with c_txt:
                            # RESTAURADO: Texto X/10
                            st.markdown(f"**{i}/10** {icone} **{nome}**")
                            if is_na: st.caption("🚫 Item desconsiderado (N/A)")
                            elif is_ch: st.caption(f"✓ {resp_n} • {st.session_state.timestamps.get(f't_{nome}','...')}")
                        with c_act:
                            c_na, c_msg = st.columns(2)
                            if nome in ["Dissipar Energia Residual", "Recompor Proteções"]:
                                st.session_state.na_etapas[k_na] = c_na.checkbox("N/A", key=k_na)
                            with c_msg.popover("💬"):
                                st.session_state.obs_etapas[nome] = st.text_area(f"Nota: {nome}", key=f"input_{nome}")
                        
                        status_etapas.append(is_ch)
                        if is_ch: progresso += 1
                        st.markdown('</div>', unsafe_allow_html=True)

                # 4. BARRA DE PROGRESSO AZUL
                st.write("##")
                st.progress(progresso / 10)
                st.write(f"**Progresso:** {progresso}/10 etapas validadas")
                obs_final = st.text_area("🗒️ Observações Gerais do Escopo", placeholder="Descreva aqui detalhes sobre o serviço ou anomalias encontradas...", key="obs_final_exec")

                # 5. AUTO-SAVE JSON (Sincroniza checklist e notas)
                estado_atual = {
                    "SETOR": setor_sel, 
                    "EQUIP": maquina_sel, 
                    "OS": os_n, 
                    "TIPO": tipo, 
                    "OBS_GERAL": obs_final,
                    "EMPRESA": st.session_state.usuario.get('EMPRESA', ''), # Vital para o filtro de colega
                    "HORA_INICIO": st.session_state.hora_inicio_loto,
                    "TIMESTAMPS": st.session_state.timestamps,
                    "OBS_ETAPAS": st.session_state.obs_etapas,
                    "NA_ETAPAS": st.session_state.na_etapas
                }
                
                # Chamada corrigida com 4 argumentos
                salvar_ativo_sql(resp_n, maquina_sel, tipo, estado_atual)
                
                # 6. BOTÕES FINAIS ALINHADOS
                if all(status_etapas):
                    st.success("✅ Protocolo completo!")

                # --- PASSO 3: EVIDÊNCIA FOTOGRÁFICA ---
                st.markdown("---")
                st.subheader("📸 Evidência de Bloqueio")
                st.caption("Capture até 5 fotos. A primeira é recomendada.")

                fotos_capturadas = []
                col_fotos = st.columns(5)
                
                for i in range(1, 6):
                    with col_fotos[i-1]:
                        f = st.camera_input(f"Foto {i}", key=f"cam_{i}")
                        if f:
                            fotos_capturadas.append(f)
                
                if fotos_capturadas:
                    st.success(f"✅ {len(fotos_capturadas)} foto(s) pronta(s) para registro!")

                st.write("---")
                # --- 2. BLOCO DE AÇÃO (BOTÕES ABAIXO DAS FOTOS) ---
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    if all(status_etapas):
                        # O BOTÃO AGORA ESTÁ FORA DO LOOP DAS FOTOS
                        if st.button("🏁 Finalizar e Registrar", type="primary", use_container_width=True, key="btn_finalizar_unico"):
                            
                            # A) SALVAMENTO DAS FOTOS
                            nomes_fotos_salvas = []
                            if fotos_capturadas:
                                try:
                                    # Usamos o fuso de Brasília para o nome do arquivo também
                                    fuso_br = datetime.timezone(datetime.timedelta(hours=-3))
                                    agora_f = datetime.datetime.now(fuso_br)
                                    agora_str_f = agora_f.strftime('%H%M%S')
                                    
                                    for idx, f_arq in enumerate(fotos_capturadas, 1):
                                        # Cria pasta com a OS / nome da foto com hora
                                        nome_arquivo = f"{os_n}/foto_{idx}_{agora_str_f}.jpg"
                                        
                                        conn.client.storage.from_("evidencias").upload(
                                            path=nome_arquivo,
                                            file=f_arq.getvalue(),
                                            file_options={"content-type": "image/jpeg"}
                                        )
                                        nomes_fotos_salvas.append(nome_arquivo)
                                except Exception as e:
                                    st.warning(f"Atenção: Algumas fotos não foram salvas. ({e})")

                            # B) PREPARAÇÃO DOS DADOS
                            lista_fotos_str = ", ".join(nomes_fotos_salvas)
                            obs_final_com_fotos = f"{st.session_state.obs_final_exec} | Fotos: {lista_fotos_str}" if nomes_fotos_salvas else st.session_state.obs_final_exec

                            dados_h = {
                                "DATA": [datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%d/%m/%Y")],
                                "HORA_FIM": [datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%H:%M:%S")],
                                "HORA_INICIO": [st.session_state.get('hora_inicio_loto', 'N/A')],
                                "OS": [os_n],
                                "RESP": [resp_n],
                                "EMPRESA": [st.session_state.usuario.get('EMPRESA', '')],
                                "SETOR": [setor_sel],
                                "EQUIP": [maquina_sel],
                                "TIPO": [tipo],
                                "OBS_GERAL": [obs_final_com_fotos],
                                "STATUS": ["CONCLUÍDO"]
                            }
                            
                            # C) ADICIONA AS ETAPAS DO CHECKLIST
                            for _, n_it in itens_loto:
                                u_it = n_it.upper()
                                dados_h[f"HORA_{u_it}"] = [st.session_state.timestamps.get(f"t_{n_it}", "N/A")]
                                dados_h[f"OBS_{u_it}"] = [st.session_state.obs_etapas.get(n_it, "")]
                                dados_h[f"NA_{u_it}"] = [st.session_state.na_etapas.get(f"na_{n_it}", False)]

                            # D) SALVAMENTO NO BANCO E LIMPEZA
                            if salvar_dataframe_no_sql(pd.DataFrame(dados_h), "historico_loto"):
                                chave_especifica = f"{resp_n}|{maquina_sel}|{tipo}"
                                conn.client.table("ativos_loto").delete().eq("resp", chave_especifica).execute()
                                
                                # Limpeza de Memória
                                st.session_state.editando_agora = False
                                st.session_state.timestamps = {}; st.session_state.obs_etapas = {}; st.session_state.na_etapas = {}
                                st.session_state.hora_inicio_loto = None
                                for c in ["os_exec", "obs_final_exec", "setor_exec", "maq_exec", "tipo_exec"]:
                                    if c in st.session_state: del st.session_state[c]
                                
                                st.toast("✅ Bloqueio finalizado!")
                                time.sleep(1)
                                navegar_para("📊 Visão Geral")
                    else:
                        # Este else está alinhado com o 'if all(status_etapas)'
                        st.info("💡 Conclua as 10 etapas do checklist para finalizar.")

                with col_f2:
                    # BOTÃO CANCELAR COM KEY ÚNICA
                    if st.button("❌ Cancelar Registro", use_container_width=True, key="btn_cancelar_unico"):
                        agora_c = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
                        dados_c = {
                            "DATA": [agora_c.strftime("%d/%m/%Y")],
                            "HORA_FIM": [agora_c.strftime("%H:%M:%S")],
                            "HORA_INICIO": [st.session_state.get('hora_inicio_loto', 'N/A')],
                            "OS": [os_n if os_n else "N/A"], 
                            "RESP": [resp_n], 
                            "EMPRESA": [st.session_state.usuario['EMPRESA']],
                            "SETOR": [setor_sel], 
                            "EQUIP": [maquina_sel], 
                            "TIPO": [tipo], 
                            "OBS_GERAL": ["Cancelado pelo usuário"], 
                            "STATUS": ["CANCELADO"]
                        }
                        for _, n_it in itens_loto:
                            u_n = n_it.upper()
                            dados_c[f"HORA_{u_n}"] = ["N/A"]
                            dados_c[f"OBS_{u_n}"] = [""]
                            dados_c[f"NA_{u_n}"] = [True]

                        if salvar_dataframe_no_sql(pd.DataFrame(dados_c), "historico_loto"):
                            chave_especifica = f"{resp_n}|{maquina_sel}|{tipo}"
                            conn.client.table("ativos_loto").delete().eq("resp", chave_especifica).execute()
                            
                            st.session_state.editando_agora = False
                            st.session_state.timestamps = {}; st.session_state.obs_etapas = {}; st.session_state.na_etapas = {}
                            st.session_state.hora_inicio_loto = None
                            for c in ["os_exec", "obs_final_exec", "setor_exec", "maq_exec", "tipo_exec"]:
                                if c in st.session_state: del st.session_state[c]
                            
                            st.warning("Execução cancelada.")
                            time.sleep(1)
                            navegar_para("📊 Visão Geral")


# --- 7. HISTÓRICO E DETALHAMENTO ---
elif st.session_state.pagina_ativa == "📊 Visão Geral":

    # --- RESET DE SCROLL "TRIPLE-CROWN" (Força o topo em qualquer navegador) ---
    st.components.v1.html(
        f"""
        <div style="display:none">{datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).timestamp()}</div>
        <script>
            // 1. Tenta scroll pela janela principal
            window.parent.window.scrollTo(0,0);
            
            // 2. Tenta scroll pelo container principal do Streamlit
            var mainContent = window.parent.document.querySelector('.main');
            if (mainContent) {{
                mainContent.scrollTo(0,0);
            }}

            // 3. Tenta novamente após um micro-atraso (garantia para conexões lentas)
            setTimeout(function() {{
                window.parent.window.scrollTo(0,0);
                if (mainContent) {{ mainContent.scrollTo(0,0); }}
            }}, 100);
        </script>
        """,
        height=0
    )

    # --- LEITURA DO HISTÓRICO VIA BANCO DE DADOS ---
    # Usamos a função ler_sql que retorna um DataFrame vazio se não houver dados
    df_hist = ler_sql("SELECT * FROM historico_loto")
    user_atual = st.session_state.usuario
    
    if not df_hist.empty:
        # Filtro de Segurança: Operador só vê o dele
        # IMPORTANTE: No banco a coluna agora se chama 'RESP' (maiúsculo)
        # Filtro de Segurança na página de listagem
        df_hist = ler_sql("historico_loto").reset_index(drop=True)
        user_atual = st.session_state.usuario
        
        if not df_hist.empty:
            if user_atual['PERFIL'] == 'Perfil Gerencial Clientes':
                # FILTRO AQUI TAMBÉM:
                emp_alvo = str(user_atual.get('EMPRESA', '')).strip()
                df_hist = df_hist[df_hist['EMPRESA'].astype(str).str.strip() == emp_alvo]
            elif user_atual['PERFIL'] == 'Perfil Operação':
                df_hist = df_hist[df_hist['RESP'] == user_atual['NOME']]

        # --- FUNÇÃO INTERNA: DESENHA O CARD ---
        def renderizar_card_na_lista(indice, dados_linha, aba):
            # Define as cores baseadas no STATUS
            if dados_linha['STATUS'] == "CONCLUÍDO":
                classe_cor = "card-concluida" # Verde
                texto_status = "● Concluído"
                classe_label = "hist-status"
            else:
                classe_cor = "card-cancelada" # Laranja
                texto_status = "● Cancelado"
                classe_label = "hist-status-cancel"

            # Cálculo de duração
            try:
                h_ini = str(dados_linha['HORA_INICIO'])
                # Se for o formato novo (com data), pegamos apenas a hora para o cálculo simples de duração finalizada
                if len(h_ini) > 8: h_ini = h_ini.split()[-1]
                
                h1 = datetime.datetime.strptime(h_ini, "%H:%M:%S")
                h2 = datetime.datetime.strptime(str(dados_linha['HORA_FIM']), "%H:%M:%S")
                delta = h2 - h1
                total_sec = abs(int(delta.total_seconds()))
                horas = total_sec // 3600
                minutos = (total_sec % 3600) // 60
                duracao_txt = f"{int(horas)}h {int(minutos)}min"
            except: duracao_txt = "N/D"

            st.markdown(f"""
                <div class="hist-card {classe_cor}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="hist-os">OS: {dados_linha['OS']}</span>
                        <span class="{classe_label}">{texto_status}</span>
                    </div>
                    <div class="hist-sub">{dados_linha['SETOR']} • {dados_linha['EQUIP']}</div>
                    <div class="hist-sub">🕒 {dados_linha['DATA']} | ⏱️ Duração: <b>{duracao_txt}</b></div>
                    <div class="hist-sub">👤 {dados_linha['RESP']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🔎 Detalhes da OS {dados_linha['OS']}", key=f"btn_det_{aba}_{indice}"):
                st.session_state.id_os_detalhe = dados_linha['OS']
                st.rerun()

        # --- LÓGICA DE TELAS (DETALHE OU LISTA) ---
        if st.session_state.id_os_detalhe is not None:
            # 1. Buscamos a OS correta dentro do histórico
            os_procurada = st.session_state.id_os_detalhe
            detalhe_os = df_hist[df_hist['OS'].astype(str) == str(os_procurada)]
            
            if detalhe_os.empty:
                st.error(f"Erro: Não localizamos os dados da OS {os_procurada} no arquivo.")
                if st.button("⬅️ Voltar para a lista"): 
                    st.session_state.id_os_detalhe = None
                    st.rerun()
                st.stop()
            
            # 2. Definimos 'row' como a primeira linha encontrada para essa OS
            row = detalhe_os.iloc[0]
            
            # 3. Botão Voltar
            if st.button("⬅️ Voltar para a lista"):
                st.session_state.id_os_detalhe = None
                st.rerun()

            # Cabeçalho do Detalhe
            col_h1, col_h2 = st.columns([4, 1])
            with col_h1:
                st.markdown(f"# OS: {row['OS']}")
                st.markdown(f"<span class='hist-status'>● {row['STATUS']}</span>", unsafe_allow_html=True)
            
            # --- CÁLCULO DE DURAÇÃO ---
            try:
                inicio_str = limpar_texto(row.get('HORA_INICIO', ''))
                fim_str = limpar_texto(row.get('HORA_FIM', ''))
                
                if inicio_str and fim_str:
                    h1 = datetime.datetime.strptime(inicio_str, "%H:%M:%S")
                    h2 = datetime.datetime.strptime(fim_str, "%H:%M:%S")
                    duracao_formatada = str(h2 - h1)
                else:
                    duracao_formatada = "N/D"
                    inicio_str = "Não registrado"
            except:
                duracao_formatada = "Erro no cálculo"
                inicio_str = "N/D"

            # --- GRID DE INFORMAÇÕES (Ficha Técnica) ---
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.caption("Setor")
                    st.markdown(f"**{row['SETOR']}**")
                    st.caption("Responsável")
                    st.markdown(f"**{row['RESP']}**")
                    st.caption("Conclusão")
                    st.markdown(f"**{row['DATA']}, {row['HORA_FIM']}**")
                with c2:
                    st.caption("Máquina"); st.markdown(f"**{row['EQUIP']}**")
                    st.caption("Início"); st.markdown(f"**{row['DATA']}, {inicio_str}**")
                    st.caption("Duração Total do Bloqueio")
                    st.success(f"⏱️ {duracao_formatada}")

                st.write("##")
                # Busca o link correto para o botão
                link_proc = df[df['EQUIPAMENTO'] == row['EQUIP']]['LINK_RAIZ'].values[0] if row['EQUIP'] in df['EQUIPAMENTO'].values else "#"
                st.link_button("📂 Abrir Procedimento (Consulta)", link_proc, use_container_width=True)

                # --- BOTÃO DE GERAR CERTIFICADO PDF ---
                pdf_bytes = gerar_pdf_loto_premium(row, itens_loto)
                st.download_button(
                    label="📄 Gerar Certificado LOTO (PDF)",
                    data=pdf_bytes,
                    file_name=f"LOTO_OS_{row['OS']}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            st.markdown("### Observações Gerais")
            with st.container(border=True):
                st.write(row['OBS_GERAL'] if str(row['OBS_GERAL']) != 'nan' else "Nenhuma observação registrada.")

            st.markdown("### Etapas")
            for _, nome_etapa in itens_loto:
                # O banco salvou como HORA_DESLIGAMENTO, etc.
                nome_upper = nome_etapa.upper()
                hora_e = limpar_texto(row.get(f"HORA_{nome_upper}", ""))
                obs_e = limpar_texto(row.get(f"OBS_{nome_upper}", ""))
                na_e = row.get(f"NA_{nome_upper}", False)
                
                status_icon = "🔘" if na_e else "✅"
                card_color = "#F1F5F9" if na_e else "#F0FDF4"
                
                # Só monta o texto de obs se ela realmente existir
                txt_obs = f'<br><i style="font-size: 0.85rem; color: #444;">Nota: {obs_e}</i>' if obs_e else ""
                # Só mostra o horário se ele existir
                txt_hora = f" • {hora_e}" if hora_e else ""

                st.markdown(f"""
                    <div style="background-color: {card_color}; padding: 15px; border-radius: 10px; margin-bottom: 8px; border: 1px solid #EEE;">
                        <span style="font-size: 1.1rem;">{status_icon} <b>{nome_etapa}</b></span><br>
                        <small style="color: gray;">{row['RESP']} • {row['DATA']}{txt_hora}</small>
                        {txt_obs}
                    </div>
                """, unsafe_allow_html=True)

        else:
            st.title("📋 Todas as Execuções" if user_atual['PERFIL'] == 'Perfil System' else "📊 Visão Geral")
            
            # --- 1. BLOCO DE FILTROS (DENTRO DO EXPANDER) ---
            with st.expander("🔍 FILTRAR REGISTROS"):
                c_limp, _ = st.columns([0.15, 0.85])
                if c_limp.button("🧹 Limpar", key="btn_clean_filtros"):
                    st.session_state.f_os = ""
                    st.session_state.f_resp = "Todos"
                    st.session_state.f_setor = "Todos"
                    st.session_state.f_maq = "Todas"
                    st.rerun()

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.text_input("Número da O.S.", key="f_os")
                    # Filtro de Empresa no Histórico (Apenas para Admin Geral)
                    if user_atual['PERFIL'] == 'Perfil System':
                        emps = ["Todas"] + sorted([str(x) for x in df_hist['EMPRESA'].unique() if x])
                        st.selectbox("Empresa", emps, key="f_empresa")
                    
                with c2:
                    setores = ["Todos"] + sorted(list(df_hist['SETOR'].unique()))
                    st.selectbox("Setor", setores, key="f_setor")
                    areas_filtro = ["Todas", "Manutenção Mecânica", "Manutenção Elétrica", "SESMT"]
                    st.selectbox("Área de Atuação", areas_filtro, key="f_area")
                    maqs = ["Todas"] + sorted(list(df_hist['EQUIP'].unique()))
                    st.selectbox("Equipamento", maqs, key="f_maq")
                
                with c3:
                    # Filtro de Data para o Download/Lista
                    hoje = datetime.date.today()
                    st.date_input("Data Início", key="f_data_de")
                    st.date_input("Data Fim", key="f_data_ate")
                    if user_atual['PERFIL'] == 'Perfil System':
                        resps = ["Todos"] + sorted(list(df_hist['RESP'].unique()))
                        st.selectbox("Responsável", resps, key="f_resp")

            # --- APLICAÇÃO DOS FILTROS UNIFICADA (Igual à Home) ---
            df_filtrado = df_hist.copy()
            if st.session_state.get('f_area', 'Todas') != "Todas":
                df_filtrado = df_filtrado[df_filtrado['TIPO'] == st.session_state.f_area] 
                # No banco, a área é gravada na coluna 'TIPO'
            
            # 1. Filtro de Perfil e Empresa (Segurança)
            if user_atual['PERFIL'] == 'Perfil System':
                if st.session_state.f_empresa != "Todas":
                    df_filtrado = df_filtrado[df_filtrado['EMPRESA'] == st.session_state.f_empresa]
            elif user_atual['PERFIL'] == 'Perfil Gerencial Clientes':
                df_filtrado = df_filtrado[df_filtrado['EMPRESA'] == user_atual.get('EMPRESA')]
            else:
                df_filtrado = df_filtrado[df_filtrado['RESP'] == user_atual['NOME']]

            # 2. Filtro de Data (Sincronizado)
            df_filtrado = filtrar_por_periodo(df_filtrado, st.session_state.f_data_de, st.session_state.f_data_ate)

            # 3. Filtros Manuais (OS, Setor, Maquina)
            if st.session_state.f_os:
                df_filtrado = df_filtrado[df_filtrado['OS'].astype(str).str.contains(st.session_state.f_os, case=False)]
            
            if st.session_state.get('f_resp', 'Todos') != "Todos" and user_atual['PERFIL'] == 'Perfil System':
                df_filtrado = df_filtrado[df_filtrado['RESP'] == st.session_state.f_resp]
            
            if st.session_state.f_setor != "Todos":
                df_filtrado = df_filtrado[df_filtrado['SETOR'] == st.session_state.f_setor]
                
            if st.session_state.f_maq != "Todas":
                df_filtrado = df_filtrado[df_filtrado['EQUIP'] == st.session_state.f_maq]
            
            df_filtrado = df_filtrado.reset_index(drop=True)

            # --- PREPARAÇÃO DOS DADOS DE ANDAMENTO (ATIVAS) ---
            df_andamento_raw = ler_sql("SELECT * FROM ativos_loto")
            df_andamento = pd.DataFrame()

            if not df_andamento_raw.empty:
                # 1. Transforma o JSON em colunas
                df_json_cols = pd.json_normalize(df_andamento_raw['DADOS_JSON'])
                
                # 2. Une as tabelas e remove o JSON original para não dar erro
                df_andamento = pd.concat([df_andamento_raw.drop(columns=['DADOS_JSON']), df_json_cols], axis=1)
                
                # 3. MATA COLUNAS DUPLICADAS (O segredo para evitar o erro do print)
                df_andamento = df_andamento.loc[:, ~df_andamento.columns.duplicated()].copy()
                
                df_andamento['STATUS'] = "EM EXECUÇÃO"

                # 4. Filtro de Empresa/Perfil (Igual ao Histórico)
                if user_atual['PERFIL'] == 'Perfil System':
                    if st.session_state.f_empresa != "Todas":
                        df_andamento = df_andamento[df_andamento['EMPRESA'] == st.session_state.f_empresa]
                elif user_atual['PERFIL'] == 'Perfil Gerencial Clientes':
                    df_andamento = df_andamento[df_andamento['EMPRESA'] == user_atual.get('EMPRESA')]
                else:
                    df_andamento = df_andamento[df_andamento['RESP'].astype(str).str.contains(user_atual['NOME'])]

                # 5. Filtros Manuais
                if st.session_state.f_os:
                    df_andamento = df_andamento[df_andamento['OS'].astype(str).str.contains(st.session_state.f_os, case=False)]
                if st.session_state.f_setor != "Todos":
                    df_andamento = df_andamento[df_andamento['SETOR'] == st.session_state.f_setor]
                if st.session_state.f_maq != "Todas":
                    # Tenta filtrar por EQUIP (nome no JSON) ou EQUIPAMENTO (nome na tabela)
                    col_maq = 'EQUIP' if 'EQUIP' in df_andamento.columns else 'EQUIPAMENTO'
                    df_andamento = df_andamento[df_andamento[col_maq] == st.session_state.f_maq]

            # 4. SISTEMA DE NAVEGAÇÃO POR STATUS (Central de Comando)
            opcoes_status = ["Todas", "Ativas", "Concluídas", "Canceladas"]
            
            # Pega o foco inicial da Home
            aba_foco = st.session_state.get('aba_desejada', "Todas")
            idx_vinda = opcoes_status.index(aba_foco) if aba_foco in opcoes_status else 0
            
            # O Radio agora é o ÚNICO que manda no restante da página
            escolha_status = st.radio("Filtrar visualização:", opcoes_status, index=idx_vinda, horizontal=True)
            
            # Limpa a vinda da Home para não travar o filtro
            if 'aba_desejada' in st.session_state:
                st.session_state.aba_admin_ativa = st.session_state.aba_desejada
                del st.session_state.aba_desejada

            # --- DEFINIÇÃO DO BANCO DE DADOS DA ABA SELECIONADA ---
            if escolha_status == "Todas":
                # Une histórico filtrado + andamento filtrado
                df_visualizacao = pd.concat([df_filtrado, df_andamento], axis=0, ignore_index=True)
            elif escolha_status == "Ativas":
                df_visualizacao = df_andamento
            elif escolha_status == "Concluídas":
                df_visualizacao = df_filtrado[df_filtrado['STATUS'] == "CONCLUÍDO"]
            else: # Canceladas
                df_visualizacao = df_filtrado[df_filtrado['STATUS'] == "CANCELADO"]

            # Limpeza final e ordenação para que os mais novos apareçam no topo
            df_visualizacao = df_visualizacao.loc[:, ~df_visualizacao.columns.duplicated()].copy()
            if not df_visualizacao.empty and 'DATA' in df_visualizacao.columns:
                # Ordena por data (as ativas podem não ter data formatada, então tratamos)
                df_visualizacao = df_visualizacao.sort_values(by='DATA', ascending=False)
            
            qtd_total_exibida = len(df_visualizacao)

            # --- BLOCO DE RESUMO E DOWNLOAD DINÂMICO ---
            c_down_info, c_down_btn = st.columns([3, 1])
            with c_down_info:
                st.markdown(f"📊 **Relatório Gerado ({escolha_status}):** {qtd_total_exibida} registros encontrados.")
                st.caption(f"Período: {st.session_state.f_data_de.strftime('%d/%m/%Y')} até {st.session_state.f_data_ate.strftime('%d/%m/%Y')}")

            with c_down_btn:
                if not df_visualizacao.empty:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_visualizacao.to_excel(writer, index=False, sheet_name='Relatório LOTO')
                    st.download_button(
                        label=f"📥 Baixar {escolha_status}",
                        data=buffer.getvalue(),
                        file_name=f"LOTO_{escolha_status}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

            # --- 5. PAGINAÇÃO E RENDERIZAÇÃO ---
            itens_por_pagina = 4
            total_paginas = (qtd_total_exibida // itens_por_pagina) + (1 if qtd_total_exibida % itens_por_pagina > 0 else 0)

            if total_paginas > 1:
                col_pag1, col_pag2, col_pag3 = st.columns([1, 1, 1])
                with col_pag2:
                    pagina_sel = st.number_input(f"Página (1 de {total_paginas})", min_value=1, max_value=total_paginas, step=1)
            else:
                pagina_sel = 1

            st.write("---")
            # Renderiza apenas os cards da página atual
            inicio = (pagina_sel - 1) * itens_por_pagina
            fim = inicio + itens_por_pagina
            df_pagina_exibicao = df_visualizacao.iloc[inicio:fim]

            if df_visualizacao.empty:
                st.info(f"Nenhum registro encontrado para '{escolha_status}' com os filtros aplicados.")
            else:
                for i, row in df_pagina_exibicao.iterrows():
                    if str(row.get('STATUS')) == "EM EXECUÇÃO":
                        # --- CÁLCULO DE TEMPO EM TEMPO REAL ---
                        tempo_formatado = "---"
                        try:
                            agora = datetime.datetime.now()
                            h_ini_str = info_loto.get('HORA_INICIO', '') # Na Visão Geral use row.get
                            
                            if h_ini_str:
                                # Se a string for longa (contém a data), usamos o formato completo com segundos
                                if len(h_ini_str) > 10:
                                    # Ajustado para ler o %S que você adicionou
                                    dt_ini = datetime.datetime.strptime(h_ini_str, "%d/%m/%Y %H:%M:%S")
                                else:
                                    # Caso existam registros antigos apenas com HH:MM:SS
                                    hoje_data = agora.strftime("%d/%m/%Y")
                                    dt_ini = datetime.datetime.strptime(f"{hoje_data} {h_ini_str}", "%d/%m/%Y %H:%M:%S")
                                
                                # Cálculo de distância absoluta
                                diff = agora - dt_ini
                                total_segundos = abs(int(diff.total_seconds()))
                                
                                dias = total_segundos // 86400
                                horas = (total_segundos % 86400) // 3600
                                minutos = (total_segundos % 3600) // 60
                                
                                if dias > 0:
                                    tempo_formatado = f"{dias}d {horas}h {minutos}min"
                                elif horas > 0:
                                    tempo_formatado = f"{horas}h {minutos}min"
                                else:
                                    tempo_formatado = f"{minutos}min"
                        except:
                            tempo_formatado = "Erro"

                        # DESENHA O CARD AZUL
                        st.markdown(f"""
                            <div class="hist-card card-ativa">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span class="hist-os">OS: {row['OS']}</span>
                                    <span style="background-color: #DBEAFE; color: #1E40AF; padding: 2px 10px; border-radius: 15px; font-size: 0.8rem; font-weight: bold;">● Em Execução</span>
                                </div>
                                <div class="hist-sub">{row['SETOR']} • {row.get('EQUIP', row.get('EQUIPAMENTO'))}</div>
                                <div class="hist-sub">🕒 Tempo decorrido: <b>{tempo_formatado}</b></div>
                                <div class="hist-sub">👤 Resp: {row['RESP']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Desenha card de Histórico (Concluído/Cancelado)
                        renderizar_card_na_lista(i, row, escolha_status)

            st.write("##")
            if st.button("➕ Iniciar Nova Execução", type="primary", use_container_width=True):
                navegar_para("➕ Nova Execução")
    else:
        st.info("Nenhum registro encontrado no sistema.")
    
    if st.button("⬅️ Voltar para o Início", key="btn_voltar_lista"): 
        navegar_para("🏠 Início")

# --- 8. MEU PERFIL ---
elif st.session_state.pagina_ativa == "👤 Meu Perfil":
    st.markdown("<h2 style='text-align: center;'>Meu Perfil</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Gerencie suas informações pessoais</p>", unsafe_allow_html=True)
    
    user = st.session_state.usuario
    
    # Card Visual
    st.markdown(f"""
        <div class="profile-card">
            <div class="profile-avatar">👤</div>
            <h3 style='margin-bottom:0;'>{user['NOME']}</h3>
            <p style='color: gray; font-size: 0.9rem;'>{user['EMAIL']}</p>
            <p style='color: #FF6B00; font-weight: bold;'>{user.get('EMPRESA', 'Empresa não definida')}</p> <!-- ADICIONE ESTA LINHA -->
            <hr style='border: 0.5px solid #EEE;'>
        </div>
    """, unsafe_allow_html=True)
    
    # Área de Atuação (Seletor)
    with st.container():
        st.write("##")
        col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
        with col_p2:
            # Lista completa de todas as áreas possíveis para exibição
            todas_areas = [
                "Manutenção Mecânica", "Manutenção Elétrica", "SESMT", "Supervisão Manutenção", "Administrador Master"
            ]
            
            # Garante que a área atual do usuário esteja na lista para não dar erro de index
            area_atual = user.get('AREA', 'Manutenção Mecânica')
            if area_atual not in todas_areas:
                todas_areas.append(area_atual)

            st.selectbox(
                "Sua Área de Atuação *", 
                todas_areas, 
                index=todas_areas.index(area_atual),
                disabled=True # Usuário não muda a própria área, apenas o admin
            )
            
            if st.button("Sair da Conta", use_container_width=True):
                st.session_state.autenticado = False
                st.rerun()

# Perfil Adm
elif st.session_state.pagina_ativa == "⚙️ Painel Admin":
    user_p = st.session_state.usuario
    
    # Proteção de acesso: só entra se for System ou Gerencial
    if user_p['PERFIL'] in ['Perfil System', 'Perfil Gerencial Clientes']:
        
        nome_empresa = user_p.get('EMPRESA') if user_p.get('EMPRESA') else "Geral"
        st.title(f"⚙️ Gestão Administrativa - {nome_empresa}")
        
        # --- CABEÇALHO DE IDENTIFICAÇÃO ---    
        st.markdown(f"""
            <div style="margin-left: 5px; margin-top: -20px; margin-bottom: 25px; padding-left: 10px;">
                <p style="color: #64748B; font-size: 1.15rem; letter-spacing: 0.5px;">
                    <span style="margin-right: 20px;"><b>Perfil:</b> {user_p['PERFIL']}</span>
                    <span style="margin-right: 20px;"><b>Setor:</b> {user_p['AREA']}</span>
                    <span><b>Usuário:</b> {user_p['NOME']}</span>
                </p>
            </div>
            <hr style="margin-top: -15px; margin-bottom: 30px; opacity: 0.3;">
        """, unsafe_allow_html=True)

        # 1. Lógica de Notificações
        df_s_contagem = ler_sql("SELECT STATUS FROM solicitacoes WHERE STATUS = 'Pendente'")
        qtd_pendente = len(df_s_contagem) if not df_s_contagem.empty else 0
        label_pedidos = f"🔑 Pedidos de Recuperação ({qtd_pendente}) 🔴" if qtd_pendente > 0 else "🔑 Pedidos de Recuperação"
                  
        # 2. SISTEMA DE NAVEGAÇÃO INTERNA (Substituindo st.tabs para persistência)
        if user_p['PERFIL'] == 'Perfil System':
            opcoes_admin = ["➕ Novo Usuário", "📝 Editar Usuário", "🛠️ Equipamentos", label_pedidos, "📁 Arquivos/Fotos"]
        else:
            opcoes_admin = ["➕ Novo Usuário", "📝 Editar Usuário", "📁 Arquivos/Fotos", label_pedidos]

        # Sincroniza a escolha
        if 'aba_admin_ativa' not in st.session_state:
            st.session_state.aba_admin_ativa = "➕ Novo Usuário"
        
        # Descobre o índice baseado na escolha salva
        try:
            # Se a escolha salva for a de pedidos, procuramos qualquer uma que comece com "🔑"
            if "🔑" in st.session_state.aba_admin_ativa:
                idx_atual = [i for i, s in enumerate(opcoes_admin) if "🔑" in s][0]
            else:
                idx_atual = opcoes_admin.index(st.session_state.aba_admin_ativa)
        except:
            idx_atual = 0

        # Navegação interna por pílulas (Horizontal)
        escolha_aba_admin = st.segmented_control(
            "Navegação:", 
            opcoes_admin, 
            default=opcoes_admin[idx_atual],
            selection_mode="single",
            key="aba_admin_ativa" # Mantemos a KEY para persistência
        )

        st.write("---")

        # --- ABA: CADASTRO (Liberada para ambos) ---
        if escolha_aba_admin == "➕ Novo Usuário":
            st.subheader("Dados do Novo Colaborador")
            
            # --- 1. FUNÇÕES DE CALLBACK (DEFINIDAS AQUI DENTRO) ---
            def sugerir_senha_callback():
                st.session_state["reg_senha"] = sugerir_senha_forte()

            def finalizar_cadastro_callback():
                nome = st.session_state.get("reg_nome", "")
                email = st.session_state.get("reg_email", "").strip()
                senha = st.session_state.get("reg_senha", "")
                area = st.session_state.get("reg_area", "Manutenção Mecânica")
                perfil = st.session_state.get("reg_perfil", "Perfil Operação")
                empresa = st.session_state.get("reg_empresa", "")

                if nome and email and senha and empresa:
                    check_user = ler_sql("SELECT EMAIL FROM usuarios WHERE EMAIL = ?", (email,))
                    if not check_user.empty:
                        st.session_state["msg_feedback"] = ("erro", f"❌ O e-mail '{email}' já está cadastrado.")
                    else:
                        query = "INSERT INTO usuarios (EMAIL, SENHA, NOME, AREA, PERFIL, ATIVO, EMPRESA) VALUES (?, ?, ?, ?, ?, ?, ?)"
                        executar_sql(query, (email, senha, nome, area, perfil, 'Sim', empresa))
                        # Limpa campos
                        for k in ["reg_nome", "reg_email", "reg_senha"]: st.session_state[k] = ""
                        st.session_state["msg_feedback"] = ("sucesso", f"✔️ Usuário {nome} cadastrado com sucesso!")
                else:
                    st.session_state["msg_feedback"] = ("aviso", "⚠️ Preencha todos os campos.")

            # --- 2. DESENHO DA INTERFACE (MANTIDO) ---
            with st.container(border=True):
                st.text_input("Nome Completo", key="reg_nome")
                st.text_input("E-mail (Login)", key="reg_email")
                
                # Bloco de Empresa inteligente
                if user_p['PERFIL'] == 'Perfil System':
                    df_u_temp = ler_sql("SELECT * FROM usuarios")
                    lista_empr = sorted(list(df_u_temp['EMPRESA'].unique())) if not df_u_temp.empty else []
                    c_emp1, c_emp2 = st.columns(2)
                    modo = c_emp1.selectbox("Modo Empresa:", ["Selecionar Existente", "Cadastrar Nova"])
                    if modo == "Selecionar Existente":
                        st.session_state["reg_empresa"] = c_emp2.selectbox("Empresas:", lista_empr)
                    else:
                        st.session_state["reg_empresa"] = c_emp2.text_input("Nova Empresa:", placeholder="Nome...")
                else:
                    st.text_input("Empresa", value=user_p['EMPRESA'], key="reg_emp_view", disabled=True)
                    st.session_state["reg_empresa"] = user_p['EMPRESA']

                col_senha, col_botao = st.columns([4, 1])
                with col_senha: st.text_input("Senha Inicial *", key="reg_senha")
                with col_botao:
                    st.write("##")
                    st.button("🎲 Sugerir", on_click=sugerir_senha_callback, use_container_width=True)

                # --- BLOCO UNIFICADO DE PERFIL E ÁREA ---
                c1, c2 = st.columns(2)

                # 1. Define as opções de Perfil baseadas em quem está logado
                if user_p['PERFIL'] == 'Perfil System':
                    opcoes_perfis_cad = ["Perfil Operação", "Perfil Gerencial Clientes", "Perfil System"]
                else:
                    # Gerencial pode criar outros supervisores da empresa dele ou operacionais
                    opcoes_perfis_cad = ["Perfil Operação", "Perfil Gerencial Clientes"]

                perfil_sel = c1.selectbox("Nível de Acesso (Perfil) *", opcoes_perfis_cad)

                # 2. Define as áreas baseadas no perfil que foi selecionado no campo acima
                if perfil_sel == "Perfil Operação":
                    areas = ["Manutenção Mecânica", "Manutenção Elétrica", "SESMT"]
                elif perfil_sel == "Perfil Gerencial Clientes":
                    areas = ["Supervisão Manutenção"]
                else: # Perfil System
                    areas = ["Administrador Master"]

                area_sel = c2.selectbox("Área de Atuação *", areas)

                # 3. Salva nas gavetas que a função 'finalizar_cadastro_callback' vai ler
                st.session_state["reg_perfil"] = perfil_sel
                st.session_state["reg_area"] = area_sel

                st.write("---")
                st.button("✅ Finalizar Cadastro", type="primary", on_click=finalizar_cadastro_callback, use_container_width=True)

                # --- 3. EXIBIÇÃO DE MENSAGENS (MANTIDO DENTRO DA ABA) ---
                if "msg_feedback" in st.session_state:
                    tipo, texto = st.session_state.pop("msg_feedback")
                    if tipo == "sucesso":
                        st.success(texto)
                    elif tipo == "erro":
                        st.error(texto)
                    else:
                        st.warning(texto)
          
        elif escolha_aba_admin == "📝 Editar Usuário":
            st.write("### Pesquisar e Editar Colaborador")
            
            # Busca todos e limpa a empresa logada para comparar
            df_u = ler_sql("SELECT * FROM usuarios")
            empresa_logada = str(user_p.get('EMPRESA', '')).strip()

            if user_p['PERFIL'] == 'Perfil Gerencial Clientes':
                # Filtro rigoroso: remove espaços e ignora maiúsculas/minúsculas
                df_u = df_u[df_u['EMPRESA'].astype(str).str.strip().str.upper() == empresa_logada.upper()]
            
            if not df_u.empty:
                # O ler_sql garante colunas em MAIÚSCULO: NOME, EMAIL, AREA...
                lista_nomes = [f"{row['NOME']} ({row['EMAIL']})" for _, row in df_u.iterrows()]
                selecao = st.selectbox("Selecione o usuário para alterar:", [""] + lista_nomes)
                
                if selecao:
                    email_original = selecao.split("(")[-1].replace(")", "").strip()
                    dados_u = df_u[df_u['EMAIL'] == email_original].iloc[0]
                    
                    with st.container(border=True):
                        c_ed1, c_ed2 = st.columns(2)
                        novo_nome = c_ed1.text_input("Nome", value=str(dados_u['NOME']))
                        novo_email = c_ed2.text_input("E-mail (Login)", value=str(dados_u['EMAIL'])) # Permite alterar e-mail
                        
                        novo_status = c_ed1.selectbox("Acesso Ativo?", ["Sim", "Não"], 
                                                    index=0 if str(dados_u['ATIVO']) == "Sim" else 1)
                        
                        # 1. Define o Perfil primeiro
                        lista_perfis_edit = ["Perfil Operação", "Perfil Gerencial Clientes", "Perfil System"]
                        perfil_idx = lista_perfis_edit.index(dados_u['PERFIL']) if dados_u['PERFIL'] in lista_perfis_edit else 0
                        novo_perfil = c_ed2.selectbox("Nível de Acesso", lista_perfis_edit, index=perfil_idx)
                        
                        # 2. Define a Área baseada no perfil (Igual ao cadastro)
                        if novo_perfil == "Perfil Operação":
                            lista_areas_edit = ["Manutenção Mecânica", "Manutenção Elétrica", "SESMT"]
                        elif novo_perfil == "Perfil Gerencial Clientes":
                            lista_areas_edit = ["Supervisão Manutenção"]
                        else:
                            lista_areas_edit = ["Administrador Master"]
                            
                        area_idx = lista_areas_edit.index(dados_u['AREA']) if dados_u['AREA'] in lista_areas_edit else 0
                        nova_area = c_ed1.selectbox("Área de Atuação", lista_areas_edit, index=area_idx)
                        
                        nova_empresa_edit = c_ed2.text_input("Empresa", value=str(dados_u.get('EMPRESA', '')))
                        
                        nova_senha = st.text_input("Resetar Senha (em branco para manter)", type="password")

                        if st.button("💾 Aplicar Alterações", type="primary", use_container_width=True):
                            query_update = """
                                UPDATE usuarios 
                                SET NOME = ?, EMAIL = ?, ATIVO = ?, AREA = ?, PERFIL = ?, EMPRESA = ?
                                WHERE EMAIL = ?
                            """
                            executar_sql(query_update, (novo_nome, novo_email, novo_status, nova_area, novo_perfil, nova_empresa_edit, email_original))
                            
                            if nova_senha:
                                executar_sql("UPDATE usuarios SET SENHA = ? WHERE EMAIL = ?", (nova_senha, novo_email))
                            
                            st.success(f"✅ O perfil de {novo_nome} foi atualizado!")
                            st.rerun()

                        # --- ÁREA DE EXCLUSÃO (PERIGOSA) ---
                        st.write("##")
                        with st.expander("⚠️ Zona de Perigo - Remover Usuário"):
                            st.write(f"Você tem certeza que deseja excluir permanentemente o acesso de **{novo_nome}**?")
                            confirmar_exclusao = st.checkbox("Eu entendo que esta ação é irreversível e apagará o usuário do banco de dados.")
                            
                            if st.button("🗑️ Confirmar Exclusão Definitiva", type="secondary", disabled=not confirmar_exclusao):
                                # Correção: usar email_original
                                executar_sql("DELETE FROM usuarios WHERE EMAIL = ?", (email_original,))
                                
                                st.error(f"O usuário {email_original} foi removido com sucesso.")
                                st.rerun()
            else:
                st.info("Não há usuários cadastrados no banco de dados.")
                
        elif escolha_aba_admin == "🛠️ Equipamentos" and user_p['PERFIL'] == 'Perfil System':
            st.subheader("Gerenciamento de Inventário")

            # --- 1. CADASTRAR NOVO EQUIPAMENTO VIA SQL ---
            with st.expander("➕ Cadastrar Novo Equipamento"):
                with st.form("form_novo_equipamento", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    new_setor = c1.text_input("Nome do Setor").upper()
                    new_equip = c2.text_input("Nome do Equipamento").upper()
                    new_link_pasta = st.text_input("Link da Pasta (OneDrive)")
                    new_link_mapa = st.text_input("Link Direto: Mapa de Bloqueio (PDF)")
                    new_link_tec = st.text_input("Link Direto: Procedimento Técnico (PDF)")
                    
                    if st.form_submit_button("✅ Salvar Novo Equipamento"):
                        if new_setor and new_equip:
                            # --- GRAVAÇÃO DIRETA NO BANCO ---
                            query_insert_maq = """
                                INSERT INTO equipamentos (SETOR, EQUIPAMENTO, LINK_RAIZ, LINK_MAPA, LINK_PROCEDIMENTO) 
                                VALUES (?, ?, ?, ?, ?)
                            """
                            # Enviamos os dados para a tabela 'equipamentos'
                            executar_sql(query_insert_maq, (new_setor, new_equip, new_link_pasta, new_link_mapa, new_link_tec))
                            
                            st.success(f"✔️ Equipamento {new_equip} cadastrado com sucesso no banco de dados!")
                            st.cache_data.clear() # Limpa o cache para a nova máquina aparecer na lista de execução
                        else:
                            st.error("Setor e Equipamento são obrigatórios!")

                st.write("---")

                # --- 2. EDITAR OU EXCLUIR EQUIPAMENTO VIA SQL ---
                st.subheader("📝 Editar ou Remover Equipamento")
                
                # Busca a lista atualizada direto do banco
                df_maq_edit = ler_sql("SELECT * FROM equipamentos")
                
                if not df_maq_edit.empty:
                    # Criamos a lista para o selectbox usando as colunas em maiúsculo do banco
                    opcoes_maq = [f"{row['SETOR']} | {row['EQUIPAMENTO']}" for _, row in df_maq_edit.iterrows()]
                    selecao_maq = st.selectbox("Selecione o equipamento para gerenciar:", [""] + opcoes_maq, key="sel_maq_edit")
                    
                    if selecao_maq:
                        # Extrai os nomes para localizar o registro
                        setor_alvo = selecao_maq.split("|")[0].strip()
                        maq_alvo = selecao_maq.split("|")[1].strip()
                        
                        # Busca os dados atuais do banco para preencher os campos
                        dados_atuais = df_maq_edit[(df_maq_edit['SETOR'] == setor_alvo) & (df_maq_edit['EQUIPAMENTO'] == maq_alvo)].iloc[0]
                        
                        with st.container(border=True):
                            st.info(f"Modificando: {maq_alvo}")
                            c_ed1, c_ed2 = st.columns(2)
                            up_setor = c_ed1.text_input("Alterar Nome do Setor", value=str(dados_atuais['SETOR'])).upper()
                            up_equip = c_ed2.text_input("Alterar Nome do Equipamento", value=str(dados_atuais['EQUIPAMENTO'])).upper()
                            
                            up_link_pasta = st.text_input("Alterar Link da Pasta", value=str(dados_atuais['LINK_RAIZ']))
                            up_link_mapa = st.text_input("Alterar Link do Mapa", value=str(dados_atuais['LINK_MAPA']))
                            up_link_tec = st.text_input("Alterar Link Técnico", value=str(dados_atuais['LINK_PROCEDIMENTO']))
                            
                            # --- BOTÃO DE SALVAR ALTERAÇÕES NO SQL ---
                            if st.button("💾 Aplicar Alterações no Equipamento", type="primary", use_container_width=True):
                                query_update_maq = """
                                    UPDATE equipamentos 
                                    SET SETOR = ?, EQUIPAMENTO = ?, LINK_RAIZ = ?, LINK_MAPA = ?, LINK_PROCEDIMENTO = ?
                                    WHERE SETOR = ? AND EQUIPAMENTO = ?
                                """
                                executar_sql(query_update_maq, (up_setor, up_equip, up_link_pasta, up_link_mapa, up_link_tec, setor_alvo, maq_alvo))
                                
                                st.success(f"✅ Dados de {up_equip} atualizados com sucesso no banco!")
                                st.cache_data.clear() # Limpa o cache para as listas mudarem no app todo
                                st.rerun()

                            # --- ZONA DE PERIGO (EXCLUSÃO VIA SQL) ---
                            st.write("##")
                            with st.expander("⚠️ Zona de Perigo - Excluir Equipamento"):
                                st.write(f"Tem certeza que deseja apagar **{maq_alvo}**?")
                                confirmar_del = st.checkbox(f"Confirmo a exclusão definitiva do equipamento {maq_alvo}")
                                
                                if st.button("🗑️ Confirmar Exclusão", type="secondary", use_container_width=True, disabled=not confirmar_del):
                                    # Executa o comando DELETE no banco
                                    executar_sql("DELETE FROM equipamentos WHERE SETOR = ? AND EQUIPAMENTO = ?", (setor_alvo, maq_alvo))
                                    
                                    st.error("Equipamento removido do sistema!")
                                    st.cache_data.clear()
                                    st.rerun()
                else:
                    st.info("Nenhum equipamento cadastrado no banco de dados.")

        # --- ABAS COMUNS (Perfil System e Perfil Gerencial Clientes) ---
        elif escolha_aba_admin == label_pedidos:
            st.write("### Solicitações")
            # Forçamos a leitura sem cache para garantir que o que foi resolvido suma na hora
            df_pendente = ler_sql("SELECT * FROM solicitacoes WHERE STATUS = 'Pendente'")
            
            if not df_pendente.empty:
                qtd = len(df_pendente)
                msg = f"Existe {qtd} solicitação aguardando revisão." if qtd == 1 else f"Existem {qtd} solicitações aguardando revisão."
                st.warning(msg)

                for idx, row in df_pendente.iterrows():
                    # Criamos uma chave única baseada no ID para o container e botões
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 2, 1.2])
                        with c1:
                            st.markdown(f"**👤 Usuário:** {row['NOME_EMPRESA']}")
                            st.caption(f"📧 {row['EMAIL']} | 🏢 {row.get('EMPRESA', 'N/D')}")
                        with c2:
                            st.markdown(f"**💬 Obs:** {row['OBSERVACAO']}")
                            st.caption(f"📅 Data: {row['DATA']}")
                        with c3:
                            # BOTÃO INDIVIDUAL: Agora com a query extremamente específica por ID
                            if st.button("Marcar como resolvido ✅", key=f"btn_sol_{row['ID']}", use_container_width=True):
                                executar_sql("UPDATE solicitacoes SET STATUS = 'Resolvido' WHERE ID = ?", (row['ID'],))
                                # Apenas o rerun é necessário, a KEY do segmented_control cuidará da posição
                                st.rerun()

                st.write("---")
                if st.button("🚨 Marcar TODAS como Resolvidas", type="secondary", use_container_width=True):
                    executar_sql("UPDATE solicitacoes SET STATUS = 'Resolvido' WHERE STATUS = 'Pendente'")
                    st.success("Todas as pendências foram limpas.")
                    time.sleep(1)
                    st.rerun()
            else:
                st.success("✅ Nenhuma solicitação pendente.")
          
        elif escolha_aba_admin == "📁 Arquivos/Fotos":
            st.subheader("📁 Gerenciador de Evidências")

            # --- ÁREA DE FILTROS REVISADA (ADMIN GERAL VÊ EMPRESA) ---
            c_f1, c_f2, c_f3 = st.columns([1.5, 1, 1])
            busca_arq = c_f1.text_input("🔍 Buscar por OS ou Nome", placeholder="Ex: OS-2026-001")
            ordem_arq = c_f2.selectbox("Ordenar por:", ["Mais recentes", "Mais antigos", "Nome (A-Z)"])

            # Lógica de Empresa para o Admin
            df_h_empresas = ler_sql("SELECT DISTINCT EMPRESA FROM historico_loto")
            lista_todas_empresas = ["Todas"] + sorted([str(x) for x in df_h_empresas['EMPRESA'].unique() if x and str(x).lower() != 'nan']) if not df_h_empresas.empty else ["Todas"]

            if user_p['PERFIL'] == 'Perfil System':
                filtro_emp_arq = c_f3.selectbox("🏢 Empresa:", lista_todas_empresas)
            else:
                filtro_emp_arq = user_p.get('EMPRESA', '')
                c_f3.info(f"🏢 {filtro_emp_arq}")

            # 1. Busca a lista bruta do Supabase
            # 1. Busca a lista bruta do Supabase
            try:
                lista_bruta = conn.client.storage.from_("evidencias").list()
                
                # --- FILTRO DE PRIVACIDADE / EMPRESA ---
                # Se não for Admin Geral OU se o Admin escolheu uma empresa específica
                if user_p['PERFIL'] != 'Perfil System' or filtro_emp_arq != "Todas":
                    empresa_alvo = filtro_emp_arq
                    
                    # Buscamos no histórico quais fotos pertencem a esta empresa
                    df_vinc = ler_sql(f"SELECT OBS_GERAL FROM historico_loto WHERE EMPRESA = '{empresa_alvo}'")
                    
                    fotos_permitidas = []
                    if not df_vinc.empty:
                        for obs in df_vinc['OBS_GERAL'].dropna():
                            if "Foto: " in str(obs):
                                nome_foto = str(obs).split("Foto: ")[-1].strip()
                                fotos_permitidas.append(nome_foto)
                    
                    # Filtra a lista do storage
                    lista_bruta = [a for a in lista_bruta if a['name'] in fotos_permitidas]

                if not lista_bruta:
                    st.info("Nenhum arquivo encontrado para os filtros selecionados.")
                else:
                    # 2. APLICAÇÃO DOS FILTROS DE BUSCA E ORDENAÇÃO EM PYTHON
                    arquivos_filtrados = [
                        a for a in lista_bruta 
                        if busca_arq.lower() in a['name'].lower()
                    ]

                    if ordem_arq == "Mais recentes":
                        arquivos_filtrados.sort(key=lambda x: x['created_at'], reverse=True)
                    elif ordem_arq == "Mais antigos":
                        arquivos_filtrados.sort(key=lambda x: x['created_at'])
                    else:
                        arquivos_filtrados.sort(key=lambda x: x['name'])

                    st.caption(f"Exibindo {len(arquivos_filtrados)} arquivos")

                    # 3. GRID DE EXIBIÇÃO
                    cols = st.columns(4)
                    for idx, arq in enumerate(arquivos_filtrados):
                        nome_arq = arq['name']
                        with cols[idx % 4]:
                            with st.container(border=True):
                                url = conn.client.storage.from_("evidencias").get_public_url(nome_arq)
                                if nome_arq.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    st.image(url, use_container_width=True)
                                else:
                                    st.write("📄 Arquivo")
                                
                                st.markdown(f"**{nome_arq[:15]}...**" if len(nome_arq) > 15 else f"**{nome_arq}**")
                                
                                data_c = arq['created_at'][:10]
                                ano, mes, dia = data_c.split('-')
                                st.caption(f"📅 {dia}/{mes}/{ano}")

                                c_down, c_del = st.columns([3, 1])
                                c_down.link_button("💾", url, use_container_width=True)
                                if c_del.button("🗑️", key=f"del_adm_{nome_arq}"):
                                    conn.client.storage.from_("evidencias").remove([nome_arq])
                                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao carregar arquivos: {e}")

    else:
        st.error("Acesso restrito a administradores.")
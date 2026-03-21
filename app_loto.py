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
    /* Cor da 1ª Coluna: TOTAL (Azul Corporativo) */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stMetricValue"] { 
        color: #1E3A8A !important;
    }
    
    /* Cor da 2ª Coluna: EM EXECUÇÃO (Azul Vibrante) */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stMetricValue"] {
        color: #3B82F6 !important;
    }
    
    /* Cor da 3ª Coluna: CONCLUÍDAS (Verde Segurança) */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stMetricValue"] {
        color: #10B981 !important;
    }
    
    /* Cor da 4ª Coluna: CANCELADAS (Vermelho Alerta) */
    div[data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stMetricValue"] {
        color: #EF4444 !important;
    }

    /* Ajuste para que o rótulo (Total, Em Execução...) fique centralizado também */
    [data-testid="stMetricLabel"] {
        display: flex;
        justify-content: center;
    }
            
    .stApp { background-color: #F8F9FA; }
    [data-testid="stMetricValue"] { font-size: 3.5rem !important; font-weight: 800 !important; color: #FF6B00 !important; }
    [data-testid="stMetricLabel"] { font-size: 1.2rem !important; font-weight: 600 !important; color: #64748B !important; }
    button[kind="primary"] { background-color: #FF6B00 !important; color: white !important; border-radius: 12px !important; height: 4rem !important; font-size: 1.1rem !important; font-weight: bold !important; width: 100%; }
    button[kind="secondary"] { background-color: #E2E8F0 !important; color: #1E293B !important; border-radius: 12px !important; height: 4rem !important; font-size: 1.1rem !important; font-weight: bold !important; width: 100%; }
    [data-testid="stMetric"] { background-color: white; padding: 25px !important; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #EDF2F7; text-align: center; }
        .hist-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border-left: 6px solid #FF6B00; /* Faixa laranja lateral */
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }
    .hist-os { font-weight: bold; font-size: 1.1rem; color: #1E293B; }
    .hist-status { 
        background-color: #DEF7EC; color: #03543F; 
        padding: 2px 10px; border-radius: 15px; font-size: 0.8rem; font-weight: bold;
    }
    .hist-sub { color: #64748B; font-size: 0.9rem; margin-top: 4px; }
    .hist-status-cancel { 
        background-color: #FDE2E2; color: #9B1C1C; 
        padding: 2px 10px; border-radius: 15px; font-size: 0.8rem; font-weight: bold;
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
    # 1. Admin de Emergência (Sempre funciona)
    if email == "admin@admin.com" and senha == "admin123":
        st.session_state.autenticado = True
        st.session_state.usuario = {"NOME": "Administrador Geral", "EMAIL": email, "AREA": "TI", "PERFIL": "Admin", "ATIVO": "Sim"}
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
            st.image("logo_ss_inicio2.png", width=150)
        
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
                f_nome = st.text_input("Seu Nome / Empresa", key="f_nome")
                f_obs = st.text_area("Observações (Ex: Esqueci a senha antiga)", key="f_obs")
                
                if st.button("Enviar Solicitação", use_container_width=True):
                    # Valida se o e-mail (lá de cima) e o nome foram preenchidos
                    if email_in and f_nome:
                        agora_sol = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                        
                        # --- GRAVAÇÃO DIRETA NO BANCO DE DADOS ---
                        query = """
                            INSERT INTO solicitacoes (DATA, EMAIL, NOME_EMPRESA, OBSERVACAO, STATUS) 
                            VALUES (?, ?, ?, ?, ?)
                        """
                        # Enviamos os dados como uma tupla para a nossa função executar_sql
                        executar_sql(query, (agora_sol, email_in, f_nome, f_obs, "Pendente"))
                        
                        st.success("✅ Solicitação enviada! O administrador recebeu seu pedido no Banco de Dados.")
                    else:
                        st.error("⚠️ Preencha seu e-mail e seu nome para enviar o pedido.")
    st.stop()

# --- CONFIGURAÇÕES DE MENU (Só roda se estiver logado) ---
OPCOES_MENU = ["🏠 Início", "➕ Nova Execução", "📋 Minhas Execuções", "👤 Meu Perfil", "⚙️ Painel Admin"]
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
    if os.path.exists("logo_ss.png"):
        st.image("logo_ss.png", use_container_width=True)
    
    st.markdown("### Menu")
    idx_atual = OPCOES_MENU.index(st.session_state.pagina_ativa)
    escolha = st.radio("Ir para:", OPCOES_MENU, index=idx_atual)
    
    # Se mudar pelo rádio, fazemos a mesma "faxina" que os botões fazem
    if escolha != st.session_state.pagina_ativa:
        st.session_state.pagina_ativa = escolha
        st.session_state.id_os_detalhe = None 
        st.session_state.editando_agora = False # LIBERA A TRAVA PARA PERGUNTAR AO VOLTAR
        st.rerun()

# --- 5. TELA DE INÍCIO (DASHBOARD) ---
if st.session_state.pagina_ativa == "🏠 Início":
    # 1. Logo Centralizada (Preservando sua imagem)
    col_logo1, col_logo2, col_logo3 = st.columns([1, 0.6, 1])
    with col_logo2:
        if os.path.exists("logo_ss_inicio2.png"):
            st.image("logo_ss_inicio2.png", use_container_width=True)

    # 2. Título Profissional (Seguindo o padrão do Login)
    st.markdown("""
        <div style='text-align: center; margin-top: -20px;'>
            <h1 style='color: #1E293B; margin-bottom: 0; font-family: sans-serif; font-size: 2.5rem;'>
                LOTO DIGITAL
        </div>
    """, unsafe_allow_html=True)
    
    # --- LÓGICA DE SAUDAÇÃO INTELIGENTE ---
    hora_agora = datetime.datetime.now().hour
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
    with st.container(border=True):
        col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
        
        hoje = datetime.date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        
        with col_f1:
            data_de = st.date_input("📅 De:", primeiro_dia_mes)
        with col_f2:
            data_ate = st.date_input("📅 Até:", hoje)
            
        with col_f3:
            lista_empresas_filtro = ["Todas"]
            if not df_h_tudo.empty and 'EMPRESA' in df_h_tudo.columns:
                # Pega empresas únicas ignorando nulos
                lista_empresas_filtro += sorted([str(x) for x in df_h_tudo['EMPRESA'].unique() if x and str(x).lower() != 'nan'])
            
            if perfil_logado == 'Admin':
                empresa_sel_home = st.selectbox("🏢 Empresa:", lista_empresas_filtro)
            else:
                empresa_sel_home = user_atual.get('EMPRESA', 'Não definida')
                st.info(f"🏢 Empresa: {empresa_sel_home}")

    # --- 3. LÓGICA DE FILTRAGEM ---
    try:
        # A) Filtro por Perfil e Empresa
        if perfil_logado == 'Admin':
            df_h_base = df_h_tudo if empresa_sel_home == "Todas" else df_h_tudo[df_h_tudo['EMPRESA'] == empresa_sel_home]
            df_a_base = df_a_tudo if empresa_sel_home == "Todas" else df_a_tudo[df_a_tudo['EMPRESA'] == empresa_sel_home]
        elif perfil_logado == 'Admin Cliente':
            df_h_base = df_h_tudo[df_h_tudo['EMPRESA'] == empresa_sel_home]
            df_a_base = df_a_tudo[df_a_tudo['EMPRESA'] == empresa_sel_home]
        else:
            df_h_base = df_h_tudo[df_h_tudo['RESP'] == user_atual['NOME']]
            df_a_base = df_a_tudo[df_a_tudo['RESP'] == user_atual['NOME']]

        # B) Filtro por Data (Usando a função que criamos no ajuste 1)
        df_h_count = filtrar_por_periodo(df_h_base, data_de, data_ate)
        
        # Totais para os cards
        total_finalizados = len(df_h_count[df_h_count['STATUS'] == 'CONCLUÍDO']) if not df_h_count.empty else 0
        total_cancelados = len(df_h_count[df_h_count['STATUS'] == 'CANCELADO']) if not df_h_count.empty else 0
        total_ativos = len(df_a_base) if not df_a_base.empty else 0
        
    except Exception as e:
        st.error(f"Erro ao processar filtros: {e}")
        total_finalizados = total_cancelados = total_ativos = 0

    # Exibição dos cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", str(total_finalizados + total_ativos + total_cancelados))
    c2.metric("Em Execução", str(total_ativos))
    c3.metric("Concluídas", str(total_finalizados))
    c4.metric("Canceladas", str(total_cancelados))

    # --- BOTÕES DE AÇÃO (Lógica Inteligente de Retomada) ---
    st.write("##")
    
    # 1. Verifica se existe trabalho pendente para este usuário no Banco de Dados
    user_nome = st.session_state.usuario['NOME']
    setor_sel = None
    maquina_sel = None
    os_n = ""
    resp_n = user_nome
    tipo = "Operação"
    obs_final = ""
    reg = None
    
    # Buscamos apenas o registro que pertence ao usuário logado
    df_at = ler_sql("SELECT * FROM ativos_loto WHERE RESP = ?", (user_nome,))
    
    registro_pendente = None
    if not df_at.empty:
        registro_pendente = df_at.iloc[0]

    # 2. Desenha os botões
    c_b1, c_b2, c_b3 = st.columns([0.2, 2.6, 0.2])
    with c_b2:
        if registro_pendente is not None:
            # --- AJUSTE SHERLOCK: O Supabase já entrega o JSON como dicionário ---
            info_loto = registro_pendente['DADOS_JSON']

            # --- LÓGICA DE MÁQUINA FORA DE OPERAÇÃO ---
            itens_concluidos = 0
            for i in range(7): # Verifica do item 1 ao 7
                nome_it = itens_loto[i][1]
                # Se tem timestamp ou se foi marcado como N/A
                if info_loto.get("TIMESTAMPS", {}).get(f"t_{nome_it}") or info_loto.get("NA_ETAPAS", {}).get(f"na_{nome_it}"):
                    itens_concluidos += 1
            
            if itens_concluidos >= 7:
                st.error(f"🚨 **ALERTA DE SEGURANÇA:** A máquina **{info_loto.get('EQUIP')}** encontra-se **FORA DE OPERAÇÃO** (Bloqueio em estágio avançado).")
            # ------------------------------------------
            
            st.warning(f"Você possui uma execução em aberto: **{info_loto.get('EQUIP', 'Equipamento')}**")
            
            if st.button(f"▶️ Continuar Trabalho (OS: {info_loto.get('OS', 'N/A')})", type="secondary", use_container_width=True):
                # INJETA OS DADOS NA MEMÓRIA (usando as chaves do JSON)
                st.session_state["setor_exec"] = str(info_loto['SETOR'])
                st.session_state["maq_exec"] = str(info_loto['EQUIP'])
                st.session_state["os_exec"] = str(info_loto['OS'])
                st.session_state["tipo_exec"] = str(info_loto['TIPO'])
                st.session_state["obs_final_exec"] = limpar_texto(info_loto.get('OBS_GERAL', ''))
                st.session_state.hora_inicio_loto = info_loto['HORA_INICIO']
                
                # Restaura memórias complexas direto do JSON
                st.session_state.timestamps = info_loto.get("TIMESTAMPS", {})
                st.session_state.obs_etapas = info_loto.get("OBS_ETAPAS", {})
                st.session_state.na_etapas = info_loto.get("NA_ETAPAS", {})
                
                # Sincroniza os componentes visuais (Checkboxes)
                for _, nome_item in itens_loto:
                    val_na = st.session_state.na_etapas.get(f"na_{nome_item}", False)
                    st.session_state[f"na_{nome_item}"] = val_na
                    h_v = st.session_state.timestamps.get(f"t_{nome_item}", "N/A")
                    st.session_state[f"check_{nome_item}"] = (h_v != "N/A") or val_na
                    st.session_state[f"input_{nome_item}"] = st.session_state.obs_etapas.get(nome_item, "")

                st.session_state.editando_agora = True
                st.session_state.pagina_ativa = "➕ Nova Execução"
                st.rerun()
            st.write("")

        # BOTÃO NOVA EXECUÇÃO (Sempre visível ou muda de cor se houver pendente)
        if st.button("➕ Nova Execução", type="primary", use_container_width=True):
            navegar_para("➕ Nova Execução")
        
        st.write("") 
        
        if st.button("📋 Minhas Execuções", type="secondary", use_container_width=True):
            navegar_para("📋 Minhas Execuções")

# --- 6. TELA DE NOVA EXECUÇÃO ---
elif st.session_state.pagina_ativa == "➕ Nova Execução":
    st.title("➕ Nova Execução")
    
    # --- 1. NASCIMENTO DAS VARIÁVEIS ---
    user_nome = st.session_state.usuario['NOME']    
    setor_sel = None
    maquina_sel = None
    os_n = ""
    resp_n = user_nome
    tipo = "Operação"
    obs_final = ""
    reg = None

    # --- 2. LÓGICA DE RETOMADA (SQL JSON) ---
    dados_retomada = ler_ativo_sql(user_nome)
    
    if dados_retomada and st.session_state.editando_agora == False:
        st.warning(f"⚠️ {user_nome}, você possui um bloqueio em aberto para a máquina **{dados_retomada['EQUIP']}**.")
        c_ret1, c_ret2 = st.columns(2)
        
        if c_ret1.button("▶️ Continuar Trabalho", use_container_width=True, key="btn_retomar_sql"):
            # 1. Carrega o pacote de dados do banco
            st.session_state["os_exec"] = dados_retomada["OS"]
            st.session_state["setor_exec"] = dados_retomada["SETOR"]
            st.session_state["maq_exec"] = dados_retomada["EQUIP"]
            st.session_state["tipo_exec"] = dados_retomada["TIPO"]
            st.session_state["obs_final_exec"] = dados_retomada["OBS_GERAL"]
            st.session_state.hora_inicio_loto = dados_retomada["HORA_INICIO"]
            
            # 2. Restaura as memórias de Etapas e Comentários
            st.session_state.timestamps = dados_retomada["TIMESTAMPS"]
            st.session_state.obs_etapas = dados_retomada["OBS_ETAPAS"]
            st.session_state.na_etapas = dados_retomada["NA_ETAPAS"]
            
            # 3. O PULO DO GATO: Injeta os valores nas chaves dos widgets para eles aparecerem marcados/preenchidos
            for _, nome_it in itens_loto:
                # Marca o N/A se estava marcado
                val_na = st.session_state.na_etapas.get(f"na_{nome_it}", False)
                st.session_state[f"na_{nome_it}"] = val_na
                
                # Marca o Checkbox principal se houver um horário salvo e não for N/A
                h_salva = st.session_state.timestamps.get(f"t_{nome_it}", "N/A")
                st.session_state[f"check_{nome_it}"] = (h_salva != "N/A") or val_na
                
                # Preenche o texto dentro do balão de comentário (popover)
                st.session_state[f"input_{nome_it}"] = st.session_state.obs_etapas.get(nome_it, "")
            
            st.session_state.editando_agora = True
            st.rerun()
            
        if c_ret2.button("➕ Iniciar Novo", use_container_width=True, key="btn_novo_sql"):
            # 1. Recupera os dados que já foram lidos no topo da página
            # Não precisa de json.loads porque a função ler_ativo_sql já fez isso!
            info_at = dados_retomada

            if dados_retomada and st.session_state.editando_agora == False:
                # --- LÓGICA DE MÁQUINA FORA DE OPERAÇÃO (TELA NOVA EXECUÇÃO) ---
                concluidos_retomada = 0
                for i in range(7):
                    nome_it = itens_loto[i][1]
                    if dados_retomada.get("TIMESTAMPS", {}).get(f"t_{nome_it}") or dados_retomada.get("NA_ETAPAS", {}).get(f"na_{nome_it}"):
                        concluidos_retomada += 1
                
                if concluidos_retomada >= 7:
                    st.error(f"🚫 **ESTADO CRÍTICO:** O equipamento **{dados_retomada['EQUIP']}** está oficialmente bloqueado e fora de operação.")
                # ---------------------------------------------------------------
                
                st.warning(f"⚠️ {user_nome}, você possui um bloqueio em aberto para a máquina **{dados_retomada['EQUIP']}**.")

            # 2. Prepara os dados para o Histórico Oficial (Achatando o JSON para colunas)
            # Isso garante que a OS antiga apareça na aba "Canceladas"
            dados_p_historico = {
                "DATA": [datetime.datetime.now().strftime("%d/%m/%Y")],
                "HORA_INICIO": [info_at.get("HORA_INICIO", "N/A")],
                "HORA_FIM": [datetime.datetime.now().strftime("%H:%M:%S")],
                "OS": [info_at.get("OS", "N/A")],
                "RESP": [user_nome],
                "SETOR": [info_at.get("SETOR", "N/A")],
                "EQUIP": [info_at.get("EQUIP", "N/A")],
                "TIPO": [info_at.get("TIPO", "N/A")],
                "OBS_GERAL": ["Cancelado automaticamente para início de nova execução"],
                "STATUS": ["CANCELADO"]
            }

            # 3. Inclui os horários e notas das etapas que já haviam sido preenchidos
            for _, nome_item in itens_loto:
                u_n = nome_item.upper()
                dados_p_historico[f"HORA_{u_n}"] = [info_at.get('TIMESTAMPS', {}).get(f"t_{nome_item}", "N/A")]
                dados_p_historico[f"OBS_{u_n}"] = [info_at.get('OBS_ETAPAS', {}).get(nome_item, "")]
                dados_p_historico[f"NA_{u_n}"] = [info_at.get('NA_ETAPAS', {}).get(f"na_{nome_item}", False)]

            # 4. Grava no Histórico Oficial e deleta da tabela de Ativos
            salvar_dataframe_no_sql(pd.DataFrame(dados_p_historico), "historico_loto")
            executar_sql("DELETE FROM ativos_loto WHERE RESP = ?", (user_nome,))
            
            # 5. Limpa a memória para o novo formulário vir totalmente em branco
            chaves_limpar = ["os_exec", "obs_final_exec", "setor_exec", "maq_exec", "tipo_exec"]
            for k in chaves_limpar:
                if k in st.session_state: 
                    del st.session_state[k]
            
            st.session_state.timestamps = {}
            st.session_state.obs_etapas = {}
            st.session_state.na_etapas = {}
            st.session_state.hora_inicio_loto = None
            
            # Liga a trava para entrar no novo formulário limpo e recarrega
            st.session_state.editando_agora = True
            st.rerun()
        st.stop()

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
            
            # Só ativa a edição se escolher uma máquina real
            if maquina_sel and maquina_sel != "Selecione o equipamento":
                st.session_state.editando_agora = True
            else:
                maquina_sel = None # Mantém o Passo 2 escondido

    # --- 4. PASSO 2: IDENTIFICAÇÃO ---
    if maquina_sel:
        if st.session_state.hora_inicio_loto is None:
            st.session_state.hora_inicio_loto = datetime.datetime.now().strftime("%H:%M:%S")

        with st.container(border=True):
            st.subheader("📝 Passo 2: Identificação")
            tipo = st.radio("Serviço:", ["Operação", "Manutenção"], horizontal=True, key="tipo_exec")
            
            # --- AGORA BUSCAMOS SE EXISTE CONFLITO PARA ESTA MÁQUINA + TIPO ---
            dados_retomada = ler_ativo_sql(user_nome, maquina_sel, tipo)
            
            # Se encontrou algo e o Jorge ainda não clicou em "Continuar" (editando_agora == False)
            if dados_retomada and st.session_state.editando_agora == False:
                st.warning(f"⚠️ Já existe um bloqueio de **{tipo}** em aberto para **{maquina_sel}**.")
                
                # --- LÓGICA DE MÁQUINA FORA DE OPERAÇÃO NO CONFLITO ---
                concluidos_c = 0
                for i in range(7):
                    n_it = itens_loto[i][1]
                    if dados_retomada.get("TIMESTAMPS", {}).get(f"t_{n_it}") or dados_retomada.get("NA_ETAPAS", {}).get(f"na_{n_it}"):
                        concluidos_c += 1
                if concluidos_c >= 7:
                    st.error(f"🚨 **ALERTA:** A máquina **{maquina_sel}** está **FORA DE OPERAÇÃO**.")

                c_ret1, c_ret2 = st.columns(2)
                
                # BOTÃO 1: CONTINUAR (O que ele já estava fazendo)
                if c_ret1.button("▶️ Continuar Este Trabalho", use_container_width=True, key="btn_retomar_conflito"):
                    # Restaura a OS e Horário
                    st.session_state["os_exec"] = dados_retomada["OS"]
                    st.session_state.hora_inicio_loto = dados_retomada["HORA_INICIO"]
                    st.session_state["obs_final_exec"] = dados_retomada.get("OBS_GERAL", "")
                    
                    # Restaura as memórias técnicas
                    st.session_state.timestamps = dados_retomada["TIMESTAMPS"]
                    st.session_state.obs_etapas = dados_retomada["OBS_ETAPAS"]
                    st.session_state.na_etapas = dados_retomada["NA_ETAPAS"]
                    
                    # O PULO DO GATO: Sincroniza Checkboxes e Popovers
                    for _, nome_it in itens_loto:
                        val_na = st.session_state.na_etapas.get(f"na_{nome_it}", False)
                        st.session_state[f"na_{nome_it}"] = val_na
                        h_s = st.session_state.timestamps.get(f"t_{nome_it}", "N/A")
                        st.session_state[f"check_{nome_it}"] = (h_s != "N/A") or val_na
                        st.session_state[f"input_{nome_it}"] = st.session_state.obs_etapas.get(nome_it, "")
                    
                    st.session_state.editando_agora = True
                    st.rerun()
                
                # BOTÃO 2: INICIAR NOVO (Cancela o antigo e limpa tudo)
                if c_ret2.button("➕ Iniciar Novo (Descarta antigo)", use_container_width=True, key="btn_novo_conflito"):
                    # 1. Registra a OS antiga como CANCELADA para não perder o rastro
                    dados_c = {
                        "DATA": [datetime.datetime.now().strftime("%d/%m/%Y")],
                        "HORA_FIM": [datetime.datetime.now().strftime("%H:%M:%S")],
                        "HORA_INICIO": [dados_retomada.get('HORA_INICIO', 'N/A')],
                        "OS": [dados_retomada.get('OS', 'N/A')],
                        "RESP": [user_nome],
                        "SETOR": [setor_sel],
                        "EQUIP": [maquina_sel],
                        "TIPO": [tipo],
                        "STATUS": ["CANCELADO"],
                        "OBS_GERAL": [f"Substituído por novo bloqueio de {tipo}"],
                        "EMPRESA": [st.session_state.usuario.get('EMPRESA', '')]
                    }
                    salvar_dataframe_no_sql(pd.DataFrame(dados_c), "historico_loto")
                    
                    # 2. Deleta APENAS a chave específica deste conflito no Banco
                    chave_conflito = f"{user_nome}|{maquina_sel}|{tipo}"
                    conn.client.table("ativos_loto").delete().eq("resp", chave_conflito).execute()
                    
                    # 3. Limpa a memória para vir em branco (O que você já fazia)
                    chaves_l = ["os_exec", "obs_final_exec"] # Setor e Maq a gente mantém selecionados
                    for k in chaves_l:
                        if k in st.session_state: del st.session_state[k]
                    
                    st.session_state.timestamps = {}
                    st.session_state.obs_etapas = {}
                    st.session_state.na_etapas = {}
                    st.session_state.hora_inicio_loto = None
                    
                    st.session_state.editando_agora = True
                    st.rerun()

                st.stop() # Importante: Trava o resto da página até ele clicar num botão acima

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
                                st.session_state.timestamps[f"t_{nome}"] = datetime.datetime.now().strftime("%H:%M:%S")
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
                    "SETOR": setor_sel, "EQUIP": maquina_sel, "OS": os_n, "TIPO": tipo, "OBS_GERAL": obs_final,
                    "HORA_INICIO": st.session_state.hora_inicio_loto,
                    "TIMESTAMPS": st.session_state.timestamps,
                    "OBS_ETAPAS": st.session_state.obs_etapas,
                    "NA_ETAPAS": st.session_state.na_etapas
                }
                salvar_ativo_sql(resp_n, estado_atual)
                
                # 6. BOTÕES FINAIS ALINHADOS
                if all(status_etapas):
                    st.success("✅ Protocolo completo!")

                # --- PASSO 3: EVIDÊNCIA FOTOGRÁFICA ---
                st.markdown("---")
                st.subheader("📸 Evidência de Bloqueio")
                st.caption("Opcional: Capture uma foto dos cadeados e etiquetas.")

                foto = st.camera_input("Capturar Evidência", label_visibility="collapsed")

                if foto:
                    st.success("✅ Foto pronta para registro!")

                st.write("---")
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    if all(status_etapas):
                        if st.button("🏁 Finalizar e Registrar", type="primary", use_container_width=True, key="btn_finalizar_unico"):
                            nome_foto_db = None
                            
                            # 1. Tenta salvar a foto no Supabase Storage
                            if foto:
                                try:
                                    # Gera o nome do arquivo usando a variável os_n
                                    agora_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                                    nome_arquivo = f"{os_n}_{agora_str}.jpg"
                                    
                                    # Upload para o bucket 'evidencias'
                                    conn.client.storage.from_("evidencias").upload(
                                        path=nome_arquivo,
                                        file=foto.getvalue(),
                                        file_options={"content-type": "image/jpeg"}
                                    )
                                    nome_foto_db = nome_arquivo
                                except Exception as e:
                                    # Se a Policy falhar, o erro aparecerá aqui
                                    st.warning(f"Atenção: A foto não pôde ser salva, mas o registro continuará. ({e})")

                            # 2. Prepara dados para o Histórico (Sua lógica original de colunas MAIÚSCULAS)
                            dados_h = {
                                "DATA": [datetime.datetime.now().strftime("%d/%m/%Y")],
                                "HORA_FIM": [datetime.datetime.now().strftime("%H:%M:%S")],
                                "HORA_INICIO": [st.session_state.get('hora_inicio_loto', 'N/A')],
                                "OS": [os_n],
                                "RESP": [resp_n],
                                "EMPRESA": [st.session_state.usuario.get('EMPRESA', '')],
                                "SETOR": [setor_sel],
                                "EQUIP": [maquina_sel],
                                "TIPO": [tipo],
                                "OBS_GERAL": [f"{obs_final} | Foto: {nome_foto_db}" if nome_foto_db else obs_final],
                                "STATUS": ["CONCLUÍDO"]
                            
                            }
                            # Inclui horários e notas das etapas
                            for _, n_it in itens_loto:
                                dados_h[f"HORA_{n_it.upper()}"] = [st.session_state.timestamps.get(f"t_{n_it}", "N/A")]
                                dados_h[f"OBS_{n_it.upper()}"] = [st.session_state.obs_etapas.get(n_it, "")]
                                dados_h[f"NA_{n_it.upper()}"] = [st.session_state.na_etapas.get(f"na_{n_it}", False)]
                            
                            # 3. Salva no Banco e DELETA dos Ativos (Limpeza imediata)
                            if salvar_dataframe_no_sql(pd.DataFrame(dados_h), "historico_loto"):
                                # Deleta apenas a chave composta específica deste trabalho
                                chave_especifica = f"{resp_n}|{maquina_sel}|{tipo}"
                                conn.client.table("ativos_loto").delete().eq("resp", chave_especifica).execute()
                                
                                # Limpeza da Memória do App para a próxima OS
                                st.session_state.editando_agora = False
                                st.session_state.timestamps = {}
                                st.session_state.obs_etapas = {}
                                st.session_state.na_etapas = {}
                                st.session_state.hora_inicio_loto = None
                                for c in ["os_exec", "obs_final_exec", "setor_exec", "maq_exec", "tipo_exec"]:
                                    if c in st.session_state: del st.session_state[c]
                                
                                st.toast("✅ Bloqueio finalizado e registrado!")
                                time.sleep(1)
                                navegar_para("📋 Minhas Execuções")
                    else:
                        st.info("💡 Conclua as 10 etapas do checklist para finalizar.")

                with col_f2:
                    # BOTÃO CANCELAR COM KEY ÚNICA
                    if st.button("❌ Cancelar Registro", use_container_width=True, key="btn_cancelar_unico"):
                        agora_c = datetime.datetime.now()
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
                            navegar_para("📋 Minhas Execuções")


# --- 7. HISTÓRICO E DETALHAMENTO ---
elif st.session_state.pagina_ativa == "📋 Minhas Execuções":

    # --- RESET DE SCROLL "TRIPLE-CROWN" (Força o topo em qualquer navegador) ---
    st.components.v1.html(
        f"""
        <div style="display:none">{datetime.datetime.now().timestamp()}</div>
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
            if user_atual['PERFIL'] == 'Admin Cliente':
                # FILTRO AQUI TAMBÉM:
                emp_alvo = str(user_atual.get('EMPRESA', '')).strip()
                df_hist = df_hist[df_hist['EMPRESA'].astype(str).str.strip() == emp_alvo]
            elif user_atual['PERFIL'] == 'Operador':
                df_hist = df_hist[df_hist['RESP'] == user_atual['NOME']]

        # --- FUNÇÃO INTERNA: DESENHA O CARD ---
        def renderizar_card_na_lista(indice, dados_linha, aba):
            # Mudamos de 'Status' para 'STATUS'
            classe_status = "hist-status" if dados_linha['STATUS'] == "CONCLUÍDO" else "hist-status-cancel"
            texto_status = "● Concluído" if dados_linha['STATUS'] == "CONCLUÍDO" else "● Cancelado"
            cor_borda = "#FF6B00" if dados_linha['STATUS'] == "CONCLUÍDO" else "#9B1C1C"
            
            # Mudamos de 'Resp' para 'RESP'
            info_extra = f" | 👤 {dados_linha['RESP']}" if user_atual['PERFIL'] == 'Admin' else ""

            st.markdown(f"""
                <div class="hist-card" style="border-left-color: {cor_borda};">
                    <div style="display: flex; justify-content: space-between;">
                        <span class="hist-os">OS: {dados_linha['OS']}</span>
                        <span class="{classe_status}">{texto_status}</span>
                    </div>
                    <div class="hist-sub">{dados_linha['SETOR']} • {dados_linha['EQUIP']}</div>
                    <div class="hist-sub">🕒 {dados_linha['DATA']}{info_extra}</div>
                </div>
            """, unsafe_allow_html=True)
            
            chave_botao = f"btn_det_{aba}_{dados_linha['OS']}_{indice}"
            if st.button(f"🔎 Detalhes da OS {dados_linha['OS']}", key=chave_botao):
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
            st.title("📋 Todas as Execuções" if user_atual['PERFIL'] == 'Admin' else "📋 Minhas Execuções")
            
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
                    if user_atual['PERFIL'] == 'Admin':
                        emps = ["Todas"] + sorted([str(x) for x in df_hist['EMPRESA'].unique() if x])
                        st.selectbox("Empresa", emps, key="f_empresa")
                    
                with c2:
                    setores = ["Todos"] + sorted(list(df_hist['SETOR'].unique()))
                    st.selectbox("Setor", setores, key="f_setor")
                    maqs = ["Todas"] + sorted(list(df_hist['EQUIP'].unique()))
                    st.selectbox("Equipamento", maqs, key="f_maq")
                
                with c3:
                    # Filtro de Data para o Download/Lista
                    hoje = datetime.date.today()
                    st.date_input("Data Início", hoje.replace(day=1), key="f_data_de")
                    st.date_input("Data Fim", hoje, key="f_data_ate")
                    if user_atual['PERFIL'] == 'Admin':
                        resps = ["Todos"] + sorted(list(df_hist['RESP'].unique()))
                        st.selectbox("Responsável", resps, key="f_resp")

            # --- APLICAÇÃO DOS FILTROS NO DATAFRAME ---
            df_filtrado = df_hist.copy()
            
            # Filtro de Data Primeiro
            df_filtrado = filtrar_por_periodo(df_filtrado, st.session_state.f_data_de, st.session_state.f_data_ate)

            if st.session_state.f_os:
                df_filtrado = df_filtrado[df_filtrado['OS'].astype(str).str.contains(st.session_state.f_os)]
            
            # Filtro de Empresa (Admin)
            if user_atual['PERFIL'] == 'Admin' and st.session_state.get('f_empresa', 'Todas') != "Todas":
                df_filtrado = df_filtrado[df_filtrado['EMPRESA'] == st.session_state.f_empresa]

            if st.session_state.get('f_resp', 'Todos') != "Todos":
                df_filtrado = df_filtrado[df_filtrado['RESP'] == st.session_state.f_resp]
            
            if st.session_state.f_setor != "Todos":
                # AJUSTE AQUI: 'SETOR'
                df_filtrado = df_filtrado[df_filtrado['SETOR'] == st.session_state.f_setor]
                
            if st.session_state.f_maq != "Todas":
                # AJUSTE AQUI: 'EQUIP'
                df_filtrado = df_filtrado[df_filtrado['EQUIP'] == st.session_state.f_maq]
            
            df_filtrado = df_filtrado.reset_index(drop=True)

            # --- BLOCO DE DOWNLOAD (EXCEL) ---
            if not df_filtrado.empty:
                st.write("---")
                c_down_info, c_down_btn = st.columns([3, 1])
                
                with c_down_info:
                    st.markdown(f"📊 **Relatório Gerado:** {len(df_filtrado)} registros encontrados.")
                    st.caption("O download incluirá a duração total de cada bloqueio.")

                with c_down_btn:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_excel = df_filtrado.copy()
                        
                        # --- CÁLCULO DE DURAÇÃO PARA O EXCEL ---
                        def calcular_intervalo(row):
                            try:
                                # Pegamos os horários limpando espaços e tratando possíveis erros
                                h_ini = str(row.get('HORA_INICIO', '')).strip()
                                h_fim = str(row.get('HORA_FIM', '')).strip()
                                
                                if h_ini and h_fim and h_ini != 'nan' and h_fim != 'nan':
                                    t1 = datetime.datetime.strptime(h_ini, "%H:%M:%S")
                                    t2 = datetime.datetime.strptime(h_fim, "%H:%M:%S")
                                    # Retorna a diferença formatada (HH:MM:SS)
                                    return str(t2 - t1)
                                return "---"
                            except:
                                return "Erro"

                        # Adiciona a nova coluna ao DataFrame que vai para o Excel
                        df_excel['DURACAO_TOTAL'] = df_excel.apply(calcular_intervalo, axis=1)
                        # --------------------------------------

                        # Ordena para que os mais recentes fiquem no topo
                        if 'DATA' in df_excel.columns:
                            df_excel = df_excel.sort_values(by=['DATA'], ascending=False)
                            
                        df_excel.to_excel(writer, index=False, sheet_name='Relatório LOTO')
                    
                    st.download_button(
                        label="📥 Baixar em Excel",
                        data=buffer.getvalue(),
                        file_name=f"Relatorio_LOTO_{datetime.datetime.now().strftime('%d_%m_%Y')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            # --- FIM DO BLOCO DE DOWNLOAD ---
            
            # 1. CONFIGURAÇÃO DA PAGINAÇÃO
            itens_por_pagina = 4
            df_hist_inv = df_filtrado.iloc[::-1]  # <--- Deve ser df_filtrado
            total_itens = len(df_hist_inv)
            total_paginas = (total_itens // itens_por_pagina) + (1 if total_itens % itens_por_pagina > 0 else 0)

            # 2. SELETOR DE PÁGINA (Aparece no topo se houver mais de 1 página)
            if total_paginas > 1:
                col_pag1, col_pag2, col_pag3 = st.columns([1, 1, 1])
                with col_pag2:
                    pagina_sel = st.number_input(f"Página (1 de {total_paginas})", min_value=1, max_value=total_paginas, step=1, key="selector_paginacao_historico")
                
            else:
                pagina_sel = 1

            # 3. FILTRA OS DADOS DA PÁGINA ATUAL
            inicio = (pagina_sel - 1) * itens_por_pagina
            fim = inicio + itens_por_pagina
            df_pagina_atual = df_hist_inv.iloc[inicio:fim]

            # 4. DESENHA AS ABAS
            tab_todas, tab_ativas, tab_concluidas, tab_canceladas = st.tabs(["Todas", "Ativas", "Concluídas", "Canceladas"])
            
            with tab_todas:
                # Aba TODAS: Mostra apenas o histórico finalizado (Concluídos e Cancelados)
                if df_hist.empty: 
                    st.info("Nenhum registro finalizado.")
                else:
                    for i, row in df_pagina_atual.iterrows():
                        renderizar_card_na_lista(i, row, "todas")

            with tab_ativas:
                # Agora lemos a tabela que contém o JSON
                df_andamento = ler_sql("SELECT * FROM ativos_loto")
                
                if not df_andamento.empty:
                    # Filtro de usuário: Operador vê apenas o dele, Admin vê todos
                    if user_atual['PERFIL'] != 'Admin':
                        df_andamento = df_andamento[df_andamento['RESP'] == user_atual['NOME']]
                    
                    if df_andamento.empty:
                        st.info("Nenhuma execução sua em andamento.")
                    else:
                        import json
                        for i, row in df_andamento.iterrows():
                            # O SEGREDO: Abrimos o JSON para pegar os dados do card
                            dados_corpo = row['DADOS_JSON']

                            if isinstance(dados_corpo, str):
                                import json
                                dados_corpo = json.loads(dados_corpo)
                            
                            st.markdown(f"""
                                <div class="hist-card" style="border-left-color: #3B82F6;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span class="hist-os">OS: {dados_corpo['OS']}</span>
                                        <span style="background-color: #DBEAFE; color: #1E40AF; padding: 2px 10px; border-radius: 15px; font-size: 0.8rem; font-weight: bold;">● Em Execução</span>
                                    </div>
                                    <div class="hist-sub">{dados_corpo['SETOR']} • {dados_corpo['EQUIP']}</div>
                                    <div class="hist-sub">🕒 Iniciado em: {dados_corpo['HORA_INICIO']} | 👤 {row['RESP']}</div>
                                </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("Não há execuções em aberto no pátio.")
            
            with tab_concluidas:
                df_conc = df_filtrado[df_filtrado['STATUS'] == "CONCLUÍDO"].iloc[::-1]
                if df_conc.empty: st.info("Nenhuma execução concluída.")
                else:
                    for i, row in df_conc.iterrows():
                        renderizar_card_na_lista(i, row, "conc")

            with tab_canceladas:
                df_canc = df_filtrado[df_filtrado['STATUS'] == "CANCELADO"].iloc[::-1]
                if df_canc.empty: st.info("Nenhuma execução cancelada.")
                else:
                    for i, row in df_canc.iterrows():
                        renderizar_card_na_lista(i, row, "canc_aba")
            
            # Botão de Nova Execução rápido no rodapé
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
            st.selectbox("Área de Atuação *", ["Manutenção", "Operação"], 
                         index=0 if user['AREA'] == "Manutenção" else 1)
            
            if st.button("Sair da Conta"):
                st.session_state.autenticado = False
                st.rerun()

# Perfil Adm
elif st.session_state.pagina_ativa == "⚙️ Painel Admin":
    user_p = st.session_state.usuario
    

    if user_p['PERFIL'] in ['Admin', 'Admin Cliente']:
        nome_empresa = user_p.get('EMPRESA') if user_p.get('EMPRESA') else "Geral"
        st.title(f"⚙️ Gestão Administrativa - {nome_empresa}")

        # 1. Lógica de Notificações
        df_s_contagem = ler_sql("SELECT STATUS FROM solicitacoes WHERE STATUS = 'Pendente'")
        qtd_pendente = len(df_s_contagem) if not df_s_contagem.empty else 0
        label_solicitacoes = f"🔑 Solicitações ({qtd_pendente}) 🔴" if qtd_pendente > 0 else "🔑 Solicitações"

        # 2. CRIAÇÃO DAS ABAS BASEADO NO PERFIL
        if user_p['PERFIL'] == 'Admin':
            # Admin Geral vê tudo
            tabs = st.tabs(["➕ Novo Usuário", "📝 Editar Usuário", "🛠️ Equipamentos", label_solicitacoes, "📁 Arquivos/Fotos"])
            tab_cadastro, tab_gerenciamento, tab_equipamentos, tab_senha, tab_arquivos = tabs
        else:
            # Admin Cliente vê apenas duas
            tabs = st.tabs(["📁 Arquivos/Fotos", label_solicitacoes])
            tab_arquivos, tab_senha = tabs

        # --- ABA: CADASTRO (Apenas Admin) ---
        if user_p['PERFIL'] == 'Admin':
            with tab_cadastro:
                if user_p['PERFIL'] == 'Admin': # Proteção extra
                    st.subheader("Dados do Novo Colaborador")
                    
                    # --- 1. FUNÇÕES DE CALLBACK (RODAM ANTES DOS COMPONENTES) ---
                    
                    # Função para sugerir senha
                    def sugerir_senha_callback():
                        st.session_state["reg_senha"] = sugerir_senha_forte()

                    # Função principal para Salvar e Limpar os campos
                    def finalizar_cadastro_callback():
                        # Coleta os dados das gavetas (keys)
                        nome = st.session_state.get("reg_nome", "")
                        email = st.session_state.get("reg_email", "").strip()
                        senha = st.session_state.get("reg_senha", "")
                        area = st.session_state.get("reg_area", "Manutenção")
                        perfil = st.session_state.get("reg_perfil", "Operador")
                        empresa = st.session_state.get("reg_empresa", "") # Pega do widget

                        if nome and email and senha and empresa:
                            check_user = ler_sql("SELECT EMAIL FROM usuarios WHERE EMAIL = ?", (email,))
                            if not check_user.empty:
                                st.session_state["msg_feedback"] = ("erro", f"❌ O e-mail '{email}' já está cadastrado.")
                            else:
                                # QUERY ÚNICA com a coluna EMPRESA
                                query = "INSERT INTO usuarios (EMAIL, SENHA, NOME, AREA, PERFIL, ATIVO, EMPRESA) VALUES (?, ?, ?, ?, ?, ?, ?)"
                                executar_sql(query, (email, senha, nome, area, perfil, 'Sim', empresa))
                                
                                st.session_state["reg_nome"] = ""
                                st.session_state["reg_email"] = ""
                                st.session_state["reg_senha"] = ""
                                st.session_state["reg_empresa"] = ""
                                st.session_state["msg_feedback"] = ("sucesso", f"✔️ Usuário {nome} cadastrado com sucesso!")
                        else:
                            st.session_state["msg_feedback"] = ("aviso", "⚠️ Preencha todos os campos, incluindo a Empresa.")

                    # --- 2. DESENHO DA INTERFACE ---
                    with st.container(border=True):
                        st.text_input("Nome Completo", key="reg_nome")
                        st.text_input("E-mail (Login)", key="reg_email")
                        st.text_input("Empresa", key="reg_empresa", placeholder="Ex: System Service")
                        
                        col_senha, col_botao = st.columns([4, 1])
                        with col_senha:
                            st.text_input("Senha Inicial *", key="reg_senha")
                        with col_botao:
                            st.write("##")
                            st.button("🎲 Sugerir", on_click=sugerir_senha_callback, use_container_width=True)

                        c1, c2 = st.columns(2)
                        c1.selectbox("Área", ["Manutenção", "Operação"], key="reg_area")
                        c2.selectbox("Perfil", ["Operador", "Admin", "Admin Cliente"], key="reg_perfil")
                        
                        st.write("---")
                        st.button("✅ Finalizar Cadastro", type="primary", on_click=finalizar_cadastro_callback, use_container_width=True)

                    # --- 3. EXIBIÇÃO DE MENSAGENS (FEEDBACK) ---
                    if "msg_feedback" in st.session_state:
                        tipo, texto = st.session_state.pop("msg_feedback")
                        if tipo == "sucesso":
                            st.success(texto)
                        elif tipo == "erro":
                            st.error(texto)
                        else:
                            st.warning(texto)

            with tab_gerenciamento:
                # --- LEITURA VIA SQL ---
                df_u = ler_sql("SELECT * FROM usuarios")
                
                st.write("### Pesquisar e Editar Colaborador")
                
                if not df_u.empty:
                    # O ler_sql garante colunas em MAIÚSCULO: NOME, EMAIL, AREA...
                    lista_nomes = [f"{row['NOME']} ({row['EMAIL']})" for _, row in df_u.iterrows()]
                    selecao = st.selectbox("Selecione o usuário para alterar:", [""] + lista_nomes)
                    
                    if selecao:
                        email_sel = selecao.split("(")[-1].replace(")", "").strip()
                        dados_u = df_u[df_u['EMAIL'] == email_sel].iloc[0]
                        
                        with st.container(border=True):
                            c_ed1, c_ed2 = st.columns(2)
                            novo_nome = c_ed1.text_input("Nome", value=str(dados_u['NOME']))
                            novo_status = c_ed2.selectbox("Acesso Ativo?", ["Sim", "Não"], 
                                                        index=0 if str(dados_u['ATIVO']) == "Sim" else 1)
                            
                            nova_area = c_ed1.selectbox("Área de Atuação", ["Manutenção", "Operação"],
                                                    index=0 if str(dados_u['AREA']) == "Manutenção" else 1)
                            
                            # AJUSTE 1: Adicionado "Admin Cliente" às opções
                            novo_perfil = c_ed2.selectbox("Nível de Acesso", ["Operador", "Admin", "Admin Cliente"],
                                                        index=["Operador", "Admin", "Admin Cliente"].index(str(dados_u['PERFIL'])))
                            
                            # AJUSTE 2: Campo para editar a Empresa (Para evitar o 'None' no futuro)
                            nova_empresa_edit = st.text_input("Empresa", value=str(dados_u.get('EMPRESA', '')))
                            
                            nova_senha = st.text_input("Resetar Senha (deixe em branco para manter a atual)", type="password")

                            if st.button("💾 Aplicar Alterações", type="primary", use_container_width=True):
                                # AJUSTE 3: Query agora inclui EMPRESA = ?
                                query_update = """
                                    UPDATE usuarios 
                                    SET NOME = ?, ATIVO = ?, AREA = ?, PERFIL = ?, EMPRESA = ?
                                    WHERE EMAIL = ?
                                """
                                
                                # AJUSTE 4: Passando os 6 parâmetros na ordem da query acima
                                executar_sql(query_update, (novo_nome, novo_status, nova_area, novo_perfil, nova_empresa_edit, email_sel))
                                
                                if nova_senha:
                                    executar_sql("UPDATE usuarios SET SENHA = ? WHERE EMAIL = ?", (nova_senha, email_sel))
                                
                                st.success(f"✅ O perfil de {novo_nome} foi atualizado!")
                                st.rerun()

                            # --- ÁREA DE EXCLUSÃO (PERIGOSA) ---
                            st.write("##")
                            with st.expander("⚠️ Zona de Perigo - Remover Usuário"):
                                st.write(f"Você tem certeza que deseja excluir permanentemente o acesso de **{novo_nome}**?")
                                confirmar_exclusao = st.checkbox("Eu entendo que esta ação é irreversível e apagará o usuário do banco de dados.")
                                
                                if st.button("🗑️ Confirmar Exclusão Definitiva", type="secondary", disabled=not confirmar_exclusao):
                                    # --- REMOÇÃO VIA SQL ---
                                    executar_sql("DELETE FROM usuarios WHERE EMAIL = ?", (email_sel,))
                                    
                                    st.error(f"O usuário {email_sel} foi removido com sucesso.")
                                    st.rerun()
                else:
                    st.info("Não há usuários cadastrados no banco de dados.")
                
            with tab_equipamentos:
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

        # --- ABAS COMUNS (Admin e Admin Cliente) ---
        with tab_senha:
            st.write("### Pedidos de Recuperação")
            
            # --- LEITURA VIA SQL ---
            # Buscamos apenas os pedidos que ainda estão pendentes
            df_pendente = ler_sql("SELECT * FROM solicitacoes WHERE STATUS = 'Pendente'")
            
            if not df_pendente.empty:
                st.warning(f"Existem {len(df_pendente)} solicitações aguardando revisão.")
                
                # Exibe a tabela (O ler_sql já garante cabeçalhos em MAIÚSCULO)
                st.dataframe(df_pendente, use_container_width=True, hide_index=True)
                
                if st.button("Marcar todas como Lidas/Resolvidas", type="secondary", use_container_width=True):
                    # --- ATUALIZAÇÃO VIA SQL ---
                    # Muda o status de TODOS que estiverem pendentes para 'Resolvido'
                    executar_sql("UPDATE solicitacoes SET STATUS = 'Resolvido' WHERE STATUS = 'Pendente'")
                    
                    st.success("✅ Todas as solicitações foram marcadas como resolvidas!")
                    st.rerun()
            else:
                st.success("Nenhuma solicitação de senha pendente no momento.")

        with tab_arquivos:
            st.subheader("📁 Gerenciador de Evidências")
            
            # --- ÁREA DE FILTROS ---
            c_f1, c_f2 = st.columns([2, 1])
            busca_arq = c_f1.text_input("🔍 Buscar por OS ou Nome do Arquivo", placeholder="Ex: OS-2026-001")
            ordem_arq = c_f2.selectbox("Ordenar por:", ["Mais recentes", "Mais antigos", "Nome (A-Z)"])

            # 1. Busca a lista bruta do Supabase
            try:
                lista_bruta = conn.client.storage.from_("evidencias").list()
                
                # --- NOVO FILTRO DE PRIVACIDADE PARA ADMIN CLIENTE ---
                if user_p['PERFIL'] == 'Admin Cliente':
                    empresa_logada = user_p.get('EMPRESA', '')
                    # Pegamos o histórico apenas da empresa dele para saber quais fotos ele pode ver
                    df_hist_privacidade = ler_sql(f"SELECT OBS_GERAL FROM historico_loto WHERE EMPRESA = '{empresa_logada}'")
                    
                    fotos_permitidas = []
                    if not df_hist_privacidade.empty:
                        for obs in df_hist_privacidade['OBS_GERAL'].dropna():
                            if "Foto: " in str(obs):
                                # Extrai o nome do arquivo que salvamos após o texto "Foto: "
                                nome_foto = str(obs).split("Foto: ")[-1].strip()
                                fotos_permitidas.append(nome_foto)
                    
                    # Filtra a lista do storage: só entra o que estiver na lista de permitidas da empresa
                    lista_bruta = [a for a in lista_bruta if a['name'] in fotos_permitidas]
                # ----------------------------------------------------

                if not lista_bruta:
                    st.info("Nenhum arquivo encontrado ou acesso restrito.")
                else:
                    # 2. APLICAÇÃO DOS FILTROS EM PYTHON
                    # Filtro de Texto (Busca)
                    arquivos_filtrados = [
                        a for a in lista_bruta 
                        if busca_arq.lower() in a['name'].lower()
                    ]

                    # Ordenação
                    if ordem_arq == "Mais recentes":
                        arquivos_filtrados.sort(key=lambda x: x['created_at'], reverse=True)
                    elif ordem_arq == "Mais antigos":
                        arquivos_filtrados.sort(key=lambda x: x['created_at'])
                    else: # Nome A-Z
                        arquivos_filtrados.sort(key=lambda x: x['name'])

                    # Exibição do contador
                    st.caption(f"Exibindo {len(arquivos_filtrados)} de {len(lista_bruta)} arquivos")

                    if not arquivos_filtrados:
                        st.warning("Nenhum arquivo corresponde à sua busca.")
                    else:
                        # 3. GRID DE EXIBIÇÃO
                        cols = st.columns(4) # 4 colunas para fotos menores e mais organizadas
                        for idx, arq in enumerate(arquivos_filtrados):
                            nome_arq = arq['name']
                            with cols[idx % 4]:
                                with st.container(border=True):
                                    url = conn.client.storage.from_("evidencias").get_public_url(nome_arq)
                                    
                                    # Preview da Imagem
                                    if nome_arq.lower().endswith(('.png', '.jpg', '.jpeg')):
                                        st.image(url, use_container_width=True)
                                    else:
                                        st.write("📄 Arquivo")
                                    
                                    # Detalhes legíveis
                                    st.markdown(f"**{nome_arq[:20]}...**" if len(nome_arq) > 20 else f"**{nome_arq}**")
                                    
                                    # Formata data para padrão brasileiro
                                    data_criacao = arq['created_at'][:10] # YYYY-MM-DD
                                    ano, mes, dia = data_criacao.split('-')
                                    st.caption(f"📅 {dia}/{mes}/{ano}")

                                    # Ações
                                    c_down, c_del = st.columns([3, 1])
                                    c_down.link_button("💾 Baixar", url, use_container_width=True)
                                    
                                    # Botão deletar com chave única
                                    if c_del.button("🗑️", key=f"del_v2_{nome_arq}"):
                                        conn.client.storage.from_("evidencias").remove([nome_arq])
                                        st.toast(f"Removido: {nome_arq}")
                                        time.sleep(1)
                                        st.rerun()
            except Exception as e:
                st.error(f"Erro ao listar arquivos: {e}")

    else:
        st.error("Acesso restrito a administradores.")
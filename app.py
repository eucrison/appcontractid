import streamlit as st
import pandas as pd
import io
import re

# 1. Configuração da Página e Injeção de CSS para Tema Claro e Estilização
st.set_page_config(
    page_title="Limpeza e Formatação de Contract IDs para SQL",
    layout="wide" 
)

# CSS para forçar tema claro, background dos inputs e estilos dos botões
st.markdown(
    """
    <style>
    /* Fundo branco e texto preto (Global) */
    .stApp {
        background-color: white;
        color: black;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp label, .stApp p {
        color: black;
    }
    
    /* Estilo para Fundo dos Inputs/Outputs (#F5F5F5) e remoção de bordas */
    /* Targetando o container do st.text_area e o campo textarea real */
    div.stTextArea > div {
        background-color: #F5F5F5;
        border: none;
        border-radius: 0.5rem;
        padding: 10px;
    }
    textarea {
        background-color: #F5F5F5 !important;
        border: none !important;
        color: black;
    }
    
    /* Targetando o bloco de código (output) para #F5F5F5 e sem borda */
    .stCode {
        background-color: #F5F5F5 !important;
        border: none;
        padding: 10px;
        border-radius: 0.5rem;
        /* Usado para alinhar verticalmente com o st.text_area */
        height: 300px !important; 
    }
    .stCode > pre {
        background-color: #F5F5F5 !important;
        padding: 0;
        height: 100%;
        overflow-y: auto;
        white-space: pre-wrap; /* Permite que o texto quebre linha no bloco de código */
    }
    
    /* Estilização do Botão Nativo Streamlit (Processar) */
    .stButton > button {
        background-color: #FFFFFF !important;
        border: 2px solid #d80073 !important;
        color: #d80073 !important;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
        border-radius: 0.2rem;
    }
    
    /* Estilo Hover para Botão Nativo */
    .stButton > button:hover {
        background-color: #d80073 !important;
        border-color: #d80073 !important;
        color: #F5F5F5 !important;
    }
    
    /* Classe para o Botão Copiar Injetado (aplicamos o hover via CSS) */
    .copy-button {
        background-color: #F5F5F5;
        border: 2px solid #d80073;
        color: #d80073;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
        padding: 0.5rem 1rem; 
        border-radius: 0.5rem; 
        cursor: pointer; 
        width: 100%; 
        margin-top: 10px;
    }
    .copy-button:hover {
        background-color: #d80073;
        border: 2px solid #d80073; /* Mantido para não mudar o tamanho */
        color: #F5F5F5;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.title("Limpeza de Contract IDs para SQL")
st.markdown("---")

st.markdown("""
**Instrução:** Use o painel à esquerda para colar seus dados e o painel à direita para ver o resultado formatado.
O aplicativo irá:
1. Remover qualquer caractere que não seja um dígito (mantendo apenas números).
2. Remover duplicatas.
3. Formatar o resultado em uma única linha separada por vírgulas e aspas simples
ex: (`'ID1', 'ID2', ...`), pronta para ser usada em cláusulas `IN` de consultas SQL.
""")


# Função de processamento (usando st.cache_data para performance)
@st.cache_data
def process_contract_ids(raw_input_text):
    """
    Recebe uma string de texto, limpa e extrai os IDs de contrato, mantendo apenas dígitos.
    """
    if not raw_input_text:
        return pd.DataFrame()

    # 1. Pré-processamento para extrair apenas números
    # Substitui qualquer caractere que não seja dígito (\D) por uma vírgula (,)
    text_processed = re.sub(r'\D+', ',', raw_input_text)
    
    # Divide o texto pela vírgula, removendo entradas vazias
    list_of_ids = [item.strip() for item in text_processed.split(',') if item.strip()]

    if not list_of_ids:
        return pd.DataFrame()

    # 2. Criação da Série Pandas
    df_split = pd.Series(list_of_ids)

    # 3. Limpeza Final e Coerção
    df_split = df_split[df_split != '']
    df_split = df_split[df_split.str.lower() != 'nan']
    df_split = df_split.astype(str).str.replace(r'\.0$', '', regex=True)
    
    try:
        df_numeric = pd.to_numeric(df_split, errors='coerce')
        df_split = df_numeric.astype('Int64')
    except:
        pass 

    df_split = df_split.dropna()
    
    result_df = pd.DataFrame(df_split.rename('Contract ID Limpo'))
    result_df = result_df.drop_duplicates().reset_index(drop=True)

    return result_df

# --- Interface do Aplicativo ---

# Criação de duas colunas para dispor os campos lado a lado
col_input, col_output = st.columns(2)

# Inicializa o estado da sessão
if 'show_output' not in st.session_state:
    st.session_state.show_output = False
    st.session_state.saida_formatada = ""
    st.session_state.total_ids = 0

with col_input:
    # Campo para colar a lista de contratos (300px)
    raw_text_input = st.text_area(
        "1. Cole a lista de Contract IDs aqui:",
        height=300,
        placeholder="Exemplo:\nID: 12345678 (Este texto será removido)\n90123456, 78901234 56789012"
    )

    # Botão de processamento nativo Streamlit
    if st.button('Processar e Formatar IDs', use_container_width=True):
        if not raw_text_input:
            st.warning("Por favor, cole os IDs de contrato antes de processar.")
            st.session_state.show_output = False
        else:
            with st.spinner('Processando...'):
                processed_df = process_contract_ids(raw_text_input)
                
                if not processed_df.empty:
                    # 2. Formatação SQL
                    numeros = processed_df['Contract ID Limpo'].astype(str).tolist()
                    saida = ",".join([f"'{n}'" for n in numeros])
    
                    st.session_state.saida_formatada = saida
                    st.session_state.total_ids = len(numeros)
                    st.session_state.show_output = True
                else:
                    st.session_state.show_output = False
                    st.session_state.saida_formatada = "Nenhum ID válido encontrado."
                    st.warning("Nenhum 'Contract ID' válido foi encontrado na entrada fornecida.")

with col_output:
    
    # Título da Saída
    st.subheader("2. Saída Formatada (Cláusula IN)")
    
    if st.session_state.show_output and st.session_state.saida_formatada:
        saida = st.session_state.saida_formatada
        total_ids = st.session_state.total_ids
        
        st.info(f"Total de **{total_ids}** IDs únicos encontrados e formatados.")

        # Exibe o resultado formatado no bloco de código (300px)
        st.code(saida, language="sql", height=300)
        
        # Botão Copiar Injetado (usa a classe copy-button definida no CSS)
        # O JS usa navigator.clipboard.writeText e fornece feedback visual na própria UI
        
        js_saida = saida.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        
        copy_button_html = f"""
        <button 
            class="copy-button"
            onclick="navigator.clipboard.writeText('{js_saida}'); 
                     var btn = event.target; 
                     var originalText = btn.innerHTML;
                     btn.innerHTML = '✅ Lista Copiada!'; 
                     setTimeout(() => {{ btn.innerHTML = originalText; }}, 2000);"
        >
            📋 Copiar Lista Formatada
        </button>
        """
        st.markdown(copy_button_html, unsafe_allow_html=True)
        
    else:
        # Placeholder quando o aplicativo é carregado ou após um erro (300px)
        st.code("Aguardando colagem e processamento dos dados...", language="sql", height=300)
        # Placeholder para o botão copiado
        st.markdown('<div class="copy-button" style="text-align: center; cursor: default;">📋 Copiar Lista Formatada</div>', unsafe_allow_html=True)



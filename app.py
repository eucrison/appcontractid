import streamlit as st
import pandas as pd
import io
import re

# 1. Configuração da Página e Injeção de CSS para Tema Claro
st.set_page_config(
    page_title="Limpeza e Formatação de Contract IDs para SQL",
    layout="wide" # Usando layout wide para melhor visualização lado a lado
)

# CSS para forçar fundo branco, texto preto e remover borda de inputs (melhor estética)
st.markdown(
    """
    <style>
    /* 3. Estilo: Altera o fundo e a cor da fonte */
    .stApp {
        background-color: white;
        color: black;
    }
    .stApp > header {
        background-color: white;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp label, .stApp p, .stApp a {
        color: black;
    }
    /* Estilo do bloco de código para fundo branco */
    .stCode {
        background-color: #F8F9FA !important; 
        border: 1px solid #DEE2E6;
        color: #333333;
    }
    
    /* Remove a borda padrão do text_area para um visual mais limpo */
    textarea {
        border: 1px solid #ced4da;
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

    # O spinner agora é gerenciado pelo botão de processamento
    
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

    # Converte para string e remove o '.0'
    df_split = df_split.astype(str).str.replace(r'\.0$', '', regex=True)
    
    # Tenta converter para numérico para garantir a validade
    try:
        df_numeric = pd.to_numeric(df_split, errors='coerce')
        df_split = df_numeric.astype('Int64')
    except:
        pass 

    # Remove linhas que resultaram em <NA> (nulo)
    df_split = df_split.dropna()
    
    # Cria o DataFrame final, remove duplicatas e reseta o índice
    result_df = pd.DataFrame(df_split.rename('Contract ID Limpo'))
    result_df = result_df.drop_duplicates().reset_index(drop=True)

    return result_df

# --- Interface do Aplicativo ---

# Criação de duas colunas para dispor os campos lado a lado
col_input, col_output = st.columns(2)

with col_input:
    # Campo para colar a lista de contratos
    raw_text_input = st.text_area(
        "1. Cole a lista de Contract IDs aqui:",
        height=300,
        placeholder="Exemplo:\nID: 12345678 (Este texto será removido)\n90123456, 78901234 56789012"
    )

    # Botão de processamento abaixo do input (fica mais organizado)
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
    
                    # Armazena o resultado no estado da sessão para ser exibido na coluna 2
                    st.session_state.saida_formatada = saida
                    st.session_state.total_ids = len(numeros)
                    st.session_state.show_output = True
                else:
                    st.session_state.show_output = False
                    st.session_state.saida_formatada = ""
                    st.warning("Nenhum 'Contract ID' válido foi encontrado na entrada fornecida.")

# O estado da sessão precisa ser inicializado
if 'show_output' not in st.session_state:
    st.session_state.show_output = False
    st.session_state.saida_formatada = ""
    st.session_state.total_ids = 0

with col_output:
    
    # Título da Saída
    st.subheader("2. Saída Formatada (Cláusula IN)")
    
    if st.session_state.show_output and st.session_state.saida_formatada:
        saida = st.session_state.saida_formatada
        total_ids = st.session_state.total_ids
        
        st.info(f"Total de **{total_ids}** IDs únicos encontrados e formatados.")

        # Exibe o resultado formatado no bloco de código
        # Ajustamos a altura do bloco de código para acompanhar o input (aprox. 300px)
        st.code(saida, language="sql", height=250)
        
        # 2. Botão Copiar (implementado via injeção JS)
        # O JS usa navigator.clipboard.writeText e fornece feedback visual na própria UI
        
        # Escapa a string para ser segura no JS (importante para evitar erros de aspas)
        js_saida = saida.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        
        copy_button_html = f"""
        <button 
            onclick="navigator.clipboard.writeText('{js_saida}'); 
                     var btn = event.target; 
                     var originalText = btn.innerHTML;
                     btn.innerHTML = '✅ Lista Copiada!'; 
                     setTimeout(() => {{ btn.innerHTML = originalText; }}, 2000);"
            style="
                background-color: #17A2B8; /* Cor Streamlit */
                color: white; 
                padding: 0.5rem 1rem; 
                border: none; 
                border-radius: 0.5rem; 
                cursor: pointer; 
                font-weight: bold;
                transition: background-color 0.3s;
                width: 100%; 
                margin-top: 10px;
            "
        >
            📋 Copiar Lista Formatada
        </button>
        """
        st.markdown(copy_button_html, unsafe_allow_html=True)
        
    else:
        # Placeholder quando o aplicativo é carregado ou após um erro
        st.code("Aguardando processamento dos dados...", language="sql", height=300)
        st.markdown('<div style="height: 48px;"></div>', unsafe_allow_html=True) # altura do botão para manter o alinhamento

import streamlit as st
import pandas as pd
import io

# Configuração da página
st.set_page_config(
    page_title="Limpeza e Extração de Contract IDs",
    layout="centered"
)

st.title("📄 Processador de Contract IDs")
st.markdown("---")

st.markdown("""
Este aplicativo limpa e extrai IDs de contrato de uma coluna de planilha,
separando múltiplos IDs que estejam em uma mesma célula (separados por vírgula, espaço ou quebra de linha).
""")

# Função de processamento (usando st.cache_data para performance)
@st.cache_data
def process_contract_ids(uploaded_file):
    """
    Carrega o arquivo, limpa e explode a coluna 'Contract ID'.
    """
    try:
        # 1. Leitura do arquivo Excel
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: Certifique-se de que é um arquivo Excel válido (.csv). Detalhes: {e}")
        return None

    if 'Contract ID' not in df.columns:
        st.error("A coluna 'Contract ID' não foi encontrada no arquivo. Por favor, verifique o nome da coluna.")
        return None

    st.subheader("Visualização Inicial dos Dados")
    st.dataframe(df.head(), use_container_width=True)

    with st.spinner('Processando e limpando os Contract IDs...'):
        # 2. Limpeza e Explode (adaptação do script original)
        
        # Substitui espaços e quebras de linha por vírgulas e explode a coluna
        df_split = df['Contract ID'].apply(
            lambda x: str(x).replace(' ', ',').replace('\n', ',').replace('\r\n', ',').split(',')
            if pd.notna(x) else [None] # Manteve None/NaN para tratamento posterior
        ).explode()

        # Remove espaços em branco
        df_split = df_split.str.strip()

        # Converte para string e remove o '.0' que pode aparecer se o Excel tratar como float
        df_split = df_split.astype(str).str.replace(r'\.0$', '', regex=True)

        # Remove strings vazias e 'nan'
        df_split = df_split[df_split != '']
        df_split = df_split[df_split.str.lower() != 'nan']

        # 3. Conversão para Numérico (Int64) e remoção de valores nulos
        try:
            # Tenta converter para numérico e depois para Int64 (inteiro com suporte a nulos)
            df_split = pd.to_numeric(df_split, errors='coerce').astype('Int64')
        except:
            # Caso a conversão falhe (por exemplo, IDs muito longos), usa string
            st.warning("Aviso: Alguns IDs não puderam ser convertidos para números inteiros (Int64). Usando strings para manter a integridade dos dados.")
            df_split = pd.to_numeric(df_split, errors='coerce').fillna('').astype(str)

        # Remove linhas que resultaram em <NA> (nulo)
        df_split = df_split.dropna()
        
        # Cria o DataFrame final
        result_df = pd.DataFrame(df_split.rename('Contract ID Limpo'))
        
        # Remove duplicatas (opcional, mas útil)
        result_df = result_df.drop_duplicates().reset_index(drop=True)

    return result_df

# --- Interface do Aplicativo ---

uploaded_file = st.file_uploader(
    "1. Faça o upload do arquivo Excel (.csv)",
    type=['csv'],
    help="O arquivo deve ter uma coluna chamada 'Contract ID'."
)

if uploaded_file is not None:
    st.success("Arquivo carregado com sucesso!")
    
    # Processa o arquivo
    processed_df = process_contract_ids(uploaded_file)
    
    if processed_df is not None and not processed_df.empty:
        st.markdown("---")
        st.subheader("2. Resultado Final (IDs Limpos e Separados)")
        st.info(f"Total de {len(processed_df)} IDs únicos encontrados após a limpeza.")
        
        # Exibe as primeiras linhas do resultado
        st.dataframe(processed_df.head(10), use_container_width=True)
        
        # Prepara o arquivo para download
        csv_buffer = io.StringIO()
        processed_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue().encode('utf-8')

        # Botão de download
        st.download_button(
            label="3. Baixar 'contract_ids_limpos.csv'",
            data=csv_data,
            file_name='contract_ids_limpos.csv',
            mime='text/csv',
            help="Clique para baixar o arquivo CSV com a lista limpa de IDs."
        )
    elif processed_df is not None and processed_df.empty:
        st.warning("O processamento foi concluído, mas nenhum 'Contract ID' válido foi encontrado.")




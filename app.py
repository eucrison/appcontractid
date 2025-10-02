import streamlit as st
import pandas as pd
import io
import re

# Configuração da página
st.set_page_config(
    page_title="Limpeza e Extração de Contract IDs",
    layout="centered"
)

st.title("📄 Processador de Contract IDs por Colagem")
st.markdown("---")

st.markdown("""
Cole os IDs de contrato na caixa de texto abaixo. O aplicativo irá **remover qualquer caractere que não seja número**, 
extraindo apenas as sequências numéricas e removendo duplicatas.
""")

# Função de processamento (usando st.cache_data para performance)
@st.cache_data
def process_contract_ids(raw_input_text):
    """
    Recebe uma string de texto, limpa e extrai os IDs de contrato, mantendo apenas dígitos.
    """
    if not raw_input_text:
        return pd.DataFrame()

    with st.spinner('Processando e limpando os Contract IDs...'):
        
        # 1. Pré-processamento para extrair apenas números
        
        # NOVO AJUSTE: Substitui qualquer caractere que não seja dígito (\D) por uma vírgula (,)
        # Isso lida com espaços, letras, quebras de linha e outros separadores de forma robusta.
        text_processed = re.sub(r'\D+', ',', raw_input_text)
        
        # Divide o texto pela vírgula. O [item.strip() for item in ... if item.strip()]
        # garante que valores vazios ou apenas espaços sejam removidos, resultando apenas em números.
        list_of_ids = [item.strip() for item in text_processed.split(',') if item.strip()]

        if not list_of_ids:
            return pd.DataFrame()

        # 2. Criação da Série Pandas
        df_split = pd.Series(list_of_ids)

        # 3. Limpeza Final e Coerção
        
        # Remove strings vazias e 'nan' (caso algum resíduo tenha ficado)
        df_split = df_split[df_split != '']
        df_split = df_split[df_split.str.lower() != 'nan']

        # Converte para string e remove o '.0' que pode aparecer em números inteiros
        df_split = df_split.astype(str).str.replace(r'\.0$', '', regex=True)
        
        # 4. Conversão para Numérico (Int64) e remoção de valores nulos
        try:
            # Tenta converter para numérico e depois para Int64 (inteiro com suporte a nulos)
            # errors='coerce' transforma não-números (que não devem existir após o re.sub) em NaN
            df_numeric = pd.to_numeric(df_split, errors='coerce')
            df_split = df_numeric.astype('Int64')
        except:
            # Caso a conversão falhe (improvável com o novo regex), mantém como string
            st.warning("Aviso: Falha na conversão para número inteiro. Mantendo IDs como texto.")
            pass 

        # Remove linhas que resultaram em <NA> (nulo, gerado pelo 'coerce')
        df_split = df_split.dropna()
        
        # Cria o DataFrame final, remove duplicatas e reseta o índice
        result_df = pd.DataFrame(df_split.rename('Contract ID Limpo'))
        result_df = result_df.drop_duplicates().reset_index(drop=True)

    return result_df

# --- Interface do Aplicativo ---

raw_text_input = st.text_area(
    "1. Cole a lista de Contract IDs aqui:",
    height=200,
    placeholder="Exemplo:\nID: 12345678 (Este texto será removido)\n90123456, 78901234 56789012"
)

if st.button('Processar IDs') and raw_text_input:
    # Processa o texto inserido
    processed_df = process_contract_ids(raw_text_input)
    
    if processed_df is not None and not processed_df.empty:
        st.markdown("---")
        st.subheader("2. Resultado Final (IDs Limpos e Separados)")
        st.info(f"Total de **{len(processed_df)}** IDs únicos encontrados após a limpeza.")
        
        # Exibe as primeiras linhas do resultado
        st.dataframe(processed_df.head(10), use_container_width=True)
        
        # Prepara o arquivo para download
        csv_buffer = io.StringIO()
        # Converte para string antes de salvar para garantir que 'Int64' seja salvo corretamente
        processed_df['Contract ID Limpo'] = processed_df['Contract ID Limpo'].astype(str)
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
        st.warning("O processamento foi concluído, mas nenhum 'Contract ID' válido foi encontrado na entrada fornecida.")
    else:
        st.error("Ocorreu um erro desconhecido durante o processamento.")

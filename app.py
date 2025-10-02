import streamlit as st
import pandas as pd
import io
import re

# Configuração da página
st.set_page_config(
    page_title="Limpeza e Formatação de Contract IDs para SQL",
    layout="centered"
)

st.title("📄 Processador de Contract IDs para SQL")
st.markdown("---")

st.markdown("""
**Instrução:** Cole a lista de Contract IDs na caixa de texto. O aplicativo irá:
1. Remover qualquer caractere que não seja um dígito (mantendo apenas números).
2. Remover duplicatas.
3. Formatar o resultado em uma única linha separada por vírgulas e aspas simples (`'ID1', 'ID2', ...`), pronta para ser usada em consultas SQL.
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
        
        # Substitui qualquer caractere que não seja dígito (\D) por uma vírgula (,)
        text_processed = re.sub(r'\D+', ',', raw_input_text)
        
        # Divide o texto pela vírgula, removendo entradas vazias
        list_of_ids = [item.strip() for item in text_processed.split(',') if item.strip()]

        if not list_of_ids:
            return pd.DataFrame()

        # 2. Criação da Série Pandas
        df_split = pd.Series(list_of_ids)

        # 3. Limpeza Final e Coerção
        
        # Remove strings vazias e 'nan'
        df_split = df_split[df_split != '']
        df_split = df_split[df_split.str.lower() != 'nan']

        # Converte para string e remove o '.0' que pode aparecer em números inteiros
        df_split = df_split.astype(str).str.replace(r'\.0$', '', regex=True)
        
        # Tenta converter para numérico e depois para Int64, para garantir que são apenas números válidos
        try:
            df_numeric = pd.to_numeric(df_split, errors='coerce')
            df_split = df_numeric.astype('Int64')
        except:
            pass # Mantém como string se a conversão falhar

        # Remove linhas que resultaram em <NA> (nulo)
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

if st.button('Processar e Formatar IDs') and raw_text_input:
    # Processa o texto inserido
    processed_df = process_contract_ids(raw_text_input)
    
    if processed_df is not None and not processed_df.empty:
        
        # 2. Formatação SQL
        # Converta a coluna de IDs limpos para uma lista de strings para formatação
        numeros = processed_df['Contract ID Limpo'].astype(str).tolist()
        
        # Formata cada número com aspas simples, juntando-os com vírgula
        saida = ",".join([f"'{n}'" for n in numeros])

        st.markdown("---")
        st.subheader("2. Saída Formatada para SQL (`IN` Clause)")
        st.info(f"Total de **{len(numeros)}** IDs únicos encontrados e formatados.")

        # Exibe o resultado formatado em um bloco de código SQL
        st.code(saida, language="sql")

        # Botão para copiar (Download Button é o padrão do Streamlit para exportar dados)
        st.download_button(
            label="📋 Copiar Lista Formatada",
            data=saida,
            file_name="contratos_sql_list.txt",
            mime="text/plain",
            help="Baixa um arquivo de texto contendo a lista formatada, facilitando a cópia para sua consulta SQL."
        )
        
    elif processed_df is not None and processed_df.empty:
        st.warning("O processamento foi concluído, mas nenhum 'Contract ID' válido foi encontrado na entrada fornecida.")
    else:
        st.error("Ocorreu um erro desconhecido durante o processamento.")

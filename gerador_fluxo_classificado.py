import pandas as pd
import unidecode

# --- 1. CONFIGURAÇÕES ---
# Arquivos que você vai fornecer
ARQUIVO_PLANO_CONTAS = 'plano_de_contas_pcpl.csv'
ARQUIVO_FLUXO_CAIXA_ENTRADA = 'fluxo_caixa_entrada.csv'

# Arquivo final que o programa vai gerar
ARQUIVO_FLUXO_CAIXA_SAIDA = 'fluxo_caixa_classificado_final.csv'


def normalizar_texto(texto):
    """Converte texto para minúsculas, remove acentos e espaços."""
    if not isinstance(texto, str):
        return ''
    return unidecode(texto).lower().strip()


def gerar_fluxo_classificado():
    """
    Script completo e robusto que lê os arquivos brutos, limpa os dados,
    e gera o arquivo de fluxo de caixa final com as colunas Débito e Crédito
    preenchidas com os códigos das contas.
    """
    print("--- INICIANDO GERADOR DE FLUXO DE CAIXA CLASSIFICADO ---")

    try:
        # Usar 'latin-1' que se mostrou mais compatível com seus arquivos
        df_plano = pd.read_csv(ARQUIVO_PLANO_CONTAS, sep=';', encoding='latin-1')
        df_fluxo = pd.read_csv(ARQUIVO_FLUXO_CAIXA_ENTRADA, sep=';', decimal=',', encoding='latin-1')
        print(" -> Arquivos de entrada lidos com sucesso.")
    except FileNotFoundError as e:
        print(f"ERRO CRÍTICO: O arquivo '{e.filename}' não foi encontrado.")
        return
    except Exception as e:
        print(f"ERRO CRÍTICO ao ler os arquivos: {e}")
        return

    # --- LIMPEZA E CORREÇÃO AUTOMÁTICA DOS CABEÇALHOS ---
    df_plano.columns = df_plano.columns.str.strip()
    df_fluxo.columns = df_fluxo.columns.str.strip()

    mapa_correcao = {'subgrupos': 'subgrupo', 'valor': 'Valor', 'VALOR': 'Valor'}
    df_plano.rename(columns=mapa_correcao, inplace=True)
    df_fluxo.rename(columns=mapa_correcao, inplace=True)

    # Validação final para garantir que as colunas essenciais existem
    if 'subgrupo' not in df_plano.columns or 'Codigo' not in df_plano.columns:
        print(
            f"ERRO: Plano de Contas não contém as colunas 'subgrupo' e/ou 'Codigo'. Colunas encontradas: {df_plano.columns.tolist()}")
        return
    if 'subgrupo' not in df_fluxo.columns or 'Valor' not in df_fluxo.columns:
        print(
            f"ERRO: Fluxo de Caixa não contém as colunas 'subgrupo' e/ou 'Valor'. Colunas encontradas: {df_fluxo.columns.tolist()}")
        return

    # --- PREENCHIMENTO DOS CÓDIGOS DE DÉBITO E CRÉDITO ---
    print(" -> Preenchendo os lançamentos (ignorando acentos e maiúsculas)...")

    # Criação do mapa de busca normalizado
    df_plano['subgrupo_normalizado'] = df_plano['subgrupo'].apply(normalizar_texto)
    df_plano_sem_duplicatas = df_plano.drop_duplicates(subset=['subgrupo_normalizado'], keep='first')
    mapa_contas = pd.Series(df_plano_sem_duplicatas.Codigo.values,
                            index=df_plano_sem_duplicatas.subgrupo_normalizado).to_dict()

    df_fluxo['Débito'] = pd.Series(dtype='object')
    df_fluxo['Crédito'] = pd.Series(dtype='object')

    for index, row in df_fluxo.iterrows():
        subgrupo_transacao = row['subgrupo']
        subgrupo_normalizado = normalizar_texto(subgrupo_transacao)
        valor_transacao = row['Valor']

        codigo_conta = mapa_contas.get(subgrupo_normalizado)

        if codigo_conta:
            if valor_transacao < 0:
                df_fluxo.loc[index, 'Débito'] = codigo_conta
            elif valor_transacao > 0:
                df_fluxo.loc[index, 'Crédito'] = codigo_conta
        else:
            if subgrupo_transacao and pd.notna(subgrupo_transacao):
                print(f"Aviso: O subgrupo '{subgrupo_transacao}' não foi encontrado no Plano de Contas.")

    # --- FINALIZAÇÃO E EXPORTAÇÃO ---
    df_fluxo[['Débito', 'Crédito']] = df_fluxo[['Débito', 'Crédito']].fillna('')

    # Garante a ordem correta das colunas no arquivo final
    colunas_finais = [col for col in ['Débito', 'Crédito', 'Data', 'grupo', 'subgrupo', 'Valor'] if
                      col in df_fluxo.columns]
    df_fluxo = df_fluxo[colunas_finais]

    print(" -> Preenchimento concluído.")

    try:
        df_fluxo.to_csv(ARQUIVO_FLUXO_CAIXA_SAIDA, sep=';', decimal=',', index=False)
        print(f"\nArquivo final '{ARQUIVO_FLUXO_CAIXA_SAIDA}' salvo com sucesso!")
        print("\n--- Amostra do Resultado Final ---")
        print(df_fluxo.head().to_string())
    except Exception as e:
        print(f"\nOcorreu um erro ao salvar o arquivo de saída: {e}")

    print("\n--- PROCESSO CONCLUÍDO ---")


if __name__ == "__main__":
    try:
        from unidecode import unidecode
    except ImportError:
        print("ERRO: A biblioteca 'unidecode' não está instalada.")
        print("Por favor, execute no seu terminal: pip install Unidecode")
    else:
        gerar_fluxo_classificado()
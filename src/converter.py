import logging
import zipfile
from pathlib import Path
from typing import BinaryIO

import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


def stream_csv_stream_to_parquet(
    csv_stream: BinaryIO,  # Arquivo para ser convertido por stream
    output_path: Path,  # Diretório de armazenamento do Parquet
    block_size_mb: int = 10,  # Tamanho do lote a ser lido em MB
    compression: str = "zstd",  # Tipo de compressão do arquivo Parquet
) -> int:
    """ "
    Consome um stream de CSV em lotes (sem carregar na memória) e grava incrementalmente em um arquivo Parquet.
    Retorna quantidade de linhas processadas.
    """
    # Definindo as configurações de leitura e conversão do arquivo
    read_options = pacsv.ReadOptions(
        block_size=block_size_mb
        * 1024
        * 1024,  # Tamanho da chunk em MB - 10 * 1024 bytes * 1024 bytes = 10 MB
        encoding="latin1",  # Configuração de enconding do arquivo
    )
    convert_options = pacsv.ConvertOptions(default_column_type=pa.string())
    parse_options = pacsv.ParseOptions(delimiter=";")

    # Streaming reader sobre o stream binário
    reader = pacsv.open_csv(  # Um leitor csv por chunks (stream), recebendo as configurações de leitura e conversão.
        csv_stream,
        read_options=read_options,
        parse_options=parse_options,
        convert_options=convert_options,
    )

    # Garantia da existência do diretório
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_linhas = 0
    writer = None

    try:
        for batch in reader:  # Itera sobre os chunks (lotes) lidos do CSV
            if writer is None:  # Verifica se o writer é inicializado
                writer = pq.ParquetWriter(  # Inicializa o gravador com suas configurações
                    output_path,  # Define o diretório de saída do arquivo convertido
                    reader.schema,
                    compression=compression,
                )
            writer.write_batch(batch)  # Grava o chunk lido com o `writer`
            total_linhas += batch.num_rows  # Soma o total de linhas processadas

    finally:
        if writer is not None:
            writer.close()

    return total_linhas


def convert_zip_to_parquet(
    zip_path: Path,  # Caminho do arquivo ZIP para descompactação
    target_csv_name: str,  # Nome do arquivo de interesse para conversão
    output_parquet_path: Path,  # Caminho de saída para o arquivo Parquet
) -> bool:
    """
    Localiza o arquivo CSV dentro do arquivo ZIP e converte pra Parquet via Streaming.
    """
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Lista dos arquivos presentes dentro do ZIP
        nomes_no_zip = zip_ref.namelist()

        # Procura pelo nome do arquivo com case-sensitive e fallback.
        arquivo_encontrado = None
        if target_csv_name in nomes_no_zip:  # Verifica se o CSV está no ZIP
            arquivo_encontrado = target_csv_name
        elif (
            target_csv_name.upper() in nomes_no_zip
        ):  # Verifica se o CSV em Maiúsculo está no ZIP
            arquivo_encontrado = target_csv_name.upper()
        if (
            not arquivo_encontrado
        ):  # Se o arquivo não for encontrado encerra a operação.
            logger.warning(
                f"Arquivo '{target_csv_name}' não foi encontrado dentro de {zip_path.name}"
            )
            return False

        logger.info(f"Iniciando conversão de '{arquivo_encontrado}' para Parquet...")
        # Abre o arquivo CSV de interesse encontrado
        with zip_ref.open(arquivo_encontrado) as csv_stream:
            # Grava o resultado da conversão do arquivo CSV para Parquet através da função `stream_csv_stram_to_parquet`
            total_linhas = stream_csv_stream_to_parquet(csv_stream, output_parquet_path)
            logger.info(
                f"Conversão concluída: {total_linhas:,} linhas gravadas em {output_parquet_path}"
            )
            return True

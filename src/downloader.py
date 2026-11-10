import requests
import os
import http
import tempfile
import zipfile
import logging
import time
from pathlib import Path
from requests.adapters import HTTPAdapter
from itertools import product
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.util import Retry
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn
    )
from src.datasets import TSEDataset, DATASETS_CATALOG
from src.console import console

logger = logging.getLogger(__name__)

DATA_PATH = "./data"

class DownloadTSE:
    def __init__(self):
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)

    def ingest_dataset_year(
        self, 
        dataset: TSEDataset, 
        ano:int, 
        session: requests.Session, 
        progress: Progress = None,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ):
        # Monta a URL de Download.
        url = dataset.build_url(ano)
        # Formata e monta o nome do arquivo ZIP de Download.
        nome_arquivo_zip = dataset.arquivo_zip.format(nome=dataset.nome, ano=ano)
        # Definição do nome de arquivo, diretório de armazenamento e caminho completo destino.
        nome_arquivo_csv = dataset.build_csv_filename(ano)
        # Nome da pasta de armazenamento local dos arquivos.
        diretorio_destino = Path(DATA_PATH) / dataset.endpoint
         
        # Verificação da existência do diretório para download do arquivo.
        diretorio_destino.mkdir(parents=True, exist_ok=True)
        
        # Inicia a abertura de um diretório temporário para operações subsequentes. 
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_zip_path = Path(temp_dir)/nome_arquivo_zip # Nome do diretório temporário.
            sucess_download = False # Variável indicadora de operação do download.
            task_id = None

            try:             
                # Requisição e Armazenamento.
                for tentativa in range(1, max_retries + 1):
                    try:
                        espera = backoff_factor * (2 ** (tentativa-1))
                        with session.get(url, stream=True, timeout=(15, 300)) as response:
                            if response.status_code == http.HTTPStatus.NOT_FOUND:
                                logger.error(f"Arquivo {nome_arquivo_zip} não encontrado no servidor (404).")
                                return False

                            if response.status_code != http.HTTPStatus.OK:
                                logger.warning(f"Tentativa {tentativa}/{max_retries} falhou para {nome_arquivo_zip}. Status Code: {response.status_code}")
                                if tentativa < max_retries:
                                    time.sleep(espera)
                                    continue
                                return False
                            
                            # Obtenção do tamanho total do arquivo, em bytes, para uso na Barra de Progresso.
                            content_length = response.headers.get("content-length") # Tamanho, em bytes, do arquivo requisitado.
                            total_bytes = int(content_length) if content_length else None

                            if progress:
                                if task_id is None:
                                    task_id = progress.add_task(f"[cyan]{nome_arquivo_zip}", total=total_bytes)
                                else:
                                    progress.reset(task_id, total=total_bytes)

                            # Gravação em chunks(streaming) para arquivos grandes
                            with open(temp_zip_path, "wb") as f:
                                for chunk in response.iter_content(chunk_size=1024 * 1024):
                                    if chunk:
                                        f.write(chunk)
                                        if progress and task_id is not None:
                                            progress.advance(task_id, advance=len(chunk))

                            # Verificação de Integridade
                            tamanho_baixado = temp_zip_path.stat().st_size
                            if total_bytes and tamanho_baixado < total_bytes:
                                logger.warning(f"Download incompleto de {nome_arquivo_zip} na tentativa {tentativa}/{max_retries}: Recebidos {tamanho_baixado} de {total_bytes} bytes.")
                                if tentativa < max_retries:
                                    time.sleep(espera)
                                    continue
                                else:
                                    logger.error(f"Falha definitiva ao baixar {nome_arquivo_zip}: arquivo incompleto após {max_retries} tentativas.")
                                    return False

                            logger.info(f"Arquivo {nome_arquivo_zip} baixado com sucesso temporariamente.")
                            sucess_download = True
                            break
                    
                    except requests.exceptions.RequestException as e:
                        logger.warning(f"Erro de conexão na tentativa {tentativa}/{max_retries} de {nome_arquivo_zip}: {e}")
                        if tentativa < max_retries:
                            time.sleep(espera)
                            continue
                        else:
                            logger.error(f"Falha definitiva de conexão para {nome_arquivo_zip} após {max_retries} tentativas.")
                            return False
                    

                # Descompactação do arquivo. 
                if sucess_download: 
                    if progress and task_id is not None:
                        progress.update(task_id, description=f"[yellow]Descompactando {nome_arquivo_zip}...")

                    with zipfile.ZipFile(temp_zip_path,"r") as zip_ref:
                        # Lista com todos os nomes de arquivos dentro do ZIP
                        arquivos_no_zip = zip_ref.namelist()

                        # Procura pelo nome do arquivo de interesse _BRASIL_
                        if nome_arquivo_csv in arquivos_no_zip:
                            zip_ref.extract(nome_arquivo_csv, path=diretorio_destino)
                            logger.info(f"Arquivo {nome_arquivo_csv} descompactado com sucesso")
                            return True
                        elif nome_arquivo_csv.upper() in arquivos_no_zip:
                            zip_ref.extract(nome_arquivo_csv.upper(), path=diretorio_destino)
                            logger.info(f"Arquivo {nome_arquivo_csv.upper()} descompactado com sucesso")
                            return True
                        else:
                            logger.warning(f"Arquivo {nome_arquivo_csv} não encontrado no ZIP")
                            return False
            
            finally:
                if progress and task_id is not None:
                    progress.remove_task(task_id)
                
    def _execute_batch_download(self, etapas:list, max_workers: int = 4):
        retry_strategy = Retry(
            total= 3,
            backoff_factor=2,
            status_forcelist=[425, 429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"]
        )
        with requests.Session() as session:
            adapter = HTTPAdapter(
                pool_connections=max_workers,
                pool_maxsize=max_workers,
                max_retries=retry_strategy
            )
            session.mount("https://", adapter)
            session.mount("http://", adapter)

            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                console=console
            ) as progress:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submissão das tarefas às threads.
                    futuros = {
                        executor.submit(self.ingest_dataset_year, dataset, ano, session, progress): (dataset,ano)
                        for dataset, ano in etapas
                    }
                    for futuro in as_completed(futuros):
                        dataset, ano = futuros[futuro]
                        try:
                            futuro.result()
                        except Exception as e:
                            logger.error(f"Erro ao baixar {dataset.nome} ({ano}): {e}")
                        finally:
                            logger.info(f"Concluído: {dataset.nome} ({ano})")

    def ingest_all_datasets(self, anos:list):
        """
        Baixa todos os datasets disponíveis para uma lista de anos.
        Args:
            anos (list): Lista de anos para o qual os datasets devem ser baixados.
        """
        
        etapas = list(product(DATASETS_CATALOG.values(), anos))
        etapas.sort(key=lambda etapa: (etapa[0].peso, etapa[1]), reverse=True)
        self._execute_batch_download(etapas)

    def ingest_one_dataset(self, dataset: TSEDataset, anos:list):
        """
        Baixa apenas um dataset disponíveis para uma lista de anos.
        Args:
            dataset (TSEDataset): Dataset a ser baixado.
            anos (list): Lista de anos para o qual os datasets devem ser baixados.
        """

        etapas = list(product([dataset], anos))
        etapas.sort(key=lambda etapa: etapa[1], reverse=True)
        self._execute_batch_download(etapas)
        

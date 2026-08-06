from pathlib import Path
import requests
import os
import http
from rich.progress import Progress
from itertools import product
import logging
from src.datasets import TSEDataset, DATASETS_CATALOG

import tempfile
import zipfile

logger = logging.getLogger(__name__)

DATA_PATH = "./data"

class DownloadTSE:
    def __init__(self):
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)

    def ingest_dataset_year(self, dataset: TSEDataset, ano:int):
        url = dataset.build_url(ano)
        
        nome_arquivo_zip = dataset.arquivo_zip.format(nome=dataset.nome, ano=ano)

        # Definição do nome de arquivo, diretório de armazenamento e caminho completo destino.
        nome_arquivo_csv = dataset.build_csv_filename(ano)
        diretorio_destino = Path(DATA_PATH) / dataset.endpoint # Nome da pasta de armazenamento local dos arquivos.
        destino = diretorio_destino / nome_arquivo_csv # Destino completo da localização do arquivo.
         
        # Verificação da existência do diretório para download do arquivo.
        if not os.path.exists(diretorio_destino):
            os.makedirs(diretorio_destino)  # Caso não exista, será criado.
            logger.info(f"Diretório {diretorio_destino} criado com sucesso.") 
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_zip_path = Path(temp_dir)/nome_arquivo_zip

            # Requisição e Armazenamento.
            response = requests.get(url, stream=True)
            if response.status_code == http.HTTPStatus.OK:
                # Gravação em chunks(streaming) para arquivos grandes
                with open(temp_zip_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"Arquivo {nome_arquivo_zip} acessado temporariamente.")
                
                # Descompactação do arquivo ZIP
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
            else:
                logger.error(f"Falha ao acessar o ZIP {nome_arquivo_zip}. Status Code: {response.status_code}")
                return False
            
    def ingest_all_datasets(self, anos:list):
        """
        Baixa todos os datasets disponíveis para uma lista de anos.
        Args:
            anos (list): Lista de anos para o qual os datasets devem ser baixados.
        """

        etapas = list(product(DATASETS_CATALOG.values(), anos))

        with Progress() as progress:
            task = progress.add_task("[cyan]Iniciando downloads...", total=len(etapas))

            for dataset, ano in etapas:
                progress.update(task, description=f"[bold blue]Baixando[/bold blue] {dataset.nome} ({ano})")
                self.ingest_dataset_year(dataset, ano)
                progress.advance(task)

    def ingest_one_dataset(self, dataset: TSEDataset, anos:list):
        """
        Baixa apenas um dataset disponíveis para uma lista de anos.
        Args:
            dataset (TSEDataset): Dataset a ser baixado.
            anos (list): Lista de anos para o qual os datasets devem ser baixados.
        """

        etapas = list(product([dataset], anos))

        with Progress() as progress:
            task = progress.add_task("[cyan]Iniciando downloads...", total=len(etapas))

            for dataset, ano in etapas:
                progress.update(task, description=f"[bold blue]Baixando[/bold blue] {dataset.nome} ({ano})")
                self.ingest_dataset_year(dataset, ano)
                progress.advance(task)


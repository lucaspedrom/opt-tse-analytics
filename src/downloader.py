from pathlib import Path
import requests
import os
import http
from rich.progress import Progress
from itertools import product
import logging
from src.datasets import TSEDataset, DATASETS_CATALOG

logger = logging.getLogger(__name__)

DATA_PATH = "./data"

class DownloadTSE:
    def __init__(self):
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)

    def ingest_dataset_year(self, dataset: TSEDataset, ano:int):
        url = dataset.build_url(ano)
        print(url)
        
        # Definição dos nomes de arquivo, diretório de armazenamento e caminho completo destino.
        nome_arquivo = dataset.arquivo.format(nome=dataset.nome, ano=ano)
        diretorio_arquivo = Path(DATA_PATH) / dataset.endpoint
        destino = diretorio_arquivo / nome_arquivo
        
        # Verificação da existência do diretório para download do arquivo.
        if not os.path.exists(diretorio_arquivo):
            os.makedirs(diretorio_arquivo)  # Caso não exista, será criado.
            print(f"Diretório {diretorio_arquivo} criado com sucesso.") 
        
        # Requisição e Armazenamento.
        response = requests.get(url)
        if response.status_code == http.HTTPStatus.OK:
            with open(destino, "wb") as f:
                f.write(response.content)
            logger.info(f"Arquivo {nome_arquivo} baixado com sucesso")
            return True
        
        logger.error(f"Falha ao baixar o arquivo {nome_arquivo}. Status Code: {response.status_code}")
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


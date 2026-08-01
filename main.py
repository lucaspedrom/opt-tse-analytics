import argparse
import logging

from src.downloader import DownloadTSE
from src.datasets import DATASETS_CATALOG

if __name__ == "__main__":
    # Configura o logging básico para ver os logs do downloader
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="Baixar dados do TSE")
    
    # As chaves válidas são as chaves de DATASETS_CATALOG + 'all'
    bases_disponiveis = list(DATASETS_CATALOG.keys())
    
    parser.add_argument(
        "--base", "-b",
        type=str,
        default="all",
        choices=bases_disponiveis + ["all"],
        help=f"Base de dados a ser baixada. Opções: {', '.join(bases_disponiveis)} ou 'all'"
    )
    parser.add_argument("--inicio", '-i', type=int, default=2014, help="Ano inicial a ser baixado")
    parser.add_argument("--fim", '-f', type=int, default=2022, help="Ano final a ser baixado")
    parser.add_argument("--intervalo", type=int, default=2, help="Intervalo entre os anos a serem baixados (2 ou 4 anos)")
    args = parser.parse_args()

    downloader = DownloadTSE()
    
    # Gera a lista de anos com base no início, fim e intervalo
    anos = list(range(args.inicio, args.fim + 1, args.intervalo))
    
    # Executa o download conforme a opção escolhida
    if args.base == "all":
        downloader.ingest_all_datasets(anos)
    else:
        downloader.ingest_one_dataset(dataset=DATASETS_CATALOG[args.base], anos=anos)

            
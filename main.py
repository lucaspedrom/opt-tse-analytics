import argparse

from downloader import DownloadTSE

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baixar dados do TSE")
    parser.add_argument("--inicio", '-i', type=int, default=2014, help="Ano inicial a ser baixado")
    parser.add_argument("--fim", '-f', type=int, default=2022, help="Ano final a ser baixado")
    parser.add_argument("--intervalo", type=int, default=2022, help="Intervalo entre os anos a serem baixados")
    args = parser.parse_args()

    downloader = DownloadTSE()
    downloader.download_anos(range(args.inicio, args.fim + 1, args.intervalo))
            
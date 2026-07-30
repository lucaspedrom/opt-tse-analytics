import requests
import os
import http
from rich.progress import track

DATA_PATH = "./data"

class DownloadTSE:
    def __init__(self):
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)

    def download_consulta_candidatura(self, ano:int, base_path:str = DATA_PATH):
        url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_{ano}.zip"
        response = requests.get(url)

        if response.status_code == http.HTTPStatus.OK:
            path = os.path.join(base_path, f"consulta_cand_{ano}.zip")
            with open(path, "wb") as f:
                f.write(response.content)
            print (f"Arquivo consulta_cand_{ano}.zip baixado com sucesso")
            return True
        
        print(f"Falha ao baixar o arquivo consult_cand{ano}.zip. Status Code: {response.status_code}")
        return False

    def download_bens_candidatos(self, ano:int, base_path:str = DATA_PATH):
        url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/bem_candidato/bem_candidato_{ano}.zip"
        response = requests.get(url)

        if response.status_code == http.HTTPStatus.OK:
            path = os.path.join(base_path, f"bem_candidato_{ano}.zip")
            with open(path, "wb") as f:
                f.write(response.content)
            print (f"Arquivo bem_candidato_{ano}.zip baixado com sucesso")
            return True
        
        print(f"Falha ao baixar o arquivo consult_cand{ano}.zip. Status Code: {response.status_code}")
        return False

    def download_coligacoes(self, ano:int, base_path:str = DATA_PATH):
        url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_coligacao/consulta_coligacao_{ano}.zip"
        response = requests.get(url)

        if response.status_code == http.HTTPStatus.OK:
            path = os.path.join(base_path, f"consulta_coligacao_{ano}.zip")
            with open(path, "wb") as f:
                f.write(response.content)
            print (f"Arquivo consulta_coligacao_{ano}.zip baixado com sucesso")
            return True
        
        print(f"Falha ao baixar o arquivo consult_cand{ano}.zip. Status Code: {response.status_code}")
        return False

    def download_motivo_cassacao(self, ano:int, base_path:str = DATA_PATH):
        url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/motivo_cassacao/motivo_cassacao_{ano}.zip"
        response = requests.get(url)

        if response.status_code == http.HTTPStatus.OK:
            path = os.path.join(base_path, f"motivo_cassacao_{ano}.zip")
            with open(path, "wb") as f:
                f.write(response.content)
            print (f"Arquivo motivo_cassacao_{ano}.zip baixado com sucesso")
            return True
        
        print(f"Falha ao baixar o arquivo consult_cand{ano}.zip. Status Code: {response.status_code}")
        return False

    def download_votacao_candidato_municipio_zona(self, ano:int, base_path:str = DATA_PATH):
        url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{ano}.zip"
        response = requests.get(url)

        if response.status_code == http.HTTPStatus.OK:
            path = os.path.join(base_path, f"votacao_candidato_munzona_{ano}.zip")
            with open(path, "wb") as f:
                f.write(response.content)
            print (f"Arquivo votacao_candidato_munzona_{ano}.zip baixado com sucesso")
            return True
        
        print(f"Falha ao baixar o arquivo votacao_candidato_munzona_{ano}.zip. Status Code: {response.status_code}")
        return False

    def download_ano(self, ano:int):
        if not os.path.exists(os.path.join(DATA_PATH, str(ano))):
            os.makedirs(os.path.join(DATA_PATH, str(ano)))
        
        self.download_consulta_candidatura(ano, os.path.join(DATA_PATH, str(ano)))
        self.download_bens_candidatos(ano, os.path.join(DATA_PATH, str(ano)))
        self.download_coligacoes(ano, os.path.join(DATA_PATH, str(ano)))
        self.download_motivo_cassacao(ano, os.path.join(DATA_PATH, str(ano)))
        self.download_votacao_candidato_municipio_zona(ano, os.path.join(DATA_PATH, str(ano)))

    def download_anos(self, anos:list):
        for ano in track(anos, description=f"Baixando dados dos anos... [{anos}]"):
            self.download_ano(ano)

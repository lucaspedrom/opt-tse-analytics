# %%
import requests

class DownloadTSE:
    def __init__(self):
        pass

    def download_consulta_candidatura(self, ano:int):
        url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_{ano}.zip"
        response = requests.get(url)

        if response.status_code == 200:
            with open(f"consulta_cand_{ano}.zip", "wb") as f:
                f.write(response.content)
            print (f"Arquivo consulta_cand_{ano}.zip baixado com sucesso")
            return True
        
        print(f"Falha ao baixar o arquivo consult_cand{ano}.zip. Status Code: {response.status_code}")
        return False

    def download_bens_candidatos(self, ano:int):
        url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/bem_candidato/bem_candidato_{ano}.zip"
        response = requests.get(url)

        if response.status_code == 200:
            with open(f"bem_candidato_{ano}.zip", "wb") as f:
                f.write(response.content)
            print (f"Arquivo bem_candidato_{ano}.zip baixado com sucesso")
            return True
        
        print(f"Falha ao baixar o arquivo consult_cand{ano}.zip. Status Code: {response.status_code}")
        return False

    def download_coligacoes(self, ano:int):
        url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_coligacao/consulta_coligacao_{ano}.zip"
        response = requests.get(url)

        if response.status_code == 200:
            with open(f"consulta_coligacao_{ano}.zip", "wb") as f:
                f.write(response.content)
            print (f"Arquivo consulta_coligacao_{ano}.zip baixado com sucesso")
            return True
        
        print(f"Falha ao baixar o arquivo consult_cand{ano}.zip. Status Code: {response.status_code}")
        return False

    def download_motivo_cassacao(self, ano:int):
        url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/motivo_cassacao/motivo_cassacao_{ano}.zip"
        response = requests.get(url)

        if response.status_code == 200:
            with open(f"motivo_cassacao_{ano}.zip", "wb") as f:
                f.write(response.content)
            print (f"Arquivo motivo_cassacao_{ano}.zip baixado com sucesso")
            return True
        
        print(f"Falha ao baixar o arquivo consult_cand{ano}.zip. Status Code: {response.status_code}")
        return False

    def download_votacao_candidato_municipio_zona(self, ano:int):
        url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{ano}.zip"
        response = requests.get(url)

        if response.status_code == 200:
            with open(f"votacao_candidato_munzona_{ano}.zip", "wb") as f:
                f.write(response.content)
            print (f"Arquivo votacao_candidato_munzona_{ano}.zip baixado com sucesso")
            return True
        
        print(f"Falha ao baixar o arquivo votacao_candidato_munzona_{ano}.zip. Status Code: {response.status_code}")
        return False
# %%
downloader = DownloadTSE()
downloader.download_bens_candidatos(2022)
            
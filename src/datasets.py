from dataclasses import dataclass
from urllib.parse import urljoin

DEFAULT_BASE_URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/"


@dataclass(frozen=True)
class TSEDataset:
    endpoint: str
    nome: str
    arquivo_zip: str = "{nome}_{ano}.zip"  # Valor padrão
    arquivo_csv: str = (
        "{nome}_{ano}_BRASIL.csv"  # Nome do arquivo de interesse (todos os dados do)
    )
    base_url: str = DEFAULT_BASE_URL
    peso: int = 1  # Tamanho estimado para priorização

    def build_url(self, ano: int) -> str:
        """Monta a URL exata para um único endpoit de arquivo zip por ano.
        Exemplo de url de endpoint:
        Real: https://cdn.tse.jus.br/estatistica/sead/odsele/processual/processo_eleitoral_2024.zip
        Formatado: https://cdn.tse.jus.br/estatistica/sead/odsele/{endpoint}/{nome}_{ano}.zip
        """
        arquivo_formatado = self.arquivo_zip.format(nome=self.nome, ano=ano)
        caminho = f"{self.endpoint}/{arquivo_formatado}"
        return urljoin(self.base_url, caminho)

    def build_csv_filename(self, ano: int) -> str:
        return self.arquivo_csv.format(nome=self.nome, ano=ano)


"""
    Exemplo de catálogo de uma URL.
    URL: https://cdn.tse.jus.br/estatistica/sead/odsele/processual/processo_eleitoral_2024.zip
    'processos':TSEDataset(
        endpoint='processual',
        nome='precesso_eleitoral'
    )
"""
DATASETS_CATALOG = {
    "candidatos": TSEDataset(endpoint="consulta_cand", nome="consulta_cand", peso=300),
    "bens_candidatos": TSEDataset(
        endpoint="bem_candidato", nome="bem_candidato", peso=250
    ),
    "coligacoes": TSEDataset(
        endpoint="consulta_coligacao", nome="consulta_coligacao", peso=50
    ),
    "motivo_cassacao": TSEDataset(
        endpoint="motivo_cassacao", nome="motivo_cassacao", peso=5
    ),
    "votacao_candidato_municipio_zona": TSEDataset(
        endpoint="votacao_candidato_munzona",
        nome="votacao_candidato_munzona",
        peso=1000,
    ),
}

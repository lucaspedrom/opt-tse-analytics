from dataclasses import dataclass
from urllib.parse import urljoin

DEFAULT_BASE_URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/"

@dataclass(frozen=True)
class TSEDataset:
    nome: str
    endpoint: str
    arquivo:str # {nome}_{ano}.zip
    base_url: str = DEFAULT_BASE_URL

    def build_url(self, ano:int) -> str:
        """Monta a URL exata para um único endpoit de arquivo zip por ano."""
        """Exemplo de url de endpoint: 
            Real: https://cdn.tse.jus.br/estatistica/sead/odsele/processual/processo_eleitoral_2024.zip
            Formatado: https://cdn.tse.jus.br/estatistica/sead/odsele/{endpoint}/{arquivo}.zip
        """
        arquivo = self.arquivo.format(nome=self.nome, ano=ano)
        caminho = f"{self.endpoint}/{arquivo}"
        return urljoin(self.base_url, caminho)

DATASETS_CATALOG = {
    "candidatos":TSEDataset(
        nome='consulta_cand',        
        endpoint='consulta_cand',        
        arquivo='{nome}_{ano}.zip'        
    ),
    "bens_candidatos":TSEDataset(
        nome='bem_candidato',
        endpoint='bem_candidato',
        arquivo='{nome}_{ano}.zip'
    ),
    "coligacoes":TSEDataset(
        nome='consulta_coligacao',
        endpoint='consulta_coligacao',
        arquivo='{nome}_{ano}.zip'
    ),
    "motivo_cassacao":TSEDataset(
        nome='motivo_cassacao',
        endpoint='motivo_cassacao',
        arquivo='{nome}_{ano}.zip'
    ),
    "votacao_candidato_municipio_zona":TSEDataset(
        nome='votacao_candidato_munzona',
        endpoint='votacao_candidato_munzona',
        arquivo='{nome}_{ano}.zip'
    )
}


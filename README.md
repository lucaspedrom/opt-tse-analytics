# TSE Ingestão 🗳️

O **TSE Ingestão** é um script utilitário em Python projetado para automatizar o download de dados públicos de estatísticas eleitorais diretamente dos servidores do Tribunal Superior Eleitoral (TSE) do Brasil. 

Este projeto serve como base para coleta de dados de candidaturas, bens de candidatos, coligações, motivos de cassação e votações por município e zona eleitoral.

> [!IMPORTANT]
> **Créditos e Atribuição:** O código original deste projeto foi desenvolvido por **Teo Calvo** no vídeo [TSE Analytics 2026 - Coletando Dados](https://www.youtube.com/watch?v=TNW990c3Vh4&t=2222s). Este repositório constitui uma implementação base para estudos e testes de otimização de performance.

[![TSE Analytics 2026 - Coletando Dados](https://img.youtube.com/vi/TNW990c3Vh4/hqdefault.jpg)](https://www.youtube.com/watch?v=TNW990c3Vh4&t=2222s)

---

## 📂 Estrutura do Projeto

O projeto foi estruturado em submódulos para melhorar a manutenção e a reutilização do código:

- [main.py](file:///d:/Projetos/tse-ingestao/main.py): Ponto de entrada do script que atua como Interface de Linha de Comando (CLI), interpretando argumentos fornecidos no terminal e inicializando o fluxo de downloads.
- [src/](file:///d:/Projetos/tse-ingestao/src): Diretório contendo a lógica interna do projeto:
  - [datasets.py](file:///d:/Projetos/tse-ingestao/src/datasets.py): Contém a classe [TSEDataset](file:///d:/Projetos/tse-ingestao/src/datasets.py#L7), que encapsula as configurações de cada conjunto de dados e constrói as URLs de download, além de definir o [DATASETS_CATALOG](file:///d:/Projetos/tse-ingestao/src/datasets.py#L23).
  - [downloader.py](file:///d:/Projetos/tse-ingestao/src/downloader.py): Contém a classe principal [DownloadTSE](file:///d:/Projetos/tse-ingestao/src/downloader.py#L14), responsável por realizar as requisições HTTP, gerenciar a criação das pastas e orquestrar os fluxos de download.

---

## 🛠️ Novas Funções e Módulos

### 1. Representação do Dataset: [datasets.py](file:///d:/Projetos/tse-ingestao/src/datasets.py)
Introduzimos a classe de dados imutável [TSEDataset](file:///d:/Projetos/tse-ingestao/src/datasets.py#L7) contendo os metadados necessários para mapear os endpoints do TSE:
* `endpoint`: Caminho relativo da categoria de dados no servidor do TSE.
* `nome`: Prefixo do arquivo a ser baixado (ex: `consulta_cand`).
* `arquivo_zip`: String template do arquivo compactado (`{nome}_{ano}.zip`).
* `arquivo_csv`: String template do arquivo CSV de interesse (`{nome}_{ano}_BRASIL.csv`).
* [build_url](file:///d:/Projetos/tse-ingestao/src/datasets.py#L13): Constrói a URL absoluta concatenando a URL base padrão com o endpoint específico do conjunto de dados e o ano desejado.
* [build_csv_filename](file:///d:/Projetos/tse-ingestao/src/datasets.py#L22): Retorna o nome formatado do arquivo CSV de interesse.

Também definimos o catálogo [DATASETS_CATALOG](file:///d:/Projetos/tse-ingestao/src/datasets.py#L31), com as bases disponíveis:
* `candidatos`
* `bens_candidatos`
* `coligacoes`
* `motivo_cassacao`
* `votacao_candidato_municipio_zona`

### 2. Otimização do Downloader: [downloader.py](file:///d:/Projetos/tse-ingestao/src/downloader.py)
A classe [DownloadTSE](file:///d:/Projetos/tse-ingestao/src/downloader.py#L14) foi otimizada e agora dispõe de novas funções:
* [ingest_dataset_year](file:///d:/Projetos/tse-ingestao/src/downloader.py#L22): Efetua o download do arquivo ZIP de forma temporária em um diretório temporário via streaming (chunks). Em seguida, extrai apenas o arquivo CSV de interesse (ex: `{nome}_{ano}_BRASIL.csv`) e o armazena no diretório de destino correspondente.
* [ingest_all_datasets](file:///d:/Projetos/tse-ingestao/src/downloader.py#L68): Itera em lote baixando **todas** as bases listadas no catálogo para a lista de anos informados, exibindo uma barra de progresso avançada no console (`rich.progress.Progress`).
* [ingest_one_dataset](file:///d:/Projetos/tse-ingestao/src/downloader.py#L85): Efetua o download focado em **apenas uma** base selecionada no catálogo para a lista de anos desejada.

---

## 📊 Disposição e Distribuição dos Dados

A disposição física dos arquivos baixados no disco foi alterada para simplificar o agrupamento, economizar armazenamento local (evitando reter arquivos ZIP completos e desnecessários) e facilitar o consumo posterior dos dados.

Agora, os arquivos ZIP são baixados em uma pasta temporária do sistema operacional, o arquivo de interesse contendo os dados consolidados do Brasil (ex: `*_BRASIL.csv`) é extraído, e o arquivo ZIP temporário é descartado. 

Com o novo modelo estruturado, os dados são distribuídos **por conjunto de dados/endpoint** diretamente em arquivos `.csv`. Isso significa que todos os arquivos `.csv` do mesmo tipo (independente do ano eleitoral) são agregados em uma mesma pasta específica.

A estrutura lógica do diretório resultante é mostrada abaixo:

```text
data/
├── bem_candidato/
│   ├── bem_candidato_2014_BRASIL.csv
│   ├── bem_candidato_2018_BRASIL.csv
│   └── bem_candidato_2022_BRASIL.csv
├── consulta_cand/
│   ├── consulta_cand_2014_BRASIL.csv
│   ├── consulta_cand_2018_BRASIL.csv
│   └── consulta_cand_2022_BRASIL.csv
├── consulta_coligacao/
│   └── ...
├── motivo_cassacao/
│   └── ...
└── votacao_candidato_munzona/
    ├── votacao_candidato_munzona_2014_BRASIL.csv
    └── ...
```

---

## 🚀 Como Executar Localmente

Siga as instruções abaixo para configurar o ambiente e executar a ingestão dos dados utilizando os novos parâmetros.

### Pré-requisitos
* **Python** 3.10 ou superior.
* Gerenciador de pacotes **[uv](https://github.com/astral-sh/uv)** instalado globalmente (recomendado para melhor performance).

### 1. Instalação e Configuração do Ambiente

Abra o terminal no diretório do projeto:
```powershell
# Cria o ambiente virtual
uv venv

# Ativa o ambiente virtual
# No Windows (PowerShell):
.venv\Scripts\Activate.ps1
# No Windows (CMD):
.venv\Scripts\activate.bat
# No Linux/macOS:
source .venv/bin/activate

# Instala a partir do requirements.txt
uv pip install -r requirements.txt
```

### 2. Parâmetros e Argumentos de CLI

O arquivo [main.py](file:///d:/Projetos/tse-ingestao/main.py) foi estendido para suportar a seleção flexível dos datasets via linha de comando:

```powershell
uv run main.py [argumentos]
```

#### Argumentos disponíveis:
* `-b`, `--base` (str): Define qual base de dados baixar. Opções válidas: `candidatos`, `bens_candidatos`, `coligacoes`, `motivo_cassacao`, `votacao_candidato_municipio_zona` ou `all` (padrão: `all`).
* `-i`, `--inicio` (int): Ano inicial do intervalo eleitoral (padrão: `2014`).
* `-f`, `--fim` (int): Ano final do intervalo eleitoral (padrão: `2022`).
* `--intervalo` (int): Passo em anos entre as eleições a serem consideradas no download (padrão: `2`).

#### Exemplos práticos de uso:

* **Download de todas as bases eleitorais de 2014 a 2022, a cada 2 anos:**
  ```powershell
  uv run main.py --base all --inicio 2014 --fim 2022 --intervalo 2
  ```

* **Download de apenas a base de bens declarados por candidatos de 4 em 4 anos (2014, 2018, 2022):**
  ```powershell
  uv run main.py --base bens_candidatos --inicio 2014 --fim 2022 --intervalo 4
  ```

* **Download apenas do resultado de votação por município e zona do ano de 2020:**
  ```powershell
  uv run main.py --base votacao_candidato_municipio_zona --inicio 2020 --fim 2020
  ```

---

## 📊 Evidências da Primeira Execução (Código Original de Referência)

Abaixo estão mantidos os registros e imagens das execuções originais em formato sequencial para servir de linha de base (baseline) comparativa de desempenho:

### 1. Execução do download sequencial para o ano 2022:
* **Tempo de Execução:** 5 minutos, 13 segundos e 2 décimos.  
* **Data de Execução:** 29/07/2026 21:19:13 (GMT -03:00)

![Download Ano 2022](md-images/execucao-download-2022.png)  
*Execução correspondente ao código original/baseline.*

![Detalhes Execução Ano 2022](md-images/detalhes-execucao-download-2022.png)  
*Detalhes do tempo de execução.*

### 2. Execução para os anos 2014, 2018 e 2022:
* **Tempo de Execução:** 13 minutos, 29 segundos.  
* **Data de Execução:** 29/07/2026 21:31:38 (GMT -03:00)

![Download Anos 2014, 2018 e 2022](md-images/execucao-download-2014_2018_2022.png)  
*Execução da função para os anos 2014, 2018 e 2022.*

![Detalhes Horário de Execução Anos 2014, 2018 e 2022](md-images/detalhes-execucao-download-2014_2018_2022.png)  
*Tempo de execução sequencial das três edições eleitorais.*
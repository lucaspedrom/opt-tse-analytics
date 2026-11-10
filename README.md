# TSE Ingestão 🗳️

O **TSE Ingestão** é um script utilitário em Python de alta performance projetado para automatizar o download, conversão em streaming e armazenamento eficiente de dados públicos de estatísticas eleitorais diretamente dos servidores do Tribunal Superior Eleitoral (TSE) do Brasil. 

Este projeto serve como base para coleta e engenharia de dados de candidaturas, bens de candidatos, coligações, motivos de cassação e votações por município e zona eleitoral.

> [!IMPORTANT]
> **Créditos e Atribuição:** O código original deste projeto foi desenvolvido por **Teo Calvo** no vídeo [TSE Analytics 2026 - Coletando Dados](https://www.youtube.com/watch?v=TNW990c3Vh4&t=2222s). Este repositório constitui uma implementação evoluída para estudos e testes de otimização de performance, eficiência de armazenamento e resiliência de pipelines.

[![TSE Analytics 2026 - Coletando Dados](https://img.youtube.com/vi/TNW990c3Vh4/hqdefault.jpg)](https://www.youtube.com/watch?v=TNW990c3Vh4&t=2222s)

---

## 📂 Estrutura do Projeto

O projeto foi estruturado em submódulos desacoplados para garantir facilidade de manutenção, testabilidade e baixo consumo de recursos:

- [pyproject.toml](file:///d:/Projetos/tse-ingestao/pyproject.toml): Configuração padronizada do projeto conforme a **PEP 621**, gerenciando dependências e ambiente via `uv`.
- [main.py](file:///d:/Projetos/tse-ingestao/main.py): Ponto de entrada do script que atua como Interface de Linha de Comando (CLI), interpretando argumentos fornecidos no terminal e inicializando o fluxo de downloads.
- [src/](file:///d:/Projetos/tse-ingestao/src): Diretório contendo os módulos centrais da aplicação:
  - [datasets.py](file:///d:/Projetos/tse-ingestao/src/datasets.py): Contém a classe [TSEDataset](file:///d:/Projetos/tse-ingestao/src/datasets.py#L8), que mapeia os endpoints do TSE, constrói as URLs de download e define as regras de particionamento Hive, além de fornecer o catálogo [DATASETS_CATALOG](file:///d:/Projetos/tse-ingestao/src/datasets.py#L37).
  - [converter.py](file:///d:/Projetos/tse-ingestao/src/converter.py): Motor de conversão colunar em streaming via `pyarrow`. Lê o arquivo CSV comprimido diretamente do stream do arquivo ZIP em blocos e grava em formato Parquet incrementalmente, mantendo o consumo de memória fixo e sem gravar arquivos intermediários no disco.
  - [downloader.py](file:///d:/Projetos/tse-ingestao/src/downloader.py): Contém a classe principal [DownloadTSE](file:///d:/Projetos/tse-ingestao/src/downloader.py#L30), responsável por requisições HTTP persistentes com connection pooling, retentativas com backoff exponencial, verificação de integridade de arquivos e orquestração concorrente de downloads e conversões.
  - [console.py](file:///d:/Projetos/tse-ingestao/src/console.py): Configuração da instância compartilhada do console `rich` para exibição de logs e barras de progresso.

---

## 🛠️ Módulos e Funcionalidades

### 1. Representação do Dataset: [datasets.py](file:///d:/Projetos/tse-ingestao/src/datasets.py)
A classe de dados imutável [TSEDataset](file:///d:/Projetos/tse-ingestao/src/datasets.py#L8) encapsula os metadados necessários para mapear os endpoints do TSE:
* `endpoint`: Caminho relativo da categoria de dados no servidor do TSE.
* `nome`: Prefixo do arquivo a ser baixado (ex: `consulta_cand`).
* `arquivo_zip`: Template do arquivo compactado no servidor (`{nome}_{ano}.zip`).
* `arquivo_csv`: Template do arquivo CSV de interesse interno do ZIP (`{nome}_{ano}_BRASIL.csv`).
* [build_url](file:///d:/Projetos/tse-ingestao/src/datasets.py#L16): Constrói a URL absoluta concatenando a URL base padrão com o endpoint específico do conjunto de dados e o ano desejado.
* [build_csv_filename](file:///d:/Projetos/tse-ingestao/src/datasets.py#L26): Retorna o nome formatado do arquivo CSV consolidado nacional esperado dentro do ZIP.
* [build_parquet_filename](file:///d:/Projetos/tse-ingestao/src/datasets.py#L30): Gera o caminho de saída com **particionamento no padrão Hive** (`<base_dir>/<endpoint>/ano=<ano>/dados.parquet`).

Catálogo disponível em [DATASETS_CATALOG](file:///d:/Projetos/tse-ingestao/src/datasets.py#L37):
* `candidatos` (peso 300)
* `bens_candidatos` (peso 250)
* `coligacoes` (peso 50)
* `motivo_cassacao` (peso 5)
* `votacao_candidato_municipio_zona` (peso 1000)

### 2. Motor de Streaming e Conversão: [converter.py](file:///d:/Projetos/tse-ingestao/src/converter.py)
* [stream_csv_stream_to_parquet](file:///d:/Projetos/tse-ingestao/src/converter.py#L12): Consome o stream binário de um CSV em lotes (*chunks* de 10 MB) via `pyarrow.csv.open_csv` e grava incrementalmente em Parquet usando `pyarrow.parquet.ParquetWriter`.
* [convert_zip_to_parquet](file:///d:/Projetos/tse-ingestao/src/converter.py#L62): Localiza o CSV de interesse dentro do arquivo ZIP e alimenta o stream diretamente para a conversão sem descompactar o arquivo no disco rígido.

### 3. Orquestrador de Download: [downloader.py](file:///d:/Projetos/tse-ingestao/src/downloader.py)
* [ingest_dataset_year](file:///d:/Projetos/tse-ingestao/src/downloader.py#L35): Realiza o download seguro do ZIP temporário em blocos com retentativas, valida o tamanho do download contra o cabeçalho `Content-Length`, dispara a conversão em streaming para Parquet e remove o ZIP temporário imediatamente.
* [_execute_batch_download](file:///d:/Projetos/tse-ingestao/src/downloader.py#L164): Orquestra a execução concorrente em `ThreadPoolExecutor` com estratégia de retry na sessão HTTP e barras de progresso reativas via `rich.progress`.

---

## ⚡ Técnicas de Otimização e Engenharia de Dados Implementadas

* **Consumo de Memória Constante ($O(1)$):**
  Ao processar arquivos de mais de 4 GB (como a base de votação por zona eleitoral), a leitura é realizada em blocos de 10 MB. Cada lote é escrito no Parquet e liberado da RAM imediatamente. Isso permite que o pipeline rode com total estabilidade até mesmo em máquinas virtuais ou instâncias com **menos de 1 GB de RAM**.
* **Zero Escrita de CSV em Disco (Zero Disk Overhead):**
  O arquivo CSV descompactado **nunca é gravado no disco rígido**. A leitura é feita via *streaming* diretamente do arquivo ZIP em memória para os *batches* do PyArrow, poupando gigabytes de I/O em disco e evitando desgaste de SSDs.
* **Redução Drástica de Armazenamento (>90% de compressão):**
  Armazenamento no formato colunar **Apache Parquet com compressão ZSTD**. O *Dictionary Encoding* nativo do Parquet indexa termos textuais repetidos (como nomes de estados, partidos e cargos), reduzindo arquivos de 4 GB para menos de 400 MB.
* **Resiliência a Mudanças de Schema (String Typing na Camada Raw):**
  Todas as colunas são convertidas como `string` na extração (`default_column_type = pa.string()`). Isso previne falhas de inferência de tipo causadas por valores sentinelas do TSE (`#NULO#`, `#NE#`, `-1`, `-3`), mudanças de layout entre anos ou códigos com zeros à esquerda (como números de títulos e zonas).
* **Particionamento em Diretórios (Padrão Hive):**
  Os arquivos são organizados na estrutura `ano=YYYY/dados.parquet`. Esse formato permite que motores analíticos modernos realizem **Partition Discovery** (injetando a coluna de ano automaticamente) e **Partition Pruning** (carregando apenas a pasta do ano desejado sem ler a base inteira).
* **Retentativas com Backoff Exponencial e Validação de Integridade:**
  O download implementa até 3 tentativas automáticas com tempo de espera incremental (`backoff_factor * 2^(tentativa-1)`) e checa se o tamanho do arquivo em disco coincide com o `Content-Length` do servidor antes de aprovar o arquivo para conversão.
* **Concorrência Sobreposta (I/O Bound + CPU Bound):**
  Como as operações em C++ do PyArrow liberam a trava de execução do Python (GIL), enquanto uma *thread* aguarda pacotes de rede do download, outra *thread* que já baixou o arquivo processa a conversão para Parquet em paralelo.

---

## 📊 Estrutura e Distribuição dos Dados no Disco

Com o particionamento Hive, os dados ficam estruturados da seguinte forma:

```text
data/
├── bem_candidato/
│   ├── ano=2014/
│   │   └── dados.parquet
│   ├── ano=2018/
│   │   └── dados.parquet
│   └── ano=2022/
│       └── dados.parquet
├── consulta_cand/
│   ├── ano=2014/
│   │   └── dados.parquet
│   └── ...
├── motivo_cassacao/
│   ├── ano=2014/
│   │   └── dados.parquet
│   ├── ano=2018/
│   │   └── dados.parquet
│   └── ano=2022/
│       └── dados.parquet
└── votacao_candidato_munzona/
    ├── ano=2014/
    │   └── dados.parquet
    ├── ano=2018/
    │   └── dados.parquet
    └── ano=2022/
        └── dados.parquet
```

---

## 🚀 Como Executar Localmente

### Pré-requisitos
* **Python** 3.13 ou superior.
* Gerenciador de pacotes **[uv](https://github.com/astral-sh/uv)** (recomendado).

### 1. Configuração do Ambiente

Abra o terminal na raiz do projeto:

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

# Instala as dependências sincronizando com o pyproject.toml
uv sync
```

### 2. Parâmetros e Argumentos de CLI

O arquivo [main.py](file:///d:/Projetos/tse-ingestao/main.py) permite selecionar as bases e os anos desejados:

```powershell
uv run main.py [argumentos]
```

#### Argumentos disponíveis:
* `-b`, `--base` (str): Base de dados a ser baixada. Opções: `candidatos`, `bens_candidatos`, `coligacoes`, `motivo_cassacao`, `votacao_candidato_municipio_zona` ou `all` (padrão: `all`).
* `-i`, `--inicio` (int): Ano inicial da coleta (padrão: `2014`).
* `-f`, `--fim` (int): Ano final da coleta (padrão: `2022`).
* `--intervalo` (int): Intervalo em anos entre eleições (padrão: `2`).

#### Exemplos práticos:

* **Download de todas as bases de 2014 a 2024, de 2 em 2 anos:**
  ```powershell
  uv run main.py --base all --inicio 2014 --fim 2024 --intervalo 2
  ```

* **Download focado em bens de candidatos (2014, 2018 e 2022):**
  ```powershell
  uv run main.py --base bens_candidatos --inicio 2014 --fim 2022 --intervalo 4
  ```

* **Download rápido para teste (motivo de cassação de 2022):**
  ```powershell
  uv run main.py --base motivo_cassacao --inicio 2022 --fim 2022
  ```

---

## 🔍 Como Consumir os Dados Particionados

Uma das grandes vantagens da estrutura gerada é a simplicidade e a performance de leitura nos principais ecossistemas de análise:

### Com Polars (Lazy Evaluation com Leitura Rápida):
```python
import polars as pl

# Lê todas as partições descobrindo a coluna 'ano' automaticamente
df = pl.scan_parquet("data/motivo_cassacao/**/*.parquet")

# Filtra apenas o ano desejado sem ler os demais arquivos do disco
dados_2022 = df.filter(pl.col("ano") == "2022").collect()
print(dados_2022.head())
```

### Com Pandas:
```python
import pandas as pd

# Lê toda a pasta particionada com Hive Partitioning automático
df = pd.read_parquet("data/motivo_cassacao")
print(df.head())
```

### Com PyArrow Dataset:
```python
import pyarrow.dataset as ds

dataset = ds.dataset("data/motivo_cassacao", format="parquet", partitioning="hive")
tabela = dataset.to_table(filter=ds.field("ano") == "2022")
print(tabela.num_rows)
```

---

## 📊 Evidências de Desempenho e Histórico

### Execuções Históricas (Baseline Original):
* **Ano 2022 (Sequencial original):** 5 minutos, 13 segundos (29/07/2026).
* **Anos 2014, 2018 e 2022 (Sequencial original):** 13 minutos, 29 segundos (29/07/2026).
* **Otimização Concorrente HTTP (09/11/2026):** 39 segundos para 3 anos de `motivo_cassacao`.
* **Versão Atual (Novembro/2026):** Ingestão completa com streaming direto para Parquet ZSTD particionado em Hive, sem salvar CSVs intermediários e garantindo pegada de memória fixa ($< 150\text{ MB}$).

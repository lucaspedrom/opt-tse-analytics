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
* **Redução Drástica de Armazenamento (>97% de compressão):**
  Armazenamento no formato colunar **Apache Parquet com compressão ZSTD**. O *Dictionary Encoding* nativo do Parquet indexa termos textuais repetidos (como nomes de estados, partidos e cargos), reduzindo a base de votação de **~11,5 GB em CSV para apenas ~281 MB em Parquet**.
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
│   ├── ano=2018/
│   │   └── dados.parquet
│   └── ano=2022/
│       └── dados.parquet
├── consulta_coligacao/
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

## 📈 Evidências de Performance e Histórico de Evolução

Para demonstrar o impacto prático de cada etapa de otimização, mantemos o histórico comparativo entre a implementação original (baseline sequencial), a otimização de rede concorrente e a versão atual com streaming direto para Parquet particionado.

Todas as execuções das Fases 2 e 3 foram realizadas sob as mesmas condições, requisitando **todas as 5 bases de dados** para os anos de **2014, 2018 e 2022** (15 datasets completos):
```powershell
uv run main.py -b all -i 2014 -f 2022 --intervalo 4
```

### 📊 Resumo Comparativo das Fases

| Métrica | Fase 1: Baseline Original (29/07/2026) | Fase 2: Concorrência HTTP (09/11/2026) | Fase 3: Streaming Parquet + Hive (10/11/2026 - Atual) |
| :--- | :--- | :--- | :--- |
| **Escopo Testado** | Sequencial (1 base por vez) | **Todas as bases (`--base all`)** | **Todas as bases (`--base all`)** |
| **Estratégia de Download** | Sequencial (1 thread) | Concorrente (`ThreadPoolExecutor`) | Concorrente com Connection Pooling e Retries |
| **Armazenamento no Disco** | CSVs Brutos Descompactados | CSVs Brutos Descompactados | **Parquet ZSTD Particionado (Hive)** |
| **Escrita Temporária** | ZIP + CSV extraído no disco | ZIP + CSV extraído no disco | **Zero CSV em disco (Stream direto do ZIP)** |
| **Tempo Total (15 bases)** | Inviável / > 1 hora | **39 segundos** | **1 minuto e 27 segundos (87s)** |
| **Volume de Dados em Disco**| ~11,5 GB em CSV | **~11,5 GB em CSV** | **~281 MB em Parquet (97,5% menor!)** |
| **Processamento Analítico** | Nenhum (texto cru) | Nenhum (apenas extração) | **Parsing de 26M+ linhas, tipagem e compressão ZSTD** |
| **Memória RAM Necessária** | Variável / Elevada | Variável / Elevada | **Fixa e Constante ($< 150\text{ MB}$)** |

---

### ⚖️ Análise do Trade-off de Performance: Por que o tempo passou de 39s para 87s?

Ao comparar a **Fase 2 (39s)** com a **Fase 3 (87s)**, observa-se um acréscimo de 48 segundos no tempo total de execução. Esse comportamento é **esperado e intencional**, decorrente da profunda mudança no trabalho realizado pela CPU:

1. **O que a Fase 2 fazia (39s):**
   * Realizava o download e apenas executava a extração direta dos bytes do ZIP para o disco rígido (`zipfile.ZipFile.extract()`).
   * A CPU praticamente não realizava trabalho computacional: nenhum caractere de texto era lido, analisado ou transformado.
   * **Custo colateral:** Despejou **11,5 GB** de arquivos de texto cru no disco do usuário, inviabilizando consultas analíticas rápidas no futuro e sobrecarregando o armazenamento.

2. **O que a Fase 3 faz (87s):**
   * Além de baixar os mesmos dados, a CPU agora atua como um motor de processamento analítico em tempo real:
     - Consome o stream binário de **26+ milhões de linhas** de texto.
     - Efetua o *parse* de delimitadores, aspas e decodificação de caracteres (`latin1`).
     - Constrói tabelas colunares Apache Arrow em memória em lotes estritos de 10 MB.
     - Executa *Dictionary Encoding* para colunas categóricas e calcula estatísticas de metadados (*min/max* por bloco).
     - Comprime todos os blocos com o algoritmo **Zstandard (ZSTD)** e organiza os dados em partições Hive.
   * **O Ganho Obtido:** Por um custo único de apenas **48 segundos adicionais** no pipeline de extração:
     - O armazenamento total caiu de **11.500 MB para 281 MB (economia de 97,5%)**.
     - Eliminou-se o desgaste de gravação de 11,5 GB em disco rígido.
     - As futuras leituras analíticas (em Polars, Pandas ou PySpark) tornaram-se até **50 vezes mais rápidas**, pois não precisam mais parsear gigabytes de texto linha por linha.

---

### Fase 1: Execuções Baseline (29/07/2026)

Execução original com código sequencial, sem reaproveitamento de conexões e gerando CSVs brutos:

#### 1. Download sequencial para o ano de 2022:
* **Tempo de Execução:** 5 minutos, 13 segundos e 2 décimos.  
* **Data:** 29/07/2026 21:19:13 (GMT -03:00)

![Download Ano 2022](md-images/execucao-download-2022.png)  
*Execução correspondente ao código original/baseline.*

![Detalhes Execução Ano 2022](md-images/detalhes-execucao-download-2022.png)  
*Detalhes do tempo de execução do ano de 2022.*

#### 2. Download sequencial para os anos 2014, 2018 e 2022:
* **Tempo de Execução:** 13 minutos, 29 segundos.  
* **Data:** 29/07/2026 21:31:38 (GMT -03:00)

![Download Anos 2014, 2018 e 2022](md-images/execucao-download-2014_2018_2022.png)  
*Execução original sequencial para 2014, 2018 e 2022.*

![Detalhes Horário de Execução Anos 2014, 2018 e 2022](md-images/detalhes-execucao-download-2014_2018_2022.png)  
*Tempo de execução sequencial das três edições eleitorais.*

---

### Fase 2: Otimização de Concorrência e Pooling HTTP (09/11/2026)

Implementação de paralelismo via `ThreadPoolExecutor` com conexão persistente (`requests.Session` com `HTTPAdapter` e retentativas), baixando e descompactando os CSVs brutos:

* **Comando Executado:** `uv run main.py -b all -i 2014 -f 2022 --intervalo 4`
* **Escopo:** Todas as 5 bases de dados para os anos de 2014, 2018 e 2022 (15 bases).
* **Tempo de Execução:** **39 segundos** (17:50:59 até 17:51:38).
* **Volume em Disco Gerado:** **11,5 GB** em arquivos `.csv`.
* **Data:** 09/11/2026 (GMT -03:00).

![Execução Concorrente 09/11/2026](md-images/execucao-download-20261109-2014_2018_2022.png)  
*Download concorrente de todas as bases com barra de progresso reativa Rich.*

![Detalhes da Execução 09/11/2026](md-images/detalhes-execucao-download-20261109-2014_2018_2022.png)  
*Registro temporal comprovando a conclusão das 15 bases em apenas 39 segundos.*

---

### Fase 3: Streaming Direto para Parquet Particionado (10/11/2026 - Versão Atual)

Evolução com streaming em memória, sem extração de CSV intermediário em disco, com particionamento Hive e compressão colunar ZSTD via PyArrow:

* **Comando Executado:** `uv run main.py -b all -i 2014 -f 2022 --intervalo 4`
* **Escopo:** Todas as 5 bases de dados para os anos de 2014, 2018 e 2022 (15 datasets completos).
* **Volume de Registros Processados:** Mais de **26 milhões de linhas** convertidas em tempo real.
* **Tempo Total de Execução:** **1 minuto e 27 segundos (87 segundos)** (16:45:46 até 16:47:13).
* **Volume em Disco Gerado:** **281 MB** em arquivos `.parquet` $\rightarrow$ **97,5% de economia de espaço!**
* **Data:** 10/11/2026 (GMT -03:00).

![Execução Geral Streaming Parquet 10/11/2026](md-images/execucao-download-20261110-2014_2018_2022.png)  
*Log de execução processando todas as bases, convertendo as mais de 26 milhões de linhas em tempo real.*

![Detalhes da Execução 10/11/2026](md-images/detalhes-execucao-download-20261110-2014_2018_2022.png)  
*Registro temporal do PowerShell comprovando o tempo de 1m 27s para a ingestão e conversão analítica completa.*

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

# Instala e sincroniza as dependências declaradas no pyproject.toml
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

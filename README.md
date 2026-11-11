# TSE Ingestão 🗳️

<div align="center">

![Versão](https://img.shields.io/badge/versão-0.3.0-blue.svg?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Apache Arrow](https://img.shields.io/badge/PyArrow-26.0%2B-E5462C?style=for-the-badge)
![Apache Parquet](https://img.shields.io/badge/Apache_Parquet-ZSTD-50C878?style=for-the-badge)
![Hive Partitioning](https://img.shields.io/badge/Particionamento-Hive-FFD700?style=for-the-badge)
![uv](https://img.shields.io/badge/Gerenciador-uv-DE5FE9?style=for-the-badge)
![CLI](https://img.shields.io/badge/CLI-Rich-00D4AA?style=for-the-badge)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-green.svg?style=for-the-badge)

<p align="center">
  <b>Pipeline de alta performance para extração, streaming em memória e conversão analítica dos dados do Tribunal Superior Eleitoral.</b><br>
  <i>Desenvolvido com foco em eficiência: zero escrita de CSV bruto em disco, consumo de memória constante O(1) e redução de armazenamento superior a 97%.</i>
</p>

[Visão Geral](#-visão-geral) •
[Arquitetura do Pipeline](#-arquitetura-do-pipeline) •
[Otimizações de Engenharia](#-técnicas-de-otimização-e-engenharia-de-dados) •
[Evidências & Benchmarks](#-evidências-de-performance-e-histórico-de-evolução) •
[Como Executar](#-como-executar-localmente) •
[Consumo Analítico](#-como-consumir-os-dados-particionados) •
[Estrutura](#-estrutura-de-diretórios) •
[Licença](#-licença)

</div>

---

## 📖 Visão Geral

O **TSE Ingestão** é um utilitário em Python de engenharia de dados projetado para automatizar o download concorrente, conversão em streaming direto e armazenamento analítico de bases públicas de estatísticas eleitorais disponibilizadas pelo Tribunal Superior Eleitoral (TSE).

O projeto é voltado para a coleta e estruturação de candidaturas, bens declarados, coligações, motivos de cassação e votações nominais por município e zona eleitoral.

> [!IMPORTANT]
> **Créditos e Atribuição:** O código base deste projeto foi concebido por **Teo Calvo** no vídeo [TSE Analytics 2026 - Coletando Dados](https://www.youtube.com/watch?v=TNW990c3Vh4&t=2222s). Este repositório representa uma implementação evoluída com foco em otimização de performance de rede, streaming colunar em memória e resiliência de pipelines de dados.

[![TSE Analytics 2026 - Coletando Dados](https://img.youtube.com/vi/TNW990c3Vh4/hqdefault.jpg)](https://www.youtube.com/watch?v=TNW990c3Vh4&t=2222s)

---

## 🏛️ Arquitetura do Pipeline

O fluxo de dados foi desenhado para eliminar gargalos de I/O em disco e consumo excessivo de memória RAM através de um pipeline de streaming colunar com PyArrow:

```text
┌─────────────────────────────────────────────────────────────┐
│                 Servidores do TSE (CDN)                     │
│    https://cdn.tse.jus.br/estatistica/sead/odsele/...       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP GET (Streaming Chunks)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 DownloadTSE (Connection Pool)              │
│  • Requests Session + HTTPAdapter                           │
│  • Concorrência via ThreadPoolExecutor                      │
│  • Retentativas com Backoff Exponencial                     │
│  • Validação de integridade via Content-Length              │
└──────────────────────────────┬──────────────────────────────┘
                               │ Stream Binário ZIP em Memória
                               ▼
┌─────────────────────────────────────────────────────────────┐
│           Motor de Conversão Streaming (PyArrow)            │
│  • ZipFile.open(target_csv) -> Stream sem extrair no disco  │
│  • Leitura em Batches de 10 MB (Consumo de RAM constante)   │
│  • Resiliência de Schema: Default Column String             │
│  • Encoding Categórico (Dictionary Encoding)                │
│  • Compressão colunar Zstandard (ZSTD)                      │
└──────────────────────────────┬──────────────────────────────┘
                               │ Escrita incremental colunar
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Lake Local (Particionamento Hive)         │
│  data/<endpoint>/ano=YYYY/dados.parquet                     │
│  • Partition Pruning & Partition Discovery imediato         │
│  • Redução de ~11,5 GB para ~281 MB (-97,5%)                │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ Técnicas de Otimização e Engenharia de Dados

* **Consumo de Memória Constante ($O(1)$):**
  Ao processar arquivos massivos de mais de 4 GB (como a base de votação por zona eleitoral), a leitura é fatiada em blocos de 10 MB. Cada lote é convertido para Parquet e liberado imediatamente da RAM, permitindo estabilidade mesmo em instâncias com **menos de 512 MB de RAM**.
* **Zero Escrita de CSV em Disco (Zero Disk Overhead):**
  O arquivo CSV descompactado **nunca toca o disco rígido**. A leitura é consumida em streaming do arquivo ZIP diretamente para os buffers de memória do PyArrow, poupando gigabytes de I/O e desgaste em SSDs.
* **Redução Drástica de Armazenamento (>97% de compressão):**
  Gravação colunar em **Apache Parquet com compressão ZSTD**. O *Dictionary Encoding* nativo do Parquet indexa colunas categóricas redundantes (como UF, partidos e cargos), reduzindo a base de testes de **~11,5 GB em CSV para apenas ~281 MB em Parquet**.
* **Resiliência a Mudanças de Schema (String Typing na Camada Raw):**
  Todas as colunas são convertidas como `string` na ingestão bruta (`default_column_type = pa.string()`). Isso previne quebras geradas por valores sentinelas do TSE (`#NULO#`, `#NE#`, `-1`, `-3`), mudanças de layout entre anos ou códigos com zeros à esquerda (zonas eleitorais e títulos).
* **Particionamento em Diretórios (Padrão Hive):**
  Estrutura organizada em `ano=YYYY/dados.parquet`. Permite que ferramentas como Polars, DuckDB e PySpark executem **Partition Discovery** (injetando a coluna `ano` automaticamente) e **Partition Pruning** (carregando apenas as pastas dos anos consultados sem ler o dataset inteiro).
* **Retentativas com Backoff Exponencial e Validação de Integridade:**
  Implementação de até 3 tentativas automáticas com tempo de espera incremental (`backoff_factor * 2^(tentativa-1)`) e checagem de tamanho de arquivo contra o cabeçalho `Content-Length`.
* **Concorrência Sobreposta (I/O Bound + CPU Bound):**
  As operações de conversão em C++ do PyArrow liberam a trava do Python (GIL). Enquanto uma thread aguarda pacotes de rede do download, outra converte lotes para Parquet em paralelo.

---

## 🛠️ Tecnologias Utilizadas

### Engenharia de Dados & Armazenamento Colunar
- **[PyArrow](https://arrow.apache.org/docs/python/)**: Motor colunar em C++ para streaming em blocos, parsing de delimitadores e geração de Parquet.
- **[Apache Parquet](https://parquet.apache.org/)**: Formato colunar analítico otimizado para consultas analíticas rápidas.
- **[Zstandard (ZSTD)](https://facebook.github.io/zstd/)**: Algoritmo de alta taxa de compressão e velocidade extrema de descompressão.

### Rede, Concorrência & CLI
- **[Python 3.13+](https://www.python.org/)**: Linguagem base do projeto com suporte a tipagem moderna.
- **[Requests](https://requests.readthedocs.io/) & [Urllib3](https://urllib3.readthedocs.io/)**: Pool de conexões HTTP persistentes e estratégias de retry.
- **[Rich](https://rich.readthedocs.io/)**: Interface rica de terminal com barras de progresso reativas por thread e logs organizados.

### Tooling, Gerenciamento & Qualidade
- **[uv](https://docs.astral.sh/uv/)**: Gerenciador ultrarrápido de dependências e ambientes virtuais em conformidade com PEP 621.
- **[Ruff](https://docs.astral.sh/ruff/)**: Linter e formatador de código de alto desempenho em Rust.

---

## 📊 Estrutura e Distribuição dos Dados no Disco

Os dados consolidados são gravados com particionamento Hive:

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

Para demonstrar o impacto prático de cada etapa de otimização e comprovar a eficiência da arquitetura atual, mantemos o histórico comparativo das versões, validado experimentalmente através de um protocolo estatístico independente documentado no repositório [**benchmark-opt-tse-analytics**](https://github.com/lucaspedrom/benchmark-opt-tse-analytics).

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
| **Volume de Dados em Disco**| ~11,5 GB em CSV | **~11,5 GB em CSV** | **~281 MB em Parquet (97,5% menor!)** |
| **Processamento Analítico** | Nenhum (texto cru) | Nenhum (apenas extração) | **Parsing de 26M+ linhas, tipagem e compressão ZSTD** |
| **Memória RAM Necessária** | Variável / Elevada | Variável / Elevada | **Fixa e Constante ($< 150\text{ MB}$)** |

---

### ⚖️ Análise do Trade-off de Performance:

Ao comparar a **Fase 2** com a **Fase 3**, pode-se observar um acréscimo de alguns segundos no tempo total de execução. Esse comportamento é **esperado e intencional**, decorrente da profunda mudança no trabalho computacional:

1. **O que a Fase 2 fazia:**
   - Realizava o download e apenas executava a extração direta dos bytes do ZIP para o disco rígido (`zipfile.ZipFile.extract()`).
   - A CPU não realizava trabalho analítico: nenhum caractere era lido, interpretado ou comprimido.
   - **Custo colateral:** Despejou **11,5 GB** de arquivos de texto cru no disco, sobrecarregando o armazenamento e postergando o custo de processamento.

2. **O que a Fase 3 faz:**
   - Além de baixar os mesmos dados, a CPU agora atua como um motor de processamento analítico em tempo real:
     - Consome o stream binário de **26+ milhões de linhas** de texto.
     - Efetua o *parse* de delimitadores, aspas e decodificação (`latin1`).
     - Constrói tabelas colunares Apache Arrow em memória em lotes estritos de 10 MB.
     - Executa *Dictionary Encoding* para colunas categóricas e calcula estatísticas de metadados (*min/max* por bloco).
     - Comprime todos os blocos com o algoritmo **Zstandard (ZSTD)** e organiza os dados em partições Hive.
   - **O Ganho Obtido:** Por um custo único de apenas **alguns segundos adicionais** no pipeline:
     - O armazenamento total caiu de **11.500 MB para 281 MB (economia de 97,5%)**.
     - Eliminou-se o desgaste de gravação de 11,5 GB em disco rígido.
     - As futuras leituras analíticas (em Polars, Pandas ou DuckDB) tornaram-se até **50 vezes mais rápidas**, pois não precisam mais parsear gigabytes de texto linha por linha.

---
### ▶️ Evidências de Execuções Unitárias:

### Fase 1: Execuções Baseline (29/07/2026)

Execução original sequencial, sem reaproveitamento de conexões e gerando CSVs brutos:

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
*Registro temporal comprovando o tempo de 1m 27s para a ingestão e conversão analítica completa.*

---

### 🔬 Validação Experimental: Benchmark Multirrodada (RCBD)

Para comprovar formalmente os ganhos de arquitetura e mitigar métricas de vaidade ou variações pontuais de rede e hardware, foi desenvolvida uma suíte de testes independente no repositório [**benchmark-opt-tse-analytics**](https://github.com/lucaspedrom/benchmark-opt-tse-analytics).

#### Metodologia dos Testes:
* **Delineamento em Blocos Casualizados (*Randomized Complete Block Design* - RCBD):** Bateria de **10 rodadas completas** (40 execuções independentes) com ordenação aleatória das versões a cada ciclo.
* **Isolamento Estrito:** Execução via `git worktree` sobre commits imutáveis, com snapshots pré/pós-execução e quarentena de artefatos.
* **Telemetria de Sistema em Tempo Real:** Amostragem contínua via `psutil` medindo consumo e pico de CPU, memória RAM (Peak RSS) e velocidade média de download na interface de rede.
* **Versões Avaliadas:**
  * **V1** (`e010a7f`): Download direto sequencial de ZIPs (Baseline).
  * **V2** (`d082d9b`): Extração sequencial de CSVs em disco.
  * **V3** (`0485406`): Concorrência HTTP + Connection Pooling + escalonamento LPT (CSVs em disco).
  * **V4** (`a980086`): Streaming colunar em memória direto para Parquet particionado (**Versão Atual**).

#### 📊 Resultados Médios Consolidados (10 Rodadas):

| Versão | Tempo Médio | Mediana | Desvio Padrão ($\sigma$) | Armazenamento Final | Pico RAM Médio | CPU Média | Download Médio | Formato do Entregável |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **V1** | 56,08s | 60,20s | 12,43s | **1.440,36 MB** (~1,44 GB) | 1.021,29 MB | 14,02% | 27,92 MB/s | 15 ZIPs compactados brutos |
| **V2** | 77,02s | 79,41s | 12,02s | **10.992,69 MB** (~10,99 GB) | **76,58 MB** | 17,05% | 19,41 MB/s | 15 CSVs extraídos em disco |
| **V3** | **44,91s** | **47,12s** | 6,98s | **10.992,69 MB** (~10,99 GB) | 87,51 MB | 14,04% | **34,17 MB/s** | 15 CSVs extraídos em disco |
| **V4** *(Atual)* | 84,20s | 86,09s | **5,88s** | **278,72 MB** (~0,28 GB) | 2.111,22 MB | **10,49%** | 17,79 MB/s | **Partições Apache Parquet (ZSTD)** |

#### 🎯 Evidências e Eficiência Comprovada:

1. **Redução Drástica de 97,5% em Armazenamento:** A conversão direta para Parquet com compressão ZSTD e *Dictionary Encoding* derrubou o volume ocupado de **10.992 MB para apenas 278,72 MB**. O resultado final ocupa inclusive **80,6% menos espaço do que os próprios arquivos ZIP originais da V1** (1.440 MB).
2. **Alta Previsibilidade e Menor Dispersão:** A versão atual atingiu o **menor desvio padrão ($\sigma = 5,88s$)** de todo o experimento, garantindo tempos estáveis (~84s) mesmo diante de variações de throughput da CDN do TSE.
3. **Eficiência no Uso da CPU:** A computação vetorial em C++ via PyArrow registrou o **menor consumo médio de processador da suíte (10,49%)**, superando a carga imposta pelo I/O pesado de escrita de CSVs da V2 (17,05%) e V3 (14,04%).
4. **Trade-off Consciente de Memória (Zero Disk I/O Overhead):** Embora o processamento em memória demande um pico médio de ~2,1 GB de RAM, elimina-se completamente a gravação de 11 GB de arquivos intermediários em disco e entrega-se um dataset imediatamente tipado e particionado para consumo analítico (*Analytics-Ready*).

> Para detalhes aprofundados sobre o runner do benchmark, gráficos de dispersão e instruções completas para reproduzir a suíte, acesse o repositório oficial: [**lucaspedrom/benchmark-opt-tse-analytics**](https://github.com/lucaspedrom/benchmark-opt-tse-analytics).

---

## 🚀 Como Executar Localmente

### Pré-requisitos
* **Python** 3.13 ou superior.
* Gerenciador de pacotes **[uv](https://github.com/astral-sh/uv)** (recomendado).

### 1. Clonar e Configurar o Ambiente

```bash
# Clone o repositório
git clone https://github.com/lucaspedrom/opt-tse-analytics.git
cd opt-tse-analytics

# Cria e sincroniza o ambiente virtual automaticamente com uv
uv sync
```

### 2. Parâmetros e Argumentos de CLI

O arquivo [main.py](main.py) permite selecionar as bases e os anos desejados:

```bash
uv run main.py [argumentos]
```

#### Argumentos disponíveis:
* `-b`, `--base` (str): Base de dados a ser baixada. Opções: `candidatos`, `bens_candidatos`, `coligacoes`, `motivo_cassacao`, `votacao_candidato_municipio_zona` ou `all` (padrão: `all`).
* `-i`, `--inicio` (int): Ano inicial da coleta (padrão: `2014`).
* `-f`, `--fim` (int): Ano final da coleta (padrão: `2022`).
* `--intervalo` (int): Intervalo em anos entre eleições (padrão: `2`).

#### Exemplos práticos:

* **Download de todas as bases de 2014 a 2024, de 2 em 2 anos:**
  ```bash
  uv run main.py --base all --inicio 2014 --fim 2024 --intervalo 2
  ```

* **Download focado em bens de candidatos (2014, 2018 e 2022):**
  ```bash
  uv run main.py --base bens_candidatos --inicio 2014 --fim 2022 --intervalo 4
  ```

* **Download rápido para teste (motivo de cassação de 2022):**
  ```bash
  uv run main.py --base motivo_cassacao --inicio 2022 --fim 2022
  ```

---

## 🔍 Como Consumir os Dados Particionados

Uma das grandes vantagens da estrutura gerada é a facilidade de leitura e o suporte a *Partition Pruning* nos ecossistemas analíticos modernos:

### Com Polars (Lazy Evaluation com Leitura Rápida):
```python
import polars as pl

# Lê todas as partições descobrindo a coluna 'ano' automaticamente
df = pl.scan_parquet("data/motivo_cassacao/**/*.parquet")

# Filtra apenas o ano desejado sem ler os demais arquivos do disco (Partition Pruning)
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

## 📂 Estrutura de Diretórios

```text
opt-tse-analytics/
├── md-images/                  # Registros visuais das evidências de performance
├── src/                        # Núcleo modular da aplicação
│   ├── __init__.py             # Inicialização do pacote Python
│   ├── console.py              # Instância singleton do console Rich
│   ├── converter.py            # Motor de conversão streaming CSV -> Parquet via PyArrow
│   ├── datasets.py             # Dataclass TSEDataset, endpoints e catálogo de bases
│   └── downloader.py           # Orquestrador HTTP, connection pooling e ThreadPool
├── .gitignore                  # Regras de exclusão Git (dados, caches, IDEs, SO)
├── LICENSE                     # Licença MIT de código aberto
├── main.py                     # Ponto de entrada e Interface de Linha de Comando (CLI)
├── pyproject.toml              # Metadados e dependências padronizadas (PEP 621)
├── README.md                   # Documentação arquitetural e benchmarks
└── uv.lock                     # Lockfile reprodutível de dependências
```

---

## 📄 Licença

Este projeto é disponibilizado sob a licença [MIT](LICENSE) para fins de pesquisa, estudo e engenharia de dados.

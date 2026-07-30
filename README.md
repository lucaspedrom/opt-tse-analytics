# TSE Ingestão 🗳️

O **TSE Ingestão** é um script utilitário em Python projetado para automatizar o download de dados públicos de estatísticas eleitorais diretamente dos servidores do Tribunal Superior Eleitoral (TSE) do Brasil. 

Este projeto serve como base para coleta de dados de candidaturas, bens de candidatos, coligações, motivos de cassação e votações por município e zona eleitoral.

> [!IMPORTANT]
> **Créditos e Atribuição:** O código original deste projeto foi desenvolvido por **Teo Calvo** no vídeo [TSE Analytics 2026 - Coletando Dados](https://www.youtube.com/watch?v=TNW990c3Vh4&t=2222s). Este repositório constitui uma implementação base para estudos e testes de otimização de performance.

[![TSE Analytics 2026 - Coletando Dados](https://img.youtube.com/vi/TNW990c3Vh4/hqdefault.jpg)](https://www.youtube.com/watch?v=TNW990c3Vh4&t=2222s)

---

## 🛠️ O que ele faz e Como funciona

O projeto está estruturado em dois módulos principais:
1. **[downloader.py](file:///d:/Projetos/tse-ingestao/downloader.py):** Contém a classe [DownloadTSE](file:///d:/Projetos/tse-ingestao/downloader.py#L8), responsável por toda a lógica de negócio, criação de diretórios e downloads.
2. **[main.py](file:///d:/Projetos/tse-ingestao/main.py):** Funciona como a interface de linha de comando (CLI) do projeto, interpretando argumentos e inicializando o fluxo de downloads.

### Fluxo de Funcionamento:
1. **Inicialização:** A classe [DownloadTSE](file:///d:/Projetos/tse-ingestao/downloader.py#L8) cria automaticamente a pasta `./data` para salvar os arquivos baixados, se ela não existir.
2. **Download das Categorias:** Para cada ano especificado, o script faz requisições HTTP `GET` síncronas usando a biblioteca `requests` (e validações via `http.HTTPStatus`) para obter os seguintes conjuntos de dados zipados do repositório do TSE:
   - **Consulta Candidatura:** Informações cadastrais de candidatos (`consulta_cand_<ano>.zip`).
   - **Bens de Candidatos:** Relação de bens declarados pelos candidatos (`bem_candidato_<ano>.zip`).
   - **Coligações:** Detalhes de coligações partidárias (`consulta_coligacao_<ano>.zip`).
   - **Motivo de Cassação:** Registro de candidatos cassados e motivos (`motivo_cassacao_<ano>.zip`).
   - **Votação por Município/Zona:** Resultados detalhados de votação (`votacao_candidato_munzona_<ano>.zip`).
3. **Organização Local:** Salva os zips na pasta `./data/<ano>/`.
4. **Monitoramento:** Utiliza o utilitário `track` da biblioteca `rich` para renderizar uma barra de progresso interativa no terminal durante a iteração de anos.

> [!NOTE]
> No estado atual, as requisições de download são executadas de forma sequencial (síncrona), o que pode limitar a performance dependendo da velocidade de conexão e do volume de dados.

---

## 🚀 Como Executar Localmente

Siga o passo a passo abaixo para configurar o ambiente e testar o script de ingestão.

### Pré-requisitos
* **Python** 3.10 ou superior.
* Gerenciador de pacotes **[uv](https://github.com/astral-sh/uv)** instalado globalmente (recomendado para performance e isolamento simples).

### 1. Clonar ou acessar o repositório
Abra o seu terminal no diretório do projeto:
```powershell
cd d:/Projetos/tse-ingestao
```

### 2. Configurar o Ambiente Virtual e Dependências
Você pode utilizar o ambiente virtual integrado `.venv`. Caso precise instalar as dependências requeridas (`requests` e `rich`):

**Usando o `uv`:**
```powershell
# Cria o ambiente virtual caso não exista
uv venv

# Ativa o ambiente virtual
# No Windows (PowerShell):
.venv\Scripts\Activate.ps1
# No Windows (CMD):
.venv\Scripts\activate.bat
# No Linux/macOS:
source .venv/bin/activate

# Instala as dependências necessárias
uv pip install requests rich
```

### 3. Executar o Script de Ingestão (CLI)
Com as dependências instaladas e o ambiente virtual ativo, você pode rodar o script com diferentes parâmetros de ano e intervalo através da CLI suportada pelo `argparse`:

```powershell
uv run main.py [argumentos]
```

#### Argumentos disponíveis:
* `-i`, `--inicio` (int): Ano inicial a ser baixado (padrão: `2014`).
* `-f`, `--fim` (int): Ano final a ser baixado (padrão: `2022`).
* `--intervalo` (int): Passo/intervalo entre os anos (padrão: `2022`).

#### Exemplos de uso:
* **Execução padrão (baixa apenas o ano inicial `2014` devido ao intervalo de `2022`):**
  ```powershell
  uv run main.py
  ```
* **Baixar os anos eleitorais de 4 em 4 anos (2014, 2018, 2022):**
  ```powershell
  uv run main.py --inicio 2014 --fim 2022 --intervalo 4
  ```
* **Baixar apenas um ano específico (ex: 2022):**
  ```powershell
  uv run main.py --inicio 2022 --fim 2022
  ```

Os arquivos resultantes serão salvos progressivamente no diretório `./data/`.

---

## 📊 Evidências da Primeira Execução (Código Original)

Abaixo estão as evidências de execuções do código original desenvolvido por **Teo Calvo**, obtidas durante os testes iniciais do script em seu estado atual. Estes dados servirão como linha de base (baseline) para avaliar e comprovar a eficácia de futuras otimizações de performance (como concorrência, paralelismo ou assincronismo).


### 1. Execução da função `download_ano()`, apenas para o ano 2022:
> [!NOTE]
> **Versão de referência da execução:** `1d951ea` (Commit correspondente ao código original/baseline).

![Download Ano 2022](md-images/execucao-download-2022.png)  
*Execução da função download_ano(2022).*

![Detalhes Execução Ano 2022](md-images/detalhes-execucao-download-2022.png)  
*Detalhes do tempo de execução da função download_ano(2022).*

* **Tempo de Execução:** 5 minutos, 13 segundos e 2 décimos.  
* **Data de Execução:** 29/07/2026 21:19:13 (GMT -03:00)

### 2. Execução da função `download_anos()`, para os anos 2014, 2018 e 2022:
> [!NOTE]
> **Versão de referência da execução:** `1d951ea` (Commit correspondente ao código original/baseline).

![Download Anos 2014, 2018 e 2022](md-images/execucao-download-2014_2018_2022.png)  
*Execução da função download_anos(2014, 2018, 2022).*

![Detalhes Horário de Execução Anos 2014, 2018 e 2022](md-images/detalhes-execucao-download-2014_2018_2022.png)  
*Detalhes do tempo de execução da função download_anos(2014, 2018, 2022).*

* **Tempo de Execução:** 13 minutos, 29 segundos.  
* **Data de Execução:** 29/07/2026 21:31:38 (GMT -03:00)
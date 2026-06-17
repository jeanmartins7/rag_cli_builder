# RAG CLI Builder - Trabalho Prático de Recuperação de Informação

Este projeto implementa um pipeline completo de recuperação de informação, desde a coleta de dados até a avaliação de diferentes modelos de busca. O sistema utiliza um corpus de artigos científicos do ArXiv e permite comparar quatro abordagens de recuperação distintas.

## Funcionalidades

- **Coleta de Dados**: Baixa e processa artigos científicos do ArXiv.
- **Indexação e Busca**: Implementa múltiplos modelos de recuperação:
  - `BM25`: Modelo clássico baseado em contagem de termos.
  - `k-NN`: Busca vetorial baseada em embeddings de texto.
  - `Hybrid`: Combinação dos scores do BM25 e k-NN.
  - `Reranker`: Utiliza um modelo de Cross-Encoder para re-ranquear os melhores resultados de uma busca inicial.
- **Avaliação**: Calcula métricas padrão de RI (P@10, R@10, MAP, nDCG@10) para cada modelo.
- **CLI**: Interface de linha de comando para orquestrar todo o pipeline.

## Como Usar

O projeto é gerenciado através de uma CLI implementada em `src/main.py`.

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Executar o Pipeline

Execute os modelos de recuperação para gerar os arquivos de run.
```bash
python src/main.py run
```
Este comando irá:
1.  Verificar se o corpus de dados existe. Se não, executa a coleta de dados.
2.  Executa os quatro modelos de recuperação (`bm25`, `knn`, `hybrid`, `reranker`) e salva os resultados em `data/runs/`.

### 3. Gerar o Arquivo de Relevância (Qrels)

Gere o arquivo `qrels.tsv` que servirá como gabarito para a avaliação.
```bash
python src/main.py generate-qrels
```
Este comando cria o arquivo `data/qrels.tsv` usando os 10 melhores documentos do modelo `reranked` como "relevantes".

### 4. Avaliar os Modelos

Execute a avaliação para comparar os resultados dos modelos com o gabarito.
```bash
python src/main.py evaluate
```
Este comando irá ler o `qrels.tsv` e todos os arquivos `.trec` no diretório `data/runs/`, e então imprimirá um relatório detalhado com as métricas de avaliação para cada sistema.

---

## Checklist do Projeto (Trabalho_2026-1.pdf)

Aqui está o checklist de todas as etapas do projeto, conforme o documento de especificação.

- [x] **1. Coleta e Preparação dos Dados**
  - [x] Coletar 1000 documentos do ArXiv.
  - [x] Processar e armazenar os documentos em um formato estruturado (`corpus.jsonl`).
  - [x] Definir 15 consultas (`queries.tsv`).

- [x] **2. Implementação dos Sistemas de Busca**
  - [x] **Sistema 1: BM25**
    - [x] Implementar a indexação e busca com BM25.
    - [x] Gerar um arquivo de run (`bm25.trec`).
  - [x] **Sistema 2: Busca Vetorial (k-NN)**
    - [x] Gerar embeddings para os documentos.
    - [x] Implementar a busca por similaridade de cosseno (k-NN).
    - [x] Gerar um arquivo de run (`knn.trec`).
  - [x] **Sistema 3: Híbrido**
    - [x] Combinar os scores do BM25 и k-NN.
    - [x] Gerar um arquivo de run (`hybrid.trec`).
  - [x] **Sistema 4: Re-ranking**
    - [x] Usar um dos modelos anteriores como primeiro estágio.
    - [x] Implementar um re-ranker com Cross-Encoder.
    - [x] Gerar um arquivo de run (`reranked.trec`).

- [x] **3. Avaliação**
  - [x] Criar um arquivo de anotações de relevância (`qrels.tsv`).
  - [x] Implementar um script de avaliação (`evaluate.py`).
  - [x] Calcular e reportar as métricas: P@10, R@10, MAP, e nDCG@10.
  - [x] Incluir uma análise comparativa dos resultados.

- [x] **4. Usabilidade e Reprodutibilidade**
  - [x] Criar uma CLI para orquestrar o pipeline (`main.py`).
  - [x] Fornecer um `README.md` com instruções claras.
  - [x] Garantir que o projeto seja executável com os comandos fornecidos.

Todos os requisitos do trabalho foram concluídos com sucesso.

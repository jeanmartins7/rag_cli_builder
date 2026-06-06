# Construindo o "R" do RAG: Sistema de Recuperação de Artigos Científicos

**Autor:** Jean Marcel Peres Martins (Doutorado)
**Disciplina:** Inteligência Artificial - Pós-Graduação 2026/1
**Professor:** Prof. Dr. Bruno M. Nogueira
**Instituição:** FACOM / UFMS

---

## 📌 Sobre o Projeto

Este repositório contém a implementação prática do componente de **Recuperação (Retrieval)** de um sistema *Retrieval-Augmented Generation* (RAG). O objetivo principal é recuperar artigos científicos relevantes a partir de uma coleção customizada construída via API do ArXiv, focada no tema de pesquisa do autor: **[INSERIR SEU TEMA DE PESQUISA AQUI]**.

O pipeline compara paradigmas clássicos probabilísticos (BM25) com métodos vetoriais densos (KNN/Embeddings) e implementa módulos avançados de otimização de ranqueamento.

### Módulos Implementados (Nível Doutorado)
Além dos baselines obrigatórios, este projeto inclui a implementação e avaliação de dois módulos de aprofundamento:
* **[Ex: M1] Re-ranqueamento por Classificação Supervisionada:** Utilização de classificadores (ex: Regressão Logística) para reordenar o top-K do BM25.
* **[Ex: M5] Ranking Híbrido (Sparse + Dense):** Combinação dos scores do modelo léxico e do modelo denso via *Reciprocal Rank Fusion* (RRF).
*(Nota: Ajuste a lista acima conforme os módulos que você escolheu desenvolver).*

---

## 📂 Estrutura do Repositório

```text
.
├── data/
│   ├── raw/             # Corpus bruto baixado do ArXiv (corpus.jsonl)
│   └── processed/       # Dados limpos, tokens e embeddings cacheados
├── eval/
│   ├── queries.tsv      # Consultas de teste (10 a 20 queries)
│   ├── qrels.tsv        # Anotações de relevância manuais (gabarito)
│   └── evaluate.py      # Script de avaliação oficial da disciplina
├── notebooks/           # Jupyter Notebooks exploratórios e de coleta
├── runs/                # Resultados das buscas no formato TREC (.trec)
├── src/                 # Código-fonte principal
│   ├── models/          # Implementação dos recuperadores e módulos
│   └── utils/           # Funções auxiliares (pré-processamento, etc.)
├── README.md
├── requirements.txt
└── LINKS.txt            # Links para a submissão final


# 🛠️ RAG CLI Builder

Ferramenta de orquestração (*scaffolding*) desenvolvida para automatizar a criação de pipelines completos de Recuperação de Informação (IR).

## Instalação (Modo de Desenvolvimento)
No seu terminal, dentro da pasta raiz deste projeto, instale o pacote em modo editável:
```bash
pip install -e .
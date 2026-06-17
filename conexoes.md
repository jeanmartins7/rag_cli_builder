# Conexões: Componentes do Trabalho e Conceitos da Disciplina

Este documento detalha as decisões de projeto e as conexões entre cada componente implementado no trabalho e os tópicos teóricos vistos na disciplina de Recuperação de Informação e Inteligência Artificial.

### BM25 / Paradigmas Estatísticos (ex: Naive Bayes)

- **Conceito da Disciplina:** Modelos probabilísticos de recuperação e classificação, como o Naive Bayes, se baseiam na probabilidade de ocorrência de termos para tomar decisões. Eles usam estatísticas extraídas do corpus (frequência de termos, frequência de documentos) para calcular probabilidades como `P(classe|documento)`.

- **Conexão no Trabalho:** O **BM25 (Best Match 25)** é um descendente direto dessa família de modelos estatísticos. Ele não usa a probabilidade de forma explícita como o Naive Bayes, mas seu núcleo é totalmente estatístico.
  - **TF (Term Frequency):** O BM25 usa a frequência de um termo em um documento, um conceito estatístico fundamental.
  - **IDF (Inverse Document Frequency):** Ele mede a raridade de um termo em todo o corpus. Termos raros (estatisticamente menos frequentes) recebem um peso maior, pois são mais discriminativos.
  - **Saturação de TF e Normalização de Documento:** O BM25 refina o TF-IDF clássico com componentes que modelam estatisticamente o fato de que a importância de um termo não cresce linearmente (saturação) e que documentos mais longos têm maior probabilidade de conter um termo por acaso.

**Decisão de Projeto:** Escolhemos o BM25 como nosso primeiro sistema por ser o **baseline padrão-ouro** em RI. É um modelo estatístico robusto, eficiente e surpreendentemente difícil de superar, representando o auge da recuperação de informação clássica.

### k-NN sobre Vetores / Classificador k-NN

- **Conceito da Disciplina:** O classificador **k-Nearest Neighbors (k-NN)** opera em um espaço vetorial. Para classificar um novo ponto, ele encontra os 'k' vizinhos mais próximos (outros pontos de dados) e usa um "voto" da classe majoritária entre eles. A premissa é que pontos próximos no espaço vetorial compartilham características semelhantes.

- **Conexão no Trabalho:** Nossa **busca vetorial** é uma aplicação direta do princípio do k-NN.
  - **Espaço Vetorial:** Em vez de pontos de dados com features, nosso espaço é um **espaço de embeddings semânticos**. Cada documento e cada consulta é representado por um vetor denso.
  - **Distância/Similaridade:** Em vez da distância euclidiana, usamos a **similaridade de cosseno** para medir a "proximidade" entre os vetores da consulta e dos documentos. Uma similaridade de cosseno alta é análoga a uma distância pequena.
  - **k-Vizinhos:** A busca consiste em encontrar os **k documentos** cujos vetores têm a maior similaridade de cosseno com o vetor da consulta.

**Decisão de Projeto:** Incluímos a busca vetorial para explorar a **recuperação semântica**. Diferente do BM25, que busca por palavras-chave, este método busca por **significado**. Ele pode encontrar documentos relevantes que não compartilham nenhuma palavra-chave com a consulta, mas que são conceitualmente similares.

### Re-ranqueamento / Modelos de Classificação (Regressão Logística, SVM, etc.)

- **Conceito da Disciplina:** Modelos como Regressão Logística, SVM ou mesmo Naive Bayes são usados para **classificação**. Eles aprendem uma função `f(features) -> classe`. No contexto de RI, isso pode ser adaptado para a tarefa de **Learning to Rank (LTR)**, onde o modelo aprende a prever a relevância de um documento para uma consulta: `f(query, document) -> relevance_score`.

- **Conexão no Trabalho:** O **re-ranker (Cross-Encoder)** é uma implementação sofisticada deste conceito.
  - **Função de Relevância:** Um Cross-Encoder é um modelo Transformer que processa o par `(query, document)` simultaneamente. Ele funciona como uma função de classificação binária extremamente poderosa, que retorna um score indicando a probabilidade de o documento ser relevante para a consulta.
  - **Arquitetura de Dois Estágios:** Como essa função é computacionalmente cara, é inviável aplicá-la a todos os 1000 documentos. Por isso, usamos uma arquitetura de dois estágios:
    1.  **Primeiro Estágio (Candidate Generation):** Um modelo rápido (como o BM25) seleciona um conjunto inicial de candidatos promissores (ex: top 50).
    2.  **Segundo Estágio (Re-ranking):** O Cross-Encoder, mais lento e poderoso, reordena apenas esses 50 candidatos para produzir o ranking final.

**Decisão de Projeto:** O re-ranking foi implementado para **aumentar a precisão** do sistema. Ele combina a eficiência de um modelo de primeiro estágio com a alta qualidade de um modelo de aprendizado profundo, representando o estado da arte em arquiteturas de busca modernas.

### Embeddings Densos (Opcional)

- **Conceito da Disciplina:** Embeddings densos são representações vetoriais de baixa dimensão para itens como palavras ou documentos. Eles são "densos" porque a maioria de seus valores são não-zero, contrastando com os vetores esparsos do TF-IDF. Esses vetores são treinados para que a distância entre eles no espaço vetorial capture relações semânticas.

- **Conexão no Trabalho:** Os embeddings densos são a **espinha dorsal** do nosso sistema de busca vetorial (k-NN) e do re-ranker.
  - **Para k-NN (Bi-Encoder):** Usamos um modelo como o Sentence-BERT (um Bi-Encoder) para gerar um vetor para cada documento de forma independente. Esses vetores são armazenados e usados para a busca rápida por similaridade de cosseno.
  - **Para Re-ranking (Cross-Encoder):** O Cross-Encoder não gera um embedding independente, mas usa os mesmos princípios de atenção dos Transformers para avaliar a interação semântica profunda entre os tokens da consulta e do documento quando processados em conjunto.

**Decisão de Projeto:** O uso de embeddings densos foi uma escolha deliberada para introduzir a capacidade de **compreensão semântica** no pipeline, indo além da simples correspondência de palavras-chave.

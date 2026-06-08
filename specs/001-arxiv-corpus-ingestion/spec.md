# Feature Specification: Ingestão de Corpus ArXiv

**Feature Branch**: `001-arxiv-corpus-ingestion`

**Created**: 2026-06-06

**Status**: Draft

**Input**: Definir requisitos exatos para Passo 1 (escopo e coleta) e Passo 2
(pré-processamento) do pipeline de recuperação científica, incluindo geração do
`corpus.jsonl` a partir da API do ArXiv.

**Constitution**: Plans and requirements MUST comply with `.specify/memory/constitution.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Definir escopo e coletar artigos (Priority: P1)

Como pesquisador de poda estrutural e compressão de LLMs open source, preciso
configurar os critérios de coleta (tema, palavras-chave, categorias, janela
temporal e volume alvo) e executar a ingestão para obter uma coleção própria de
artigos do ArXiv, de forma que eu possa reutilizá-la na revisão bibliográfica do
meu projeto de pesquisa e como base dos recuperadores BM25 e KNN.

**Why this priority**: Sem corpus válido e documentado, nenhuma etapa posterior do
pipeline (recuperação, avaliação, módulos opcionais) pode ser executada.

**Independent Test**: Executar o notebook de coleta com parâmetros padrão do tema;
verificar que `corpus.jsonl` é gerado com volume dentro do intervalo configurado,
sem duplicatas e com todos os campos obrigatórios preenchidos.

**Acceptance Scenarios**:

1. **Given** parâmetros de coleta configurados (tema, 2023–2026, categorias
   cs.CL/cs.LG/cs.AI, volume alvo 2.000), **When** o pesquisador executa o
   notebook de coleta até a conclusão, **Then** o sistema produz `corpus.jsonl`
   com entre 1.000 e 5.000 artigos únicos (conforme parâmetro) contendo id,
   title, abstract, authors, categories e date em cada linha.

2. **Given** uma coleta interrompida por falha da API (e.g., HTTP 429 ou 503),
   **When** o pesquisador reexecuta a mesma célula de coleta, **Then** o sistema
   retoma a partir do progresso salvo sem duplicar artigos já persistidos.

3. **Given** dois registros com o mesmo arxiv_id ou DOI retornados em páginas
   distintas, **When** a coleta finaliza, **Then** apenas uma linha por
   identificador único permanece em `corpus.jsonl`.

---

### User Story 2 - Pré-processar textos para indexação (Priority: P2)

Como pesquisador, preciso transformar título e abstract de cada artigo em texto
normalizado e tokenizado, aplicando o mesmo pipeline a documentos e consultas
futuras, para que os recuperadores esparsos e densos operem sobre representações
consistentes.

**Why this priority**: Pré-processamento inconsistente entre corpus e queries
degrada a qualidade de BM25 e KNN; deve ser definido antes dos recuperadores.

**Independent Test**: Aplicar o pipeline de pré-processamento a um subconjunto de
10 artigos do `corpus.jsonl` e a uma query de exemplo; verificar saída
tokenizada, em minúsculas, sem pontuação e sem stopwords, com opção de
stemming/lematização desligada por padrão.

**Acceptance Scenarios**:

1. **Given** um artigo com título e abstract em `corpus.jsonl`, **When** o
   pipeline de pré-processamento é executado com stemming desabilitado, **Then**
   a saída é a concatenação título + abstract após tokenização, lower-casing,
   remoção de pontuação e remoção de stopwords.

2. **Given** o módulo opcional de stemming/lematização habilitado via
   configuração, **When** o mesmo artigo é processado, **Then** a saída difere
   da execução sem stemming de forma documentada e reproduzível.

3. **Given** uma query de teste em texto livre, **When** o pipeline de
   pré-processamento é aplicado, **Then** as mesmas etapas e parâmetros usados
   no corpus são aplicados à query.

---

### Edge Cases

- A API do ArXiv retorna menos artigos que o volume alvo após esgotar resultados:
  o sistema MUST registrar o total obtido e sinalizar que o alvo não foi atingido.
- Artigo sem abstract ou com abstract vazio: MUST ser excluído ou registrado em
  log de qualidade; não deve gerar linha inválida silenciosa no corpus.
- Palavras-chave com caracteres especiais ou termos muito raros: query de coleta
  MUST permanecer válida para a sintaxe da API do ArXiv.
- Reexecução com parâmetros alterados (novas keywords ou janela temporal): MUST
  gerar novo corpus ou versão identificada, sem sobrescrever silenciosamente
  coleção anterior sem confirmação explícita do operador.

## Requirements *(mandatory)*

### Escopo e Definição da Coleção (Passo 1)

- **FR-001**: O tema da coleção MUST ser "Poda estrutural (structural pruning) e
  compressão de LLMs Open Source durante o processo de fine-tuning", documentado
  no relatório e no README do repositório.

- **FR-002**: A janela temporal de coleta MUST filtrar publicações de **2023 a
  2026** (inclusive), justificada pelo volume de trabalhos sobre otimização de
  LLMs abertos e técnicas de poda (e.g., AMP — Attention heads and MLP Pruning).

- **FR-003**: A query de coleta na API do ArXiv MUST combinar palavras-chave
  amplas com operador lógico OR, incluindo no mínimo: `"structural pruning"`,
  `"LLM compression"`, `"attention heads pruning"`, `"MLP pruning"`,
  `"parameter efficient fine-tuning"`. Termos adicionais relacionados ao tema
  MAY ser incluídos sem reduzir a cobertura dos termos mínimos.

- **FR-004**: A coleta MUST restringir categorias do ArXiv a `cs.CL`
  (Computation and Language), `cs.LG` (Machine Learning) e `cs.AI`
  (Artificial Intelligence).

- **FR-005**: O volume alvo da coleção MUST ser **parametrizável** com valor
  padrão de 2.000 artigos e limites aceitos entre **1.000 e 5.000** artigos
  (conforme enunciado do trabalho).

- **FR-006**: O processo de coleta MUST remover duplicatas por `arxiv_id` (campo
  `id`) ou DOI antes de persistir o corpus final.

### Execução da Coleta e Geração do Corpus (Passo 2)

- **FR-007**: O notebook `coleta_arxiv.ipynb` MUST orquestrar a paginação da API
  do ArXiv com tolerância a falhas: retry com backoff, retomada por offset e
  **salvamento incremental** do progresso para que interrupções não exijam
  reinício completo.

- **FR-008**: A saída obrigatória da etapa de coleta MUST ser o arquivo
  `corpus.jsonl` (um objeto JSON por linha).

- **FR-009**: Cada linha de `corpus.jsonl` MUST conter obrigatoriamente as
  chaves: `id`, `title`, `abstract`, `authors`, `categories`, `date`.

- **FR-010**: O campo `id` MUST corresponder ao identificador ArXiv (e.g.,
  `2401.12345`); `authors` MUST ser uma lista; `categories` MUST ser uma lista de
  categorias ArXiv; `date` MUST ser a data de publicação em formato ISO 8601
  (YYYY-MM-DD).

- **FR-011**: Critérios de coleta (palavras-chave, categorias, janela temporal,
  volume alvo, total efetivo obtido) MUST ser registrados em log ou célula de
  resumo do notebook para reprodutibilidade e documentação no relatório.

### Pré-processamento Textual

- **FR-012**: O texto base para indexação MUST ser a **concatenação** de
  `title` + `abstract` de cada documento (com separador explícito documentado,
  e.g., espaço ou `". "`).

- **FR-013**: O pipeline de pré-processamento MUST aplicar, nesta ordem:
  (1) tokenização, (2) normalização (lower-casing e remoção de pontuação),
  (3) remoção de stopwords.

- **FR-014**: Stemming ou lematização MUST ser **opcional e modular** (ativável
  por flag de configuração), desabilitado por padrão, permitindo execuções
  comparativas documentadas no relatório.

- **FR-015**: O mesmo pipeline e parâmetros de pré-processamento MUST ser
  aplicáveis tanto a documentos do corpus quanto a consultas de usuário
  (interface reutilizável, e.g., função ou módulo `preprocessing`).

- **FR-016**: Decisões de pré-processamento (idioma das stopwords, uso ou não de
  stemming, separador título/abstract) MUST ser documentadas para reprodutibilidade.

### Key Entities

- **Artigo (corpus.jsonl)**: `id`, `title`, `abstract`, `authors`, `categories`,
  `date` — documento bruto coletado do ArXiv.

- **Configuração de coleta**: tema, keywords (lista OR), categorias, `date_from`,
  `date_to`, `target_count`, caminhos de saída.

- **Checkpoint de coleta**: estado incremental (offset, ids já coletados) para
  retomada após falha.

- **Texto indexável**: saída do pré-processamento — tokens normalizados derivados
  de título + abstract (ou query).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pesquisador obtém `corpus.jsonl` com volume entre 1.000 e 5.000
  artigos (conforme parâmetro) em até uma sessão de coleta com retomada, sem
  duplicatas por id ou DOI.

- **SC-002**: 100% das linhas em `corpus.jsonl` possuem as seis chaves
  obrigatórias com valores não vazios para `id`, `title` e `date`.

- **SC-003**: Após falha simulada ou interrupção manual, reexecução do notebook
  adiciona apenas artigos novos (zero duplicatas no arquivo final).

- **SC-004**: Pipeline de pré-processamento produz saída determinística para o
  mesmo texto de entrada e mesma configuração (com stemming on/off).

- **SC-005**: Mesmo pipeline processa corpus e query de exemplo produzindo
  tokens compatíveis (mesmas regras de normalização e stopwords).

- **SC-006**: Critérios de coleta e pré-processamento estão documentados de forma
  que um terceiro possa reproduzir a coleção sem decisões implícitas.

## Assumptions

- A API pública do ArXiv permanece acessível com rate limiting por IP; não há
  chave de API.
- Stopwords em inglês são suficientes, dado que abstracts do ArXiv neste domínio
  são predominantemente em inglês.
- Volume padrão de coleta é 2.000 artigos (ajustável via parâmetro).
- Stemming/lematização permanece desabilitado na configuração inicial; comparação
  com stemming é experimento opcional documentado no relatório.
- O notebook `coleta_arxiv.ipynb` reside em `resource/` como base e será adaptado
  ou referenciado pelo módulo `src/collection/` conforme arquitetura modular da
  constituição.
- A biblioteca `arxiv` (wrapper Python) é aceita para coleta, alinhada ao material
  de apoio do trabalho; dependências de coleta (`arxiv`, `tqdm`) são declaradas
  em `requirements.txt` além do conjunto principal de recuperação.

## Out of Scope

- Implementação dos recuperadores BM25 e KNN (Passos 3 e 4).
- Construção de queries de avaliação e qrels (Passo 5).
- Módulos opcionais de aprofundamento (M1–M5).
- Geração de embeddings ou índices de busca (etapa posterior ao pré-processamento).

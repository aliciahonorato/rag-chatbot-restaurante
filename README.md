# Dataset Curado para Chatbot RAG - Receitas de Restaurante

## Visão Geral

Este projeto consiste no desenvolvimento de um chatbot inteligente para um restaurante, utilizando a abordagem de Retrieval-Augmented Generation (RAG).
O sistema responde perguntas dos usuários exclusivamente com base em documentos oficiais do restaurante, como fichas técnicas de receitas, garantindo respostas confiáveis, padronizadas e alinhadas ao contexto gastronômico profissional.


## Objetivo do Projeto
Este projeto tem como objetivo demonstrar, de forma prática, o uso de **RAG (Retrieval-Augmented Generation)** aplicado a um cenário real. A proposta envolve a **curadoria e validação de dados, a integração de modelos de IA generativa com dados estruturados e não estruturados**, e a **construção de uma interface funcional** que permita ao usuário final consultar informações de forma clara, contextualizada e confiável.


## Uso Educacional

Projeto desenvolvido exclusivamente para **fins educacionais**, utilizando dados adaptados do menu oficial do restaurante **Mocotó**, de Rodrigo Oliveira e equipe. O uso dos dados tem caráter demonstrativo e educacional, não havendo qualquer finalidade comercial, redistribuição oficial ou substituição de materiais institucionais do restaurante.


## Estrutura do Dataset

### Composição
- **26 PDFs**: Fichas técnicas detalhadas das receitas
- **26 Imagens**: Representações dos pratos finalizados/empratamento
- **1 CSV**: Inventário e metadados de todos os documentos (54 registros)

### Categorias de Receitas
1. **Tradicionais** (5 receitas): Baião-de-Dois, Favada, Feijão-de-Corda, Sarapatel, Caldo de Mocotó
2. **Especialidades** (8 receitas): Mocofava, Moqueca Sertaneja, Carne-de-Sol na Brasa, Carne-Seca Desfiada, Atolado de Vaca, Dobradinha, Rabada, Costelinha de Porco Recheada
3. **Saladas** (3 receitas): Salada Nordestina, Salada de Maxixe, Vinagrete Sertanejo
4. **Sobremesas** (10 receitas): Sorvete de Rapadura, Sorvete de Doce de Leite, Pudim de Tapioca, Musse de Chocolate com Cachaça, Crème Brûlée de Doce de Leite, Cocada Cremosa, Cartola, Bolo de Rolo, Quindim, Paçoca de Pilão


## Informações das Fichas Técnicas

Cada PDF contém:
- Nome da receita
- Categoria
- Descrição do prato
- Ingredientes completos
- Modo de preparo detalhado (padronizado, estilo restaurante)
- Tempo médio de preparo
- Possíveis substituições
- Indicação de restrições alimentares
- Sugestão de empratamento e harmonização
- Chef responsável
- Versão do documento
- Data de criação

### Chef Responsável
- **Tradicionais, Especialidades e Saladas**: Rodrigo Oliveira e equipe
- **Sobremesas**: Alex Sotero e equipe


## Metadados (CSV)

O arquivo `inventario_dataset.csv` contém os seguintes campos:

| Campo | Descrição |
|-------|-----------|
| `document_id` | Identificador único do documento |
| `tipo` | Tipo do arquivo (pdf ou imagem) |
| `path_arquivo` | Caminho relativo do arquivo |
| `titulo` | Título do documento/imagem |
| `origem` | Origem do documento (Ficha técnica oficial ou Manual interno do restaurante) |
| `data` | Data de criação/modificação |
| `categoria` | Categoria da receita |
| `versao` | Versão do documento |
| `nivel_confianca` | Nível de confiança do documento (alto, médio) |

---

## Problemas Intencionais para Curadoria

Este dataset contém **problemas propositais** para exercícios de curadoria e limpeza de dados:

### PDFs (4 problemas)
- ✗ **2 PDFs com versão inconsistente**: Variação no formato da versão (v1, v1.0, versão 1, 1.0)
- ✗ **1 PDF com data ausente**: Documento sem informação de data
- ✗ **1 PDF simulando conteúdo escaneado**: Texto menos estruturado, simulando OCR

### Imagens (2 problemas)
- ✗ **2 imagens com nomes de arquivo inconsistentes**: Padrão de nomenclatura diferente

### CSV (5 problemas)
- ✗ **2 linhas duplicadas**: Registros repetidos
- ✗ **1 caminho de arquivo incorreto**: Path apontando para arquivo inexistente
- ✗ **2 registros com categoria incorreta**: Categoria não corresponde à receita
- ✗ **Variação de formatação de datas**: Múltiplos formatos (DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY)


## Objetivo do Dataset

Este dataset permite:
1. **Exercícios de curadoria e limpeza de dados**
2. **Validação de metadados**
3. **Uso em pipeline de RAG**
4. **Análise de qualidade** (duplicatas, OCR, inconsistências)
5. **Treinamento de chatbots** para responder perguntas sobre:
   - Preparação de receitas passo a passo
   - Ingredientes e substituições
   - Tempo de preparo
   - Restrições alimentares
   - Empratamento e harmonização
   - Custos médios
   - Fichas técnicas oficiais
   - Informações sobre chefs


## Uso Recomendado

### Para RAG (Retrieval-Augmented Generation)
1. **Indexação**: Processar os PDFs e extrair texto estruturado
2. **Embeddings**: Gerar embeddings dos textos para busca semântica
3. **Metadados**: Utilizar o CSV para enriquecer as buscas com filtros
4. **Curadoria**: Limpar os problemas intencionais antes da indexação
5. **Validação**: Verificar consistência entre PDFs, imagens e CSV

### Perguntas que o Chatbot Pode Responder
- Como preparar a receita X passo a passo, no padrão do restaurante?
- Quais são os ingredientes necessários e possíveis substituições?
- Qual o tempo médio de preparo da receita?
- Essa receita possui versões para restrições alimentares (vegana, sem glúten, sem lactose)?
- Qual a melhor forma de empratar e harmonizar o prato?
- Qual o custo médio dos pratos?
- Onde encontro a ficha técnica oficial dessa receita?
- Quem foi o chef responsável pela criação do prato?



## Arquitetura do Sistema

O projeto é composto por três camadas principais:

1. **Camada de Dados**
   - PDFs de fichas técnicas
   - Imagens de pratos
   - CSV com metadados e inventário

2. **Pipeline RAG**
   - Extração de texto dos PDFs
   - Geração de embeddings
   - Recuperação semântica baseada na pergunta do usuário
   - Geração de resposta condicionada ao contexto recuperado

3. **Interface (Streamlit)**
   - Chat interativo
   - Histórico de mensagens
   - Identidade visual personalizada

---

## Estrutura de Diretórios

```
atividade6
└──.streamlit/
    └──config.toml
└──dataset_restaurante/
    ├── README.md
    ├── fichas_tecnicas/
    │   ├── ficha_01_baião_de_dois.pdf
    │   ├── ficha_02_favada.pdf
    │   └── ... (26 PDFs no total)
    ├── imagens/
    │   ├── img_01_baião_de_dois.jpg
    │   ├── img_02_favada.jpg
    │   └── ... (26 imagens no total)
    └── inventario_dataset.csv
└── notebooks/
    ├── 01_validacao_dataset.ipynb
    └── 02_preparacao_rag.ipynb
├── .gitignore
├── app.py
├── rag_pipeline.py
├── README.md
└── requirements.txt
```


## Como Executar o Projeto

1. Clone o repositório
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
3. Execute a aplicação:
    ```bash
    streamlit run app.py


## Informações Técnicas

- **Formato dos PDFs**: PDF padrão com texto pesquisável (exceto 1 simulando escaneamento)
- **Formato das Imagens**: JPEG, resolução variável (400x300 a 1200x900)
- **Encoding do CSV**: UTF-8
- **Total de registros no CSV**: 54 (26 PDFs + 26 imagens + 2 duplicatas)


## Tecnologias Utilizadas

- **Python** – linguagem principal do projeto
- **Streamlit** – construção da interface web interativa
- **RAG (Retrieval-Augmented Generation)** – arquitetura de recuperação e geração de respostas
- **Azure OpenAI** – modelo de linguagem para geração de respostas
- **Sentence Transformers** – geração de embeddings semânticos
- **FAISS** – indexação e busca vetorial
- **Pandas** – manipulação e validação de dados tabulares
- **NumPy** – operações numéricas e vetoriais
- **PDFPlumber** – extração de texto de arquivos PDF
- **Pytesseract (OCR)** – extração de texto de documentos simulando escaneamento
- **Pillow (PIL)** – manipulação de imagens
- **Azure Key Vault** – gerenciamento seguro de segredos e credenciais
- **Azure Identity** – autenticação segura com serviços Azure
- **Regex (re)** – limpeza e padronização de texto
- **Pathlib & OS** – manipulação de caminhos e sistema de arquivos


## Limitações Conhecidas

Não mostra ou gera imagens.

---

**Versão do Dataset**: 2.0  
**Data de Criação**: Janeiro 2026  
**Domínio**: Gastronomia profissional / Padronização de receitas

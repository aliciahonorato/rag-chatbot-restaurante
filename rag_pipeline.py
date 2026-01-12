from pathlib import Path
import pandas as pd
import faiss
import re
import unicodedata

from sentence_transformers import SentenceTransformer
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# =====================
# PATHS
# =====================
BASE_PATH = Path(__file__).parent
DATASET_PATH = BASE_PATH / "dataset_restaurante"
RAG_CHUNKS_PATH = DATASET_PATH / "rag_dataset_chunks.csv"

assert RAG_CHUNKS_PATH.exists(), f"Arquivo não encontrado: {RAG_CHUNKS_PATH}"

# =====================
# AZURE OPENAI
# =====================
def load_azure_openai_from_keyvault():
    KEY_VAULT_NAME = "kv-academy-01"
    KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net"

    credential = DefaultAzureCredential()
    kv_client = SecretClient(vault_url=KV_URI, credential=credential)

    endpoint = kv_client.get_secret("URL-API-GPT").value
    api_version = kv_client.get_secret("VERSION-API-GPT").value
    api_key = kv_client.get_secret("KEY-API-GPT").value
    deployment = kv_client.get_secret("MODELO-APT-GPT").value

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint,
    )

    return client, deployment


client, AZURE_OPENAI_CHAT_DEPLOY = load_azure_openai_from_keyvault()

# =====================
# LOAD DATA + EMBEDDINGS
# =====================
rag_dataset = pd.read_csv(RAG_CHUNKS_PATH)

model_st = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

texts = rag_dataset["chunks"].fillna("").astype(str).tolist()

embeddings = model_st.encode(
    texts,
    convert_to_numpy=True,
    normalize_embeddings=True,
).astype("float32")

# =====================
# FAISS
# =====================
dim = embeddings.shape[1]
index = faiss.IndexFlatIP(dim)
index.add(embeddings)


def retrieve_faiss(query: str, top_k: int = 10):
    q = model_st.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")

    scores, idx = index.search(q, top_k)
    hits = rag_dataset.iloc[idx[0]].copy()
    hits["score"] = scores[0]
    return hits.sort_values("score", ascending=False)


# =====================
# CONTEXTO FORMATADO
# =====================
def format_context(rows, max_chars=4500):
    parts, total = [], 0
    for r in rows.itertuples():
        tag = f"[Fonte: {r.document_id} | chunk {r.chunk_id} | {r.path_arquivo}]"
        block = f"{tag}\n{str(r.chunks).strip()}\n"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n".join(parts)


# =====================
# CATEGORIAS / UTILS
# =====================
CATEGORIAS_OFICIAIS = ["Tradicional", "Especialidade", "Salada", "Sobremesa"]


def hits_empty(query: str = "", fonte: str = "rag_dataset_chunks.csv"):
    return pd.DataFrame([{
        "document_id": fonte,
        "chunk_id": "-",
        "score": 1.0,
        "categoria": "-",
        "categoria_corr": "-",
        "titulo": "-",
        "tipo": "dataset",
        "path_arquivo": fonte
    }])


def listar_categorias():
    return CATEGORIAS_OFICIAIS


def extrair_categoria_da_pergunta(pergunta: str):
    p = pergunta.lower()
    if "tradicion" in p:
        return "Tradicional"
    if "especial" in p:
        return "Especialidade"
    if "salad" in p:
        return "Salada"
    if "sobremes" in p:
        return "Sobremesa"
    return None


def listar_pratos_da_categoria(cat: str):
    df_menu = rag_dataset[rag_dataset["tipo"].astype(str).str.lower() == "pdf"]
    pratos = (
        df_menu.loc[df_menu["categoria_corr"] == cat, "titulo"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
    return sorted(set(p for p in pratos if p and p.lower() != "nan"))


# =====================
# NORMALIZAÇÃO
# =====================
def _norm_text(s: str) -> str:
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


_TITULOS_MENU = (
    rag_dataset[rag_dataset["tipo"].astype(str).str.lower() == "pdf"][["titulo", "categoria_corr"]]
    .dropna()
    .drop_duplicates()
)

TITULO_NORM_TO_ORIG = {_norm_text(t): t for t in _TITULOS_MENU["titulo"]}
TITULO_NORM_TO_CAT = {_norm_text(t): c for t, c in zip(_TITULOS_MENU["titulo"], _TITULOS_MENU["categoria_corr"])}


# =====================
# INTENTS
# =====================
def eh_pergunta_categoria_de_prato(pergunta: str) -> bool:
    p = pergunta.lower()
    gatilhos = [
        "qual a categoria", "qual é a categoria", "qual categoria",
        "em qual categoria", "categoria do prato", "categoria da receita",
        "esse prato é de qual categoria", "essa receita é de qual categoria",
    ]
    return ("categoria" in p) and any(g in p for g in gatilhos)


def encontrar_prato_na_pergunta(pergunta: str):
    qn = _norm_text(pergunta)

    for tnorm in sorted(TITULO_NORM_TO_ORIG.keys(), key=len, reverse=True):
        if tnorm and tnorm in qn:
            return tnorm

    q_tokens = set(qn.split())
    best, best_score = None, 0
    for tnorm in TITULO_NORM_TO_ORIG:
        score = len(q_tokens & set(tnorm.split()))
        if score >= 2 and score > best_score:
            best, best_score = tnorm, score
    return best


def eh_pergunta_listar_itens_categoria(pergunta: str) -> bool:
    p = pergunta.lower()
    return any(k in p for k in [
        "liste", "listar", "quais pratos", "pratos da categoria",
        "itens da categoria", "menu da categoria"
    ]) and extrair_categoria_da_pergunta(pergunta) is not None


def eh_pergunta_de_categorias(pergunta: str) -> bool:
    if eh_pergunta_categoria_de_prato(pergunta):
        return False
    p = pergunta.lower()
    return any(k in p for k in [
        "quantas categorias", "listar categorias",
        "categorias do cardápio", "todas as categorias"
    ])


# =====================
# MAIN
# =====================
def answer_question(query: str, top_k=5, temperature=0.2, min_score=0.28):

    # 1) LISTAR PRATOS POR CATEGORIA
    if eh_pergunta_listar_itens_categoria(query):
        cat = extrair_categoria_da_pergunta(query)
        pratos = listar_pratos_da_categoria(cat)

        if not pratos:
            return f"Não encontrei pratos para a categoria **{cat}**.", hits_empty()

        texto = f"Pratos da categoria **{cat}**:\n- " + "\n- ".join(pratos)
        texto += f"\n\nTotal: {len(pratos)} pratos."
        return texto, hits_empty(query, f"lista_pratos_{cat}")

    # 2) CATEGORIA DE UM PRATO
    if eh_pergunta_categoria_de_prato(query):
        tnorm = encontrar_prato_na_pergunta(query)
        if tnorm and tnorm in TITULO_NORM_TO_CAT:
            prato = TITULO_NORM_TO_ORIG[tnorm]
            cat = TITULO_NORM_TO_CAT[tnorm]
            return f"O prato **{prato}** pertence à categoria **{cat}**.", hits_empty()
        return "Não consegui identificar o prato na pergunta.", hits_empty()

    # 3) LISTAR CATEGORIAS
    if eh_pergunta_de_categorias(query):
        cats = listar_categorias()
        texto = f"O cardápio possui {len(cats)} categorias:\n- " + "\n- ".join(cats)
        return texto, hits_empty()

    # 4) RAG NORMAL
    hits = retrieve_faiss(query, top_k=max(top_k, 20))
    hits = hits[hits["score"] >= min_score]
    hits = hits.drop_duplicates(subset=["document_id"]).head(top_k)

    if hits.empty:
        return "Não encontrei informações na base para responder.", hits_empty()

    context = format_context(hits)

    system = (
        "Você é um assistente de um restaurante. "
        "Responda SOMENTE com base no CONTEXTO. "
        "Não invente informações. "
        "Liste as fontes no final."
    )

    user = f"PERGUNTA:\n{query}\n\nCONTEXTO:\n{context}"

    resp = client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOY,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )

    return resp.choices[0].message.content, hits

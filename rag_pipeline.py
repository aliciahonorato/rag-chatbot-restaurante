from pathlib import Path
import pandas as pd
import faiss
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
# AZURE KEY VAULT + OPENAI
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


# inicializa uma única vez
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
# FAISS VECTOR STORE
# =====================
dim = embeddings.shape[1]
index = faiss.IndexFlatIP(dim)
index.add(embeddings)

# =====================
# RETRIEVAL FUNCTIONS
# =====================
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


def format_context(rows, max_chars: int = 4500):
    parts, total = [], 0

    for r in rows.itertuples():
        tag = f"[Fonte: {r.document_id} | chunk {r.chunk_id}]"
        block = f"{tag}\n{str(r.chunks).strip()}\n"

        if total + len(block) > max_chars:
            break

        parts.append(block)
        total += len(block)

    return "\n".join(parts)


# =====================
# MAIN RAG FUNCTION
# =====================
def answer_question(query: str) -> str:
    hits = retrieve_faiss(query, top_k=10)

    # threshold de relevância
    hits = hits[hits["score"] >= 0.28]

    # reduz poluição (1 chunk por documento)
    hits = hits.drop_duplicates(subset=["document_id"]).head(5)

    if hits.empty:
        return "Não encontrei informações suficientes na base para responder a essa pergunta."

    context = format_context(hits)

    system = (
        "Você é um assistente virtual de um restaurante. "
        "Responda de forma clara, educada e objetiva. "
        "Use apenas as informações do CONTEXTO fornecido. "
        "Se a resposta não estiver na base, diga isso explicitamente. "
        "Ao final, liste as fontes utilizadas."
    )

    user = f"PERGUNTA:\n{query}\n\nCONTEXTO:\n{context}"

    resp = client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOY,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )

    return resp.choices[0].message.content

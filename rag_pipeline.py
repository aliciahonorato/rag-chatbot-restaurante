from pathlib import Path
from datetime import datetime
import re
import unicodedata

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
IMAGENS_DIR = DATASET_PATH / "imagens"

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
# LOAD DATA
# =====================
rag_dataset = pd.read_csv(RAG_CHUNKS_PATH)

# =====================
# NORMALIZAÇÕES / CATEGORIA_CORR
# =====================
CATEGORIAS_OFICIAIS = ["Tradicional", "Especialidade", "Salada", "Sobremesa"]

def _strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))

def _norm_text(s: str) -> str:
    s = "" if s is None else str(s)
    s = _strip_accents(s).lower()
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def normalizar_categoria(raw: str) -> str:
    if not isinstance(raw, str):
        return ""
    t = _norm_text(raw)
    if "tradicion" in t: return "Tradicional"
    if "especial" in t: return "Especialidade"
    if "salad" in t: return "Salada"
    if "sobremes" in t: return "Sobremesa"
    return ""

def extrair_categoria_do_chunk(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    m = re.search(r'(?i)\bCATEGORIA\b\s*[:\n]\s*([^\n\r]+)', texto)
    return m.group(1).strip() if m else ""

if "categoria_corr" not in rag_dataset.columns:
    rag_dataset["categoria_norm"] = rag_dataset.get("categoria", "").apply(normalizar_categoria)
    rag_dataset["categoria_in_chunk"] = rag_dataset["chunks"].apply(extrair_categoria_do_chunk)
    rag_dataset["categoria_chunk_norm"] = rag_dataset["categoria_in_chunk"].apply(normalizar_categoria)
    rag_dataset["categoria_corr"] = rag_dataset.apply(
        lambda r: r["categoria_chunk_norm"] if r["categoria_chunk_norm"] else r["categoria_norm"],
        axis=1
    )
else:
    # ainda assim garante padronização
    rag_dataset["categoria_corr"] = rag_dataset["categoria_corr"].apply(normalizar_categoria)


# =====================
# EMBEDDINGS + FAISS VECTOR STORE
# =====================
model_st = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

texts = rag_dataset["chunks"].fillna("").astype(str).tolist()

embeddings = model_st.encode(
    texts,
    convert_to_numpy=True,
    normalize_embeddings=True,
).astype("float32")

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


def retrieve_by_dish_title(dish_title: str, top_k: int = 8):
    """
    Busca determinística no CSV pelos chunks do prato (pelo titulo).
    Evita depender do score do FAISS quando o prato já foi identificado.
    """
    if not dish_title or "titulo" not in rag_dataset.columns:
        return rag_dataset.iloc[0:0].copy()

    dish_norm = _norm_text(dish_title)

    df = rag_dataset.copy()
    df["__titulo_norm"] = df["titulo"].fillna("").astype(str).apply(_norm_text)

    # prioriza PDFs (texto real)
    if "tipo" in df.columns:
        df_pdf = df[df["tipo"].astype(str).str.lower() == "pdf"].copy()
    else:
        df_pdf = df

    # match exato normalizado
    hits = df_pdf[df_pdf["__titulo_norm"] == dish_norm].copy()

    # fallback: "contém"
    if hits.empty:
        hits = df_pdf[df_pdf["__titulo_norm"].str.contains(dish_norm, na=False)].copy()

    hits = hits.drop(columns=["__titulo_norm"], errors="ignore")

    # score alto só pra padronizar
    hits["score"] = 1.0
    return hits.head(top_k)


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


#===================
#IMAGNES(título -> arquivo)
#===================
def slugify_title(title: str) -> str:
    return _norm_text(title).replace(" ", "_")

def get_image_path_for_dish(title: str):
    if not title:
        return None

    slug = slugify_title(title)  

    # 1) tenta direto (caso exista sem prefixo)
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        p = IMAGENS_DIR / f"{slug}{ext}"
        if p.exists():
            return str(p)

    # 2) procura arquivo que contenha o slug
    if IMAGENS_DIR.exists():
        slug_lower = slug.lower()
        for p in IMAGENS_DIR.iterdir():
            if p.is_file():
                name_lower = p.name.lower()
                if slug_lower in name_lower:
                    return str(p)

    return None


# =====================
# MAPAS (título -> categoria) e match de prato
# =====================
def _build_menu_maps():
    df_menu = rag_dataset[rag_dataset["tipo"].astype(str).str.lower() == "pdf"][["titulo", "categoria_corr"]].dropna()
    df_menu = df_menu.drop_duplicates()

    titulo_norm_to_orig = {_norm_text(t): t for t in df_menu["titulo"].tolist()}
    titulo_norm_to_cat = {_norm_text(t): c for t, c in zip(df_menu["titulo"], df_menu["categoria_corr"])}
    return titulo_norm_to_orig, titulo_norm_to_cat

TITULO_NORM_TO_ORIG, TITULO_NORM_TO_CAT = _build_menu_maps()

def encontrar_prato_na_pergunta(pergunta: str):
    qn = _norm_text(pergunta)

    # 1) substring do título
    for tnorm in sorted(TITULO_NORM_TO_ORIG.keys(), key=len, reverse=True):
        if tnorm and tnorm in qn:
            return tnorm

    # 2) overlap mínimo
    q_tokens = set(qn.split())
    best, best_score = None, 0
    for tnorm in TITULO_NORM_TO_ORIG.keys():
        t_tokens = set(tnorm.split())
        score = len(q_tokens & t_tokens)
        if score > best_score and score >= 2:
            best, best_score = tnorm, score
    return best

# =====================
# INTENTS (categorias, listagens, categoria do prato, meta)
# =====================
def extrair_categoria_da_pergunta(pergunta: str):
    p = pergunta.lower()
    if "tradicion" in p: return "Tradicional"
    if "especial" in p: return "Especialidade"
    if "salad" in p: return "Salada"
    if "sobremes" in p: return "Sobremesa"
    return None

def listar_pratos_da_categoria(cat: str):
    df_menu = rag_dataset[rag_dataset["tipo"].astype(str).str.lower() == "pdf"].copy()
    pratos = (
        df_menu.loc[df_menu["categoria_corr"] == cat, "titulo"]
        .dropna().astype(str).str.strip().unique().tolist()
    )
    return sorted(set([p for p in pratos if p and p.lower() != "nan"]))

def listar_pratos_da_categoria(cat: str):
    df_menu = rag_dataset[rag_dataset["tipo"].astype(str).str.lower() == "pdf"].copy()
    pratos = (
        df_menu.loc[df_menu["categoria_corr"] == cat, "titulo"]
        .dropna().astype(str).str.strip().unique().tolist()
    )
    return sorted(set([p for p in pratos if p and p.lower() != "nan"]))


# ✅ ADICIONE ESSA FUNÇÃO AQUI
def listar_todos_pratos():
    df_menu = rag_dataset[rag_dataset["tipo"].astype(str).str.lower() == "pdf"].copy()

    pratos = (
        df_menu["titulo"]
        .dropna().astype(str).str.strip()
        .unique().tolist()
    )

    # limpa "nan" e strings vazias e ordena
    pratos = sorted(set([p for p in pratos if p and p.lower() != "nan"]))
    return pratos

def eh_pergunta_listar_itens_categoria(pergunta: str) -> bool:
    p = pergunta.lower()
    tem_intencao = any(k in p for k in [
        "liste", "listar", "quais pratos", "quais itens",
        "itens da categoria", "pratos da categoria", "menu da categoria"
    ])
    return tem_intencao and (extrair_categoria_da_pergunta(pergunta) is not None)

def eh_pergunta_categoria_de_prato(pergunta: str) -> bool:
    p = pergunta.lower()
    gatilhos = [
        "qual a categoria", "qual é a categoria", "qual categoria",
        "em qual categoria", "categoria do prato", "categoria da receita",
        "esse prato é de qual categoria", "essa receita é de qual categoria",
    ]
    return ("categoria" in p) and any(g in p for g in gatilhos)

def eh_pergunta_de_categorias(pergunta: str) -> bool:
    p = pergunta.lower().strip()
    if eh_pergunta_categoria_de_prato(pergunta):
        return False
    gatilhos = [
        "quantas categorias",
        "liste as categorias",
        "listar categorias",
        "quais sao as categorias",
        "quais são as categorias",
        "categorias do cardapio",
        "categorias do cardápio",
        "todas as categorias",
    ]
    return any(g in p for g in gatilhos)

def eh_pergunta_listar_todos_itens_cardapio(pergunta: str) -> bool:
    p = _norm_text(pergunta)
    gatilhos = [
        "itens do cardapio", "itens do cardápio",
        "quais os itens do cardapio", "quais os itens do cardápio",
        "listar cardapio", "listar cardápio",
        "me mostre o cardapio", "me mostre o cardápio",
        "cardapio completo", "cardápio completo",
        "todas as opcoes", "todas as opções",
        "todas as comidas", "todas as receitas",
        "menu completo", "menu inteiro"
    ]
    return any(g in p for g in gatilhos)

def eh_followup_sem_prato(pergunta: str) -> bool:
    p = pergunta.lower()
    gatilhos = [
        "ingredientes", "modo de preparo", "como prepara", "preparo",
        "preço", "preco", "quanto custa",
        "tempo de preparo", "quanto tempo",
        "tem lactose", "tem glúten", "tem gluten", "restrições", "restricoes"
    ]
    return any(g in p for g in gatilhos) and (encontrar_prato_na_pergunta(pergunta) is None)

def meta_answer(query: str, state: dict):
    q = query.lower().strip()
    if "que dia é hoje" in q or "data de hoje" in q:
        agora = datetime.now()
        return f"Hoje é {agora.strftime('%d/%m/%Y')}."
    if "que horas são" in q or "que horas sao" in q:
        agora = datetime.now()
        return f"Agora são {agora.strftime('%H:%M')}."
    if "ultima pergunta" in q or "última pergunta" in q:
        last_q = state.get("last_user_question")
        return f"Sua última pergunta foi: {last_q}" if last_q else "Ainda não tenho uma pergunta anterior registrada."
    return None


# =====================
# MAIN RAG FUNCTION
# =====================
def answer_question(query: str, state: dict | None = None, top_k: int = 10, min_score: float = 0.28):
    """
    Retorna dict:
      - text: resposta
      - sources: list de fontes
      - dish_title: prato identificado (ou None)
      - dish_image: caminho da imagem (ou None)
      - state: estado atualizado (memória)
    """
    if state is None:
        state = {}

    # registra última pergunta
    state["last_user_question"] = query

    # meta (data/hora/última pergunta)
    m = meta_answer(query, state)
    if m is not None:
        return {
            "text": m,
            "sources": ["sistema (data/hora/contexto)"],
            "dish_title": None,
            "dish_image": None,
            "show_image": False,
            "state": state
        }
    
    dish_mentioned = False

    # detecta prato na pergunta
    tnorm = encontrar_prato_na_pergunta(query)
    if tnorm and tnorm in TITULO_NORM_TO_ORIG:
        dish_mentioned = True
        prato_atual = TITULO_NORM_TO_ORIG[tnorm]
        state["current_dish"] = prato_atual
    else:
        prato_atual = state.get("current_dish")
        # follow-up (ex.: "qual o modo de preparo?") sem prato explícito
        if prato_atual and eh_followup_sem_prato(query):
            query = f"Sobre o prato {prato_atual}: {query}"

    dish_image = get_image_path_for_dish(prato_atual) if prato_atual else None

    # 1) Listar pratos por categoria
    if eh_pergunta_listar_itens_categoria(query):
        cat = extrair_categoria_da_pergunta(query)
        pratos = listar_pratos_da_categoria(cat)
        if not pratos:
            return {
                "text": f"Não encontrei pratos para a categoria **{cat}** na base atual.",
                "sources": [f"rag_dataset_chunks.csv (lista de pratos: {cat})"],
                "dish_title": None,
                "dish_image": None,
                "show_image": False,
                "state": state
            }
        texto = f"Pratos da categoria **{cat}**:\n- " + "\n- ".join(pratos)
        texto += f"\n\nTotal: {len(pratos)} pratos."
        return {
            "text": texto,
            "sources": [f"rag_dataset_chunks.csv (lista de pratos: {cat})"],
            "dish_title": None,
            "dish_image": None,
            "show_image": False,
            "state": state
        }

    # 2) Categoria de um prato específico
    if eh_pergunta_categoria_de_prato(query):
        t2 = encontrar_prato_na_pergunta(query)
        if t2 and t2 in TITULO_NORM_TO_CAT:
            prato = TITULO_NORM_TO_ORIG[t2]
            cat = TITULO_NORM_TO_CAT[t2]
            img = get_image_path_for_dish(prato)
            state["current_dish"] = prato
            return {
                "text": f"O prato **{prato}** fica na categoria **{cat}**.",
                "sources": [f"rag_dataset_chunks.csv (categoria do prato: {prato})"],
                "dish_title": prato,
                "dish_image": img,
                "show_image": True,
                "state": state
            }
        return {
            "text": "Não consegui identificar o nome do prato. Digite o nome exato (como no cardápio).",
            "sources": ["rag_dataset_chunks.csv (categoria do prato)"],
            "dish_title": prato_atual,
            "dish_image": dish_image,
            "show_image": False,
            "state": state
        }

    # 3) Listar categorias
    if eh_pergunta_de_categorias(query):
        texto = "As categorias no cardápio são:\n- " + "\n- ".join(CATEGORIAS_OFICIAIS)
        texto += f"\n\nTotal: {len(CATEGORIAS_OFICIAIS)} categorias."
        return {
            "text": texto,
            "sources": ["rag_dataset_chunks.csv (categorias oficiais)"],
            "dish_title": None,
            "dish_image": None,
            "show_image": False,
            "state": state
        }
        # 3.5) LISTAR TODOS OS ITENS DO CARDÁPIO (determinístico)
    if eh_pergunta_listar_todos_itens_cardapio(query):
        pratos = listar_todos_pratos()

        if not pratos:
            return {
                "text": "Não encontrei itens do cardápio na base atual.",
                "sources": ["rag_dataset_chunks.csv (títulos do cardápio)"],
                "dish_title": None,
                "dish_image": None,
                "show_image": False,
                "state": state
            }

        # OBS: resposta pode ficar grande, mas vai listar tudo.
        texto = "Itens do cardápio:\n- " + "\n- ".join(pratos)
        texto += f"\n\nTotal: {len(pratos)} itens."

        return {
            "text": texto,
            "sources": ["rag_dataset_chunks.csv (títulos do cardápio)"],
            "dish_title": None,
            "dish_image": None,
            "show_image": False,
            "state": state
        }

    # =====================
    # 4) RAG normal
    # =====================

    # A) Se eu já sei qual é o prato, tento puxar diretamente os chunks dele
    hits = rag_dataset.iloc[0:0].copy()
    if prato_atual:
        hits = retrieve_by_dish_title(prato_atual, top_k=8)

    # B) Se não achou por título, cai no FAISS (busca semântica normal)
    if hits.empty:
        hits = retrieve_faiss(query, top_k=top_k)

        # threshold só faz sentido no FAISS
        hits = hits[hits["score"] >= min_score]

        # tenta focar no prato dentro dos hits (se existir)
        if prato_atual and "titulo" in hits.columns:
            hits_prato = hits[hits["titulo"].astype(str).str.lower().str.contains(prato_atual.lower(), na=False)]
            if len(hits_prato) > 0:
                hits = hits_prato.copy()

    # reduz poluição
    hits = hits.drop_duplicates(subset=["document_id"]).head(5)

    if hits.empty:
        return {
            "text": "Não encontrei informações suficientes na base para responder a essa pergunta.",
            "sources": [],
            "dish_title": prato_atual,
            "dish_image": dish_image,
            "show_image": dish_mentioned,
            "state": state
        }

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

    sources = [f"{r.document_id} (chunk {r.chunk_id})" for r in hits.itertuples()]

    return {
        "text": resp.choices[0].message.content,
        "sources": sources,
        "dish_title": prato_atual,
        "dish_image": dish_image,
        "show_image": dish_mentioned,
        "state": state
    }
import streamlit as st
from rag_pipeline import answer_question

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="Chatbot Restaurante",
    page_icon="🍽️",
    layout="centered"
)

# =====================
# CSS – IDENTIDADE VISUAL
# =====================
st.markdown(
    """
    <style>

    /* FUNDO GERAL */
    .stApp {
        background-color: #ecd6b5;
        color: #5d1d18;
        font-family: "Segoe UI", sans-serif;
    }

    p, span, div, label {
        color: #5d1d18 !important;
    }

    /* HEADER */
    header[data-testid="stHeader"] {
        background-color: #fdaf19;
    }

    header[data-testid="stHeader"] * {
        color: #ffffff !important;
    }

    /* FOOTER */
    footer {
        background-color: #fdaf19;
    }

    footer * {
        color: #ffffff !important;
    }

    /* SIDEBAR  */
    section[data-testid="stSidebar"] {
        background-color: #f3ca75;
    }

    section[data-testid="stSidebar"] * {
        color: #5d1d18 !important;
    }

    /* ======================
       CARDS DO CHAT
    ====================== */
    .chat-card {
        background-color: #ffffff;
        color: #5d1d18;
        padding: 12px 16px;
        border-radius: 14px;
        max-width: 75%;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 10px;
        line-height: 1.5;
        display: inline-block;
    }

    .chat-user-wrapper {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-bottom: 10px;
    }

    .chat-bot-wrapper {
        display: flex;
        justify-content: flex-start;
        gap: 8px;
        margin-bottom: 10px;
    }

    .chat-icon {
        font-size: 1.3rem;
        margin-top: 4px;
    }

    /* INPUT */
    textarea {
        background-color: #e9c1a8 !important;
        color: #5d1d18 !important;
        border-radius: 10px;
        border: 1px solid #5d1d18;
    }

    textarea::placeholder {
        color: #5d1d18aa;
    }

    div[data-testid="stChatInput"] {
        background-color: #ecd6b5 !important;
        border-top: 1px solid #5d1d18;
    }

    button {
        background-color: #5d1d18 !important;
        color: #ffffff !important;
        border-radius: 10px;
    }

    button:hover {
        background-color: #fdaf19 !important;
        color: #5d1d18 !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =====================
# HEADER
# =====================
st.markdown(
    """
    <h1 style='text-align: center;'>Assistente IA do Restaurante</h1>
    <p style='text-align: center;'>
        Fique à vontade para perguntar sobre pratos, preços ou opções do cardápio 💛
    </p>
    <hr>
    """,
    unsafe_allow_html=True
)

# =====================
# SIDEBAR
# =====================
with st.sidebar:
    st.markdown("### ℹ️ Sobre")
    st.write(
        "Este chatbot foi criado para ajudar você a explorar o cardápio "
        "de forma simples e agradável.\n\n"
        "As respostas são geradas com **RAG**, sempre com base "
        "nas informações reais do restaurante."
    )

    st.markdown("---")
    st.caption("🍴 Projeto BlueAcademy • IA aplicada")

# =====================
# SESSION STATE
# =====================
if "messages" not in st.session_state:
    st.session_state.messages = []

# guarda memória (prato atual / última pergunta etc.)
if "rag_state" not in st.session_state:
    st.session_state.rag_state = {}

# =====================
# CHAT HISTORY
# =====================
seen_deshies = set()

for msg in st.session_state.messages:
    # quebra de linha bonita dentro do HTML
    content_html = str(msg.get("content", "")).replace("\n", "<br>")

    if msg["role"] == "assistant":
        # título do prato (se houver)
        if msg.get("dish_title"):
            st.markdown(
                f"""
                <div class="chat-bot-wrapper">
                    <div class="chat-card"><b>{msg["dish_title"]}</b></div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # imagem do prato (se houver)
        if msg.get("dish_image"):
            st.image(msg["dish_image"], use_container_width=True)

        # resposta
        st.markdown(
            f"""
            <div class="chat-bot-wrapper">
                <div class="chat-card">{content_html}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # fontes (opcional)
        if msg.get("sources"):
            with st.expander("Fontes"):
                for s in msg["sources"]:
                    st.write(f"- {s}")

    else:
        st.markdown(
            f"""
            <div class="chat-user-wrapper">
                <div class="chat-card">{content_html}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# =====================
# INPUT
# =====================
prompt = st.chat_input("O que você gostaria de saber hoje?")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    st.markdown(
        f"""
        <div class="chat-user-wrapper">
            <div class="chat-card">{prompt}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.spinner("Conferindo o cardápio..."):
        try:
            result = answer_question(prompt, state=st.session_state.rag_state)

            # atualiza a memória do chat
            st.session_state.rag_state = result.get("state", st.session_state.rag_state)

            response_text = result.get("text", "")
            dish_title = result.get("dish_title")
            dish_image = result.get("dish_image")
            sources = result.get("sources", [])

        except Exception:
            response_text = (
                "Não consegui encontrar essa informação agora. "
                "Pode tentar novamente?"
            )
            dish_title, dish_image, sources = None, None, []

    # salva resposta completa no histórico
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "dish_title": dish_title,
        "dish_image": dish_image,
        "sources": sources
    })
    st.rerun()
    
    # render imediato
    response_html = response_text.replace("\n", "<br>")

    if dish_title:
        st.markdown(
            f"""
            <div class="chat-bot-wrapper">
                <div class="chat-card"><b>{dish_title}</b></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    if dish_image:
        st.image(dish_image, use_container_width=True)

    st.markdown(
        f"""
        <div class="chat-bot-wrapper">
            <div class="chat-card">{response_html}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if sources:
        with st.expander("Fontes"):
            for s in sources:
                st.write(f"- {s}")


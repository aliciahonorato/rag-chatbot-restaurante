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

    /* ======================
       FUNDO GLOBAL
    ====================== */
    html, body, .stApp {
        background-color: #ecd6b5;
        color: #5d1d18;
        font-family: "Segoe UI", sans-serif;
    }

    /* ======================
       HEADER
    ====================== */
    header[data-testid="stHeader"] {
        background-color: #fdaf19;
        border-bottom: none;
    }

    header[data-testid="stHeader"] * {
        color: #ffffff !important;
    }

    /* ======================
       CONTEÚDO PRINCIPAL
    ====================== */
    section.main {
        background-color: #ecd6b5;
    }

    /* ======================
       CHAT MESSAGES
    ====================== */
    div[data-testid="stChatMessage"] {
        background-color: #e9c1a8;
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 10px;
    }

    /* ======================
       CONTAINER INFERIOR (O "FOOTER FEIO")
    ====================== */
    div[data-testid="stChatInput"] {
        background-color: #fdaf19 !important;
        border-top: 2px solid #5d1d18;
        padding-top: 10px;
        padding-bottom: 10px;
    }

    /* REMOVE FUNDO PRETO INTERNO */
    div[data-testid="stChatInput"] > div {
        background-color: transparent !important;
    }

    /* ======================
       INPUT DO USUÁRIO
    ====================== */
    textarea {
        background-color: #e9c1a8 !important;
        color: #5d1d18 !important;
        border-radius: 12px;
        border: 1px solid #5d1d18;
        padding: 10px;
    }

    textarea::placeholder {
        color: #5d1d18aa;
    }

    /* ======================
       BOTÃO DE ENVIAR
    ====================== */
    button {
        background-color: #5d1d18 !important;
        color: #ffffff !important;
        border-radius: 10px;
    }

    button:hover {
        background-color: #e9c1a8 !important;
        color: #5d1d18 !important;
    }

    /* ======================
       FOOTER REAL (SE EXISTIR)
    ====================== */
    footer {
        background-color: #fdaf19;
    }

    footer * {
        color: #ffffff !important;
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
    <p class="subtitle">
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
# SESSION STATE (CHAT)
# =====================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =====================
# CHAT HISTORY
# =====================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(
                f"<div class='chatbot-box'>{msg['content']}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(msg["content"])

# =====================
# INPUT
# =====================
prompt = st.chat_input("O que você gostaria de saber hoje?")

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("assistant"):
        with st.spinner("Conferindo o cardápio..."):
            try:
                response = answer_question(prompt)
                st.markdown(
                    f"<div class='chatbot-box'>{response}</div>",
                    unsafe_allow_html=True
                )
            except Exception:
                response = (
                    "Não consegui encontrar essa informação agora. "
                    "Pode tentar novamente?"
                )
                st.markdown(
                    f"<div class='chatbot-box'>{response}</div>",
                    unsafe_allow_html=True
                )

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

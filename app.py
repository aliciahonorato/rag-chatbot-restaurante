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
import streamlit as st

st.markdown(
    """
    <style>

    /* ======================
       FUNDO GERAL
    ====================== */
    .stApp {
        background-color: #ecd6b5;
        color: #5d1d18;
        font-family: "Segoe UI", sans-serif;
    }

    /* ======================
       TEXTO GERAL
    ====================== */
    p, span, div, label {
        color: #5d1d18 !important;
    }

    /* ======================
       HEADER (TOPO)
    ====================== */
    header[data-testid="stHeader"] {
        background-color: #fdaf19;
    }

    header[data-testid="stHeader"] * {
        color: #ffffff !important;
    }

    /* ======================
       FOOTER (RODAPÉ)
    ====================== */
    footer {
        background-color: #fdaf19;
    }

    footer * {
        color: #ffffff !important;
    }

    /* ======================
       ÁREA DO CHAT
    ====================== */
    section[data-testid="stChatMessage"] {
        background-color: #e9c1a8;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 8px;
    }

    /* ======================
       INPUT DO USUÁRIO
    ====================== */
    textarea {
        background-color: #e9c1a8 !important;
        color: #5d1d18 !important;
        border-radius: 10px;
        border: 1px solid #5d1d18;
    }

    textarea::placeholder {
        color: #5d1d18aa;
    }

    /* ======================
       BARRA AZUL/CINZA (CHAT INPUT CONTAINER)
    ====================== */
    div[data-testid="stChatInput"] {
        background-color: #ecd6b5 !important;
        border-top: 1px solid #5d1d18;
    }

    /* ======================
       BOTÕES
    ====================== */
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

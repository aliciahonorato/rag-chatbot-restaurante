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

    /* ======================
       HEADER
    ====================== */

    header[data-testid="stHeader"] {
        background-color: #fdaf19;
    }

    header[data-testid="stHeader"] * {
        color: #ffffff !important;
    }

    /* FOOTER */
    footer {
        background-color: #e9c1a8;
    }

    footer * {
        color: #5d1d18 !important;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #e9c1a8;
    }

    section[data-testid="stSidebar"] * {
        color: #5d1d18 !important;
    }


    /* CARDS DO CHAT */
    .chat-card {
        background-color: #ffffff;
        color: #5d1d18;
        padding: 12px 16px;
        border-radius: 14px;
        max-width: 75%;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 10px;
        line-height: 1.5;
    }

    .chat-user {
        margin-left: auto;
        text-align: right;
    }

    .chat-bot {
        margin-right: auto;
        text-align: left;
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

# =====================
# CHAT HISTORY
# =====================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown(
                f"<div class='chat-card chat-bot'>{msg['content']}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='chat-card chat-user'>{msg['content']}</div>",
                unsafe_allow_html=True
            )

# =====================
# INPUT (BUG CORRIGIDO)
# =====================
prompt = st.chat_input("O que você gostaria de saber hoje?")

if prompt:
    # mostra a pergunta imediatamente
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(
            f"<div class='chat-card chat-user'>{prompt}</div>",
            unsafe_allow_html=True
        )

    # gera resposta
    with st.chat_message("assistant"):
        with st.spinner("Conferindo o cardápio..."):
            try:
                response = answer_question(prompt)
            except Exception:
                response = (
                    "Não consegui encontrar essa informação agora. "
                    "Pode tentar novamente?"
                )

            st.markdown(
                f"<div class='chat-card chat-bot'>{response}</div>",
                unsafe_allow_html=True
            )

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

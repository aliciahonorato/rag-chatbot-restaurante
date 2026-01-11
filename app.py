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
    /* Fundo geral */
    .stApp {
        background-color: #ecd6b5;
        color: #5d1d18;
    }

    /* Remove barras padrão (topo e rodapé) */
    header, footer {
        visibility: hidden;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #e9c1a8;
        color: #5d1d18;
    }

    /* Texto padrão */
    p, span, label, div {
        color: #5d1d18 !important;
    }

    /* Títulos */
    h1, h2, h3, h4 {
        color: #5d1d18;
    }

    /* Caixa das mensagens do bot */
    .chatbot-box {
        background-color: #e9c1a8;
        padding: 16px;
        border-radius: 12px;
        border-left: 6px solid #fdaf19;
        color: #5d1d18;
    }

    /* Input do chat */
    textarea {
        background-color: #ffffff;
        color: #5d1d18;
        border-radius: 10px;
    }

    /* Remove bordas e foco azul */
    textarea:focus, input:focus {
        outline: none !important;
        box-shadow: none !important;
        border: 2px solid #fdaf19 !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #fdaf19 !important;
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

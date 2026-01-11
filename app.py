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
    .stApp {
        background-color: #ecd6b5;
        color: #5d1d18;
    }

    section[data-testid="stSidebar"] {
        background-color: #e9c1a8;
    }

    h1, h2, h3 {
        color: #5d1d18;
    }

    .subtitle {
        text-align: center;
        color: #5d1d18;
        font-size: 16px;
        margin-bottom: 20px;
    }

    .chatbot-box {
        background-color: #e9c1a8;
        padding: 16px;
        border-radius: 12px;
        border-left: 6px solid #fdaf19;
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
    <h1 style='text-align: center;'>🍽️ Assistente do Restaurante</h1>
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
        "As respostas são geradas com **RAG + Azure OpenAI**, sempre com base "
        "nas informações reais do restaurante."
    )

    st.markdown("---")
    st.caption("🍴 Projeto acadêmico • IA aplicada")

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
prompt = st.chat_input("💬 O que você gostaria de saber hoje?")

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("assistant"):
        with st.spinner("👀 Deixa eu conferir o cardápio pra você..."):
            try:
                response = answer_question(prompt)
                st.markdown(
                    f"<div class='chatbot-box'>{response}</div>",
                    unsafe_allow_html=True
                )
            except Exception:
                response = (
                    "😕 Tive um probleminha ao buscar essa informação agora. "
                    "Pode tentar novamente?"
                )
                st.markdown(
                    f"<div class='chatbot-box'>{response}</div>",
                    unsafe_allow_html=True
                )

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

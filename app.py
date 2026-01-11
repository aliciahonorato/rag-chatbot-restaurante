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

    /* SIDEBAR – dourado mais claro */
    section[data-testid="stSidebar"] {
        background-color: #f3ddc0;
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

# =====================
# CHAT HISTORY
# =====================
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        st.markdown(
            f"""
            <div class="chat-bot-wrapper">
                <div class="chat-icon">🤖</div>
                <div class="chat-card">{msg['content']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="chat-user-wrapper">
                <div class="chat-card">{msg['content']}</div>
                <div class="chat-icon">🧑</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# =====================
# INPUT
# =====================
prompt = st.chat_input("O que você gostaria de saber hoje?")

if prompt:
    # mostra pergunta imediatamente
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    st.markdown(
        f"""
        <div class="chat-user-wrapper">
            <div class="chat-card">{prompt}</div>
            <div class="chat-icon">🧑</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.spinner("Conferindo o cardápio..."):
        try:
            response = answer_question(prompt)
        except Exception:
            response = (
                "Não consegui encontrar essa informação agora. "
                "Pode tentar novamente?"
            )

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

    st.markdown(
        f"""
        <div class="chat-bot-wrapper">
            <div class="chat-icon">🤖</div>
            <div class="chat-card">{response}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

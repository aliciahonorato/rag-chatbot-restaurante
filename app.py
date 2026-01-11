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
# HEADER
# =====================
st.markdown(
    """
    <h1 style='text-align: center;'>Chatbot do Restaurante</h1>
    <p style='text-align: center; color: gray;'>
    Pergunte sobre pratos, preços ou categorias do cardápio
    </p>
    <hr>
    """,
    unsafe_allow_html=True
)

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
        st.markdown(msg["content"])

# =====================
# INPUT
# =====================
prompt = st.chat_input("Digite sua pergunta")

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                response = answer_question(prompt)
                st.markdown(response)
            except Exception as e:
                response = "Erro ao gerar resposta."
                st.markdown(response)

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

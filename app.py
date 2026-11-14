import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="RAG Ассистент", page_icon="📚")
st.title("📚 Умный поиск по документу")
st.markdown("Загрузите любой PDF-файл и задайте по нему вопрос.")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Управление документом")
    
    uploaded_file = st.file_uploader("Выберите PDF файл", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Обработать файл"):
            with st.spinner("Читаю и обрабатываю документ..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                try:
                    response = requests.post(f"{API_URL}/upload", files=files)
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Успех! Загружено {data['chunks_count']} фрагментов.")
                        st.session_state.messages = [] # Очищаем старый чат
                    else:
                        st.error(f"Ошибка: {response.text}")
                except Exception as e:
                    st.error(f"Ошибка подключения к API: {e}")
                    
    st.divider()
    if st.button("Загрузить тестовый data/document.pdf"):
        with st.spinner("Загружаю тестовый документ..."):
            try:
                response = requests.post(f"{API_URL}/load_document")
                if response.status_code == 200:
                    st.success(f"Успех! Загружено {response.json()['chunks_count']} фрагментов.")
                    st.session_state.messages = []
                else:
                    st.error(f"Ошибка: {response.text}")
            except Exception as e:
                st.error(f"Ошибка подключения: {e}")

# Отображение истории
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ввод вопроса
if prompt := st.chat_input("Ваш вопрос по документу..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Ищу ответ..."):
            try:
                response = requests.post(f"{API_URL}/ask", json={"question": prompt})
                if response.status_code == 200:
                    data = response.json()
                    st.markdown(data["answer"])
                    
                    if data["sources"]:
                        with st.expander("Посмотреть источники"):
                            for i, source in enumerate(data["sources"]):
                                st.info(f"Фрагмент {i+1}:\n{source}")
                    
                    st.session_state.messages.append({"role": "assistant", "content": data["answer"]})
                elif response.status_code == 400:
                    st.warning("Сначала загрузите документ в боковой панели!")
                else:
                    st.error(f"Ошибка API: {response.text}")
            except Exception as e:
                st.error(f"Ошибка соединения: {e}")

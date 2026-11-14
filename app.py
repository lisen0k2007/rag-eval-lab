import streamlit as st
import requests
import os

# Берем адрес API из переменных окружения (для Docker), иначе используем localhost
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="RAG Ассистент", page_icon="📚")
st.title("📚 Умный поиск по документу")
st.markdown("Загрузите любой PDF-файл и задайте по нему вопрос.")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Управление документом")
    
    # Виджет загрузки файла
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
                        # Очищаем историю чата при загрузке нового документа
                        st.session_state.messages = []
                    else:
                        st.error(f"Ошибка: {response.text}")
                except Exception as e:
                    st.error(f"Не могу подключиться к API. ({e})")
                    
    st.divider()
    st.markdown("Или загрузите тестовый документ из папки `data`:")
    if st.button("Загрузить data/document.pdf"):
        with st.spinner("Загружаю тестовый документ..."):
            try:
                response = requests.post(f"{API_URL}/load_document")
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Успех! Загружено {data['chunks_count']} фрагментов.")
                    st.session_state.messages = []
                else:
                    st.error(f"Ошибка: {response.text}")
            except Exception as e:
                st.error(f"Ошибка соединения: {e}")

# Отображение истории сообщений
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Поле ввода вопроса
if prompt := st.chat_input("Ваш вопрос по документу..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Ищу ответ..."):
            try:
                response = requests.post(
                    f"{API_URL}/ask", 
                    json={"question": prompt}
                )
                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    sources = data["sources"]
                    
                    st.markdown(answer)
                    
                    if sources:
                        with st.expander("Посмотреть источники (контекст)"):
                            for i, source in enumerate(sources):
                                st.info(f"Фрагмент {i+1}:\n{source}")
                    
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                elif response.status_code == 400:
                    st.warning("Сначала загрузите документ в боковой панели!")
                else:
                    st.error(f"Ошибка API: {response.text}")
            except Exception as e:
                st.error(f"Ошибка соединения: {e}")

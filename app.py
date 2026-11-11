import streamlit as st
import requests

import os
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="RAG Ассистент", page_icon="📚")
st.title("📚 Умный поиск по документу")
st.markdown("Задайте вопрос по методичке, и я найду ответ в тексте.")

# Инициализация истории чата в сессии
if "messages" not in st.session_state:
    st.session_state.messages = []

# Боковая панель с кнопкой загрузки документа
with st.sidebar:
    st.header("Управление")
    if st.button("Загрузить документ (PDF)"):
        with st.spinner("Читаю и режу на куски..."):
            try:
                response = requests.post(f"{API_URL}/load_document")
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Успех! Загружено {data.get('chunks', 0)} кусков текста.")
                else:
                    st.error(f"Ошибка: {response.text}")
            except Exception as e:
                st.error(f"Не могу подключиться к API. Запущен ли сервер? ({e})")

# Отображение истории сообщений
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Поле ввода вопроса
if prompt := st.chat_input("Ваш вопрос (например: О чём этот документ?)"):
    # Добавляем вопрос пользователя в историю
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Отправляем запрос к FastAPI
    with st.chat_message("assistant"):
        with st.spinner("Ищу ответ в документе..."):
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
                    
                    # Показываем источники (откуда взялся ответ)
                    if sources:
                        with st.expander("Посмотреть источники (контекст)"):
                            for i, source in enumerate(sources):
                                st.info(f"Фрагмент {i+1}:\n{source}")
                    
                    # Сохраняем ответ в историю
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"Ошибка API: {response.text}")
            except Exception as e:
                st.error(f"Ошибка соединения: {e}")

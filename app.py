import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
import database as db
import auth

load_dotenv()
st.set_page_config(page_title="Quran AI Bot", page_icon="📖")

# Initialize DB
db.init_user_db()

# Fix: Ensure logic matches database.py arguments
if not db.get_user("naved"):
    db.create_user("naved", auth.get_password_hash("1234"), "naved@gmail.com")

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🌙 Login")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            user = db.get_user(u)
            if user and auth.verify_password(p, user["hashed_password"]):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid Login")
    st.stop()

st.title("📖 Quran AI Assistant")

if prompt := st.chat_input("Ask a question..."):
    st.chat_message("user").write(prompt)
    
    # RAG Search
    verses = db.search_quran_json(prompt)
    context = ""
    if verses:
        context = "Context:\n" + "\n".join([f"{v['surah']} {v['ayah']}: {v['text']}" for v in verses])

    # AI Call
    try:
        client = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key="ollama")
        res = client.chat.completions.create(
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            messages=[
                {"role": "system", "content": "You are a Quran scholar. Use the context provided."},
                {"role": "system", "content": context},
                {"role": "user", "content": prompt}
            ]
        )
        st.chat_message("assistant").write(res.choices[0].message.content)
    except Exception as e:
        st.error(f"AI Error: {e}")

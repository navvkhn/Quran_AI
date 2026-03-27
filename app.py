import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
import database as db
import auth

load_dotenv()

# Page Config
st.set_page_config(page_title="Quran AI Bot", page_icon="📖")

# Initialize Databases
db.init_user_db()

# --- Authentication Logic ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.title("Login to Quran AI")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            user = db.get_user(username)
            if user and auth.verify_password(password, user["hashed_password"]):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password")

if not st.session_state.authenticated:
    login()
    st.stop()

# --- Main App Interface ---
st.title("📖 Quranic AI Assistant")
st.sidebar.write(f"Logged in as: {st.session_state.username}")
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()

# Initialize Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask a question about the Quran..."):
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. RAG: Search JSON for context
    with st.spinner("Searching verses..."):
        related_verses = db.search_quran_json(prompt)
        
        context_str = ""
        if related_verses:
            context_str = "Use these verses as context:\n"
            for v in related_verses:
                context_str += f"- {v['surah']} {v['ayah']}: {v['text']}\n"

    # 3. Call AI (Ollama via Tunnel)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            client = OpenAI(
                base_url=os.getenv("OLLAMA_BASE_URL"), 
                api_key=os.getenv("OLLAMA_API_KEY", "ollama")
            )
            
            # Prepare messages for AI
            system_prompt = (
                "You are a helpful Quranic Assistant. Use the provided context to answer. "
                "Always cite Surah names and Ayah numbers."
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": context_str}
            ] + st.session_state.messages

            # Stream the response
            stream = client.chat.completions.create(
                model=os.getenv("OLLAMA_MODEL", "llama3"),
                messages=messages,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # Save to session and history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            # Optional: Save to SQLite db.save_msg(1, "assistant", full_response)
            
        except Exception as e:
            st.error(f"Connection Error: {e}")

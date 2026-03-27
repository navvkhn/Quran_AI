import streamlit as st
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import database as db
import auth

load_dotenv()

# --- Configuration & DB Init ---
st.set_page_config(page_title="Quran AI Bot", page_icon="📖")
db.init_user_db()

# Create default user 'naved' if not exists
if not db.get_user("naved"):
    db.create_user("naved", auth.get_password_hash("1234"), "naved")

# --- Authentication UI ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🌙 Quran AI Login")
    with st.form("login_gate"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            user = db.get_user(username)
            if user and auth.verify_password(password, user["hashed_password"]):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

# --- Main Chat App ---
st.title("📖 Quranic AI Assistant")
st.sidebar.title("Settings")
st.sidebar.write(f"Logged in as: **{st.session_state.username}**")

if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about the Quran..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 1. RAG: Search the JSON Data
    with st.status("Searching Quranic verses...", expanded=False) as status:
        # Search quran.json and map names from en.json
        verses = db.search_quran_json(prompt, lang="en")
        
        context_text = ""
        if verses:
            context_text = "Use the following verses for context:\n"
            for v in verses:
                context_text += f"- Surah {v['surah']} Ayah {v['ayah']}: {v['text']}\n"
            status.update(label=f"Found {len(verses)} relevant verses", state="complete")
        else:
            status.update(label="No direct verse matches found, using general knowledge.", state="complete")

    # 2. Call Ollama via OpenAI SDK
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            client = OpenAI(
                base_url=os.getenv("OLLAMA_BASE_URL"), 
                api_key=os.getenv("OLLAMA_API_KEY", "ollama")
            )
            
            # Prepare System Prompt
            messages = [
                {"role": "system", "content": "You are a knowledgeable Quranic scholar AI. Use the provided context to answer questions accurately and respectfully."},
                {"role": "system", "content": f"CONTEXT:\n{context_text}"}
            ] + st.session_state.messages

            # Stream the response for a "typing" effect
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
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Could not connect to AI Server: {e}")
            st.info("Check if your Ollama tunnel is active at " + os.getenv("OLLAMA_BASE_URL", ""))

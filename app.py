import streamlit as st
from openai import OpenAI
import database as db
import auth

# --- Configuration & DB Init ---
st.set_page_config(page_title="Quran AI Bot", page_icon="📖", layout="wide")
db.init_user_db()

# --- Authentication UI ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🌙 Quran AI")
    
    # Use Tabs for Login vs. Sign Up
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                user = db.get_user(username)
                if user and auth.verify_password(password, user["hashed_password"]):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
    with tab2:
        with st.form("signup_form"):
            st.subheader("Create a New Account")
            new_user = st.text_input("Choose a Username")
            new_email = st.text_input("Email Address")
            new_pass = st.text_input("Choose a Password", type="password")
            if st.form_submit_button("Sign Up"):
                if new_user and new_pass:
                    success = db.create_user(new_user, auth.get_password_hash(new_pass), new_email)
                    if success:
                        st.success("Account created successfully! You can now log in.")
                    else:
                        st.error("Username already exists. Please choose another.")
                else:
                    st.warning("Please fill out all fields.")
    st.stop()

# --- Main Chat App & History Setup ---

# Ensure the user has an active thread
if 'current_thread_id' not in st.session_state:
    user_threads = db.get_threads(st.session_state.username)
    if user_threads:
        st.session_state.current_thread_id = user_threads[0]['id'] # Load most recent
    else:
        st.session_state.current_thread_id = db.create_thread(st.session_state.username)

# Load messages for the current thread from the database
st.session_state.messages = db.get_messages(st.session_state.current_thread_id)

# --- Sidebar Management ---
st.sidebar.title("📖 Quran AI")
st.sidebar.write(f"User: **{st.session_state.username}**")

if st.sidebar.button("➕ New Chat", use_container_width=True):
    st.session_state.current_thread_id = db.create_thread(st.session_state.username)
    st.rerun()

if st.sidebar.button("🗑️ Clear Current Chat", use_container_width=True):
    db.clear_thread(st.session_state.current_thread_id)
    st.rerun()

# Download Chat feature
if st.session_state.messages:
    chat_export = "\n\n".join([f"{m['role'].upper()}:\n{m['content']}" for m in st.session_state.messages])
    st.sidebar.download_button(
        label="💾 Download Chat (.txt)",
        data=chat_export,
        file_name="quran_ai_history.txt",
        mime="text/plain",
        use_container_width=True
    )

st.sidebar.divider()
st.sidebar.subheader("Previous Chats")

# Display history in the sidebar
user_threads = db.get_threads(st.session_state.username)
for thread in user_threads:
    # Highlight the currently active thread
    button_type = "primary" if thread['id'] == st.session_state.current_thread_id else "secondary"
    if st.sidebar.button(f"💬 {thread['title']} ({thread['created_at'][:10]})", key=f"thread_{thread['id']}", type=button_type, use_container_width=True):
        st.session_state.current_thread_id = thread['id']
        st.rerun()

st.sidebar.divider()
if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

# --- Chat Interface ---
st.title("Quranic AI Assistant")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about Islam or the Quran..."):
    # 1. Display and save User message
    st.chat_message("user").markdown(prompt)
    db.add_message(st.session_state.current_thread_id, "user", prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Call AI
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            api_key = st.secrets.get("OLLAMA_API_KEY", "ollama")
            base_url = st.secrets.get("OLLAMA_BASE_URL", "https://test.mynewgen.xyz/v1")
            target_model = st.secrets.get("OLLAMA_MODEL", "aden/quran-guide:latest")

            client = OpenAI(base_url=base_url, api_key=api_key)
            
            system_prompt = (
                "You are an expert Islamic and Quranic scholar AI. "
                "You must answer all questions strictly based on the teachings of Islam, the Quran, and authentic Hadith. "
                "Do not provide information, opinions, or philosophies from the outside world or other belief systems. "
                "If a user asks about a topic outside of Islam, politely decline and state your purpose."
            )

            messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

            stream = client.chat.completions.create(
                model=target_model,
                messages=messages,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # 3. Save Assistant response
            db.add_message(st.session_state.current_thread_id, "assistant", full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Could not connect to AI Server: {e}")

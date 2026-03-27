```markdown
# 📖 Quranic AI Assistant

A fast, secure, and locally-powered AI chatbot designed to answer questions strictly based on Islamic teachings, the Quran, and authentic Hadith. Built with Streamlit and powered by Ollama.

## ✨ Features

* **Authentic Knowledge Base:** Uses the `aden/quran-guide:latest` model and a strict system prompt to ensure answers remain within the context of Islamic theology.
* **User Authentication:** Built-in Sign Up and Login system with securely hashed passwords (using `passlib` and `bcrypt`).
* **Persistent Chat History:** Conversations are saved to a local SQLite database. 
* **Sidebar Management:** * Seamlessly switch between past conversation threads.
  * Start new chats or clear current chat history.
  * Download your entire conversation as a `.txt` file.
* **Cloud-Ready:** Configured to securely connect to a local Ollama instance exposed via a Cloudflare/ngrok tunnel using Streamlit Secrets.

## 🛠️ Prerequisites

* Python 3.9+
* A running instance of [Ollama](https://ollama.com/) with the `aden/quran-guide:latest` model pulled.
* (Optional) A tunneling service like Cloudflare or ngrok if you are hosting the Ollama instance on a different machine than your Streamlit frontend.

## 🚀 Setup & Installation

**1. Clone the repository:**
```bash
git clone [https://github.com/yourusername/quran-ai-assistant.git](https://github.com/yourusername/quran-ai-assistant.git)
cd quran-ai-assistant
```

**2. Create a virtual environment and install dependencies:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure your Secrets:**
Create a `.streamlit` folder in the root directory, and inside it, create a `secrets.toml` file. Add your Ollama connection details:

```toml
# .streamlit/secrets.toml
OLLAMA_BASE_URL = "[https://your-tunnel-url.xyz/v1](https://your-tunnel-url.xyz/v1)"
OLLAMA_API_KEY = "ollama"
OLLAMA_MODEL = "aden/quran-guide:latest"
```
*(Note: If deploying to Streamlit Cloud, paste these exact lines into the App Settings > Secrets section instead).*

**4. Run the Application:**
```bash
streamlit run app.py
```

## 📂 Project Structure

* `app.py`: The main Streamlit application containing the UI, routing, and AI integration logic.
* `database.py`: Handles SQLite connections, table creation, user management, and chat thread history.
* `auth.py`: A lightweight security module utilizing `passlib` to hash and verify user passwords.
* `requirements.txt`: The required Python packages (`streamlit`, `openai`, `passlib[bcrypt]`, `bcrypt==3.2.2`).

## ⚠️ Troubleshooting: Cloudflare Tunnel Issues
If your Ollama instance is hosted behind a Cloudflare tunnel and the app fails to connect, Cloudflare's Bot Fight Mode may be blocking the API request. 
* **Fix:** Go to your Cloudflare Dashboard > Security > WAF > Custom Rules, and create a rule to **Skip** all security checks for requests where the `Hostname` equals your tunnel's domain.
```

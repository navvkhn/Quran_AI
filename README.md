Markdown
# RAG Quran AI Bot

A FastAPI backend for an AI chatbot that uses Retrieval-Augmented Generation (RAG) to search a local SQLite Quran database and feed exact verses to a local instance of Ollama via a tunnel.

## Prerequisites
- Python 3.9+
- A running instance of Ollama exposed via an ngrok/Cloudflare tunnel.
- A converted `quran.db` SQLite database file.

## Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
Install dependencies:

Bash
pip install -r requirements.txt
Database Preparation:
Ensure your Quran .sql dump is converted to a SQLite database named quran.db and placed in the root directory.
(Note: If you only have a .sql file, you can convert it in terminal by running sqlite3 quran.db < your_dump.sql)

Environment Variables:
Create a .env file in the root directory (refer to the provided .env format).

Run the Server:

Bash
uvicorn app:app --host 0.0.0.0 --port 3001 --reload
Testing the API
Navigate to http://localhost:3001/docs in your browser.

Authenticate using the "Authorize" button:

Username: naved

Password: 1234

Use the /chat endpoint to send messages. The bot will query quran.db and send the context to your tunneled Ollama model.

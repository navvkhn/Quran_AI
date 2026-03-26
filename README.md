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

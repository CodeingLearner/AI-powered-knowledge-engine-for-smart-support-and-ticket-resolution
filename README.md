# AI-Powered Support System

An intelligent ticket resolution system using RAG (Retrieval-Augmented Generation) with local AI.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   # Option 1: Direct Python execution
   python ai_powered/app/app.py

   # Option 2: Streamlit command
   streamlit run ai_powered/app/app.py
   ```

3. **Access the web interface:**
   - Open your browser to the URL shown (usually http://localhost:8501)
   - Login with default credentials: `admin` / `admin123` or `testuser` / `user123`
   - Or create a new account

## Features

- 🔐 User authentication and registration
- 🎫 Submit support tickets with AI-powered resolution
- 📚 Knowledge base integration using FAISS vector search
- 🤖 Local LLM integration (Ollama + llama3.1:8b)
- 📊 Ticket history and feedback system
- 🎨 Modern dark-mode UI

## Project Structure

```
ai_powered/
├── app/
│   ├── app.py              # Main Streamlit UI
│   ├── auth_service.py     # User authentication
│   ├── database.py         # SQLite database operations
│   ├── llm_engine.py       # AI resolution engine
│   ├── rag_engine.py       # Knowledge base & embeddings
│   ├── ticket_service.py   # Business logic
│   ├── config.py           # Configuration
│   └── test_backend.py     # Backend testing
├── data/
│   ├── raw/                # Knowledge base documents (PDF/TXT)
│   └── processed/          # Processed data & FAISS index
└── ingest.py               # Document ingestion script
```

## Adding Knowledge Base

1. Place PDF or TXT files in `ai_powered/data/raw/`
2. Run the ingestion script:
   ```bash
   python ai_powered/ingest.py
   ```

## Requirements

- Python 3.8+
- Ollama (for local AI models)
- Install llama3.1:8b model: `ollama pull llama3.1:8b`
- Install tinyllama model: `ollama pull tinyllama`
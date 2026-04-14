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

## 📁 Project Structure

```
AI-powered/
│
├── ai_powered/                # Main application package
│   ├── app/                  # Core application logic
│   │   ├── views/            # UI views (Streamlit dashboards)
│   │   │   ├── __init__.py
│   │   │   ├── admin_dashboard.py
│   │   │   ├── user_dashboard.py
│   │   │   ├── components.py
│   │   │   └── styles.py
│   │   │
│   │   ├── auth_service.py   # Authentication logic
│   │   ├── config.py         # App configuration & environment variables
│   │   ├── database.py       # Database connection and queries
│   │   ├── llm_engine.py     # AI/LLM processing
│   │   ├── rag_engine.py     # Retrieval-Augmented Generation logic
│   │   ├── ticket_service.py # Support ticket handling
│   │   ├── test_backend.py   # Backend tests
│   │   └── test_retrieval.py # Retrieval tests
│   │
│   ├── data/                 # Data storage / datasets
│   ├── ingest.py             # Data ingestion script
│   ├── logo.png              # Project logo
│   └── project_modules_guide.md
│  
│
├── venv/                     # Virtual environment (ignored in Git)
├── .env                      # Environment variables (ignored)
├── .gitignore                # Git ignore rules
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
└── package-lock.json         # Node dependencies (if used)
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
- bcrypt
- langchain
- langchain-community
- langchain-core
- langchain-text-splitters
- faiss-cpu
- tqdm
- pypdf
- numpy
- streamlit
- pandas
- plotly

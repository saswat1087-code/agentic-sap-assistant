# 🤖 Agentic SAP Assistant

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29.0-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An AI-powered assistant that resolves SAP errors across **EWM, MM, QM, PP, AMM, MFG** modules using **Gemini 1.5 Pro** and semantic search over historical incidents.

## 🎯 Features

- 🔍 **Semantic search** over 300+ real SAP incidents
- 🧠 **Agentic reasoning** with Gemini 1.5 Pro
- 📚 **Multi-module support** (EWM, MM, QM, PP, AMM, MFG)
- 💬 **Interactive UI** with Streamlit
- 🗄️ **Supabase vector database** for fast retrieval
- 🐳 **Docker support** for easy deployment
- 📊 **Analytics dashboard** with incident statistics

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Supabase account (free tier works)
- Google Cloud account (for Gemini API)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/agentic-sap-assistant.git
cd agentic-sap-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your credentials

# Import Excel data to Supabase
python scripts/import_excel_to_supabase.py

# Run Streamlit app
streamlit run app/streamlit_app.py

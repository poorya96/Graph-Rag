"""
config.py
─────────
Loads all settings from .env and exposes them as typed constants.
Every other module imports from here — never from os.environ directly.
"""

import os
from dotenv import load_dotenv

# Load .env file from the project root
load_dotenv()
 
# ── Groq ──────────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.environ["GROQ_API_KEY"]
GROQ_MODEL: str = "llama3-70b-8192"   # fastest + smartest free Groq model
 
# ── Neo4j ─────────────────────────────────────────────────────────────────────
NEO4J_URI: str      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD: str = os.environ["NEO4J_PASSWORD"]
 
# ── Data ──────────────────────────────────────────────────────────────────────
CSV_PATH: str = os.getenv("CSV_PATH", "database/faq_qa_pairs.csv")
 
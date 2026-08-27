"""
config.py
---------
Central place for all configurable constants used across the app.
Keeping these in one file makes it trivial to tune scoring weights,
switch the AI feedback backend, or change the DB location without
touching business logic in other modules.
"""

import os

# ----------------------------------------------------------------------
# Database
# ----------------------------------------------------------------------
DB_PATH = os.getenv("RESUME_DB_PATH", "resume_analyzer.db")

# ----------------------------------------------------------------------
# File upload constraints
# ----------------------------------------------------------------------
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 5

# ----------------------------------------------------------------------
# Feedback generation backend
# ----------------------------------------------------------------------
# "template"    -> pure Python rule-based feedback. No ML downloads.
#                  ALWAYS WORKS. Best default for fresh installs / HF Spaces
#                  free tier / CI environments.
# "ollama"      -> calls a locally running Ollama server (http://localhost:11434).
#                  Best for local development with a real LLM, offline, private.
#                  Requires `ollama serve` + `ollama pull llama3` beforehand.
# "huggingface" -> uses a local transformers pipeline (flan-t5-base by default).
#                  Works on HF Spaces but slower cold start & more RAM.
FEEDBACK_BACKEND = os.getenv("FEEDBACK_BACKEND", "template")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

HF_FEEDBACK_MODEL = os.getenv("HF_FEEDBACK_MODEL", "google/flan-t5-base")

# ----------------------------------------------------------------------
# Scoring weights (must sum to 1.0)
# ----------------------------------------------------------------------
WEIGHT_KEYWORD_MATCH = 0.5
WEIGHT_STRUCTURE = 0.5

# Minimum resume length (in words) before we flag it as "too short"
MIN_RESUME_WORDS = 150
MAX_RESUME_WORDS = 1200

# Section headings we look for to gauge structural completeness
EXPECTED_SECTIONS = [
    "experience",
    "education",
    "skills",
    "summary",
    "objective",
    "projects",
    "certifications",
]

# A small built-in technical/soft-skill vocabulary used as a fallback
# keyword universe when no job description is supplied.
DEFAULT_SKILL_VOCAB = [
    "python", "java", "javascript", "sql", "aws", "azure", "gcp", "docker",
    "kubernetes", "react", "node.js", "django", "flask", "machine learning",
    "deep learning", "nlp", "data analysis", "data visualization", "git",
    "agile", "scrum", "communication", "leadership", "project management",
    "excel", "tableau", "power bi", "rest api", "microservices", "ci/cd",
    "testing", "linux", "c++", "html", "css", "typescript", "pandas",
    "numpy", "tensorflow", "pytorch", "spark", "hadoop", "problem solving",
]

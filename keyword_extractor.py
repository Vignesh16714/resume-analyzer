"""
keyword_extractor.py
---------------------
Extracts candidate keywords/skills from resume and job-description text,
then computes overlap ("keyword match") between the two.

Design notes
------------
* spaCy (en_core_web_sm) is used for tokenization, stopword removal and
  noun-chunk extraction because it's fast and lightweight compared to a
  full transformer model — appropriate for a real-time UI.
* If the spaCy model isn't installed (e.g. first run before
  `python -m spacy download en_core_web_sm`), we fall back to a pure
  regex tokenizer so the app NEVER crashes — it just gets a little less
  linguistically precise.
* A small built-in technical-skill vocabulary (config.DEFAULT_SKILL_VOCAB)
  is used to boost recall for common resume/JD keywords that generic
  noun-chunking might miss (e.g. "AWS", "CI/CD").
"""

import re
from collections import Counter
from typing import List, Tuple

from config import DEFAULT_SKILL_VOCAB

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for",
    "with", "is", "are", "was", "were", "be", "been", "being", "this",
    "that", "these", "those", "as", "at", "by", "it", "its", "from",
    "we", "you", "your", "our", "will", "can", "have", "has", "had",
}

_nlp = None
_SPACY_AVAILABLE = False

try:
    import spacy

    try:
        _nlp = spacy.load("en_core_web_sm")
        _SPACY_AVAILABLE = True
    except OSError:
        # Model not downloaded yet — fall back gracefully (see module docstring).
        _nlp = None
        _SPACY_AVAILABLE = False
except ImportError:
    _SPACY_AVAILABLE = False


def _regex_tokenize(text: str) -> List[str]:
    """Fallback tokenizer used when spaCy / its model is unavailable."""
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#/-]{1,}", text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]


def _spacy_tokenize(text: str) -> List[str]:
    """Lemmatized, stopword-free tokens plus multi-word noun chunks."""
    doc = _nlp(text.lower())
    tokens = [
        tok.lemma_ for tok in doc
        if not tok.is_stop and not tok.is_punct and not tok.is_space
        and len(tok.lemma_) > 2
    ]
    noun_chunks = [chunk.text.strip() for chunk in doc.noun_chunks if len(chunk.text.strip()) > 3]
    return tokens + noun_chunks


def extract_keywords(text: str, top_n: int = 25) -> List[str]:
    """
    Returns the top_n most frequent meaningful keywords/phrases in `text`,
    plus any DEFAULT_SKILL_VOCAB terms found verbatim (so important but
    low-frequency skills like "docker" aren't dropped just because they
    appear once).
    """
    text_lower = text.lower()

    tokens = _spacy_tokenize(text) if _SPACY_AVAILABLE else _regex_tokenize(text)
    freq = Counter(tokens)
    frequent_keywords = [kw for kw, _ in freq.most_common(top_n)]

    vocab_hits = [skill for skill in DEFAULT_SKILL_VOCAB if skill in text_lower]

    # Preserve order, de-duplicate.
    combined = []
    for kw in vocab_hits + frequent_keywords:
        if kw not in combined:
            combined.append(kw)
    return combined[:top_n]


def compute_keyword_match(
    resume_text: str, job_description: str
) -> Tuple[float, List[str], List[str]]:
    """
    Compares resume keywords against job-description keywords.

    Returns:
        score          -- percentage (0-100) of JD keywords found in resume
        matched        -- JD keywords present in the resume
        missing        -- JD keywords absent from the resume
    """
    resume_lower = resume_text.lower()

    if job_description and job_description.strip():
        jd_keywords = extract_keywords(job_description, top_n=30)
    else:
        # No JD supplied: fall back to the general skill vocabulary so the
        # app still produces a meaningful, non-zero keyword score.
        jd_keywords = DEFAULT_SKILL_VOCAB

    if not jd_keywords:
        return 0.0, [], []

    matched, missing = [], []
    for kw in jd_keywords:
        # Simple substring containment is robust to lemma/plural mismatches
        # for short technical terms; good enough for a scoring heuristic.
        if kw.lower() in resume_lower:
            matched.append(kw)
        else:
            missing.append(kw)

    score = round((len(matched) / len(jd_keywords)) * 100, 1)
    return score, matched, missing

import ollama
import logging
import re

import config
import rag_engine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MODEL_NAME = config.OLLAMA_MODEL

GENERIC_RESPONSE_PATTERNS = (
    "contact support",
    "reach out to your administrator",
    "not enough information",
    "unable to determine",
    "please provide more details",
    "i don't have",
    "i do not have",
    "cannot assist",
)


def check_model_availability():
    """Checks if the model is available locally, pulls if not."""
    try:
        models_response = ollama.list()
        model_names = []
        if 'models' in models_response:
            for m in models_response['models']:
                if isinstance(m, dict):
                    model_names.append(m.get('name', ''))
                    model_names.append(m.get('model', ''))

        if MODEL_NAME not in model_names and f"{MODEL_NAME}:latest" not in model_names:
            logging.info(f"Model {MODEL_NAME} not found. Pulling...")
            ollama.pull(MODEL_NAME)
            logging.info(f"Model {MODEL_NAME} pulled successfully.")
        else:
            logging.info(f"Model {MODEL_NAME} is ready.")
    except Exception as e:
        logging.warning(f"Error checking model ({e}). Attempting pull...")
        try:
            ollama.pull(MODEL_NAME)
        except Exception as pull_error:
            logging.error(f"Failed to pull model: {pull_error}")


def _slugify_filename(text):
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return "_".join(tokens[:6]) if tokens else "missing_knowledge_article"


def _suggest_kb_filename(title, description, category):
    source_text = f"{title} {description}".strip().lower()
    tokens = [
        token for token in re.findall(r"[a-z0-9]+", source_text)
        if token not in {
            "the", "and", "for", "with", "from", "that",
            "this", "have", "need", "cannot", "cant"
        }
    ]
    phrase = " ".join(tokens[:6]) or category or "knowledge gap"
    return f"{_slugify_filename(phrase)}_guide.md"


def _calculate_confidence(retrieval_score, kb_context_found, resolution_text, had_error):
    """
    Confidence scoring:
    - retrieval_score : 0.0–1.0  (from FAISS, up to 0.5 weight)
    - kb_context_found: +0.3     (big boost — we found real knowledge)
    - resolution length: +0.1    (LLM gave a real answer)
    - generic patterns: -0.3     (LLM admitted it didn't know)
    """
    if had_error:
        return 0.0

    # ✅ Cap retrieval contribution at 0.5 so other signals matter
    confidence = min(retrieval_score, 0.5)

    # ✅ Increased weight — finding KB context is the strongest signal
    if kb_context_found:
        confidence += 0.3

    # ✅ LLM produced a meaningful response
    if resolution_text and len(resolution_text.strip()) >= 80:
        confidence += 0.1

    # ✅ Penalize generic/unhelpful LLM responses harder
    lowered = resolution_text.lower() if resolution_text else ""
    if any(pattern in lowered for pattern in GENERIC_RESPONSE_PATTERNS):
        confidence -= 0.3

    return max(0.0, min(1.0, round(confidence, 3)))


def analyze_ticket(title, description, priority, category):
    """Uses LLM + RAG context to generate a resolution."""
    logging.info("Retrieving relevant context from knowledge base...")
    retrieval = rag_engine.get_relevant_context(f"{title} {description}")
    context        = retrieval.get("context_text", "")
    retrieval_score = retrieval.get("retrieval_score", 0.0)
    kb_context_found = retrieval.get("kb_context_found", False)

    # ✅ Build context block clearly
    if kb_context_found and context:
        context_block = f"""KNOWLEDGE BASE CONTEXT (use this as your primary source):
---
{context}
---"""
    else:
        context_block = "KNOWLEDGE BASE CONTEXT: No relevant articles found."

    # ✅ Fixed prompt — explicitly instructs LLM to use context
    user_prompt = f"""
{context_block}

SUPPORT TICKET:
- Title: {title}
- Category: {category}
- Priority: {priority}
- Description: {description}

Using ONLY the knowledge base context above (if available), provide a clear resolution.
If the context is relevant, base your answer on it directly.
Format your response with bullet points.
Do NOT say "As an AI" or "I cannot help".
If no context is available, provide general best-practice steps.
"""

    # ✅ Use system + user roles — llama3.1:8b is fine-tuned for this
    system_prompt = (
        "You are a precise IT support assistant. "
        "You resolve support tickets using the provided knowledge base context. "
        "Be concise, practical, and always respond with actionable steps."
    )

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': user_prompt},
            ],
            options={
                "temperature": 0.1,   # ✅ Low temp = factual, consistent answers
                "num_predict": 512,   # ✅ Enough for a good resolution
            }
        )
        resolution_text = response['message']['content'].strip()

        confidence_score = _calculate_confidence(
            retrieval_score=retrieval_score,
            kb_context_found=kb_context_found,
            resolution_text=resolution_text,
            had_error=False,
        )

        resolved_threshold = config.get_float_env("AI_CONFIDENCE_THRESHOLD", 0.65)
        if confidence_score >= resolved_threshold:
            resolution_status = "resolved"
        elif confidence_score >= 0.35:
            resolution_status = "tentative"   # ✅ Added middle ground
        else:
            resolution_status = "unresolved"

        logging.info(
            f"Ticket analyzed — confidence: {confidence_score:.1%}, "
            f"status: {resolution_status}, kb_found: {kb_context_found}"
        )

        return {
            "category":             category,
            "resolution_text":      resolution_text,
            "confidence_score":     confidence_score,
            "resolution_status":    resolution_status,
            "retrieval_score":      retrieval_score,
            "kb_context_found":     kb_context_found,
            "context_matches":      retrieval.get("matches", []),
            "suggested_kb_filename": (
                None if resolution_status == "resolved"
                else _suggest_kb_filename(title, description, category)
            ),
            "error": None,
        }

    except Exception as e:
        error_msg = str(e)
        logging.error(f"LLM Error: {error_msg}")
        return {
            "category":             category,
            "resolution_text":      f"Failed to generate resolution. Error: {error_msg}",
            "confidence_score":     0.0,
            "resolution_status":    "unresolved",
            "retrieval_score":      retrieval_score,
            "kb_context_found":     kb_context_found,
            "context_matches":      retrieval.get("matches", []),
            "suggested_kb_filename": _suggest_kb_filename(title, description, category),
            "error":                error_msg,
        }


if __name__ == "__main__":
    analysis = analyze_ticket("Internet down", "My wifi is not connecting", "High", "Network")
    print(f"Confidence : {analysis['confidence_score']:.1%}")
    print(f"Status     : {analysis['resolution_status']}")
    print(f"KB Found   : {analysis['kb_context_found']}")
    print(f"Resolution :\n{analysis['resolution_text']}")
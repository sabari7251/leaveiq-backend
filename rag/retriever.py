from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR / "chroma_db"

# Refining
LOW_VALUE_CATEGORIES = {"Footer", "Header"}
MIN_CHARS = 40
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "from",
    "in",
    "is",
    "me",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "which",
    "who",
}
FIELD_HINT_WORDS = {"address", "date", "id", "name", "no", "number"}
######################################

embeddings=HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

_db = None

def get_db(force_reload=False):
    global _db
    if _db is None or force_reload:
        if not CHROMA_DIR.exists():
            print("Chroma DB directory not found. Initializing database with default policy...")
            from rag.ingest import ingest_pdf, PDF_PATH
            try:
                ingest_pdf(PDF_PATH)
            except Exception as e:
                print(f"Failed to initialize Chroma DB from default policy: {e}")
        
        _db = Chroma(
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DIR)
        )
    return _db


# Helper Functions

def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _is_useful_doc(doc) -> bool:
    text = doc.page_content.strip()
    metadata = doc.metadata or {}

    if metadata.get("category") in LOW_VALUE_CATEGORIES:
        return False

    if len(text) < MIN_CHARS:
        return False

    if re.fullmatch(r"[\W\d_]+", text):
        return False

    return True


def _query_terms(question: str) -> list[str]:
    terms = re.findall(r"[a-zA-Z0-9]+", question.lower())
    return [term for term in terms if term not in STOP_WORDS and len(term) >= 3]


def _lexical_candidates(question: str) -> list[Document]:
    terms = _query_terms(question)
    phrase = " ".join(terms)
    compact_phrase = "".join(terms)
    label_terms = [term for term in terms if term not in FIELD_HINT_WORDS]
    compact_label = "".join(label_terms)

    if not terms:
        return []

    db = get_db()
    rows = db.get(include=["documents", "metadatas"])
    scored_candidates = []

    for text, metadata in zip(rows["documents"], rows["metadatas"]):
        normalized_text = _normalize_text(text)
        compact_text = normalized_text.replace(" ", "")
        score = sum(1 for term in terms if term in normalized_text)

        if phrase and phrase in normalized_text:
            score += len(terms) * 2

        if compact_phrase and compact_phrase in compact_text:
            score += len(terms) * 2

        if compact_label and compact_label != compact_phrase and compact_label in compact_text:
            score += len(label_terms) * 2

        if compact_label and f"{compact_label}:" in compact_text:
            score += len(label_terms) * 4 + len(terms)

        if score:
            scored_candidates.append((
                score,
                Document(page_content=text, metadata=metadata or {}),
            ))

    scored_candidates.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored_candidates[:10]]
#________________________________________________________#

def search_policy(question:str,**kwargs):
    db = get_db()
    candidates = _lexical_candidates(question)
    candidates.extend(db.similarity_search(question, k=20))
    result = []
    seen = set()

    for doc in candidates:
        key = _normalize_text(doc.page_content)
        if key in seen or not _is_useful_doc(doc):
            continue

        seen.add(key)
        result.append(doc)

        if len(result) == kwargs.get("k", 5):
            break

    if not result:
        print(f"No documents found in Chroma collection at {CHROMA_DIR}")
        return ""

    context = "\n\n---\n\n".join(
        [doc.page_content for doc in result]
    )
    
    
    return context

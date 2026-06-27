import re

from config import PINECONE_API_KEY, PINECONE_INDEX

INDEX_NAME = PINECONE_INDEX

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

_db = None
_embeddings = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings

        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return _embeddings


def _get_pinecone_index():
    from pinecone import Pinecone

    if not PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY environment variable is required")
    if not INDEX_NAME:
        raise RuntimeError("PINECONE_INDEX environment variable is required")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    return pc.Index(INDEX_NAME)

def get_db(force_reload=False):
    from langchain_pinecone import PineconeVectorStore

    global _db
    if _db is None or force_reload:
        _db = PineconeVectorStore(
            index=_get_pinecone_index(),
            embedding=_get_embeddings()
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



def search_policy(question:str,**kwargs):
    db = get_db()
    candidates=db.similarity_search(question, k=20)
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
        print(f"No documents found in Pinecone")
        return ""

    context = "\n\n---\n\n".join(
        [doc.page_content for doc in result]
    )
    
    
    return context


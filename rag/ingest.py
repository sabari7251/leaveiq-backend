from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from pathlib import Path
import re
import shutil

BASE_DIR = Path(__file__).resolve().parent
PDF_PATH = BASE_DIR / "Corporate Leave Policy Template.pdf"
CHROMA_DIR = BASE_DIR / "chroma_db"
LOW_VALUE_CATEGORIES = {"Footer", "Header"}
MIN_CHARS = 40


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def is_useful_chunk(doc) -> bool:
    text = doc.page_content.strip()
    metadata = doc.metadata or {}

    if metadata.get("category") in LOW_VALUE_CATEGORIES:
        return False

    if len(text) < MIN_CHARS:
        return False

    if re.fullmatch(r"[\W\d_]+", text):
        return False

    return True

def ingest_pdf(pdf_path: Path, chroma_dir: Path = CHROMA_DIR):
    loader = PyPDFLoader(file_path=str(pdf_path))
    docs=loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=40
    )

    chunks = splitter.split_documents(docs)
    chunks = filter_complex_metadata(chunks)
    deduped_chunks = []
    seen = set()

    for chunk in chunks:
        if not is_useful_chunk(chunk):
            continue

        key = normalize_text(chunk.page_content)
        if key in seen:
            continue

        seen.add(key)
        deduped_chunks.append(chunk)

    if chroma_dir.exists():
        shutil.rmtree(chroma_dir)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = Chroma.from_documents(
        documents=deduped_chunks,
        embedding=embeddings,
        persist_directory=str(chroma_dir)
    )

    # --- Windows file-handle release ---
    if hasattr(db, "_client") and hasattr(db._client, "close"):
        db._client.close()
    del db
    import gc
    gc.collect()
    # ------------------------------------

    return len(deduped_chunks), len(chunks)


if __name__ == "__main__":
    cleaned, raw = ingest_pdf(PDF_PATH)
    print(f"Indexed {cleaned} clean chunks from {raw} raw chunks.")

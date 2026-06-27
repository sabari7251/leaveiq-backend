from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from pathlib import Path
import re,os

from config import PINECONE_API_KEY, PINECONE_INDEX

BASE_DIR = Path(__file__).resolve().parent
PDF_PATH = BASE_DIR / "Corporate Leave Policy Template.pdf"

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

def _get_pinecone_index():
    if not PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY environment variable is required")
    if not PINECONE_INDEX:
        raise RuntimeError("PINECONE_INDEX environment variable is required")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    return pc.Index(PINECONE_INDEX)


def ingest_pdf(pdf_path: Path, **kwargs):
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

    

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    index = _get_pinecone_index()
    
    index.delete(delete_all=True)

    PineconeVectorStore.from_documents(
        documents=deduped_chunks,
        embedding=embeddings,
        index_name=PINECONE_INDEX
    )


    return len(deduped_chunks), len(chunks)


if __name__ == "__main__":
    cleaned, raw = ingest_pdf(PDF_PATH)
    print(f"Indexed {cleaned} clean chunks from {raw} raw chunks.")

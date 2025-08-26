# src/document_preprocessor.py
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import all three loaders from their correct locations
from langchain_upstage.document_parse import UpstageDocumentParseLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_unstructured import UnstructuredLoader 

# Import config values
from src.config import (
    INGESTION_PARSER, 
    UPSTAGE_API_KEY, 
    API_LOADER_CONFIG,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)

class DocumentPreprocessor:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.parser_type = INGESTION_PARSER
        
        if self.parser_type == "api":
            self.loader = UpstageDocumentParseLoader(
                str(self.filepath), 
                api_key=UPSTAGE_API_KEY, 
                **API_LOADER_CONFIG
            )
        elif self.parser_type == "unstructured":
            # --- FIX: Specify the language for better OCR accuracy ---
            self.loader = UnstructuredLoader(
                file_path=str(self.filepath), 
                mode="paged",
                strategy="hi_res",
                languages=["kor"] # Specify Korean language pack for Tesseract
            )
        else: # Default to "local" (PyMuPDF)
            self.loader = PyMuPDFLoader(str(self.filepath))

        # Use the imported config values for the splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, 
            chunk_overlap=CHUNK_OVERLAP
        )

    def process(self) -> list[Document]:
        documents = self.loader.load()
        
        if self.parser_type == "api":
            sanitized_docs = [self._sanitize_doc(doc) for doc in documents]
            return self.splitter.split_documents(sanitized_docs)
        
        return self.splitter.split_documents(documents)

    @staticmethod
    def _sanitize_doc(doc: Document) -> Document:
        meta = dict(doc.metadata)
        if "coordinates" in meta:
            meta.pop("coordinates")
        return Document(page_content=doc.page_content, metadata=meta)

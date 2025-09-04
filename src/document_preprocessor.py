# src/document_preprocessor.py
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import all three loaders from their correct locations
from langchain_upstage.document_parse import UpstageDocumentParseLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_unstructured import UnstructuredLoader 

# --- NEW IMPORTS ---
from src.vision_processor import describe_image
from src.audio_processor import transcribe_audio

# Import config values
from src.config import (
    INGESTION_PARSER, 
    UPSTAGE_API_KEY, 
    API_LOADER_CONFIG,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    VISION_MODEL,
    ASR_MODEL,
)

class DocumentPreprocessor:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.parser_type = INGESTION_PARSER

    def process(self) -> list[Document]:
        """
        파일 확장자에 따라 적절한 처리기를 호출하여 문서를 처리합니다.
        이미지나 오디오는 텍스트 설명으로 변환된 후 Document 객체로 만들어집니다.
        """
        file_extension = self.filepath.suffix.lower()
        
        content = ""
        # --- VISION PROCESSING ---
        if file_extension in ['.jpg', '.jpeg', '.png', '.webp']:
            # 이미지 파일인 경우, vision_processor를 사용하여 설명을 생성합니다.
            content = describe_image(self.filepath, VISION_MODEL)
            # 텍스트 내용을 단일 Document 객체로 직접 반환합니다.
            # 추가적인 텍스트 분할이 필요하지 않을 수 있습니다.
            return [Document(page_content=content, metadata={"source": str(self.filepath)})]

        # --- AUDIO PROCESSING ---
        elif file_extension in ['.mp3', '.wav', '.flac', '.m4a']:
            # 오디오 파일인 경우, audio_processor를 사용하여 텍스트로 변환합니다.
            content = transcribe_audio(self.filepath, ASR_MODEL)
            # 변환된 텍스트를 Document 객체로 만듭니다.
            documents = [Document(page_content=content, metadata={"source": str(self.filepath)})]
            # 텍스트가 매우 길 경우를 대비해 분할기를 적용합니다.
            return self._split_documents(documents)

        # --- EXISTING PDF/TEXT PROCESSING ---
        else:
            # 기존 로더 로직을 사용하여 텍스트 기반 문서를 처리합니다.
            loader = self._get_loader()
            documents = loader.load()
            return self._split_documents(documents)

    def _get_loader(self):
        # 기존 로더 선택 로직은 이 헬퍼 메서드로 분리합니다.
        if self.parser_type == "api":
            return UpstageDocumentParseLoader(str(self.filepath), api_key=UPSTAGE_API_KEY, **API_LOADER_CONFIG)
        elif self.parser_type == "unstructured":
            return UnstructuredLoader(file_path=str(self.filepath), mode="paged", strategy="hi_res", languages=["kor"])
        else: # Default to "local" (PyMuPDF)
            return PyMuPDFLoader(str(self.filepath))

    def _split_documents(self, documents: list[Document]) -> list[Document]:
        # 텍스트 분할 로직을 헬퍼 메서드로 분리합니다.
        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        processed_docs = [self._sanitize_doc(doc) for doc in documents]
        return splitter.split_documents(processed_docs)

    @staticmethod
    def _sanitize_doc(doc: Document) -> Document:
        meta = dict(doc.metadata)
        if "coordinates" in meta:
            meta.pop("coordinates")
        return Document(page_content=doc.page_content, metadata=meta)
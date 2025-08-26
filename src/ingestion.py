# src/ingestion.py
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from src.config import INGESTION_CHUNK_SIZE, INGESTION_CHUNK_OVERLAP
from src.logger import get_logger



# 로거 초기화
logger = get_logger(__name__)


class DocumentIngestor:
    """
    소스 디렉토리에서 문서를 로드하고, 처리하여 청크로 분할하는 클래스.
    """

    def __init__(self, source_dir: str | Path):
        """
        DocumentIngestor를 초기화합니다.

        Args:
            source_dir (str): 처리할 PDF 파일이 있는 소스 디렉토리.
        """
        self.source_dir = Path(source_dir)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=INGESTION_CHUNK_SIZE,  # 청크 크기
            chunk_overlap=INGESTION_CHUNK_OVERLAP,  # 청크 간 중첩 크기
            length_function=len,
        )
        logger.info("DocumentIngestor가 초기화되었습니다.")

    def _load_documents(self) -> list[Document]:
        """
        지정된 디렉토리에서 PDF 문서를 로드하여 페이지별로 분할합니다.
        """
        all_pages = []
        if not self.source_dir.is_dir():
            logger.error(f"디렉토리를 찾을 수 없습니다: {self.source_dir}")
            return []

        pdf_files = [f for f in self.source_dir.iterdir() if f.is_file() and f.name.lower().endswith(".pdf")]
        logger.info(f"'{self.source_dir}'에서 {len(pdf_files)}개의 PDF 파일을 찾았습니다.")

        for pdf_path in pdf_files:
            # Prefer PyMuPDF (fitz) when available because it often handles
            # CJK fonts and complex encodings better than pypdf-based loaders.
            try:
                import fitz  # PyMuPDF

                logger.info(f"Using PyMuPDF (fitz) to load '{pdf_path.name}'")
                doc = fitz.open(str(pdf_path))
                pages = []
                for i in range(len(doc)):
                    page = doc.load_page(i)
                    text = page.get_text("text") or ""
                    pages.append(Document(page_content=text, metadata={"source": str(pdf_path), "page": i + 1}))

                logger.info(f"'{pdf_path.name}' 파일을 PyMuPDF로 로드하여 {len(pages)}개의 페이지로 분할했습니다.")
                all_pages.extend(pages)

            except Exception as e_fit:
                # If PyMuPDF isn't installed or fails, fall back to PyPDFLoader
                logger.warning(f"PyMuPDF unavailable or failed for '{pdf_path.name}': {e_fit}; falling back to PyPDFLoader")
                try:
                    loader = PyPDFLoader(str(pdf_path))
                    pages = loader.load_and_split()
                    logger.info(f"'{pdf_path.name}' 파일을 PyPDFLoader로 로드하여 {len(pages)}개의 페이지로 분할했습니다.")
                    all_pages.extend(pages)
                except Exception as e:
                    logger.error(f"'{pdf_path.name}' 파일 처리 중 오류 발생: {e}")

        return all_pages

    def ingest(self) -> list[Document]:
        """
        문서 로딩 및 텍스트 분할의 전체 프로세스를 실행합니다.
        """
        logger.info("문서 처리(Ingestion)를 시작합니다...")
        documents = self._load_documents()
        if not documents:
            logger.warning("로드된 문서가 없어 처리를 중단합니다.")
            return []

        chunked_documents = self.text_splitter.split_documents(documents)
        logger.info(f"총 {len(documents)}개의 페이지를 {len(chunked_documents)}개의 청크로 분할했습니다.")
        logger.info("문서 처리가 완료되었습니다.")
        return chunked_documents

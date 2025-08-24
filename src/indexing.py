__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
# src/indexing.py
import shutil

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from src.config import ROOT_DIR
from src.ingestion import DocumentIngestor
from src.logger import get_logger


# 로거 초기화
logger = get_logger(__name__)

# --- 설정 ---
# PDF 문서가 저장된 디렉토리 경로
PDF_DIRECTORY = str(ROOT_DIR / "data" / "source_pdfs")
# 벡터 스토어를 저장할 디렉토리 경로
VECTOR_STORE_PATH = str(ROOT_DIR / "vector_store" / "chroma_db")
# 사용할 임베딩 모델 이름 (README.md에 명시된 모델)
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"


class VectorStoreManager:
    """
    벡터 스토어 생성 및 관리를 담당하는 클래스.
    """

    def __init__(self, pdf_dir: str, store_path: str, embedding_model: str):
        """
        VectorStoreManager를 초기화합니다.

        Args:
            pdf_dir (str): 소스 PDF 파일이 있는 디렉토리.
            store_path (str): 벡터 스토어를 저장할 경로.
            embedding_model (str): 임베딩을 생성할 모델의 이름.
        """
        self.pdf_dir = pdf_dir
        self.store_path = store_path
        self.embedding_model_name = embedding_model
        self.ingestor = DocumentIngestor(source_dir=self.pdf_dir)

        # 임베딩 모델 초기화 (GPU 사용 설정)
        model_kwargs = {"device": "cuda"}  # GPU 사용 가능 시 'cuda', 그렇지 않으면 'cpu'
        encode_kwargs = {"normalize_embeddings": True}  # 임베딩 정규화
        self.embedding_function = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )
        logger.info(f"임베딩 모델 '{self.embedding_model_name}'을(를) 초기화했습니다.")

    def create_vector_store(self):
        """
        전체 벡터 스토어 생성 파이프라인을 실행합니다.
        1. 문서 로드 및 분할
        2. 벡터 스토어 생성 및 저장
        """
        logger.info("--- 벡터 스토어 생성을 시작합니다 ---")

        # 1. 문서 로드 및 분할
        chunked_documents = self.ingestor.ingest()
        if not chunked_documents:
            logger.warning("처리할 문서가 없습니다. 벡터 스토어 생성을 중단합니다.")
            return

        # 2. 기존 벡터 스토어 디렉토리 삭제
        if (ROOT_DIR / "vector_store" / "chroma_db").exists():
            logger.warning(f"기존 벡터 스토어를 삭제합니다: {self.store_path}")
            shutil.rmtree(self.store_path)

        # 3. ChromaDB 벡터 스토어 생성 및 저장
        logger.info(f"'{self.store_path}' 경로에 벡터 스토어를 생성 및 저장합니다.")
        vector_store = Chroma.from_documents(
            documents=chunked_documents,
            embedding=self.embedding_function,
            persist_directory=self.store_path,
        )

        logger.info("--- 벡터 스토어 생성이 완료되었습니다 ---")
        logger.info(f"총 {vector_store._collection.count()}개의 문서 조각이 벡터 스토어에 저장되었습니다.")


if __name__ == "__main__":
    # 이 스크립트를 직접 실행하여 벡터 스토어를 생성할 수 있습니다.
    manager = VectorStoreManager(
        pdf_dir=PDF_DIRECTORY,
        store_path=VECTOR_STORE_PATH,
        embedding_model=EMBEDDING_MODEL_NAME,
    )
    manager.create_vector_store()
    print("\n인덱싱 완료. 벡터 스토어가 'vector_store' 디렉토리에 생성되었습니다.")

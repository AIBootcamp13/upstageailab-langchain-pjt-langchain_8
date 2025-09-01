# src/vector_store.py
from langchain_chroma import Chroma
from langchain_core.documents import Document

# 지원하는 모든 임베딩 모델 클래스를 import합니다.
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

# 중앙 설정 파일에서 필요한 설정값을 가져옵니다.
from src.config import (
    EMBEDDING_PROVIDER,
    EMBEDDING_MODEL,
    COLLECTION_NAME,
    # --- ADDED: 영속성 디렉토리 경로 import ---
    VECTOR_STORE_PERSIST_DIR,
)

class VectorStore:
    """
    LangChain 표준 인터페이스를 따르는 벡터 스토어 래퍼 클래스.
    설정에 따라 적절한 임베딩 모델을 사용하여 문서를 벡터화하고 ChromaDB에 저장합니다.
    --- MODIFIED: 이제 디스크에 데이터를 영속적으로 저장합니다. ---
    """
    def __init__(self):
        # 설정된 임베딩 제공자(provider)에 따라 모델을 초기화합니다.
        if EMBEDDING_PROVIDER == "openai":
            # OpenAI API를 사용하는 경우 — but if running Local GPU profile, prefer local embeddings
            # The embedding provider comes from the active profile; if a local profile
            # is selected it should not be 'openai'. We keep this branch for explicit
            # OpenAI profiles only.
            self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        elif EMBEDDING_PROVIDER == "huggingface":
            # 로컬 Hugging Face 모델을 사용하는 경우 (GPU 활용)
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={'device': 'cuda'}, # GPU가 있는 환경을 위함
                encode_kwargs={'normalize_embeddings': True},
            )
        else:
            raise ValueError(f"지원되지 않는 임베딩 제공자: {EMBEDDING_PROVIDER}")

        # --- ChromaDB가 디스크에 저장하도록 persist_directory를 지정합니다. ---
        # 이 설정을 통해 데이터베이스가 메모리가 아닌 파일로 저장되어,
        # 애플리케이션을 재시작해도 임베딩된 데이터를 그대로 사용할 수 있습니다.
        self.store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=str(VECTOR_STORE_PERSIST_DIR),
        )

    def add_documents(self, documents: list[Document], **kwargs) -> list[str]:
        """문서를 벡터 스토어에 추가합니다."""
        return self.store.add_documents(documents, **kwargs)

    def as_retriever(self, **kwargs):
        """벡터 스토어를 LangChain Retriever로 변환합니다."""
        return self.store.as_retriever(**kwargs)

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

# 지원하는 모든 임베딩 모델 클래스를 import합니다.
from langchain_openai import OpenAIEmbeddings

# 중앙 설정 파일에서 필요한 설정값을 가져옵니다.
from src.config import COLLECTION_NAME, EMBEDDING_MODEL, EMBEDDING_PROVIDER


class VectorStore:
    """
    LangChain 표준 인터페이스를 따르는 벡터 스토어 래퍼 클래스.
    설정에 따라 적절한 임베딩 모델을 사용하여 문서를 벡터화하고 ChromaDB에 저장합니다.
    """

    def __init__(self):
        # 설정된 임베딩 제공자(provider)에 따라 모델을 초기화합니다.
        if EMBEDDING_PROVIDER == "openai":
            # OpenAI API를 사용하는 경우
            self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        elif EMBEDDING_PROVIDER == "huggingface":
            # 로컬 Hugging Face 모델을 사용하는 경우 (GPU 활용)
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={"device": "cuda"},  # GPU가 있는 환경을 위함
                encode_kwargs={"normalize_embeddings": True},
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {EMBEDDING_PROVIDER}")

        # ChromaDB 벡터 스토어를 초기화합니다.
        self.store = Chroma(collection_name=COLLECTION_NAME, embedding_function=self.embeddings)

    def get_all_documents(self) -> list[Document]:
        """
        add_documents에 넣었던 Document 리스트를 '그대로' 복원합니다.
        - metadata는 어떤 키도 추가/변경하지 않고 그대로 반환합니다.
        - 컬렉션이 큰 경우 메모리 사용량이 커질 수 있습니다. 필요 시 iter_all_documents를 사용하세요.
        """
        data = self.store.get(include=["documents", "metadatas"])
        docs = data.get("documents", [])
        metas = data.get("metadatas", [])
        return [
            Document(page_content=content, metadata=(meta or {})) for content, meta in zip(docs, metas, strict=False)
        ]

    def add_documents(self, documents: list[Document], **kwargs) -> list[str]:
        """문서를 벡터 스토어에 추가합니다."""
        return self.store.add_documents(documents, **kwargs)

    def as_retriever(self, **kwargs):
        """벡터 스토어를 LangChain Retriever로 변환합니다."""
        from src.config import SEARCH_KWARGS, SEARCH_TYPE  # 순환 참조 방지를 위해 늦게 import

        # 검색 관련 설정을 config 파일에서 읽어와 적용합니다.
        search_kwargs = kwargs.copy()
        search_kwargs.update(SEARCH_KWARGS)
        return self.store.as_retriever(search_type=SEARCH_TYPE, search_kwargs=search_kwargs)

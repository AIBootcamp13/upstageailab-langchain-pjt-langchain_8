# src/retriever.py
from src.vector_store import VectorStore
from src.config import SEARCH_KWARGS, SEARCH_TYPE

class RetrieverFactory:
    """
    설정 파일(config.yaml)에 정의된 값을 기반으로 Retriever를 생성하는 팩토리 클래스.
    """
    @staticmethod
    def create(vector_store: VectorStore):
        """
        주어진 VectorStore와 중앙 설정 값을 사용하여 Retriever를 생성합니다.
        Args:
            vector_store (VectorStore): Retriever를 생성할 기반 VectorStore 객체.
        Returns:
            langchain_core.retrievers.BaseRetriever: 설정된 Retriever 객체.
        """
        return vector_store.as_retriever(
            search_type=SEARCH_TYPE,
            search_kwargs=SEARCH_KWARGS,
        )

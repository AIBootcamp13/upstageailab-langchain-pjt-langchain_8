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
        # config.py에서 직접 값을 가져오는 대신, vector_store.as_retriever()가
        # 내부적으로 설정 값을 사용하도록 이미 수정되었습니다.
        # 이 RetrieverFactory는 이제 더 간단한 인터페이스를 제공하는 역할만 합니다.
        return vector_store.as_retriever(
            search_type=SEARCH_TYPE,
            search_kwargs=SEARCH_KWARGS,
        )

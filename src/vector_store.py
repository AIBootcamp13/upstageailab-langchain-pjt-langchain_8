from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


class VectorStore:
    """
    벡터 스토어 래퍼 (LangChain 표준 인터페이스)
    langchain 의 Document 를 받아서 Vector DB 를 만들고 관리하는 객체
    """

    COLLECTION_NAME = "lecture_documents"
    EMBEDDING_MODEL = "text-embedding-3-large"

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model=self.EMBEDDING_MODEL)
        self.store = Chroma(collection_name=self.COLLECTION_NAME, embedding_function=self.embeddings)

    def add_documents(self, documents: list[Document], **kwargs) -> list[str]:
        """문서 추가"""
        return self.store.add_documents(documents, **kwargs)

    def similarity_search(self, query: str, k: int = 4, **kwargs) -> list[Document]:
        """유사도 검색"""
        return self.store.similarity_search(query, k=k, **kwargs)

    def as_retriever(self, **kwargs):
        """Retriever로 변환 (LangChain 표준)"""
        return self.store.as_retriever(**kwargs)

    def delete(self, ids: list[str] | None = None):
        """문서 삭제"""
        if hasattr(self.store, "delete"):
            self.store.delete(ids=ids)

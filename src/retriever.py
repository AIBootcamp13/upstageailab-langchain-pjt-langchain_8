# from langchain.retrievers import ContextualCompressionRetriever, EnsembleRetriever, MultiQueryRetriever
# from langchain.retrievers.document_compressors import CohereRerank
# from langchain.schema import Document
# from langchain_community.retrievers import BM25Retriever
# from langchain_core.language_models import BaseLanguageModel
# from langchain_core.retrievers import BaseRetriever

from src.vector_store import VectorStore


class RetrieverConfig:
    """Retriever 설정"""

    def __init__(self, retriever_type: str = "simple", search_kwargs: dict | None = None, **kwargs):
        self.retriever_type = retriever_type
        self.search_kwargs = search_kwargs or {"k": 5}
        self.kwargs = kwargs


class RetrieverFactory:
    """다양한 Retriever 생성"""

    @staticmethod
    def create_simple_retriever(vector_store: VectorStore, config: RetrieverConfig):
        """기본 벡터 검색"""
        return vector_store.as_retriever(search_type="mmr", search_kwargs=config.search_kwargs)

    #
    # @staticmethod
    # def create_hybrid_retriever(
    #         vector_store: VectorStore,
    #         documents: list[Document],
    #         config: RetrieverConfig
    # ):
    #     """하이브리드 검색 (BM25 + Vector)"""
    #     # BM25 retriever
    #     bm25_retriever = BM25Retriever.from_documents(documents)
    #     bm25_retriever.k = config.search_kwargs.get("k", 5)
    #
    #     # Vector retriever
    #     vector_retriever = vector_store.as_retriever(
    #         search_kwargs={"k": config.search_kwargs.get("k", 5)}
    #     )
    #
    #     # Ensemble
    #     return EnsembleRetriever(
    #         retrievers=[bm25_retriever, vector_retriever],
    #         weights=config.kwargs.get("weights", [0.5, 0.5])
    #     )
    #
    # @staticmethod
    # def create_reranking_retriever(
    #         base_retriever: BaseRetriever,
    #         config: RetrieverConfig
    # ):
    #     """Cohere Reranking 적용"""
    #     compressor = CohereRerank(
    #         model="rerank-multilingual-v3.0",
    #         top_n=config.search_kwargs.get("k", 5)
    #     )
    #
    #     return ContextualCompressionRetriever(
    #         base_compressor=compressor,
    #         base_retriever=base_retriever
    #     )
    #
    # @staticmethod
    # def create_multi_query_retriever(vector_store: VectorStore, llm: BaseLanguageModel, config: RetrieverConfig):
    #     """Multi-Query Retriever"""
    #     base_retriever = vector_store.as_retriever(
    #         search_kwargs=config.search_kwargs
    #     )
    #
    #     return MultiQueryRetriever.from_llm(
    #         retriever=base_retriever,
    #         llm=llm
    #     )

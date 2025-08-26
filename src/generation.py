# src/generation.py

import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except Exception:
    pass

from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from src.prompt_loader import load_prompt
from pathlib import Path

from src.config import (
    LLM_MODEL,
    EMBEDDING_MODEL,
    PERSIST_DIRECTORY,
    RETRIEVAL_LOCAL_K,
    RETRIEVAL_WEB_K,
    ROOT_DIR,
)
from src.logger import get_logger

# 로거 초기화
logger = get_logger(__name__)

# Load the prompt from the YAML file
rag_prompt_template_string = load_prompt("generation_prompt")
prompt = ChatPromptTemplate.from_template(rag_prompt_template_string)

class BlogGenerator:
    """
    RAG 파이프라인을 사용하여 블로그 포스트를 생성하는 클래스.
    """

    def __init__(self):
        """BlogGenerator를 초기화합니다."""
        self.vector_store = self._load_vector_store()
        self.llm = ChatOllama(model=LLM_MODEL)
        self.rag_chain = self._create_rag_chain()
        logger.info("BlogGenerator가 성공적으로 초기화되었습니다.")

    def _load_vector_store(self) -> Chroma:
        """디스크에 저장된 Chroma 벡터 스토어를 로드합니다."""
        vector_store_path = Path(PERSIST_DIRECTORY)
        if not vector_store_path.exists():
            raise FileNotFoundError(
                f"벡터 스토어를 찾을 수 없습니다: {vector_store_path}. 'src/indexing.py'를 먼저 실행해주세요."
            )
        embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        return Chroma(persist_directory=str(vector_store_path), embedding_function=embedding_function)

    @staticmethod
    def _format_context(docs: list[Document]) -> str:
        """검색된 문서 목록을 단일 문자열 컨텍스트로 변환합니다."""
        return "\n\n---\n\n".join(doc.page_content for doc in docs)

    def _create_rag_chain(self):
        """
        하이브리드 RAG 체인을 생성합니다.
        - 내부 문서 검색 (Vector Store)
        - 외부 정보 검색 (Web Search)
        """
        # 1. 리트리버 설정
        # Use RETRIEVAL_LOCAL_K from config
        local_retriever = self.vector_store.as_retriever(search_kwargs={"k": RETRIEVAL_LOCAL_K})
        # Use RETRIEVAL_WEB_K from config
        web_retriever = TavilySearchAPIRetriever(k=RETRIEVAL_WEB_K)

        # 2. 프롬프트 템플릿 정의 (REMOVED hardcoded prompt)
        # The prompt is now loaded from the YAML file at the top of the script.

        # 3. RAG 체인 구성 (LCEL 사용)
        retrieval_chain = RunnableParallel(
            {
                "internal_context": local_retriever | self._format_context,
                "web_context": web_retriever | self._format_context,
                "topic": RunnablePassthrough(),
            }
        )

        # The externally loaded 'prompt' variable is used here
        return retrieval_chain | prompt | self.llm | StrOutputParser()

    def generate(self, topic: str) -> str:
        """
        주어진 주제에 대한 블로그 포스트를 생성합니다.

        Args:
            topic (str): 블로그 포스트의 주제.

        Returns:
            str: 생성된 Markdown 형식의 블로그 포스트.
        """
        logger.info(f"주제: '{topic}'에 대한 블로그 포스트 생성을 시작합니다.")
        return self.rag_chain.invoke(topic)


if __name__ == "__main__":
    import argparse
    # UPDATED: Import OUTPUT_DIR from the central configuration
    from src.config import OUTPUT_DIR

    parser = argparse.ArgumentParser(description="RAG 기반 블로그 포스트 생성기")
    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="생성할 블로그 포스트의 주제를 입력하세요."
    )
    args = parser.parse_args()

    try:
        generator = BlogGenerator()
        blog_topic = args.topic
        generated_post = generator.generate(blog_topic)

        print("\n--- 생성된 블로그 포스트 ---\n")
        print(generated_post)

        # 생성된 포스트를 파일로 저장
        # UPDATED: Use the imported OUTPUT_DIR from src.config
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        safe_filename = blog_topic.lower().replace(" ", "_").replace("'", "")
        file_name = (safe_filename[:50] + '..') if len(safe_filename) > 50 else safe_filename
        output_path = OUTPUT_DIR / (file_name + ".md")
        
        with output_path.open("w", encoding="utf-8") as f:
            f.write(generated_post)
        print(f"\n--- 블로그 포스트가 다음 경로에 저장되었습니다: {output_path} ---")

    except Exception as e:
        logger.error(f"블로그 생성 중 오류 발생: {e}")
        print(
            "\n오류가 발생했습니다. 로그를 확인하고, .env 파일에 TAVILY_API_KEY가 올바르게 설정되었는지, "
            "그리고 Ollama 서버가 실행 중인지 확인해주세요."
        )
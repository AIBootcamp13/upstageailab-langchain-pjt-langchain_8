
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
# src/generation.py

from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from src.config import ROOT_DIR
from src.logger import get_logger


# .env 파일에서 TAVILY_API_KEY를 로드해야 합니다.
# from dotenv import load_dotenv
# load_dotenv()

# 로거 초기화
logger = get_logger(__name__)

# --- 설정 ---
VECTOR_STORE_PATH = ROOT_DIR / "vector_store" / "chroma_db"
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
LLM_MODEL = "gpt-oss:20b"  # README.md에 명시된 로컬 LLM


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
        if not VECTOR_STORE_PATH.exists():
            raise FileNotFoundError(
                f"벡터 스토어를 찾을 수 없습니다: {VECTOR_STORE_PATH}. 'src/indexing.py'를 먼저 실행해주세요."
            )
        embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        return Chroma(persist_directory=str(VECTOR_STORE_PATH), embedding_function=embedding_function)

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
        # 내부 문서 검색기 (k=5: 가장 유사한 5개 문서 검색)
        local_retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        # 웹 검색기 (k=3: 상위 3개 결과 검색)
        web_retriever = TavilySearchAPIRetriever(k=3)

        # 2. 프롬프트 템플릿 정의
        # LLM에게 역할을 부여하고, 컨텍스트와 함께 질문을 던지는 템플릿
        rag_prompt_template = """
당신은 AI 및 소프트웨어 엔지니어링 전문 기술 블로거입니다.
내부 문서 컨텍스트와 외부 웹 검색 결과를 종합하여, 명확하고 매력적인 기술 블로그 포스트를 Markdown 형식으로 작성해주세요.

**주제:**
{topic}

**내부 컨텍스트 (PDF 프레젠테이션 기반):**
---
{internal_context}
---

**외부 컨텍스트 (웹 검색 결과):**
---
{web_context}
---

**작성 지침:**
1.  **제목:** 주제를 바탕으로 SEO에 유리한 H1 제목을 만드세요.
2.  **서론:** 독자의 흥미를 유발하고, 주제의 중요성을 언급하며, 다룰 내용을 요약하는 서론을 작성하세요.
3.  **본문:**
    * 내부 컨텍스트와 외부 컨텍스트의 정보를 모두 종합하여 내용을 구성하세요.
    * 논리적인 섹션과 명확한 H2, H3 헤딩을 사용하여 구조화하세요.
    * 가독성을 높이기 위해 글머리 기호, 번호 매기기, **굵은 텍스트** 등을 활용하세요.
    * 기술적 세부 사항이나 코드 예제가 있다면 적절한 코드 블록에 포함시키세요.
4.  **결론:** 핵심 내용을 요약하고, 최종적인 생각이나 향후 전망을 제시하며 마무리하세요.
5.  **어조:** 기술 전문가 독자층에게 유익하고, 전문적이면서도 이해하기 쉬운 어조를 유지하세요.

**최종 결과물은 오직 Markdown 형식의 블로그 포스트만 출력해야 합니다. 포스트 앞뒤로 다른 설명이나 텍스트를 포함하지 마세요.**

[블로그 포스트 결과물]:
"""
        prompt = ChatPromptTemplate.from_template(rag_prompt_template)

        # 3. RAG 체인 구성 (LCEL 사용)
        # RunnableParallel을 사용하여 내부 및 외부 검색을 병렬로 수행
        retrieval_chain = RunnableParallel(
            {
                "internal_context": local_retriever | self._format_context,
                "web_context": web_retriever | self._format_context,
                "topic": RunnablePassthrough(),
            }
        )

        # 최종 체인: 검색 -> 프롬프트 -> LLM -> 출력 파서
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
    # 이 스크립트를 직접 실행하여 블로그 생성을 테스트할 수 있습니다.
    try:
        generator = BlogGenerator()
        blog_topic = "최신 AI 아키텍처에 대한 심층 분석"

        generated_post = generator.generate(blog_topic)

        print("\n--- 생성된 블로그 포스트 ---\n")
        print(generated_post)

        # 생성된 포스트를 파일로 저장
        output_dir = ROOT_DIR / "output"
        output_dir.mkdir(exist_ok=True)
        file_name = blog_topic.lower().replace(" ", "_").replace("'", "") + ".md"
        output_path = output_dir / file_name
        with output_path.open("w", encoding="utf-8") as f:
            f.write(generated_post)
        print(f"\n--- 블로그 포스트가 다음 경로에 저장되었습니다: {output_path} ---")

    except Exception as e:
        logger.error(f"블로그 생성 중 오류 발생: {e}")
        print(
            "\n오류가 발생했습니다. 로그를 확인하고, .env 파일에 TAVILY_API_KEY가 올바르게 설정되었는지, "
            "그리고 Ollama 서버가 실행 중인지 확인해주세요."
        )

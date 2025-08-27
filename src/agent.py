# src/agent.py
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# 지원하는 모든 LLM 클래스를 import합니다.
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

# 중앙 설정 파일에서 필요한 설정값을 가져옵니다.
from src.config import (
    LLM_PROVIDER, 
    LLM_MODEL, 
    DRAFT_PROMPT_TEMPLATE, 
    UPDATE_PROMPT_TEMPLATE
)

class BlogContentAgent:
    """
    검색된 컨텍스트를 바탕으로 블로그 초안을 생성하고 수정하는 에이전트 클래스.
    설정에 따라 동적으로 LLM과 프롬프트를 로드합니다.
    """
    def __init__(self, retriever):
        self.retriever = retriever
        
        # 설정된 LLM 제공자(provider)에 따라 LLM을 초기화합니다.
        if LLM_PROVIDER == "openai":
            # OpenAI API를 사용하는 경우
            self.llm = ChatOpenAI(model=LLM_MODEL)
        elif LLM_PROVIDER == "ollama":
            # 로컬 Ollama 모델을 사용하는 경우
            self.llm = ChatOllama(model=LLM_MODEL)
        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

        # config에서 로드한 프롬프트 템플릿을 사용하여 ChatPromptTemplate 객체를 생성합니다.
        self.draft_prompt_template = ChatPromptTemplate.from_template(DRAFT_PROMPT_TEMPLATE)
        self.update_prompt_template = ChatPromptTemplate.from_template(UPDATE_PROMPT_TEMPLATE)
        self.output_parser = StrOutputParser() # LLM의 출력을 문자열로 파싱합니다.

    def generate_draft(self) -> str:
        """검색된 문서를 바탕으로 블로그 포스트의 초안을 생성합니다."""
        chain = self.draft_prompt_template | self.llm | self.output_parser
        # retriever가 문서를 검색하고, format_docs를 통해 문자열로 변환된 후 프롬프트에 주입됩니다.
        return chain.invoke({"content": self.retriever | self.format_docs})

    def update_blog_post(self, blog_post: str, user_request: str) -> str:
        """사용자의 수정 요청에 따라 기존 블로그 포스트를 업데이트합니다."""
        chain = self.update_prompt_template | self.llm | self.output_parser
        return chain.invoke({"current_content": blog_post, "user_request": user_request})

    @staticmethod
    def format_docs(documents: list[Document]) -> str:
        """Document 객체 리스트를 하나의 긴 문자열로 결합합니다."""
        return "\n\n".join(doc.page_content for doc in documents)
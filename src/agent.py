<<<<<<< HEAD
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama
=======
# src/agent.py
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
>>>>>>> feature/memory

# 지원하는 모든 LLM 클래스를 import합니다.
from langchain_openai import ChatOpenAI

# 중앙 설정 파일에서 필요한 설정값을 가져옵니다.
<<<<<<< HEAD
from src.config import DRAFT_PROMPT_TEMPLATE, LLM_MODEL, LLM_PROVIDER, UPDATE_PROMPT_TEMPLATE

=======
from src.config import (
    LLM_PROVIDER,
    LLM_MODEL,
    DRAFT_PROMPT_TEMPLATE,
    UPDATE_PROMPT_TEMPLATE
)
>>>>>>> feature/memory

class BlogContentAgent:
    """
    검색된 컨텍스트를 바탕으로 블로그 초안을 생성하고,
    대화형 메모리를 사용하여 사용자의 요청에 따라 수정하는 에이전트 클래스.
    """
<<<<<<< HEAD

    def __init__(self, retriever):
        self.retriever = retriever
=======
    def __init__(self, retriever, memory: ConversationSummaryBufferMemory):
        """
        에이전트를 초기화합니다.

        Args:
            retriever: 문서를 검색하기 위한 Retriever 객체.
            memory (ConversationSummaryBufferMemory): 대화 기록을 관리하는 메모리 객체.
        """
        self.retriever = retriever
        self.memory = memory # 메모리 객체를 인스턴스 변수로 저장합니다.
>>>>>>> feature/memory

        # 설정된 LLM 제공자(provider)에 따라 LLM을 초기화합니다.
        if LLM_PROVIDER == "openai":
            self.llm = ChatOpenAI(model=LLM_MODEL)
        elif LLM_PROVIDER == "ollama":
            self.llm = ChatOllama(model=LLM_MODEL)
        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

        # 초안 생성을 위한 체인 설정
        self.draft_prompt_template = ChatPromptTemplate.from_template(DRAFT_PROMPT_TEMPLATE)
<<<<<<< HEAD
        self.update_prompt_template = ChatPromptTemplate.from_template(UPDATE_PROMPT_TEMPLATE)
        self.output_parser = StrOutputParser()  # LLM의 출력을 문자열로 파싱합니다.

    def generate_draft(self) -> str:
        """검색된 문서를 바탕으로 블로그 포스트의 초안을 생성합니다."""
        # retriever가 문서를 검색하고, format_docs를 통해 문자열로 변환된 후 프롬프트에 주입됩니다.
        chain = (
            self.retriever
            | self.format_docs
            | {"content": RunnablePassthrough()}
            | self.draft_prompt_template
            | self.llm
            | self.output_parser
        )
        return chain.invoke("")

    def update_blog_post(self, blog_post: str, user_request: str) -> str:
        """사용자의 수정 요청에 따라 기존 블로그 포스트를 업데이트합니다."""
        chain = self.update_prompt_template | self.llm | self.output_parser
        return chain.invoke(
            {
                "current_content": blog_post,
                "user_request": user_request,
            }
        )
=======
        self.output_parser = StrOutputParser()
        self.draft_chain = self.draft_prompt_template | self.llm | self.output_parser

        # 블로그 포스트 수정을 위한 대화형 체인 설정
        self.update_prompt_template = PromptTemplate.from_template(UPDATE_PROMPT_TEMPLATE)

        # ConversationChain을 초기화합니다.
        # *** FIX: memory 객체와 일치하도록 output_key를 명시적으로 설정합니다. ***
        self.update_chain = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=self.update_prompt_template,
            verbose=True, # 디버깅을 위해 체인 실행 과정을 출력합니다.
            output_key="output" # 이 부분이 핵심 수정 사항입니다.
        )

    def generate_draft(self) -> str:
        """검색된 문서를 바탕으로 블로그 포스트의 초안을 생성합니다."""
        return self.draft_chain.invoke({"content": self.retriever | self.format_docs})

    def update_blog_post(self, user_request: str) -> str:
        """
        사용자의 수정 요청에 따라 기존 블로그 포스트를 업데이트합니다.
        이제 ConversationChain을 사용합니다.
        """
        # *** FIX: .predict() 대신 .invoke()를 사용하여 전체 출력 딕셔너리를 받고,
        #          명시적으로 'output' 키를 사용하여 결과를 추출합니다. ***
        result = self.update_chain.invoke({"input": user_request})
        return result["output"]
>>>>>>> feature/memory

    @staticmethod
    def format_docs(documents: list[Document]) -> str:
        """Document 객체 리스트를 하나의 긴 문자열로 결합합니다."""
<<<<<<< HEAD
        return "\n".join(doc.page_content for doc in documents)
=======
        return "\n\n".join(doc.page_content for doc in documents)
>>>>>>> feature/memory

# src/agent.py
import json
import time
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from src.logger import get_logger
from src.config import (
    LLM_PROVIDER,
    LLM_MODEL,
    DRAFT_PROMPT_TEMPLATE,
    UPDATE_PROMPT_TEMPLATE,
)

class BlogContentAgent:
    """
    대화형 메모리를 사용하여 블로그 초안을 생성하고 수정하는 에이전트 클래스.
    """
    def __init__(self, retriever, processed_docs: list[Document]):
        self.retriever = retriever
        self.processed_docs = processed_docs
        self.logger = get_logger("src.agent")

        if LLM_PROVIDER == "openai":
            self.llm = ChatOpenAI(model=LLM_MODEL)
        else:
            self.llm = ChatOllama(model=LLM_MODEL)

        # Draft generation chain
        self.draft_prompt_template = ChatPromptTemplate.from_template(DRAFT_PROMPT_TEMPLATE)
        self.output_parser = StrOutputParser()
        self.draft_chain = self.draft_prompt_template | self.llm | self.output_parser

        # Simplified memory and update chain
        self.memory = ConversationBufferWindowMemory(k=10, memory_key="history", return_messages=True)
        self.update_prompt_template = ChatPromptTemplate.from_messages([
            ("system", UPDATE_PROMPT_TEMPLATE),
            MessagesPlaceholder(variable_name="history"),
            ("human", "[USER REQUEST]\n{input}\n\n[CURRENT DRAFT]\n{draft}"),
        ])
        self.update_chain = self.update_prompt_template | self.llm | self.output_parser

    def generate_draft(self) -> str:
        """처리된 문서 전체를 사용하여 블로그 초안을 생성합니다."""
        content = self.format_docs(self.processed_docs)
        draft = self.draft_chain.invoke({"content": content})
        self.memory.save_context({"input": "초안을 생성해줘."}, {"output": "초안이 생성되었습니다."})
        return draft

    def update_blog_post(self, user_request: str, current_draft: str) -> dict:
        """
        사용자의 요청을 단일 LLM 호출로 처리하고, 응답 JSON을 파싱합니다.
        """
        t0 = time.perf_counter()
        
        response_str = self.update_chain.invoke({
            "history": self.memory.chat_memory.messages,
            "input": user_request,
            "draft": current_draft,
        })
        
        duration = time.perf_counter() - t0
        self.logger.info(f"Update call took {duration:.2f} seconds.")

        # Robust JSON parsing
        try:
            response_json = json.loads(response_str)
            # Ensure the response has the expected structure
            if "chat_response" in response_json and "updated_draft" in response_json:
                self.memory.save_context({"input": user_request}, {"output": response_json["chat_response"]})
                return response_json
            else:
                raise ValueError("Invalid JSON structure")
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse LLM response as valid JSON: {e}\nResponse: {response_str}")
            # Fallback: Treat the entire response as a chat message and don't update the draft
            self.memory.save_context({"input": user_request}, {"output": response_str})
            return {"chat_response": response_str, "updated_draft": current_draft}

    def get_session_history(self):
        """Helper for UI to render chat history."""
        return self.memory.chat_memory

    @staticmethod
    def format_docs(documents: list[Document]) -> str:
        """Document 객체 리스트를 하나의 긴 문자열로 결합합니다."""
        return "\n\n".join(doc.page_content for doc in documents)

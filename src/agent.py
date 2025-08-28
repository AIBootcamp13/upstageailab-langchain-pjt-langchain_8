import json

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.tools import TavilySearchResults
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

# 중앙 설정 파일에서 필요한 설정값을 가져옵니다.
from src.config import DRAFT_PROMPT_TEMPLATE, LLM_MODEL, LLM_PROVIDER, TAVILY_API_KEY, UPDATE_PROMPT_TEMPLATE


class BlogContentAgent:
    """
    웹 검색 및 문서 검색 도구를 사용하여 블로그 초안을 생성하고 수정하는 Tool-Calling 에이전트.
    """

    def __init__(self, retriever, processed_docs: list[Document]):
        self.retriever = retriever
        self.processed_docs = processed_docs
        self.chat_history_store = {}

        # 1. LLM 초기화
        if LLM_PROVIDER == "openai":
            self.llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
        elif LLM_PROVIDER == "ollama":
            self.llm = ChatOllama(model=LLM_MODEL, temperature=0)
        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

        # 2. 초안 생성을 위한 체인
        self.draft_prompt_template = ChatPromptTemplate.from_template(DRAFT_PROMPT_TEMPLATE)
        self.output_parser = StrOutputParser()
        self.draft_chain = self.draft_prompt_template | self.llm | self.output_parser

        # 3. Tool-Calling 에이전트 설정
        # 3-1. 도구 생성 (Retriever Tool 및 Web Search Tool)
        retriever_tool = create_retriever_tool(
            self.retriever,
            "document_search",
            "업로드된 PDF 문서에서 정보를 검색하고 반환합니다. 문서 내용에 대한 질문에 답할 때 사용하세요.",
        )
        web_search_tool = TavilySearchResults(max_results=3, tavily_api_key=TAVILY_API_KEY)
        tools = [retriever_tool, web_search_tool]

        # 3-2. 에이전트 프롬프트
        self.update_prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", UPDATE_PROMPT_TEMPLATE),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # 3-3. 에이전트 생성
        agent = create_tool_calling_agent(self.llm, tools, self.update_prompt_template)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        # 3-4. 메모리와 함께 실행 가능한 체인으로 래핑
        self.agent_with_chat_history = RunnableWithMessageHistory(
            agent_executor,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def get_session_history(self, session_id: str):
        """세션 ID에 해당하는 채팅 기록을 가져오거나 새로 생성합니다."""
        if session_id not in self.chat_history_store:
            self.chat_history_store[session_id] = ChatMessageHistory()
        return self.chat_history_store[session_id]

    def generate_draft(self, session_id: str) -> str:
        """처리된 문서 전체를 사용하여 블로그 초안을 생성합니다."""
        content = self.format_docs(self.processed_docs)
        draft = self.draft_chain.invoke({"content": content})

        history = self.get_session_history(session_id)
        history.add_user_message("제공된 문서를 바탕으로 블로그 초안을 생성해줘.")
        history.add_ai_message(json.dumps({"type": "draft", "content": draft}))
        return draft

    def update_blog_post(self, user_request: str, session_id: str) -> dict:
        """사용자의 수정 요청에 따라 에이전트를 실행하고 응답을 파싱합니다."""
        config = {"configurable": {"session_id": session_id}}
        response = self.agent_with_chat_history.invoke({"input": user_request}, config=config)

        # JSON 파싱 안정성 확보
        try:
            output_str = response.get("output", "{}")
            parsed_json = json.loads(output_str)
            if isinstance(parsed_json, dict):
                return parsed_json
            return {"type": "chat", "content": str(parsed_json)}
        except (json.JSONDecodeError, TypeError):
            return {
                "type": "chat",
                "content": response.get("output", "죄송합니다, 응답을 처리하는 중 오류가 발생했습니다."),
            }

    @staticmethod
    def format_docs(documents: list[Document]) -> str:
        """Document 객체 리스트를 하나의 긴 문자열로 결합합니다."""
        return "\n\n".join(doc.page_content for doc in documents)

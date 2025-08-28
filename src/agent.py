# tool 사용을 위한 라이브러리 import
from langchain_core.documents import Document
from langchain_core.messages import ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama

# 지원하는 모든 LLM 클래스를 import합니다.
from langchain_openai import ChatOpenAI

from src.agent_tool import web_search  # 현재 구현된 툴(web_search) 바인딩

# 중앙 설정 파일에서 필요한 설정값을 가져옵니다.
from src.config import DRAFT_PROMPT_TEMPLATE, LLM_MODEL, LLM_PROVIDER, UPDATE_PROMPT_TEMPLATE


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
        self.output_parser = StrOutputParser()  # LLM의 출력을 문자열로 파싱합니다.

        # 추후 확장 가능한 툴 목록
        self.tools = [web_search]

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

    # 수정 (툴콜 내장)
    def update_blog_post(self, blog_post: str, user_request: str) -> str:
        """
        입력/출력은 그대로 유지.
        내부에서:
          1) 프롬프트->LLM 1차 호출(툴 사용 여부는 LLM이 결정)
          2) tool_calls가 있으면 해당 툴 실행 후 ToolMessage를 붙여 2차 호출
          3) 최종 텍스트를 반환
        """
        # 메시지 구성 (프롬프트 템플릿 유지)
        msgs = self.update_prompt_template.format_messages(
            current_content=blog_post,
            user_request=user_request,
        )

        # 툴 바인딩된 LLM으로 1차 호출 (툴 사용 여부 판단은 LLM에 위임)
        llm_with_tools = self.llm.bind_tools(self.tools)
        ai_msg = llm_with_tools.invoke(msgs)

        # 필요 시 툴콜 실행 (최대 1회로 제한)
        tool_msgs: list[ToolMessage] = []
        if getattr(ai_msg, "tool_calls", None):
            for call in ai_msg.tool_calls:
                name = call.get("name")
                args = call.get("args", {}) or {}

                if name == "web_search":
                    # args: {"q": str, "max_results": int} 예상
                    tool_output = web_search.invoke(args)
                    tool_msgs.append(
                        ToolMessage(
                            tool_call_id=call["id"],
                            name="web_search",
                            content=tool_output,
                        )
                    )

        # 툴 메시지가 있으면 대화 내역에 부착해 2차 호출 -> 최종 답변
        if tool_msgs:
            msgs = [*msgs, ai_msg, *tool_msgs]
            final_msg = self.llm.invoke(msgs)
            return self.output_parser.invoke(final_msg)

        # 툴콜이 없었으면 1차 응답을 그대로 파싱해서 반환
        return self.output_parser.invoke(ai_msg)

    @staticmethod
    def format_docs(documents: list[Document]) -> str:
        """Document 객체 리스트를 하나의 긴 문자열로 결합합니다."""
        return "\n".join(doc.page_content for doc in documents)

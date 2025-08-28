from langchain_core.documents import Document
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agent_tool import web_search  # @tool


class BlogContentAgent:
    LLM_MODEL = "gpt-5-nano"

    def __init__(self, retriever):
        self.retriever = retriever
        self.llm = ChatOpenAI(model=self.LLM_MODEL)
        self.output_parser = StrOutputParser()

        # 단일 프롬프트(툴 유무 모두 우선 추가)
        self.web_draft_prompt_template = ChatPromptTemplate.from_template(self._load_prompt_for_web_draft())
        self.update_prompt_template = ChatPromptTemplate.from_template(self._load_prompt_for_update())

        # 툴 레지스트리(추가 확장 용도)
        self.tools = [web_search]

    def generate_draft(self, user_query: str, max_web: int = 5) -> str:
        """
        단일 엔트리:
        - RAG 결과 기반 초안 작성
        - 필요시 LLM이 web_search 툴을 호출하여 보강
        """
        # RAG 컨텍스트
        docs = self.retriever.invoke(user_query)
        rag_context = self.format_docs(docs)

        # 메시지 & LLM (툴 항상 바인딩)
        msgs = self.web_draft_prompt_template.format_messages(
            user_query=user_query,
            rag_context=rag_context,
            max_results=max_web,
        )
        llm_with_tools = self.llm.bind_tools(self.tools)

        # 1차 호출
        ai_msg: AIMessage = llm_with_tools.invoke(msgs)
        msgs.append(ai_msg)

        # LLM이 툴 호출 시 처리
        if getattr(ai_msg, "tool_calls", None):
            tool_msgs = []
            for call in ai_msg.tool_calls:
                if call["name"] == "web_search":
                    args = call.get("args", {}) or {}
                    args.setdefault("q", user_query)
                    args.setdefault("max_results", max_web)
                    tool_output = web_search.invoke(args)
                    tool_msgs.append(
                        ToolMessage(
                            tool_call_id=call["id"],
                            name="web_search",
                            content=tool_output,
                        )
                    )
            msgs.extend(tool_msgs)
            final_msg: AIMessage = llm_with_tools.invoke(msgs)
            return final_msg.content

        # 툴을 안 썼으면 그대로 반환
        return ai_msg.content

    def update_blog_post(self, blog_post: str, user_request: str) -> str:
        chain = self.update_prompt_template | self.llm | self.output_parser
        return chain.invoke({"current_content": blog_post, "user_request": user_request})

    @staticmethod
    def format_docs(documents: list[Document]) -> str:
        return "\n\n".join(doc.page_content for doc in (documents or []))

    @staticmethod
    def _load_prompt_for_web_draft() -> str:
        return """[Identity]
        당신은 출처 기반으로 글을 쓰는 전문 블로그 작가입니다.

        [User Query]
        {user_query}

        [Retrieved Context]
        {rag_context}

        [Tools You Can Use]
        - web_search(q: str, max_results: int) → {"results":[{"id","title","url","snippet"}]}

        [Instructions]
        1) 먼저 Retrieved Context만으로 초안을 구성하세요.
        2) 최신/외부 정보 보강이 필요하면 web_search를 '최대 1회' 호출하세요.
        3) 본문 인용은 [W1]처럼 id로 표기하세요.
        4) 글 끝에 'References - Web' 섹션을 만들고 title+url을 bullet로 나열하세요.
        5) Markdown(H1~H3/표/목록), 과장·추측 금지, 근거 불충분 시 명시.

        이제 초안을 작성하세요:
        """

    @staticmethod
    def _load_prompt_for_update() -> str:
        return """현재 블로그 포스트를 다음 요청에 따라 수정해주세요:
        [수정 요청]
        {user_request}

        [현재 블로그 포스트]
        {current_content}

        수정된 전체 블로그 포스트를 Markdown 형식으로 작성해주세요:
        """

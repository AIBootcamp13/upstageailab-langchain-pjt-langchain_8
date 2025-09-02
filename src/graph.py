# src/graph.py
from operator import add
from typing import Annotated, Any, Dict, List, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    """
    에이전트의 상태를 나타냅니다.
    """
    draft: str
    chat_history: Annotated[List[BaseMessage], add]
    user_request: str
    route: str
    tool_output: str
    response: str


class GraphBuilder:
    """
    LangGraph의 노드와 엣지를 구성하고 관리하는 클래스입니다.
    """

    def __init__(self, llm: Runnable, tools: List[BaseTool]):
        self.llm = llm
        self.tools_map = {tool.name: tool for tool in tools}

    def call_tools(self, state: AgentState) -> Dict[str, Any]:
        """
        라우터의 결정('route')에 따라 적절한 도구를 호출하고,
        그 결과를 'tool_output'에 저장하여 반환합니다.
        """
        tool_name = state["route"]
        chosen_tool = self.tools_map.get(tool_name)
        if not chosen_tool:
            raise ValueError(f"'{tool_name}'라는 이름의 도구를 찾을 수 없습니다.")
        
        tool_output = chosen_tool.invoke(state["user_request"])
        return {"tool_output": str(tool_output)}

    def simple_llm_call(self, state: AgentState) -> Dict[str, Any]:
        """
        도구 호출 없이 LLM을 직접 호출하여 블로그 초안을 수정합니다.
        """
       
        prompt = f"""
        You are an expert blog editor. Your task is to intelligently revise the draft below based on the user's request.
        Interpret the user's intent and apply the changes thoughtfully.

        ### Guiding Principles ###
        - **Follow the User's Request**: Prioritize the user's instructions for changes to content, style, structure, or language.
        - **Preserve Markdown Integrity**: Maintain valid Markdown formatting. For example, `## Title` should remain a level-2 header unless the user asks to change its level.
        - **Return the Full Document**: Always return the complete, updated draft after applying the changes.

        ### Example ###
        [User Request]
        "Change the title to 'Understanding RAG' and make the tone more professional."

        [Original Draft]
        ## what is rag
        rag is a cool tech.

        [Correctly Revised Draft]
        ## Understanding RAG
        Retrieval-Augmented Generation (RAG) is a technique that enhances the capabilities of Large Language Models.
        ############################################

        Now, process the real request below.

        [Current Draft]
        {state['draft']}

        [User Request]
        {state['user_request']}
        """
        # -----------------------------------------------------------
        # Attempt to attach Chainlit's LangchainCallbackHandler for streaming
        try:
            from chainlit import LangchainCallbackHandler

            response = self.llm.invoke(prompt, callbacks=[LangchainCallbackHandler(stream_final_answer=True)])
        except Exception:
            response = self.llm.invoke(prompt)
        return {"draft": getattr(response, 'content', str(response))}

    def update_draft_after_tool_call(self, state: AgentState) -> Dict[str, Any]:
        """
        도구 호출 결과를 사용하여 블로그 초안을 업데이트합니다.
        """
       
        prompt = f"""
        당신은 마크다운(Markdown) 서식을 완벽하게 보존하는 전문 블로그 에디터입니다.
        아래의 초안과 도구 실행 결과를 참고하여 사용자의 요청에 맞게 초안을 수정해주세요.

        ### 매우 중요한 규칙 ###
        - **기존 마크다운 서식을 절대 변경하지 마세요.** 예를 들어, `## 제목`을 `**제목**`으로 바꾸지 마세요.
        - 요청된 내용만 수정하고, 나머지 부분과 서식은 그대로 유지해야 합니다.
        - 수정된 **전체 초안**을 항상 반환해야 합니다.
        
        ### 좋은 수정의 예시 ###
        [사용자 요청]
        "## 소개" 제목을 "## RAG란 무엇인가?"로 바꿔줘.

        [수정 전 초안]
        ## 소개
        RAG는 LLM의 한계를 보완하는 기술입니다.
        - 검색(Retrieval)
        - 보강(Augmentation)
        - 생성(Generation)

        [올바른 수정 후 초안]
        ## RAG란 무엇인가?
        RAG는 LLM의 한계를 보완하는 기술입니다.
        - 검색(Retrieval)
        - 보강(Augmentation)
        - 생성(Generation)
        ############################################

        이제 아래의 실제 요청을 처리해주세요.

        [현재 초안]
        {state['draft']}

        [도구 실행 결과]
        {state['tool_output']}

        [사용자 요청]
        {state['user_request']}
        """
        # -----------------------------------------------------------
        try:
            from chainlit import LangchainCallbackHandler

            response = self.llm.invoke(prompt, callbacks=[LangchainCallbackHandler(stream_final_answer=True)])
        except Exception:
            response = self.llm.invoke(prompt)
        return {"draft": getattr(response, 'content', str(response))}

    def conversational_chat_node(self, state: AgentState) -> Dict[str, str]:
        """
        초안을 수정하지 않는 일반적인 대화를 처리합니다.
        """
        prompt = f"""
        당신은 친절한 AI 어시스턴트입니다. 다음 대화 기록과 사용자의 질문에 기반하여 답변해주세요.

        [대화 기록]
        {state['chat_history']}
        
        [사용자 질문]
        {state['user_request']}
        """
        try:
            from chainlit import LangchainCallbackHandler

            response = self.llm.invoke(prompt, callbacks=[LangchainCallbackHandler(stream_final_answer=True)])
        except Exception:
            response = self.llm.invoke(prompt)
        return {"response": getattr(response, 'content', str(response))}

    def router(self, state: AgentState) -> Dict[str, str]:
        """
        사용자의 요청을 분석하여 다음에 실행할 노드를 결정합니다.
        """
        tool_names = ", ".join(self.tools_map.keys())
        routing_prompt = f"""
        당신은 사용자 요청의 의도를 파악하여 다음에 어떤 작업을 수행해야 할지 결정하는 라우터입니다.
        사용자의 요청의 종류를 다음 중 하나로 분류해주세요:
        
        1. tool_use: 사용자의 요청에 답변하기 위해 다음 도구 중 하나가 필요한 경우. 사용 가능한 도구: [{tool_names}]
        2. rewrite: 사용자가 명시적으로 블로그 초안의 수정을 요구하는 경우 (예: "이 부분을 수정해줘", "결론을 추가해줘").
        3. chat: 사용자가 일반적인 질문을 하거나, 인사를 하거나, 초안 수정과 관련 없는 대화를 하는 경우 (예: "안녕?", "RAG가 뭐야?").

        분류 결과만 소문자로 반환하세요 (tool_use의 경우, 사용할 도구의 이름을 반환).
        
        [대화 기록]
        {state['chat_history']}

        [사용자 요청]
        {state['user_request']}
        """
        try:
            from chainlit import LangchainCallbackHandler

            response = self.llm.invoke(routing_prompt, callbacks=[LangchainCallbackHandler()])
        except Exception:
            response = self.llm.invoke(routing_prompt)
        route = getattr(response, 'content', str(response)).strip()

        if route == "rewrite":
            return {"route": "rewrite"}
        elif route == "chat":
            return {"route": "chat"}
        elif route in self.tools_map:
            return {"route": route}
        else:
            return {"route": "chat"}

    def build(self) -> Runnable:
        """
        모든 노드와 엣지를 연결하여 실행 가능한 LangGraph를 구성하고 컴파일합니다.
        """
        graph = StateGraph(AgentState)

        # Debug wrapper: wrap node functions to log received state (best-effort, non-blocking)
        def wrap_with_logging(fn, name):
            def wrapped(state):
                try:
                    # minimal logging to stdout so it's visible in server logs
                    print(
                        f"[graph-debug] entering node={name} draft_len={len(str(state.get('draft','')))} user_request={str(state.get('user_request',''))[:80]}"
                    )
                except Exception:
                    pass
                return fn(state)

            return wrapped

        # Add nodes with logging wrapper
        graph.add_node("router", wrap_with_logging(self.router, "router"))
        graph.add_node("simple_llm_call", wrap_with_logging(self.simple_llm_call, "simple_llm_call"))
        graph.add_node("call_tools", wrap_with_logging(self.call_tools, "call_tools"))
        graph.add_node(
            "update_draft_after_tool_call",
            wrap_with_logging(self.update_draft_after_tool_call, "update_draft_after_tool_call"),
        )
        graph.add_node(
            "conversational_chat_node",
            wrap_with_logging(self.conversational_chat_node, "conversational_chat_node"),
        )

        graph.set_entry_point("router")

        graph.add_conditional_edges(
            "router",
            lambda state: state["route"],
            {
                "rewrite": "simple_llm_call",
                "chat": "conversational_chat_node",
                **{tool_name: "call_tools" for tool_name in self.tools_map},
            },
        )

        graph.add_edge("simple_llm_call", END)
        graph.add_edge("call_tools", "update_draft_after_tool_call")
        graph.add_edge("update_draft_after_tool_call", END)
        graph.add_edge("conversational_chat_node", END)

        return graph.compile()
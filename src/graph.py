# src/graph.py
from operator import add
from typing import Annotated, Any, Dict, List, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    """
    에이전트의 상태를 나타냅니다. 이 TypedDict는 LangGraph의 노드 간에
    데이터를 전달하는 데 사용됩니다.
    """

    draft: str  # 현재 블로그 초안
    chat_history: Annotated[List[BaseMessage], add]  # 대화 기록
    user_request: str  # 사용자의 현재 요청
    # 라우터가 다음 단계를 결정하는 데 사용할 값 (e.g., "rewrite", "tavily_search")
    route: str
    # 도구 호출의 출력을 저장할 필드
    tool_output: str


class GraphBuilder:
    """
    LangGraph의 노드와 엣지를 구성하고 관리하는 클래스입니다.
    에이전트의 핵심 로직(상태, 노드, 라우터)을 캡슐화합니다.
    """

    def __init__(self, llm: Runnable, tools: List[BaseTool]):
        self.llm = llm
        self.tools_map = {tool.name: tool for tool in tools}

    # --- 노드 함수 정의 ---

    def call_tools(self, state: AgentState) -> Dict[str, Any]:
        """
        라우터의 결정('route')에 따라 적절한 도구를 호출하고,
        그 결과를 'tool_output'에 저장하여 반환합니다.
        이 함수는 LangGraph에서 도구 호출을 담당하는 노드입니다.
        """
        tool_name = state["route"]
        chosen_tool = self.tools_map.get(tool_name)

        if not chosen_tool:
            # 이 경우는 라우터가 잘못된 경로를 반환했을 때 발생합니다.
            raise ValueError(f"'{tool_name}'라는 이름의 도구를 찾을 수 없습니다.")

        # 사용자의 요청을 도구의 입력으로 사용하여 호출합니다.
        # 참고: 더 복잡한 시나리오에서는 LLM이 생성한 입력을 사용할 수 있습니다.
        tool_output = chosen_tool.invoke(state["user_request"])

        return {"tool_output": str(tool_output)}

    def simple_llm_call(self, state: AgentState) -> Dict[str, Any]:
        """
        도구 호출 없이 LLM을 직접 호출하여 블로그 초안을 수정합니다.
        사용자의 요청이 간단한 텍스트 수정일 경우 사용됩니다.
        """
        # TODO: 프롬프트는 prompts.yaml에서 불러오도록 수정해야 합니다.
        prompt = f"""
        당신은 전문 블로그 에디터입니다.
        아래의 초안을 사용자의 요청에 맞게 수정해주세요.
        수정된 전체 초안을 반환해야 합니다. 다른 설명은 추가하지 마세요.

        [현재 초안]
        {state['draft']}

        [사용자 요청]
        {state['user_request']}
        """

        response = self.llm.invoke(prompt)
        return {"draft": response.content}

    def update_draft_after_tool_call(self, state: AgentState) -> Dict[str, Any]:
        """
        도구 호출 결과를 사용하여 블로그 초안을 업데이트합니다.
        """
        # TODO: 프롬프트는 prompts.yaml에서 불러오도록 수정해야 합니다.
        prompt = f"""
        당신은 전문 블로그 에디터입니다.
        아래의 초안과 도구 실행 결과를 참고하여 사용자의 요청에 맞게 초안을 수정해주세요.
        수정된 전체 초안을 반환해야 합니다. 다른 설명은 추가하지 마세요.

        [현재 초안]
        {state['draft']}

        [도구 실행 결과]
        {state['tool_output']}

        [사용자 요청]
        {state['user_request']}
        """
        response = self.llm.invoke(prompt)
        return {"draft": response.content}

    def router(self, state: AgentState) -> str:
        """
        사용자의 요청을 분석하여 다음에 실행할 노드를 결정하는 조건부 엣지입니다.
        LLM을 사용하여 요청을 분류하고, 다음 노드의 이름을 반환합니다.
        """
        tool_names = ", ".join(self.tools_map.keys())
        routing_prompt = f"""
        당신은 사용자 요청의 의도를 파악하여 다음에 어떤 작업을 수행해야 할지 결정하는 라우터입니다.
        사용자의 요청이 다음 도구 중 하나를 사용하여 답변할 수 있는 질문이라면 해당 도구의 이름을 반환하세요.
        - 사용 가능한 도구: [{tool_names}]
        - 만약 사용자의 요청이 단순히 초안을 수정하거나 다시 작성하는 것이라면 "rewrite"라고 반환하세요.

        [대화 기록]
        {state['chat_history']}

        [사용자 요청]
        {state['user_request']}
        """
        response = self.llm.invoke(routing_prompt)
        route = response.content.strip()

        if route == "rewrite":
            return "simple_llm_call"
        elif route in self.tools_map:
            return "call_tools"
        else:
            return "simple_llm_call" # 안전 장치

    def build(self) -> Runnable:
        """
        모든 노드와 엣지를 연결하여 실행 가능한 LangGraph를 구성하고 컴파일합니다.
        """
        graph = StateGraph(AgentState)

        # --- 노드 추가 ---
        graph.add_node("router", self.router)
        graph.add_node("simple_llm_call", self.simple_llm_call)
        graph.add_node("call_tools", self.call_tools)
        graph.add_node("update_draft_after_tool_call", self.update_draft_after_tool_call)

        # --- 엣지 연결 ---
        graph.set_entry_point("router")

        # 라우터의 결정에 따라 분기합니다.
        graph.add_conditional_edges(
            "router",
            lambda state: state["route"],
            {
                "rewrite": "simple_llm_call",
                **{tool_name: "call_tools" for tool_name in self.tools_map},
            },
        )
        
        # 단순 LLM 호출 후에는 그래프를 종료합니다.
        graph.add_edge("simple_llm_call", END)
        # 도구 호출 후에는 초안을 업데이트하는 노드로 이동합니다.
        graph.add_edge("call_tools", "update_draft_after_tool_call")
        # 초안 업데이트 후에는 그래프를 종료합니다.
        graph.add_edge("update_draft_after_tool_call", END)
        
        # 그래프를 컴파일하여 실행 가능한 형태로 만듭니다.
        return graph.compile()


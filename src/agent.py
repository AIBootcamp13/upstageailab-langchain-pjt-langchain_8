from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class BlogContentAgent:
    LLM_MODEL = "gpt-5-nano"

    def __init__(self, retriever):
        self.retriever = retriever
        self.llm = ChatOpenAI(model=self.LLM_MODEL)
        self.draft_prompt_template = ChatPromptTemplate.from_template(self._load_prompt_for_draft())
        self.update_prompt_template = ChatPromptTemplate.from_template(self._load_prompt_for_update())
        self.output_parser = StrOutputParser()

    def generate_draft(self) -> str:
        chain = self.draft_prompt_template | self.llm | self.output_parser
        return chain.invoke({"content": self.retriever | self.format_docs})

    def update_blog_post(self, blog_post: str, user_request: str) -> str:
        chain = self.update_prompt_template | self.llm | self.output_parser
        return chain.invoke({"current_content": blog_post, "user_request": user_request})

    @staticmethod
    def format_docs(documents: list[Document]) -> str:
        return "\n\n".join(doc.page_content for doc in documents)

    @staticmethod
    def _load_prompt_for_draft() -> str:
        return """[Identity]
        당신은 전문 블로그 작가입니다.
        제공된 자료를 바탕으로 고품질의 블로그 포스트를 작성합니다.

        [Source Material]
        {content}

        [Instructions]
        1. 자료의 핵심 내용을 파악하여 적절한 제목을 만드세요
        2. 도입부에서 독자의 관심을 끌어주세요
        3. 본문은 논리적으로 구성하세요
        4. 결론에서 핵심을 요약하세요
        5. Markdown 형식으로 작성하세요
        6. 자료의 내용을 충실히 반영하되, 블로그 독자에게 맞게 재구성하세요

        블로그 포스트를 작성해주세요:
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

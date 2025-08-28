from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory

from langchain_openai import ChatOpenAI

from src.config import (
    LLM_PROVIDER,
    LLM_MODEL,
    DRAFT_PROMPT_TEMPLATE,
    UPDATE_PROMPT_TEMPLATE,
)


class BlogContentAgent:
    """
    검색된 컨텍스트를 바탕으로 블로그 초안을 생성하고,
    대화형 메모리를 사용하여 사용자의 요청에 따라 수정하는 에이전트 클래스.
    """

    def __init__(
        self,
        retriever,
        memory: ConversationSummaryBufferMemory | None = None,
        processed_docs: list[Document] | None = None,
    ):
        self.retriever = retriever
        self.memory = memory
        self.processed_docs = processed_docs

        # initialize LLM
        if LLM_PROVIDER == "openai":
            self.llm = ChatOpenAI(model=LLM_MODEL)
        elif LLM_PROVIDER == "ollama":
            self.llm = ChatOllama(model=LLM_MODEL)
        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

        # draft generation chain
        self.draft_prompt_template = ChatPromptTemplate.from_template(DRAFT_PROMPT_TEMPLATE)
        self.output_parser = StrOutputParser()
        self.draft_chain = self.draft_prompt_template | self.llm | self.output_parser

        # update chain setup (use ConversationChain when memory is provided)
        self.update_prompt_template = PromptTemplate.from_template(UPDATE_PROMPT_TEMPLATE)
        if self.memory is not None:
            # ensure output_key matches expectation of update prompt handling
            self.update_chain = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                prompt=self.update_prompt_template,
                verbose=True,
                output_key="output",
            )
        else:
            self.update_chain = None

    def generate_draft(self) -> str:
        """Generate a blog draft using processed_docs (if provided) or retriever results."""
        docs = None
        if getattr(self, "processed_docs", None):
            docs = self.processed_docs

        if docs is None and self.retriever is not None:
            try:
                if hasattr(self.retriever, "get_relevant_documents"):
                    try:
                        docs = self.retriever.get_relevant_documents()
                    except TypeError:
                        docs = self.retriever.get_relevant_documents("")
                elif hasattr(self.retriever, "get_documents"):
                    docs = self.retriever.get_documents()
                elif hasattr(self.retriever, "retrieve"):
                    try:
                        docs = self.retriever.retrieve()
                    except TypeError:
                        docs = self.retriever.retrieve("")
            except Exception:
                docs = None

        if docs is None:
            # fallback: attempt to run a runnable pipeline if retriever supports it
            try:
                chain = (
                    self.retriever
                    | self.format_docs
                    | {"content": RunnablePassthrough()}
                    | self.draft_prompt_template
                    | self.llm
                    | self.output_parser
                )
                return chain.invoke("")
            except Exception:
                docs = []

        content = self.format_docs(docs or [])
        draft = self.draft_chain.invoke({"content": content})

        # If memory is present, persist the generated draft into memory so future updates can reference it.
        try:
            if getattr(self, "memory", None) is not None and hasattr(self.memory, "save_context"):
                # store a minimal context indicating the generated draft
                self.memory.save_context({"input": "generate_draft"}, {"output": draft})
        except Exception:
            # memory saving is best-effort; do not fail draft generation if memory saving errors
            pass

        return draft

    def update_blog_post(self, *args, **kwargs) -> str:
        """Update blog post using ConversationChain when memory exists, otherwise fall back to stateless flow.

        Supports two call patterns:
        - update_blog_post(user_request)
        - update_blog_post(current_blog_post, user_request)
        """
        user_request = None
        blog_post = None
        if len(args) == 1:
            user_request = args[0]
        elif len(args) >= 2:
            blog_post, user_request = args[0], args[1]
        else:
            user_request = kwargs.get("user_request")
            blog_post = kwargs.get("blog_post")

        if getattr(self, "update_chain", None) is not None:
            # Provide the current blog post + user's request together as the 'input'
            # so the update prompt has the full content to edit.
            combined_input = (
                f"Current blog post:\n{blog_post or ''}\n\nUser request:\n{user_request or ''}"
            )
            result = self.update_chain.invoke({"input": combined_input})

            # Normalize result
            updated = None
            if isinstance(result, dict):
                updated = result.get("output") or result.get("text")
            else:
                updated = result

            # Persist the update into memory if available (best-effort)
            try:
                if getattr(self, "memory", None) is not None and hasattr(self.memory, "save_context"):
                    self.memory.save_context({"input": combined_input}, {"output": updated})
            except Exception:
                pass

            return updated or ""

        # For stateless updates, the update prompt expects {input} (and {history} when memory exists).
        # Build a combined 'input' value that contains the current blog post and the user's request so
        # the prompt has the necessary context to perform an edit.
        combined_input = (
            f"Current blog post:\n{blog_post or ''}\n\nUser request:\n{user_request or ''}"
        )

        chain = self.update_prompt_template | self.llm | self.output_parser
        result = chain.invoke({"input": combined_input})

        # The runnable pipeline may return a mapping or a string depending on the LLM wrapper; normalize.
        if isinstance(result, dict):
            return result.get("output") or result.get("text") or ""
        return result

    @staticmethod
    def format_docs(documents: list[Document]) -> str:
        """Combine a list of Document objects into a single string."""
        return "\n\n".join(doc.page_content for doc in documents)

